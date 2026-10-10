"""Parcours Web de préparation et de confirmation des campagnes."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse

from perfcomparatorweb.http_client.pce_client import PCEContractError
from perfcomparatorweb.http_client.schemas import CampaignRequest

router = APIRouter()


def _upstream_error(error: httpx.HTTPError) -> JSONResponse:
    if isinstance(error, PCEContractError):
        return JSONResponse(
            status_code=502,
            content={
                "error": "pce_contract_error",
                "message": "La réponse de PCE est incompatible.",
            },
        )
    if isinstance(error, httpx.HTTPStatusError):
        upstream_status = error.response.status_code
        if upstream_status == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "task_not_found",
                    "message": "Cette campagne n’existe plus dans PCE.",
                },
            )
        if upstream_status == 409:
            try:
                code = error.response.json().get("error", {}).get("code")
            except ValueError, AttributeError:
                code = None
            return JSONResponse(
                status_code=409,
                content={
                    "error": code if code == "engine_busy" else "campaign_conflict",
                    "message": (
                        "Une campagne est déjà en cours. Attendez sa fin avant de continuer."
                        if code == "engine_busy"
                        else "La demande de campagne est en conflit avec son état actuel."
                    ),
                },
            )
        if upstream_status == 422:
            return JSONResponse(
                status_code=422,
                content={
                    "error": "invalid_campaign",
                    "message": "La sélection de campagne est invalide.",
                },
            )
        return JSONResponse(
            status_code=502,
            content={"error": "pce_rejected_request", "message": "PCE n’a pas accepté la demande."},
        )
    return JSONResponse(
        status_code=503,
        content={
            "error": "engine_unavailable",
            "message": "PCE est indisponible. Vérifiez que le moteur est démarré, puis réessayez.",
        },
    )


@router.get("/campaigns/new", response_class=HTMLResponse, name="new_campaign")
async def new_campaign(request: Request) -> HTMLResponse:
    try:
        catalog = await request.app.state.read_only_service.benchmarks()
    except httpx.HTTPError:
        return request.app.state.templates.TemplateResponse(
            request,
            "error.html",
            {
                "message": "PCE est indisponible. Vérifiez que le moteur est démarré, puis réessayez.",
                "status_code": 503,
            },
            status_code=503,
        )
    return request.app.state.templates.TemplateResponse(
        request,
        "campaign_new.html",
        {"catalog": catalog},
    )


@router.post("/api/campaigns/readiness")
async def campaign_readiness(
    campaign: CampaignRequest,
    request: Request,
) -> JSONResponse:
    del campaign  # Valide la sélection avant le contrôle préalable ; PCE ne reçoit aucun choix ici.
    try:
        result = await request.app.state.campaign_service.readiness()
    except httpx.HTTPError as error:
        return _upstream_error(error)
    return JSONResponse(content=result)


@router.post("/api/campaigns")
async def create_campaign(
    campaign: CampaignRequest,
    request: Request,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=200,
        pattern=r"^[A-Za-z0-9._:-]+$",
    ),
) -> JSONResponse:
    try:
        result = await request.app.state.campaign_service.create(
            campaign,
            idempotency_key=idempotency_key,
        )
    except httpx.HTTPError as error:
        return _upstream_error(error)
    return JSONResponse(status_code=202 if result["created"] else 200, content=result)


@router.get("/api/campaigns/{task_id}")
async def get_campaign(task_id: str, request: Request) -> JSONResponse:
    try:
        task = await request.app.state.campaign_service.task(task_id)
    except httpx.HTTPError as error:
        return _upstream_error(error)
    return JSONResponse(content=task)


@router.get("/api/campaigns/{task_id}/events")
async def campaign_events(task_id: str, request: Request) -> Response:
    try:
        upstream = await request.app.state.campaign_service.open_events(
            task_id,
            last_event_id=request.headers.get("last-event-id"),
        )
    except httpx.HTTPError as error:
        return _upstream_error(error)

    async def stream() -> AsyncIterator[bytes]:
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        finally:
            await upstream.aclose()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

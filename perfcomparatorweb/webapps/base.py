"""Pages de consultation locale de PCWEB."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from perfcomparatorweb.http_client.pce_client import PCEContractError

router = APIRouter()


def _error_page(request: Request, error: httpx.HTTPError) -> HTMLResponse:
    if isinstance(error, PCEContractError):
        status_code = 502
        message = (
            "PCE a renvoyé un format incompatible. Vérifiez que PCE et PCWEB sont à jour, "
            "puis relancez les serveurs."
        )
    elif isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 404:
        status_code = 404
        message = "Cette ressource n’existe pas ou n’est plus disponible."
    else:
        status_code = 503
        message = "PCE est indisponible. Vérifiez que le moteur est démarré, puis réessayez."
    return request.app.state.templates.TemplateResponse(
        request,
        "error.html",
        {"message": message, "status_code": status_code},
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request) -> HTMLResponse:
    try:
        inventory = await request.app.state.read_only_service.system()
    except httpx.RequestError:
        status = {
            "web": "available",
            "engine": "unavailable",
            "detail": "PCE est indisponible. Vérifiez que le moteur est démarré, puis réessayez.",
        }
        return request.app.state.templates.TemplateResponse(
            request,
            "index.html",
            {"inventory": None, "status": status},
        )
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return request.app.state.templates.TemplateResponse(
        request,
        "index.html",
        {"inventory": inventory},
    )


@router.get("/benchmarks", response_class=HTMLResponse, name="benchmarks")
async def benchmarks(request: Request) -> HTMLResponse:
    try:
        catalog = await request.app.state.read_only_service.benchmarks()
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return request.app.state.templates.TemplateResponse(
        request,
        "benchmarks.html",
        {"catalog": catalog},
    )


@router.get("/benchmarks/{benchmark_id}", response_class=HTMLResponse, name="benchmark")
async def benchmark(request: Request, benchmark_id: str) -> HTMLResponse:
    try:
        details = await request.app.state.read_only_service.benchmark(benchmark_id)
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return request.app.state.templates.TemplateResponse(
        request,
        "benchmark.html",
        {"benchmark": details},
    )


@router.get("/reports", response_class=HTMLResponse, name="reports")
async def reports(
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> HTMLResponse:
    try:
        page = await request.app.state.read_only_service.reports(offset=offset, limit=limit)
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return request.app.state.templates.TemplateResponse(
        request,
        "reports.html",
        {"page": page},
    )


@router.get("/reports/{report_id}", response_class=HTMLResponse, name="report")
async def report(request: Request, report_id: str) -> HTMLResponse:
    try:
        details = await request.app.state.read_only_service.report(report_id)
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return request.app.state.templates.TemplateResponse(
        request,
        "report.html",
        {"report": details},
    )


@router.get("/health", name="health")
async def health() -> dict[str, str]:
    return {"status": "ok", "component": "pcweb"}

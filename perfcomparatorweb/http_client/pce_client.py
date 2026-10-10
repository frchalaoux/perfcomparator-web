"""Client HTTP partagé pour les appels PCWEB vers PCE."""

from __future__ import annotations

from typing import TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from perfcomparatorweb.http_client import schemas

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class PCEContractError(httpx.HTTPError):
    """PCE returned a payload that does not match the v1 client contract."""


class PCEClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(5.0, connect=1.0),
            headers={"Authorization": f"Bearer {token}"} if token else {},
            trust_env=False,
        )

    async def _get(
        self,
        path: str,
        response_model: type[ResponseModel],
        *,
        params: dict[str, int] | None = None,
    ) -> dict[str, object]:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        try:
            payload = response_model.model_validate(response.json())
        except (ValidationError, TypeError, ValueError) as error:
            raise PCEContractError(f"Réponse PCE incompatible pour {path}.") from error
        return payload.model_dump(mode="json")

    async def _post(
        self,
        path: str,
        response_model: type[ResponseModel],
        *,
        payload: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        if payload is None:
            response = await self._client.post(path, headers=headers)
        else:
            response = await self._client.post(path, json=payload, headers=headers)
        response.raise_for_status()
        try:
            parsed = response_model.model_validate(response.json())
        except (ValidationError, TypeError, ValueError) as error:
            raise PCEContractError(f"Réponse PCE incompatible pour {path}.") from error
        return parsed.model_dump(mode="json")

    async def health(self) -> dict[str, object]:
        return await self._get("/api/v1/health", schemas.HealthResponse)

    async def system(self) -> dict[str, object]:
        return await self._get("/api/v1/system", schemas.SystemEnvelope)

    async def benchmarks(self) -> dict[str, object]:
        return await self._get("/api/v1/benchmarks", schemas.BenchmarkCatalog)

    async def benchmark(self, benchmark_id: str) -> dict[str, object]:
        path = f"/api/v1/benchmarks/{quote(benchmark_id, safe='')}"
        return await self._get(path, schemas.BenchmarkDetail)

    async def reports(self, *, offset: int = 0, limit: int = 20) -> dict[str, object]:
        return await self._get(
            "/api/v1/reports",
            schemas.ReportPage,
            params={"offset": offset, "limit": limit},
        )

    async def report(self, report_id: str) -> dict[str, object]:
        path = f"/api/v1/reports/{quote(report_id, safe='')}"
        return await self._get(path, schemas.ReportDetail)

    async def readiness(self) -> dict[str, object]:
        return await self._post("/api/v1/readiness", schemas.CampaignReadiness)

    async def create_campaign(
        self,
        campaign: schemas.CampaignRequest,
        *,
        idempotency_key: str,
    ) -> dict[str, object]:
        return await self._post(
            "/api/v1/runs",
            schemas.CampaignSubmission,
            payload=campaign.model_dump(mode="json"),
            headers={"Idempotency-Key": idempotency_key},
        )

    async def campaign(self, task_id: str) -> dict[str, object]:
        path = f"/api/v1/jobs/{quote(task_id, safe='')}"
        return await self._get(path, schemas.CampaignTask)

    async def open_campaign_events(
        self,
        task_id: str,
        *,
        last_event_id: str | None = None,
    ) -> httpx.Response:
        path = f"/api/v1/jobs/{quote(task_id, safe='')}/events"
        headers = {"Last-Event-ID": last_event_id} if last_event_id is not None else None
        request = self._client.build_request(
            "GET",
            path,
            headers=headers,
            timeout=httpx.Timeout(30.0, connect=1.0),
        )
        response = await self._client.send(request, stream=True)
        try:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";", 1)[0]
            if content_type.strip().lower() != "text/event-stream":
                raise PCEContractError("PCE n’a pas renvoyé un flux d’événements.")
        except BaseException:
            await response.aclose()
            raise
        return response

    async def close(self) -> None:
        await self._client.aclose()

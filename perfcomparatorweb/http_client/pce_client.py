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

    async def close(self) -> None:
        await self._client.aclose()

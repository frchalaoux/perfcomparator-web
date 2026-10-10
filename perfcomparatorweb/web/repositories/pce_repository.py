"""Repository HTTP vers l'API versionnée de PCE."""

import httpx

from perfcomparatorweb.http_client.pce_client import PCEClient
from perfcomparatorweb.http_client.schemas import CampaignRequest


class PCERepository:
    def __init__(self, client: PCEClient) -> None:
        self._client = client

    async def health(self) -> dict[str, object]:
        return await self._client.health()

    async def system(self) -> dict[str, object]:
        return await self._client.system()

    async def benchmarks(self) -> dict[str, object]:
        return await self._client.benchmarks()

    async def benchmark(self, benchmark_id: str) -> dict[str, object]:
        return await self._client.benchmark(benchmark_id)

    async def reports(self, *, offset: int = 0, limit: int = 20) -> dict[str, object]:
        return await self._client.reports(offset=offset, limit=limit)

    async def report(self, report_id: str) -> dict[str, object]:
        return await self._client.report(report_id)

    async def readiness(self) -> dict[str, object]:
        return await self._client.readiness()

    async def create_campaign(
        self,
        campaign: CampaignRequest,
        *,
        idempotency_key: str,
    ) -> dict[str, object]:
        return await self._client.create_campaign(campaign, idempotency_key=idempotency_key)

    async def campaign(self, task_id: str) -> dict[str, object]:
        return await self._client.campaign(task_id)

    async def open_campaign_events(
        self, task_id: str, *, last_event_id: str | None
    ) -> httpx.Response:
        return await self._client.open_campaign_events(task_id, last_event_id=last_event_id)

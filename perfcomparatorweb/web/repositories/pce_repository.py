"""Repository HTTP vers l'API versionnée de PCE."""

from perfcomparatorweb.http_client.pce_client import PCEClient


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

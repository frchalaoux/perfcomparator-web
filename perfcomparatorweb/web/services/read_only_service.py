"""Cas d’usage de consultation du moteur PCE."""

from perfcomparatorweb.web.repositories.pce_repository import PCERepository


class ReadOnlyService:
    def __init__(self, pce: PCERepository) -> None:
        self._pce = pce

    async def system(self) -> dict[str, object]:
        return await self._pce.system()

    async def benchmarks(self) -> dict[str, object]:
        return await self._pce.benchmarks()

    async def benchmark(self, benchmark_id: str) -> dict[str, object]:
        return await self._pce.benchmark(benchmark_id)

    async def reports(self, *, offset: int = 0, limit: int = 20) -> dict[str, object]:
        return await self._pce.reports(offset=offset, limit=limit)

    async def report(self, report_id: str) -> dict[str, object]:
        return await self._pce.report(report_id)

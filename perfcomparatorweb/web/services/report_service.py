"""Cas d’usage de correction des métadonnées d’un rapport."""

from perfcomparatorweb.web.repositories.pce_repository import PCERepository


class ReportService:
    def __init__(self, pce: PCERepository) -> None:
        self._pce = pce

    async def update_machine_metadata(
        self,
        report_id: str,
        *,
        model: str,
        model_year: int | None,
        product_sku: str | None,
    ) -> dict[str, object]:
        return await self._pce.update_report_machine(
            report_id,
            model=model,
            model_year=model_year,
            product_sku=product_sku,
        )

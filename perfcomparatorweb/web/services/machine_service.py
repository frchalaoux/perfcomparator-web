"""Cas d’usage de correction des propriétés locales de la machine."""

from perfcomparatorweb.web.repositories.pce_repository import PCERepository


class MachineService:
    def __init__(self, pce: PCERepository) -> None:
        self._pce = pce

    async def update_metadata(
        self,
        *,
        model: str,
        model_year: int | None,
        product_sku: str | None,
    ) -> dict[str, object]:
        return await self._pce.update_machine_metadata(
            model=model,
            model_year=model_year,
            product_sku=product_sku,
        )

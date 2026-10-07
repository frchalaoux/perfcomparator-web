"""Service de diagnostic de connexion entre PCWEB et PCE."""

import httpx

from perfcomparatorweb.web.repositories.pce_repository import PCERepository


class StatusService:
    def __init__(self, pce: PCERepository) -> None:
        self._pce = pce

    async def get_status(self) -> dict[str, object]:
        try:
            engine = await self._pce.health()
        except httpx.HTTPError as error:
            return {"web": "available", "engine": "unavailable", "detail": str(error)}
        return {"web": "available", "engine": engine.get("status", "unknown")}

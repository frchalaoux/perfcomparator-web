"""Repository HTTP vers l'API versionnée de PCE."""

from perfcomparatorweb.http_client.pce_client import PCEClient


class PCERepository:
    def __init__(self, client: PCEClient) -> None:
        self._client = client

    async def health(self) -> dict[str, object]:
        return await self._client.health()

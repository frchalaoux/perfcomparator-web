"""Client HTTP partagé pour les appels PCWEB vers PCE."""

from __future__ import annotations

import httpx


class PCEClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(5.0, connect=1.0),
            headers={"Authorization": f"Bearer {token}"} if token else {},
            trust_env=False,
        )

    async def health(self) -> dict[str, object]:
        response = await self._client.get("/api/v1/health")
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

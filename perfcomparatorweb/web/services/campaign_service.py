"""Cas d’usage de préparation et de création d’une campagne."""

import httpx

from perfcomparatorweb.http_client.schemas import CampaignRequest
from perfcomparatorweb.web.repositories.pce_repository import PCERepository


class CampaignService:
    def __init__(self, pce: PCERepository) -> None:
        self._pce = pce

    async def readiness(self) -> dict[str, object]:
        return await self._pce.readiness()

    async def create(self, campaign: CampaignRequest, *, idempotency_key: str) -> dict[str, object]:
        return await self._pce.create_campaign(campaign, idempotency_key=idempotency_key)

    async def task(self, task_id: str) -> dict[str, object]:
        return await self._pce.campaign(task_id)

    async def open_events(self, task_id: str, *, last_event_id: str | None) -> httpx.Response:
        return await self._pce.open_campaign_events(task_id, last_event_id=last_event_id)

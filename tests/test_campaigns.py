from fastapi.testclient import TestClient

from perfcomparatorweb import app as app_module
from perfcomparatorweb.app import create_app
from perfcomparatorweb.core.config import Settings

CAMPAIGN = {
    "profile": "quick",
    "benchmark_ids": ["cpu.integer"],
    "repetitions": 2,
    "label": "Avant mise à niveau",
}
IDEMPOTENCY_KEY = "campaign-web-0001"


class FakePCEClient:
    def __init__(self, *_args, **_kwargs):
        self.readiness_calls = 0
        self.campaigns = []
        self.event_stream_requests = []

    async def close(self):
        pass

    async def benchmarks(self):
        return {
            "benchmarks": [
                {
                    "benchmark_id": "cpu.integer",
                    "group": "cpu",
                    "name": "Entiers mono-cœur",
                    "description": "Mesure entière courte.",
                }
            ],
            "groups": [{"group_id": "cpu", "benchmark_ids": ["cpu.integer"]}],
            "profiles": [
                {
                    "profile_id": "quick",
                    "duration_seconds": 10,
                    "memory_size_bytes": 1024,
                    "disk_size_bytes": 1024,
                    "random_operations": 10,
                    "sqlite_rows": 10,
                }
            ],
        }

    async def readiness(self):
        self.readiness_calls += 1
        return {
            "sample_seconds": 1,
            "cpu_percent": 18,
            "memory_available_percent": 42,
            "memory_available_bytes": 4_200_000,
            "swap_percent": 0,
            "active_processes": [{"name": "browser", "cpu_percent": 12, "memory_percent": 8}],
            "warnings": ["Charge CPU initiale élevée (18.0 %)."],
            "suitable": False,
        }

    async def create_campaign(self, campaign, *, idempotency_key):
        self.campaigns.append((campaign.model_dump(mode="json"), idempotency_key))
        return {
            "task": {
                "task_id": "task-123",
                "status": "queued",
                "created_at": "2026-10-09T12:00:00Z",
                "started_at": None,
                "finished_at": None,
                "request": CAMPAIGN,
                "current_benchmark": None,
                "completed_benchmarks": 0,
                "total_benchmarks": 1,
                "report_id": None,
                "error_code": None,
            },
            "created": True,
        }

    async def campaign(self, task_id):
        assert task_id == "task-123"
        return {
            "task_id": task_id,
            "status": "running",
            "created_at": "2026-10-09T12:00:00Z",
            "started_at": "2026-10-09T12:00:01Z",
            "finished_at": None,
            "request": CAMPAIGN,
            "current_benchmark": "cpu.integer",
            "completed_benchmarks": 0,
            "total_benchmarks": 1,
            "report_id": None,
            "error_code": None,
        }

    async def open_campaign_events(self, task_id, *, last_event_id):
        self.event_stream_requests.append((task_id, last_event_id))

        class EventStream:
            async def aiter_bytes(self):
                yield b"id: 1\nevent: started\ndata: {}\n\n"

            async def aclose(self):
                pass

        return EventStream()


def test_campaign_page_places_preflight_before_explicit_confirmation(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "PCEClient", FakePCEClient)
    with TestClient(create_app(Settings()), base_url="http://127.0.0.1") as client:
        response = client.get("/campaigns/new")

    assert response.status_code == 200
    assert "Vérifier la préparation" in response.text
    assert "Conditions de mesure" in response.text
    assert "J’ai pris connaissance de ces conditions" in response.text
    assert "Confirmer et lancer la campagne" in response.text
    assert 'fetch("/api/campaigns/readiness"' in response.text
    assert 'fetch("/api/campaigns"' in response.text


def test_readiness_and_confirmation_are_forwarded_to_pce(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "PCEClient", FakePCEClient)
    with TestClient(create_app(Settings()), base_url="http://127.0.0.1") as client:
        readiness = client.post("/api/campaigns/readiness", json=CAMPAIGN)
        launched = client.post(
            "/api/campaigns",
            json=CAMPAIGN,
            headers={"Idempotency-Key": IDEMPOTENCY_KEY},
        )
        pce_client = client.app.state.pce_client

    assert readiness.status_code == 200
    assert readiness.json()["warnings"] == ["Charge CPU initiale élevée (18.0 %)."]
    assert readiness.json()["active_processes"][0]["name"] == "browser"
    assert launched.status_code == 202
    assert launched.json()["task"]["task_id"] == "task-123"
    assert pce_client.readiness_calls == 1
    assert pce_client.campaigns == [(CAMPAIGN, IDEMPOTENCY_KEY)]


def test_campaign_api_rejects_empty_benchmark_selection(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "PCEClient", FakePCEClient)
    with TestClient(create_app(Settings()), base_url="http://127.0.0.1") as client:
        response = client.post(
            "/api/campaigns/readiness",
            json={**CAMPAIGN, "benchmark_ids": []},
        )

    assert response.status_code == 422


def test_campaign_status_and_sse_are_proxied_to_pce(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "PCEClient", FakePCEClient)
    with TestClient(create_app(Settings()), base_url="http://127.0.0.1") as client:
        status = client.get("/api/campaigns/task-123")
        events = client.get(
            "/api/campaigns/task-123/events",
            headers={"Last-Event-ID": "4"},
        )
        pce_client = client.app.state.pce_client

    assert status.status_code == 200
    assert status.json()["current_benchmark"] == "cpu.integer"
    assert events.status_code == 200
    assert events.headers["content-type"].startswith("text/event-stream")
    assert "event: started" in events.text
    assert pce_client.event_stream_requests == [("task-123", "4")]

import asyncio

from perfcomparatorweb.http_client import pce_client, schemas


def test_pce_client_posts_readiness_and_idempotent_campaign_request(monkeypatch) -> None:
    calls = []

    class Response:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            calls.append(("init", kwargs))

        async def post(self, path, **kwargs):
            calls.append((path, kwargs))
            if path.endswith("readiness"):
                return Response(
                    {
                        "sample_seconds": 1,
                        "cpu_percent": 8,
                        "memory_available_percent": 70,
                        "memory_available_bytes": 7_000_000,
                        "swap_percent": 0,
                        "active_processes": [],
                        "warnings": [],
                        "suitable": True,
                    }
                )
            return Response(
                {
                    "task": {
                        "task_id": "task-123",
                        "status": "queued",
                        "created_at": "2026-10-09T12:00:00Z",
                        "started_at": None,
                        "finished_at": None,
                        "request": {
                            "profile": "quick",
                            "benchmark_ids": ["cpu.integer"],
                            "repetitions": 2,
                            "label": "Test",
                        },
                        "current_benchmark": None,
                        "completed_benchmarks": 0,
                        "total_benchmarks": 1,
                        "report_id": None,
                        "error_code": None,
                    },
                    "created": True,
                }
            )

        async def aclose(self):
            pass

    monkeypatch.setattr(pce_client.httpx, "AsyncClient", FakeAsyncClient)

    async def exercise_client():
        client = pce_client.PCEClient("http://127.0.0.1:8765", "engine-token")
        readiness = await client.readiness()
        campaign = await client.create_campaign(
            schemas.CampaignRequest(
                profile="quick",
                benchmark_ids=["cpu.integer"],
                repetitions=2,
                label="Test",
            ),
            idempotency_key="campaign-web-0001",
        )
        await client.close()
        return readiness, campaign

    readiness, campaign = asyncio.run(exercise_client())

    assert readiness["suitable"] is True
    assert campaign["task"]["task_id"] == "task-123"
    assert calls[1][0] == "/api/v1/readiness"
    assert "json" not in calls[1][1]
    create_path, create_options = calls[2]
    assert create_path == "/api/v1/runs"
    assert create_options["json"] == {
        "profile": "quick",
        "benchmark_ids": ["cpu.integer"],
        "repetitions": 2,
        "label": "Test",
    }
    assert create_options["headers"]["Idempotency-Key"] == "campaign-web-0001"

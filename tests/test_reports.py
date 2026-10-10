from fastapi.testclient import TestClient

from perfcomparatorweb import app as app_module
from perfcomparatorweb.app import create_app
from perfcomparatorweb.core.config import Settings

REFERENCE_ID = f"sha256:{'a' * 64}"
CANDIDATE_ID = f"sha256:{'b' * 64}"


def _summary(report_id: str, label: str) -> dict[str, object]:
    return {
        "report_id": report_id,
        "recorded_at": "2026-10-01T12:00:00Z",
        "label": label,
        "profile": "quick",
        "repetitions": 3,
        "machine": label,
        "suite_version": "0.5.0",
        "protocol_version": "0.3.0",
        "result_count": 1,
        "failure_count": 0,
    }


def _machine(report_id: str, label: str, index: float) -> dict[str, object]:
    return {
        "report_id": report_id,
        "label": label,
        "recorded_at": "2026-10-01T12:00:00Z",
        "profile": "quick",
        "system": {
            "system": "Darwin",
            "release": "25.0",
            "machine": "arm64",
            "model": "TestModel",
            "manufacturer": "Test",
            "product_name": label,
            "processor": "Test CPU",
            "physical_cpu_count": 8,
            "logical_cpu_count": 8,
            "memory_bytes": 16 * 1_073_741_824,
            "gpu_devices": ["Test GPU"],
        },
        "overall_index": index,
        "categories": {"cpu": index},
        "scenarios": {"quotidien": index},
        "narrative": f"Résumé {label}",
        "metrics": {
            "cpu.integer": {
                "benchmark_id": "cpu.integer",
                "name": "Entiers mono-cœur",
                "group": "cpu",
                "value": index / 10,
                "unit": "Mop/s",
                "index": index,
                "difference_percent": index - 100,
                "conclusion": "différence légère",
                "uncertainty": "plages min–max séparées",
                "spread_percent": 2.0,
            }
        },
    }


class FakePCEClient:
    def __init__(self, *_args, **_kwargs):
        self.comparison_calls = []

    async def close(self):
        pass

    async def reports(self, *, offset: int = 0, limit: int = 20):
        reports = [_summary(REFERENCE_ID, "Machine référence"), _summary(CANDIDATE_ID, "Machine candidate")]
        return {
            "reports": reports[offset : offset + limit],
            "offset": offset,
            "limit": limit,
            "total": len(reports),
            "warnings": [],
        }

    async def compare_reports(self, report_ids, *, reference_report_id):
        self.comparison_calls.append((report_ids, reference_report_id))
        ordered = [reference_report_id] + [item for item in report_ids if item != reference_report_id]
        labels = {REFERENCE_ID: "Machine référence", CANDIDATE_ID: "Machine candidate"}
        indices = {REFERENCE_ID: 100.0, CANDIDATE_ID: 125.0}
        return {
            "baseline_report_id": reference_report_id,
            "baseline_label": labels[reference_report_id],
            "common_benchmarks": ["cpu.integer"],
            "scenario_weights": {"quotidien": 1.0},
            "warnings": ["Moins de trois passages : la dispersion est peu représentative."],
            "machines": [
                _machine(report_id, labels[report_id], indices[report_id])
                for report_id in ordered
            ],
        }


def test_comparison_page_sends_selection_and_reference_to_pce(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "PCEClient", FakePCEClient)
    with TestClient(create_app(Settings()), base_url="http://127.0.0.1") as client:
        response = client.get(
            "/compare",
            params=[
                ("report_id", CANDIDATE_ID),
                ("report_id", REFERENCE_ID),
                ("reference_report_id", REFERENCE_ID),
            ],
        )
        pce_client = client.app.state.pce_client

    assert response.status_code == 200
    assert pce_client.comparison_calls == [([CANDIDATE_ID, REFERENCE_ID], REFERENCE_ID)]
    assert "Résultat de la comparaison" in response.text
    assert "Machine référence" in response.text
    assert "Machine candidate" in response.text
    assert "Indice global" in response.text
    assert "Entiers mono-cœur" in response.text
    assert "dispersion est peu représentative" in response.text


def test_comparison_page_requires_two_selected_reports(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "PCEClient", FakePCEClient)
    with TestClient(create_app(Settings()), base_url="http://127.0.0.1") as client:
        response = client.get("/compare", params={"report_id": REFERENCE_ID})
        pce_client = client.app.state.pce_client

    assert response.status_code == 200
    assert "Sélectionnez au moins deux rapports" in response.text
    assert pce_client.comparison_calls == []

from fastapi.testclient import TestClient

from perfcomparatorweb.app import create_app
from perfcomparatorweb.core.config import Settings


def test_health_is_local_and_reports_component() -> None:
    with TestClient(create_app(Settings()), base_url="http://127.0.0.1") as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "component": "pcweb"}


def test_untrusted_host_is_rejected() -> None:
    with TestClient(create_app(Settings()), base_url="http://127.0.0.1") as client:
        response = client.get("/health", headers={"host": "example.com"})

    assert response.status_code == 400


def test_home_page_shows_engine_unavailable_without_connection() -> None:
    settings = Settings(engine_url="http://127.0.0.1:1")
    with TestClient(create_app(settings), base_url="http://127.0.0.1") as client:
        response = client.get("/")
        inventory_response = client.get("/machine/inventory")

    assert response.status_code == 200
    assert "Chargement de l’inventaire" in response.text
    assert inventory_response.status_code == 503
    assert "Moteur PCE" in inventory_response.text

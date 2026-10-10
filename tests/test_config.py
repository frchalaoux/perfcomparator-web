import json

from perfcomparatorweb.core.config import Settings


def test_settings_fall_back_to_engine_state_when_environment_is_missing(
    tmp_path, monkeypatch
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "engine.json").write_text(
        json.dumps({"url": "http://127.0.0.1:54321", "api_token": "local-secret"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PERFCOMPARATOR_STATE_DIR", str(state_dir))
    monkeypatch.delenv("PERFCOMPARATOR_ENGINE_URL", raising=False)
    monkeypatch.delenv("PERFCOMPARATOR_ENGINE_TOKEN", raising=False)

    settings = Settings.from_environment()

    assert settings.engine_url == "http://127.0.0.1:54321"
    assert settings.engine_token == "local-secret"


def test_environment_engine_settings_take_precedence_over_state(
    tmp_path, monkeypatch
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "engine.json").write_text(
        json.dumps({"url": "http://127.0.0.1:54321", "api_token": "state-secret"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PERFCOMPARATOR_STATE_DIR", str(state_dir))
    monkeypatch.setenv("PERFCOMPARATOR_ENGINE_URL", "http://127.0.0.1:54322")
    monkeypatch.setenv("PERFCOMPARATOR_ENGINE_TOKEN", "environment-secret")

    settings = Settings.from_environment()

    assert settings.engine_url == "http://127.0.0.1:54322"
    assert settings.engine_token == "environment-secret"

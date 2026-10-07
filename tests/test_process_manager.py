import json
import urllib.error

import pytest

from perfcomparatorweb import process_manager


class _FakeProcess:
    pid = 58123

    def __init__(self) -> None:
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False
        self.waited = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        self.waited = True
        return self.returncode or 0


def test_failed_web_start_terminates_process_and_removes_its_state(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web_state_file = tmp_path / "web.json"
    engine_state_file = tmp_path / "engine.json"
    engine_state_file.write_text(
        json.dumps({"url": "http://127.0.0.1:8765", "api_token": "engine-token"}),
        encoding="utf-8",
    )
    process = _FakeProcess()
    request_count = 0
    monkeypatch.setattr(process_manager, "STATE_DIR", tmp_path)
    monkeypatch.setattr(process_manager, "WEB_STATE_FILE", web_state_file)
    monkeypatch.setattr(process_manager, "ENGINE_STATE_FILE", engine_state_file)
    monkeypatch.setattr(process_manager, "_free_port", lambda: 8766)
    monkeypatch.setattr(process_manager.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(process_manager.time, "sleep", lambda _seconds: None)

    def request(url: str, token: str | None = None, *, post: bool = False) -> bytes:
        nonlocal request_count
        request_count += 1
        if url.endswith("/api/v1/health"):
            return b'{"component":"pce"}'
        raise urllib.error.URLError("not ready")

    monkeypatch.setattr(process_manager, "_request", request)

    with pytest.raises(RuntimeError, match="PCWEB ne répond pas"):
        process_manager.start()

    assert request_count > 1
    assert process.terminated
    assert process.waited
    assert not process.killed
    assert not web_state_file.exists()

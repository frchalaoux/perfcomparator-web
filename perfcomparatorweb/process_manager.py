"""Démarrage et arrêt local du processus PCWEB."""

from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from platformdirs import user_state_path

STATE_DIR = Path(
    os.environ.get("PERFCOMPARATOR_STATE_DIR")
    or user_state_path("perfcomparator", appauthor=False)
)
WEB_STATE_FILE = STATE_DIR / "web.json"
ENGINE_STATE_FILE = STATE_DIR / "engine.json"


def _state_dir() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        STATE_DIR.chmod(0o700)
    return STATE_DIR


def _read(path: Path) -> dict[str, object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write(data: dict[str, object]) -> None:
    _state_dir()
    temporary = WEB_STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(data), encoding="utf-8")
    if os.name != "nt":
        temporary.chmod(0o600)
    temporary.replace(WEB_STATE_FILE)


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _request(url: str, token: str | None = None, *, post: bool = False) -> bytes:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = urllib.request.Request(url, headers=headers, method="POST" if post else "GET")
    with urllib.request.urlopen(request, timeout=1.0) as response:
        return response.read()


def is_running() -> bool:
    state = _read(WEB_STATE_FILE)
    if not state:
        return False
    try:
        payload = json.loads(_request(f"{state['url']}/health"))
        return payload.get("component") == "pcweb"
    except (OSError, urllib.error.URLError, KeyError, ValueError):
        return False


def start() -> dict[str, object]:
    if is_running():
        return _read(WEB_STATE_FILE) or {}
    engine = _read(ENGINE_STATE_FILE)
    if not engine:
        raise RuntimeError("PCE n'est pas configuré. Lancez `perfcomparator engine start` d'abord.")
    try:
        payload = json.loads(
            _request(f"{engine['url']}/api/v1/health", str(engine["api_token"]))
        )
        if payload.get("component") != "pce":
            raise RuntimeError("L'adresse configurée ne correspond pas à un moteur PCE.")
    except (OSError, urllib.error.URLError, KeyError):
        raise RuntimeError("PCE ne répond pas ; PCWEB ne peut pas démarrer.") from None

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    control_token = secrets.token_urlsafe(32)
    env = os.environ.copy()
    env.update(
        {
            "PERFCOMPARATOR_WEB_PORT": str(port),
            "PERFCOMPARATOR_WEB_CONTROL_TOKEN": control_token,
            "PERFCOMPARATOR_ENGINE_URL": str(engine["url"]),
            "PERFCOMPARATOR_ENGINE_TOKEN": str(engine["api_token"]),
        }
    )
    log_path = _state_dir() / "web.log"
    with log_path.open("ab") as log_file:
        kwargs: dict[str, object] = {"stdout": log_file, "stderr": subprocess.STDOUT}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        process = subprocess.Popen(
            [sys.executable, "-m", "perfcomparatorweb.server"],
            stdin=subprocess.DEVNULL,
            env=env,
            close_fds=True,
            **kwargs,
        )
    state: dict[str, object] = {
        "pid": process.pid,
        "url": url,
        "control_token": control_token,
        "log": str(log_path),
    }
    _write(state)
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError(f"PCWEB s'est arrêté au démarrage. Consultez {log_path}.")
        try:
            payload = json.loads(_request(f"{url}/health"))
            if payload.get("component") == "pcweb":
                return state
        except (OSError, urllib.error.URLError, ValueError):
            time.sleep(0.1)
    raise RuntimeError(f"PCWEB ne répond pas après 10 secondes. Consultez {log_path}.")


def stop() -> bool:
    state = _read(WEB_STATE_FILE)
    if not state:
        return False
    try:
        _request(f"{state['url']}/_control/shutdown", str(state["control_token"]), post=True)
    except (OSError, urllib.error.URLError, KeyError):
        WEB_STATE_FILE.unlink(missing_ok=True)
        return False
    for _ in range(100):
        try:
            _request(f"{state['url']}/health")
        except (OSError, urllib.error.URLError, KeyError):
            WEB_STATE_FILE.unlink(missing_ok=True)
            return True
        time.sleep(0.1)
    raise RuntimeError("PCWEB ne s'est pas arrêté après la demande d'arrêt.")


def status() -> dict[str, object] | None:
    state = _read(WEB_STATE_FILE)
    if not state or not is_running():
        return None
    return state

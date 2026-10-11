"""Configuration du serveur PCWEB."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_state_path


def _engine_state() -> dict[str, object]:
    state_dir = Path(
        os.environ.get("PERFCOMPARATOR_STATE_DIR")
        or user_state_path("perfcomparator", appauthor=False)
    )
    try:
        state = json.loads((state_dir / "engine.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return state if isinstance(state, dict) else {}


@dataclass(frozen=True)
class Settings:
    """Paramètres d'exécution résolus depuis l'environnement du processus."""

    engine_url: str = "http://127.0.0.1:8765"
    engine_token: str = ""
    control_token: str = ""
    port: int = 8766

    @classmethod
    def from_environment(cls) -> Settings:
        engine = _engine_state()
        return cls(
            engine_url=os.environ.get("PERFCOMPARATOR_ENGINE_URL")
            or str(engine.get("url", "http://127.0.0.1:8765")),
            engine_token=os.environ.get("PERFCOMPARATOR_ENGINE_TOKEN")
            or str(engine.get("api_token", "")),
            control_token=os.environ.get("PERFCOMPARATOR_WEB_CONTROL_TOKEN", ""),
            port=int(os.environ.get("PERFCOMPARATOR_WEB_PORT", "8766")),
        )

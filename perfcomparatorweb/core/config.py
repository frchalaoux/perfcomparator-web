"""Configuration du serveur PCWEB."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Paramètres d'exécution résolus depuis l'environnement du processus."""

    engine_url: str = "http://127.0.0.1:8765"
    engine_token: str = ""
    control_token: str = ""
    port: int = 8766

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            engine_url=os.environ.get("PERFCOMPARATOR_ENGINE_URL", "http://127.0.0.1:8765"),
            engine_token=os.environ.get("PERFCOMPARATOR_ENGINE_TOKEN", ""),
            control_token=os.environ.get("PERFCOMPARATOR_WEB_CONTROL_TOKEN", ""),
            port=int(os.environ.get("PERFCOMPARATOR_WEB_PORT", "8766")),
        )

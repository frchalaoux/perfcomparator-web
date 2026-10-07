"""Point d'entrée du serveur PCWEB géré par la commande CLI."""

from __future__ import annotations

import asyncio

import uvicorn

from perfcomparatorweb.app import create_app
from perfcomparatorweb.core.config import Settings


async def serve() -> None:
    settings = Settings.from_environment()
    app = create_app(settings)
    config = uvicorn.Config(app, host="127.0.0.1", port=settings.port)
    server = uvicorn.Server(config)

    async def watch_shutdown() -> None:
        while not getattr(app.state, "shutdown_requested", False):
            await asyncio.sleep(0.1)
        server.should_exit = True

    watcher = asyncio.create_task(watch_shutdown())
    try:
        await server.serve()
    finally:
        watcher.cancel()


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()

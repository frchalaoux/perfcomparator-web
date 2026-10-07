"""Fabrique FastAPI du serveur PCWEB."""

from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from perfcomparatorweb import __version__
from perfcomparatorweb.core.config import Settings
from perfcomparatorweb.http_client.pce_client import PCEClient
from perfcomparatorweb.web.repositories.pce_repository import PCERepository
from perfcomparatorweb.web.services.status_service import StatusService
from perfcomparatorweb.webapps.base import router

PACKAGE_DIR = Path(__file__).parent


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings.from_environment()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = PCEClient(resolved.engine_url, resolved.engine_token)
        app.state.pce_client = client
        app.state.status_service = StatusService(PCERepository(client))
        try:
            yield
        finally:
            await client.close()

    app = FastAPI(title="PerfComparator Web", version=__version__, lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.state.settings = resolved
    app.state.templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
    app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
    app.include_router(router)

    @app.middleware("http")
    async def check_origin(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            expected_origin = f"{request.url.scheme}://{request.headers.get('host', '')}"
            if origin is not None and origin != expected_origin:
                return JSONResponse(status_code=403, content={"detail": "origin rejected"})
        return await call_next(request)

    @app.post("/_control/shutdown", include_in_schema=False)
    async def shutdown(
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> dict[str, str]:
        token = resolved.control_token
        if not token or not secrets.compare_digest(authorization or "", f"Bearer {token}"):
            raise HTTPException(status_code=403, detail="forbidden")
        request.app.state.shutdown_requested = True
        return {"status": "stopping"}

    return app

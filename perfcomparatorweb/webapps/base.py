"""Routes HTML de base de PCWEB."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request) -> HTMLResponse:
    status = await request.app.state.status_service.get_status()
    return request.app.state.templates.TemplateResponse(
        request,
        "index.html",
        {"status": status},
    )


@router.get("/health", name="health")
async def health() -> dict[str, str]:
    return {"status": "ok", "component": "pcweb"}

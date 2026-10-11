"""Pages de consultation locale de PCWEB."""

from __future__ import annotations

import platform
from typing import Annotated
from urllib.parse import parse_qs

import httpx
from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from perfcomparatorweb.http_client.pce_client import PCEContractError

router = APIRouter()

CATEGORY_LABELS = {
    "application": "Applications",
    "cpu": "Processeur",
    "memory": "Mémoire",
    "storage": "Stockage",
    "gpu": "Processeur graphique",
}
SCENARIO_LABELS = {
    "quotidien": "Réactivité quotidienne",
    "developpement": "Développement",
    "calcul-intensif": "Calcul intensif",
    "fichiers": "Gestion de fichiers",
    "base-de-donnees": "Base de données locale",
    "creation": "Création 3D/vidéo",
    "jeu-3d": "Jeu et rendu 3D généraliste",
}


def _error_page(request: Request, error: httpx.HTTPError) -> HTMLResponse:
    if isinstance(error, PCEContractError):
        status_code = 502
        message = (
            "PCE a renvoyé un format incompatible. Vérifiez que PCE et PCWEB sont à jour, "
            "puis relancez les serveurs."
        )
    elif isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 404:
        status_code = 404
        message = "Cette ressource n’existe pas ou n’est plus disponible."
    else:
        status_code = 503
        message = "PCE est indisponible. Vérifiez que le moteur est démarré, puis réessayez."
    return request.app.state.templates.TemplateResponse(
        request,
        "error.html",
        {"message": message, "status_code": status_code},
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse, name="home")
async def home(
    request: Request,
    saved: int = Query(default=0, ge=0, le=1),
    edit_error: int = Query(default=0, ge=0, le=1),
) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request,
        "index.html",
        {
            "windows": platform.system() == "Windows",
            "saved": bool(saved),
            "edit_error": bool(edit_error),
        },
    )


@router.get("/machine/inventory", response_class=HTMLResponse, name="machine_inventory")
async def machine_inventory(
    request: Request,
    saved: int = Query(default=0, ge=0, le=1),
    edit_error: int = Query(default=0, ge=0, le=1),
) -> HTMLResponse:
    try:
        inventory = await request.app.state.read_only_service.system()
    except httpx.RequestError:
        status = {
            "web": "available",
            "engine": "unavailable",
            "detail": "PCE est indisponible. Vérifiez que le moteur est démarré, puis réessayez.",
        }
        return request.app.state.templates.TemplateResponse(
            request,
            "machine_status.html",
            {"status": status},
            status_code=503,
        )
    except httpx.HTTPError as error:
        status_code = 502 if isinstance(error, PCEContractError) else 503
        if isinstance(error, PCEContractError):
            message = (
                "PCE a renvoyé un format incompatible. Vérifiez que PCE et PCWEB sont à jour, "
                "puis relancez les serveurs."
            )
        else:
            message = "PCE est indisponible. Vérifiez que le moteur est démarré, puis réessayez."
        return request.app.state.templates.TemplateResponse(
            request,
            "machine_status.html",
            {"status": {"web": "available", "engine": "unavailable", "detail": message}},
            status_code=status_code,
        )
    return request.app.state.templates.TemplateResponse(
        request,
        "machine_inventory.html",
        {"inventory": inventory, "saved": bool(saved), "edit_error": bool(edit_error)},
    )


@router.post("/machine/properties", name="update_machine_properties")
async def update_machine_properties(request: Request) -> Response:
    form = parse_qs((await request.body()).decode("utf-8"), keep_blank_values=True)
    model = form.get("model", [""])[0].strip()
    year_text = form.get("model_year", [""])[0].strip()
    product_sku = " ".join(form.get("product_sku", [""])[0].split()) or None
    try:
        model_year = int(year_text) if year_text else None
    except ValueError:
        return RedirectResponse("/?edit_error=1", status_code=303)
    if not model or len(model) > 200 or len(product_sku or "") > 100 or (
        model_year is not None and not 1984 <= model_year <= 2100
    ):
        return RedirectResponse("/?edit_error=1", status_code=303)
    try:
        await request.app.state.machine_service.update_metadata(
            model=model,
            model_year=model_year,
            product_sku=product_sku,
        )
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 422:
            return RedirectResponse("/?edit_error=1", status_code=303)
        return _error_page(request, error)
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return RedirectResponse("/?saved=1", status_code=303)


@router.get("/benchmarks", response_class=HTMLResponse, name="benchmarks")
async def benchmarks(request: Request) -> HTMLResponse:
    try:
        catalog = await request.app.state.read_only_service.benchmarks()
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return request.app.state.templates.TemplateResponse(
        request,
        "benchmarks.html",
        {"catalog": catalog},
    )


@router.get("/benchmarks/{benchmark_id}", response_class=HTMLResponse, name="benchmark")
async def benchmark(request: Request, benchmark_id: str) -> HTMLResponse:
    try:
        details = await request.app.state.read_only_service.benchmark(benchmark_id)
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return request.app.state.templates.TemplateResponse(
        request,
        "benchmark.html",
        {"benchmark": details},
    )


@router.get("/reports", response_class=HTMLResponse, name="reports")
async def reports(
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> HTMLResponse:
    try:
        page = await request.app.state.read_only_service.reports(offset=offset, limit=limit)
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return request.app.state.templates.TemplateResponse(
        request,
        "reports.html",
        {"page": page},
    )


@router.get("/compare", response_class=HTMLResponse, name="compare_reports")
async def compare_reports(
    request: Request,
    report_id: Annotated[list[str] | None, Query()] = None,
    reference_report_id: str | None = None,
    action: str | None = None,
    offset: int = Query(default=0, ge=0),
    q: str = Query(default="", max_length=120),
) -> HTMLResponse:
    limit = 20
    try:
        page = await request.app.state.read_only_service.reports(
            offset=offset,
            limit=limit,
            q=q.strip(),
        )
    except httpx.HTTPError as error:
        return _error_page(request, error)

    comparison = None
    comparison_error = None
    category_rows = []
    scenario_rows = []
    request_report_ids = report_id or []
    selected_ids = list(dict.fromkeys(request_report_ids))
    if request_report_ids and action != "search":
        if len(selected_ids) < 2:
            comparison_error = "Sélectionnez au moins deux rapports à comparer."
        else:
            reference = reference_report_id or selected_ids[0]
            try:
                comparison = await request.app.state.read_only_service.compare_reports(
                    selected_ids,
                    reference_report_id=reference,
                )
                machines = comparison["machines"]
                for category in machines[0]["categories"]:
                    maximum = max(machine["categories"][category] for machine in machines)
                    category_rows.append(
                        {
                            "label": CATEGORY_LABELS.get(category, category.capitalize()),
                            "machines": [
                                {
                                    "label": machine["label"],
                                    "index": machine["categories"][category],
                                    "width": max(2, 100 * machine["categories"][category] / maximum),
                                }
                                for machine in machines
                            ],
                        }
                    )
                for scenario, weight in comparison["scenario_weights"].items():
                    maximum = max(machine["scenarios"][scenario] for machine in machines)
                    scenario_rows.append(
                        {
                            "label": SCENARIO_LABELS.get(scenario, scenario.capitalize()),
                            "weight": weight,
                            "machines": [
                                {
                                    "label": machine["label"],
                                    "index": machine["scenarios"][scenario],
                                    "width": max(2, 100 * machine["scenarios"][scenario] / maximum),
                                }
                                for machine in machines
                            ],
                        }
                    )
            except httpx.HTTPStatusError as error:
                if error.response.status_code == 422:
                    try:
                        error_payload = error.response.json()
                        detail = error_payload.get("detail")
                        api_error = error_payload.get("error")
                        if isinstance(api_error, dict):
                            detail = api_error.get("message") or detail
                    except (ValueError, AttributeError):
                        detail = None
                    if isinstance(detail, list) and any(
                        isinstance(item, dict) and item.get("type") == "too_long"
                        for item in detail
                    ):
                        comparison_error = "Sélectionnez au maximum huit rapports."
                    else:
                        comparison_error = str(detail or "Ces rapports ne peuvent pas être comparés.")
                else:
                    return _error_page(request, error)
            except httpx.HTTPError as error:
                return _error_page(request, error)

    return request.app.state.templates.TemplateResponse(
        request,
        "compare.html",
        {
            "page": page,
            "selected_ids": selected_ids,
            "visible_report_ids": [report["report_id"] for report in page["reports"]],
            "reference_report_id": reference_report_id or (selected_ids[0] if selected_ids else None),
            "search_query": q,
            "comparison": comparison,
            "category_rows": category_rows,
            "scenario_rows": scenario_rows,
            "comparison_error": comparison_error,
        },
    )


@router.get("/compare/report", response_class=HTMLResponse, name="full_comparison_report")
async def full_comparison_report(
    request: Request,
    report_id: Annotated[list[str], Query()],
    reference_report_id: str,
) -> HTMLResponse:
    if not 2 <= len(report_id) <= 8 or len(set(report_id)) != len(report_id):
        return HTMLResponse("Sélection invalide : choisissez de deux à huit rapports distincts.", status_code=422)
    if reference_report_id not in report_id:
        return HTMLResponse("Le rapport de référence doit faire partie de la sélection.", status_code=422)
    try:
        document = await request.app.state.read_only_service.comparison_html(
            report_id,
            reference_report_id=reference_report_id,
        )
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 422:
            return HTMLResponse("Ces rapports ne peuvent pas être comparés.", status_code=422)
        return _error_page(request, error)
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return HTMLResponse(document)


@router.get("/compare/export", response_class=HTMLResponse, name="export_comparison")
async def export_comparison(
    request: Request,
    report_id: Annotated[list[str], Query()],
    reference_report_id: str,
) -> HTMLResponse:
    response = await full_comparison_report(
        request,
        report_id=report_id,
        reference_report_id=reference_report_id,
    )
    if response.status_code != 200:
        return response
    response.headers["Content-Disposition"] = 'attachment; filename="perfcomparator-comparison.html"'
    return response


@router.get("/reports/{report_id}", response_class=HTMLResponse, name="report")
async def report(
    request: Request,
    report_id: str,
    saved: int = Query(default=0, ge=0, le=1),
) -> HTMLResponse:
    try:
        details = await request.app.state.read_only_service.report(report_id)
    except httpx.HTTPError as error:
        return _error_page(request, error)
    return request.app.state.templates.TemplateResponse(
        request,
        "report.html",
        {"report": details, "saved": bool(saved)},
    )


@router.post("/reports/{report_id}/machine", name="update_report_machine")
async def update_report_machine(
    request: Request,
    report_id: str,
) -> Response:
    form = parse_qs((await request.body()).decode("utf-8"), keep_blank_values=True)
    model = form.get("model", [""])[0]
    model_year = form.get("model_year", [""])[0]
    product_sku = form.get("product_sku", [""])[0]
    try:
        details = await request.app.state.read_only_service.report(report_id)
    except httpx.HTTPError as error:
        return _error_page(request, error)

    normalized_model = model.strip()
    if not normalized_model:
        return request.app.state.templates.TemplateResponse(
            request,
            "report.html",
            {
                "report": details,
                "edit_error": "Le champ model doit contenir un nom de modèle.",
                "model_value": model,
                "year_value": model_year,
                "sku_value": product_sku,
            },
            status_code=422,
        )
    try:
        normalized_year = int(model_year) if model_year.strip() else None
    except ValueError:
        return request.app.state.templates.TemplateResponse(
            request,
            "report.html",
            {
                "report": details,
                "edit_error": "L’année doit être un nombre entre 1984 et 2100.",
                "model_value": normalized_model,
                "year_value": model_year,
                "sku_value": product_sku,
            },
            status_code=422,
        )
    if normalized_year is not None and not 1984 <= normalized_year <= 2100:
        return request.app.state.templates.TemplateResponse(
            request,
            "report.html",
            {
                "report": details,
                "edit_error": "L’année doit être comprise entre 1984 et 2100.",
                "model_value": normalized_model,
                "year_value": model_year,
                "sku_value": product_sku,
            },
            status_code=422,
        )
    try:
        updated = await request.app.state.report_service.update_machine_metadata(
            report_id,
            model=normalized_model,
            model_year=normalized_year,
            product_sku=" ".join(product_sku.split()) or None,
        )
    except httpx.HTTPError as error:
        if isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 422:
            return request.app.state.templates.TemplateResponse(
                request,
                "report.html",
                {
                    "report": details,
                    "edit_error": "PCE a refusé les informations du modèle. Vérifiez les champs.",
                    "model_value": normalized_model,
                    "year_value": model_year,
                    "sku_value": product_sku,
                },
                status_code=422,
            )
        return _error_page(request, error)
    return RedirectResponse(
        url=f"/reports/{updated['report_id']}?saved=1",
        status_code=303,
    )


@router.get("/health", name="health")
async def health() -> dict[str, str]:
    return {"status": "ok", "component": "pcweb"}

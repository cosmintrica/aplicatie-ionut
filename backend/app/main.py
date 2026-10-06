from contextlib import asynccontextmanager
from datetime import datetime, timezone
import hmac
import ipaddress
import json
import logging
import secrets
import time
from urllib.parse import urlsplit
import uuid
import traceback
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from .db import connect
from .ingest import COMPANY_ID, seed_database
from .repository import (AppError, bump_revision, capabilities, check_revision, company_view,
                         compare_list, descendants, get_categories, get_evidence, get_list,
                         get_offers, get_product, get_scenarios, now, require_scenario,
                         search_catalog, snapshot_view)
from .schemas import CompanyUpdate, ComparisonCreate, LineCreate, LineUpdate, ListCreate, ListUpdate
from .settings import Settings, default_settings


logger = logging.getLogger("preturi.local")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or default_settings()
    sessions: dict[str, tuple[str, float]] = {}

    @asynccontextmanager
    async def lifespan(app):
        seed_database(settings)
        yield

    api = FastAPI(title="Prețuri achiziții · local", version="0.1.0", lifespan=lifespan)
    api.state.settings = settings

    def error_response(request, code, message, status, fields=None):
        return JSONResponse(status_code=status, content={"code": code, "message": message,
                             "field_errors": fields or {}, "request_id": getattr(request.state, "request_id", "unknown"),
                             "retryable": status in {409, 503}})

    @api.middleware("http")
    async def local_security(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex
        host = urlsplit("http://" + request.headers.get("host", "")).hostname
        if host not in settings.allowed_hosts:
            return error_response(request, "HOST_FORBIDDEN", "Serverul acceptă numai acces local loopback.", 403)
        if not settings.testing and request.client:
            try:
                if not ipaddress.ip_address(request.client.host).is_loopback:
                    return error_response(request, "LOOPBACK_REQUIRED", "Accesul este limitat la acest calculator.", 403)
            except ValueError:
                return error_response(request, "LOOPBACK_REQUIRED", "Accesul este limitat la acest calculator.", 403)
        origin = request.headers.get("origin")
        if origin and origin not in settings.allowed_origins:
            return error_response(request, "ORIGIN_FORBIDDEN", "Originea cererii nu este permisă.", 403)
        if request.method == "GET" and request.url.path.startswith(("/api/v1/lists", "/api/v1/comparisons")):
            session = sessions.get(request.cookies.get("local_session", ""))
            if not session or session[1] < time.time():
                return error_response(request, "SESSION_REQUIRED", "Deschide aplicația pentru o sesiune locală.", 403)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            if origin not in settings.allowed_origins:
                return error_response(request, "ORIGIN_REQUIRED", "Mutațiile necesită o origine locală autorizată.", 403)
            session = sessions.get(request.cookies.get("local_session", ""))
            token = request.headers.get("x-csrf-token", "")
            if not session or session[1] < time.time() or not hmac.compare_digest(session[0], token):
                return error_response(request, "CSRF_INVALID", "Sesiunea locală a expirat. Reîncarcă aplicația.", 403)
            length = request.headers.get("content-length")
            if length and (not length.isdigit() or int(length) > 1_048_576):
                return error_response(request, "PAYLOAD_TOO_LARGE", "Cererea este prea mare.", 413)
        try:
            response = await call_next(request)
        except Exception as exc:
            # Formatează doar cadrele; nu include mesajul excepției, corpul
            # cererii sau valorile locale, care ar putea conține date private.
            frames = "".join(traceback.format_tb(exc.__traceback__))
            logger.error("request_id=%s error_type=%s\n%s", request.state.request_id, type(exc).__name__, frames)
            # Nici date private, nici stack trace în răspunsul browserului.
            return error_response(request, "INTERNAL_ERROR", "Cererea nu a putut fi procesată. Datele listei sunt păstrate.", 500)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @api.exception_handler(AppError)
    async def app_error_handler(request, error):
        return error_response(request, error.code, error.message, error.status, error.fields)

    @api.exception_handler(RequestValidationError)
    async def validation_handler(request, error):
        fields = {".".join(str(part) for part in err["loc"]): err["msg"] for err in error.errors()}
        return error_response(request, "VALIDATION_ERROR", "Verifică datele introduse.", 422, fields)

    @api.get("/api/v1/health")
    def health():
        return {"status": "ok", "mode": "offline_snapshot", "network_mode": "offline"}

    @api.get("/api/v1/bootstrap")
    def bootstrap(request: Request):
        current_cookie = request.cookies.get("local_session", "")
        session = sessions.get(current_cookie)
        if session is None or session[1] < time.time():
            # Curăță sesiunile expirate; datele private sunt în SQLite, nu aici.
            for key in list(sessions):
                if sessions[key][1] < time.time():
                    del sessions[key]
            if len(sessions) >= 1024:
                del sessions[next(iter(sessions))]
            current_cookie = secrets.token_urlsafe(32)
            session = (secrets.token_urlsafe(32), time.time() + 8 * 3600)
            sessions[current_cookie] = session
        with connect(settings) as conn:
            latest = conn.execute("SELECT id FROM shopping_list WHERE company_id=? ORDER BY updated_at DESC,id LIMIT 1", (COMPANY_ID,)).fetchone()
            data = {"capabilities": capabilities(conn), "csrf_token": session[0], "company": company_view(conn),
                    "categories": get_categories(conn), "scenarios": get_scenarios(conn),
                    "snapshots": [snapshot_view(row) for row in conn.execute("SELECT * FROM snapshot ORDER BY source_id,filename")],
                    "current_list": get_list(conn, latest[0]) if latest else None}
        response = JSONResponse(data)
        response.set_cookie("local_session", current_cookie, httponly=True, samesite="strict", max_age=8 * 3600)
        return response

    @api.get("/api/v1/capabilities")
    def get_capabilities():
        with connect(settings) as conn:
            return capabilities(conn)

    @api.get("/api/v1/categories")
    def categories():
        with connect(settings) as conn:
            return get_categories(conn)

    @api.get("/api/v1/scenarios")
    def scenarios():
        with connect(settings) as conn:
            return get_scenarios(conn)

    @api.get("/api/v1/catalog")
    def catalog(q: str = Query(default="", max_length=200), category: str | None = None,
                source: str | None = None, scenario: str | None = None, cursor: str | None = Query(default=None, max_length=2000),
                limit: int = Query(default=50, ge=1, le=100), priced_only: bool = False,
                availability: str = "all", sort: str = "recommended"):
        with connect(settings) as conn:
            return search_catalog(conn, q, category, source, scenario, cursor, limit, priced_only, availability, sort)

    @api.get("/api/v1/catalog/{item_id}")
    def product(item_id: str, scenario: str | None = None):
        with connect(settings) as conn:
            if scenario:
                require_scenario(conn, scenario)
            return get_product(conn, item_id, scenario)

    @api.get("/api/v1/offers")
    def offers(item: str, scenario: str):
        with connect(settings) as conn:
            return get_offers(conn, item, scenario)

    @api.get("/api/v1/evidence/{observation_id}")
    def evidence(observation_id: str, reference_item_id: str | None = None):
        with connect(settings) as conn:
            return get_evidence(conn, observation_id, reference_item_id)

    @api.patch("/api/v1/company")
    def update_company(payload: CompanyUpdate):
        with connect(settings) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            current = company_view(conn)
            if current["revision"] != payload.expected_revision:
                raise AppError("REVISION_CONFLICT", "Profilul firmei s-a schimbat. Reîncarcă-l.", 409)
            conn.execute("UPDATE company SET name=?,revision=revision+1 WHERE id=?", (payload.name, COMPANY_ID))
            return company_view(conn)

    @api.get("/api/v1/lists")
    def lists():
        with connect(settings) as conn:
            return {"items": [get_list(conn, row[0]) for row in conn.execute("SELECT id FROM shopping_list WHERE company_id=? ORDER BY updated_at DESC,id", (COMPANY_ID,))]}

    @api.post("/api/v1/lists", status_code=201)
    def create_list(payload: ListCreate):
        with connect(settings) as conn, conn:
            require_scenario(conn, payload.scenario_id)
            list_id = "list_" + uuid.uuid4().hex
            stamp = now()
            conn.execute("INSERT INTO shopping_list VALUES(?,?,?,?,?,?,?)", (list_id, COMPANY_ID, payload.name, payload.scenario_id, 1, stamp, stamp))
            return get_list(conn, list_id)

    @api.get("/api/v1/lists/{list_id}")
    def read_list(list_id: str):
        with connect(settings) as conn:
            return get_list(conn, list_id)

    @api.patch("/api/v1/lists/{list_id}")
    def update_list(list_id: str, payload: ListUpdate):
        with connect(settings) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            current = check_revision(conn, list_id, payload.expected_revision)
            if payload.scenario_id:
                require_scenario(conn, payload.scenario_id)
            conn.execute("UPDATE shopping_list SET name=?,scenario_id=? WHERE company_id=? AND id=?",
                         (payload.name or current["name"], payload.scenario_id or current["scenario_id"], COMPANY_ID, list_id))
            bump_revision(conn, list_id)
            return get_list(conn, list_id)

    @api.delete("/api/v1/lists/{list_id}")
    def delete_list(list_id: str, expected_revision: int = Query(ge=1)):
        with connect(settings) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            check_revision(conn, list_id, expected_revision)
            conn.execute("DELETE FROM shopping_list WHERE company_id=? AND id=?", (COMPANY_ID, list_id))
            return {"deleted": True, "id": list_id}

    @api.post("/api/v1/lists/{list_id}/lines", status_code=201)
    def add_line(list_id: str, payload: LineCreate):
        with connect(settings) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            check_revision(conn, list_id, payload.expected_revision)
            description, category_id = payload.description, payload.category_id
            if payload.source_product_id:
                product = get_product(conn, payload.source_product_id)
                description = description or product["name"]
                category_id = category_id or product["category_id"]
            if not description or not description.strip():
                raise AppError("DESCRIPTION_REQUIRED", "Descrie articolul de care ai nevoie.", 422, {"description": "Câmp necesar."})
            if category_id:
                descendants(conn, category_id)
            conn.execute("INSERT INTO list_line VALUES(?,?,?,?,?,?,?,?,?)",
                         ("line_" + uuid.uuid4().hex, COMPANY_ID, list_id, payload.source_product_id,
                          description.strip(), payload.quantity, payload.unit, category_id, now()))
            bump_revision(conn, list_id)
            return get_list(conn, list_id)

    @api.patch("/api/v1/lists/{list_id}/lines/{line_id}")
    def update_line(list_id: str, line_id: str, payload: LineUpdate):
        with connect(settings) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            check_revision(conn, list_id, payload.expected_revision)
            current = conn.execute("SELECT * FROM list_line WHERE company_id=? AND list_id=? AND id=?", (COMPANY_ID, list_id, line_id)).fetchone()
            if current is None:
                raise AppError("LINE_NOT_FOUND", "Poziția nu există în această listă.", 404)
            if payload.description is not None and not payload.description.strip():
                raise AppError("DESCRIPTION_REQUIRED", "Descrierea nu poate fi goală.", 422)
            description = payload.description.strip() if payload.description else current["description"]
            source_product_id, category_id = current["source_product_id"], current["category_id"]
            if "source_product_id" in payload.model_fields_set:
                source_product_id = payload.source_product_id
                if source_product_id is not None:
                    product = get_product(conn, source_product_id)
                    if "description" not in payload.model_fields_set:
                        description = product["name"]
                    if "category_id" not in payload.model_fields_set:
                        category_id = product["category_id"]
            if "category_id" in payload.model_fields_set:
                category_id = payload.category_id
            if category_id is not None:
                descendants(conn, category_id)
            conn.execute("UPDATE list_line SET quantity=?,description=?,source_product_id=?,category_id=? WHERE company_id=? AND list_id=? AND id=?",
                         (payload.quantity or current["quantity"], description, source_product_id, category_id, COMPANY_ID, list_id, line_id))
            bump_revision(conn, list_id)
            return get_list(conn, list_id)

    @api.delete("/api/v1/lists/{list_id}/lines/{line_id}")
    def delete_line(list_id: str, line_id: str, expected_revision: int = Query(ge=1)):
        with connect(settings) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            check_revision(conn, list_id, expected_revision)
            cursor = conn.execute("DELETE FROM list_line WHERE company_id=? AND list_id=? AND id=?", (COMPANY_ID, list_id, line_id))
            if cursor.rowcount == 0:
                raise AppError("LINE_NOT_FOUND", "Poziția nu există în această listă.", 404)
            bump_revision(conn, list_id)
            return get_list(conn, list_id)

    @api.post("/api/v1/comparisons", status_code=201)
    def create_comparison(payload: ComparisonCreate):
        with connect(settings) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            return compare_list(conn, payload.list_id, payload.expected_revision, payload.scenario_id)

    @api.get("/api/v1/comparisons/{comparison_id}")
    def read_comparison(comparison_id: str):
        with connect(settings) as conn:
            row = conn.execute("SELECT * FROM comparison WHERE company_id=? AND id=?", (COMPANY_ID, comparison_id)).fetchone()
            if row is None:
                raise AppError("COMPARISON_NOT_FOUND", "Comparația nu există în firma locală.", 404)
            result = json.loads(row["result"])
            result["is_stale_revision"] = get_list(conn, row["list_id"])["revision"] != row["list_revision"]
            return result

    # Fișierele probe-data/ și DB nu sunt niciodată montate ca resurse statice.
    dist = settings.root_dir / "web" / "dist"
    if (dist / "assets").exists():
        api.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @api.get("/{path:path}", include_in_schema=False)
    def web_index(path: str):
        if path.startswith("api/"):
            raise AppError("ENDPOINT_NOT_FOUND", "Operația nu există în această etapă.", 404)
        index = dist / "index.html"
        if index.exists():
            return FileResponse(index)
        return JSONResponse({"message": "API local pregătit. Construiește interfața web sau pornește Vite.", "mode": "offline_snapshot"})

    return api


app = create_app()

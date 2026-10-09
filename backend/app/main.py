from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.client import PortalError, UrjaPortalClient
from app.core.config import get_settings
from app.demo_data import DEMO_HIERARCHY, DEMO_METERS, demo_consumption
from app.models import (
    Consumption,
    ErrorResponse,
    HealthResponse,
    HierarchyResponse,
    Meter,
    MeterList,
    SessionResponse,
)
from app.parsers import parse_hierarchy, parse_meters

settings = get_settings()
client = UrjaPortalClient(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await client.close()


app = FastAPI(title="Flock Energy Urja Meter Ops API", version="1.0.0", description="A normalized read-only API over the Urja Meter Ops portal.", lifespan=lifespan)
allowed_origins = list(dict.fromkeys([settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"]))
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1):3000$", allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, error: HTTPException) -> JSONResponse:
    detail = error.detail if isinstance(error.detail, dict) else {"code": "HTTP_ERROR", "message": str(error.detail)}
    if "code" not in detail or "message" not in detail:
        detail = {"code": "HTTP_ERROR", "message": "The request could not be completed."}
    return JSONResponse(status_code=error.status_code, content={"error": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Request parameters are invalid."}})


def upstream_error(error: PortalError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail={"code": "UPSTREAM_ERROR", "message": str(error)})


@app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    if settings.demo_mode:
        return HealthResponse(status="ok", upstream="demo")
    return HealthResponse(status="ok", upstream="reachable" if await client.request_health() else "unavailable")


@app.get("/api/v1/session", response_model=SessionResponse, tags=["session"])
async def session_status() -> SessionResponse:
    if settings.demo_mode:
        return SessionResponse(authenticated=client.authenticated, demo_mode=True, upstream="demo")

    authenticated = client.authenticated
    if not authenticated:
        upstream = "unavailable"
    else:
        upstream = "reachable"
    return SessionResponse(authenticated=authenticated, demo_mode=False, upstream=upstream)


@app.post(
    "/api/v1/session/login",
    response_model=SessionResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
    tags=["session"],
)
async def login_session() -> SessionResponse:
    if settings.demo_mode:
        try:
            await client.login()
        except PortalError as error:
            raise upstream_error(error) from error
        return SessionResponse(authenticated=True, demo_mode=True, upstream="demo")

    if not settings.urja_username or not settings.urja_password:
        raise HTTPException(status_code=400, detail={"code": "AUTH_REQUIRED", "message": "Username and password are required."})

    try:
        await client.login()
    except PortalError as error:
        raise upstream_error(error) from error
    return SessionResponse(authenticated=True, demo_mode=False, upstream="reachable")


@app.post("/api/v1/session/logout", response_model=SessionResponse, tags=["session"])
async def logout_session() -> SessionResponse:
    await client.logout()
    return SessionResponse(authenticated=False, demo_mode=settings.demo_mode, upstream="demo" if settings.demo_mode else "unavailable")


@app.get("/api/v1/meters", response_model=MeterList, responses={422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}}, tags=["meters"])
async def list_meters(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: Optional[str] = None) -> MeterList:
    if settings.demo_mode:
        meters = DEMO_METERS
    else:
        try:
            meters = parse_meters(await client.get_html("/meters"), settings.urja_base_url)
        except PortalError as error:
            raise upstream_error(error) from error
    if search:
        term = search.casefold()
        meters = [meter for meter in meters if term in meter.model_dump_json().casefold()]
    start = (page - 1) * page_size
    return MeterList(items=meters[start:start + page_size], page=page, page_size=page_size, total=len(meters))


@app.get("/api/v1/meters/{meter_id}", response_model=Meter, responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}, tags=["meters"])
async def get_meter(meter_id: str) -> Meter:
    if settings.demo_mode:
        meters = DEMO_METERS
    else:
        try:
            meters = parse_meters(await client.get_html("/meters"), settings.urja_base_url)
        except PortalError as error:
            raise upstream_error(error) from error
    for meter in meters:
        if meter.id == meter_id:
            return meter
    raise HTTPException(status_code=404, detail={"code": "METER_NOT_FOUND", "message": "Meter was not found in the portal."})


@app.get("/api/v1/meters/{meter_id}/consumption", responses={501: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}, tags=["consumption"])
async def get_consumption(meter_id: str) -> Consumption:
    if settings.demo_mode:
        if meter_id not in {meter.id for meter in DEMO_METERS}:
            raise HTTPException(status_code=404, detail={"code": "METER_NOT_FOUND", "message": "The requested demo meter does not exist."})
        return demo_consumption(meter_id)
    raise HTTPException(status_code=501, detail={"code": "UPSTREAM_ENDPOINT_UNKNOWN", "message": "A consumption endpoint was not verified during portal reconnaissance."})


@app.get("/api/v1/hierarchy", response_model=HierarchyResponse, tags=["hierarchy"])
async def hierarchy() -> HierarchyResponse:
    if settings.demo_mode:
        return HierarchyResponse(nodes=DEMO_HIERARCHY, available=True)
    try:
        nodes = parse_hierarchy(await client.get_html("/transformers"))
    except PortalError as error:
        raise upstream_error(error) from error
    return HierarchyResponse(nodes=nodes, available=bool(nodes), message=None if nodes else "The portal page did not expose a reliable hierarchy structure.")

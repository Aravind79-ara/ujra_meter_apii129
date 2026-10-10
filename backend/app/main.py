
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.client import PortalError, UrjaPortalClient
from app.core.config import get_settings
from app.demo_data import DEMO_HIERARCHY, DEMO_METERS
from app.models import (
    ErrorResponse,
    HealthResponse,
    HierarchyResponse,
    Meter,
    MeterList,
    SessionResponse,
)
from app.parsers import parse_portal_meters, parse_portal_transformers

PORTAL_PAGE_SIZE = 20


settings = get_settings()
client = UrjaPortalClient(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await client.close()


app = FastAPI(
    title="Flock Energy Urja Meter Ops API",
    version="1.0.0",
    description=(
        "A normalized read-only API over the "
        "Urja Meter Ops portal."
    ),
    lifespan=lifespan,
)

# CORS configuration
allowed_origins = list(
    dict.fromkeys(
        [
            settings.frontend_url,
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=(
        r"^https?://(localhost|127\.0\.0\.1):3000$"
    ),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    _: Request,
    error: HTTPException,
) -> JSONResponse:
    detail = (
        error.detail
        if isinstance(error.detail, dict)
        else {
            "code": "HTTP_ERROR",
            "message": str(error.detail),
        }
    )

    if "code" not in detail or "message" not in detail:
        detail = {
            "code": "HTTP_ERROR",
            "message": "The request could not be completed.",
        }

    return JSONResponse(
        status_code=error.status_code,
        content={"error": detail},
        headers=error.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    error: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request parameters are invalid.",
            }
        },
    )


def upstream_error(error: PortalError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={
            "code": "UPSTREAM_ERROR",
            "message": str(error),
        },
    )


async def portal_meter_page(
    search: Optional[str],
    page: int,
    page_size: int,
) -> tuple[list[Meter], int]:
    start = (page - 1) * page_size
    first_portal_page = start // PORTAL_PAGE_SIZE + 1
    query = urlencode({"q": search or "", "page": first_portal_page})

    try:
        meters, total, upstream_page_size = parse_portal_meters(
            await client.get_json(f"/portal/meters/search?{query}")
        )
        start_page_offset = (first_portal_page - 1) * upstream_page_size
        local_start = start - start_page_offset
        required_count = max(0, min(page_size, total - start))
        last_offset = local_start + required_count
        next_page = first_portal_page + 1

        while len(meters) < last_offset:
            next_query = urlencode({"q": search or "", "page": next_page})
            next_meters, _, next_page_size = parse_portal_meters(
                await client.get_json(f"/portal/meters/search?{next_query}")
            )
            if next_page_size != upstream_page_size or not next_meters:
                raise PortalError("The Urja portal returned inconsistent meter pages.")
            meters.extend(next_meters)
            next_page += 1
    except ValueError as error:
        raise PortalError("The Urja portal returned invalid meter data.") from error

    return meters[local_start:last_offset], total


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["health"],
)
async def health() -> HealthResponse:
    if settings.demo_mode:
        return HealthResponse(
            status="ok",
            upstream="demo",
        )

    reachable = await client.request_health()

    return HealthResponse(
        status="ok",
        upstream="reachable" if reachable else "unavailable",
    )


@app.get(
    "/api/v1/session",
    response_model=SessionResponse,
    tags=["session"],
)
async def session_status() -> SessionResponse:
    authenticated = client.authenticated

    if settings.demo_mode:
        return SessionResponse(
            authenticated=authenticated,
            demo_mode=True,
            upstream="demo",
        )

    return SessionResponse(
        authenticated=authenticated,
        demo_mode=False,
        upstream="reachable" if authenticated else "unavailable",
    )


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
    if not settings.demo_mode:
        if (
            not settings.urja_username
            or not settings.urja_password
        ):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "AUTH_REQUIRED",
                    "message": (
                        "Username and password must be configured."
                    ),
                },
            )

    try:
        await client.login()
    except PortalError as error:
        raise upstream_error(error) from error

    # This assumes client.login() only succeeds after
    # validating the actual portal login response.
    if not client.authenticated:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "AUTHENTICATION_FAILED",
                "message": "The portal session was not authenticated.",
            },
        )

    return SessionResponse(
        authenticated=True,
        demo_mode=settings.demo_mode,
        upstream="demo" if settings.demo_mode else "reachable",
    )


@app.post(
    "/api/v1/session/logout",
    response_model=SessionResponse,
    tags=["session"],
)
async def logout_session() -> SessionResponse:
    await client.logout()

    return SessionResponse(
        authenticated=client.authenticated,
        demo_mode=settings.demo_mode,
        upstream="demo" if settings.demo_mode else "unavailable",
    )


@app.get(
    "/api/v1/meters",
    response_model=MeterList,
    responses={
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    tags=["meters"],
)
async def list_meters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
) -> MeterList:
    if settings.demo_mode:
        meters = DEMO_METERS
        if search:
            term = search.casefold()
            meters = [
                meter
                for meter in meters
                if term in meter.model_dump_json().casefold()
            ]
        start = (page - 1) * page_size
        total = len(meters)
        items = meters[start : start + page_size]
    else:
        try:
            items, total = await portal_meter_page(search, page, page_size)
        except PortalError as error:
            raise upstream_error(error) from error

    return MeterList(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


@app.get(
    "/api/v1/meters/{meter_id}",
    response_model=Meter,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    tags=["meters"],
)
async def get_meter(meter_id: str) -> Meter:
    if settings.demo_mode:
        meters = DEMO_METERS
        if meter_id not in {meter.id for meter in meters}:
            meters = []
    else:
        try:
            meters, _ = await portal_meter_page(meter_id, 1, 100)
        except PortalError as error:
            raise upstream_error(error) from error

    for meter in meters:
        if meter.id == meter_id:
            return meter

    raise HTTPException(
        status_code=404,
        detail={
            "code": "METER_NOT_FOUND",
            "message": "Meter was not found in the portal.",
        },
    )


@app.get(
    "/api/v1/hierarchy",
    response_model=HierarchyResponse,
    responses={502: {"model": ErrorResponse}},
    tags=["hierarchy"],
)
async def hierarchy() -> HierarchyResponse:
    if settings.demo_mode:
        return HierarchyResponse(
            nodes=DEMO_HIERARCHY,
            available=True,
        )

    try:
        first_page, total, page_size = parse_portal_transformers(
            await client.get_json("/portal/dts?page=1")
        )
        nodes = first_page
        for page in range(2, (total + page_size - 1) // page_size + 1):
            next_nodes, _, next_page_size = parse_portal_transformers(
                await client.get_json(f"/portal/dts?page={page}")
            )
            if next_page_size != page_size:
                raise PortalError("The Urja portal returned inconsistent transformer pages.")
            nodes.extend(next_nodes)
    except ValueError as error:
        raise upstream_error(
            PortalError("The Urja portal returned invalid transformer data.")
        ) from error
    except PortalError as error:
        raise upstream_error(error) from error

    return HierarchyResponse(
        nodes=nodes,
        available=bool(nodes),
        message=(
            None
            if nodes
            else (
                "The portal did not return any distribution transformers."
            )
        ),
    )

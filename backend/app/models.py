from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class Meter(BaseModel):
    id: str
    serial_number: Optional[str] = None
    make: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    dt_code: Optional[str] = None
    network: Dict[str, Optional[str]] = Field(default_factory=dict)
    source_url: Optional[str] = None


class MeterList(BaseModel):
    items: List[Meter]
    page: int = 1
    page_size: int = 20
    total: int


class HierarchyNode(BaseModel):
    id: str
    label: str
    kind: str
    feeder_code: Optional[str] = None
    capacity_kva: Optional[int] = None
    children: List["HierarchyNode"] = Field(default_factory=list)


class HierarchyResponse(BaseModel):
    nodes: List[HierarchyNode]
    available: bool
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    upstream: str


class SessionResponse(BaseModel):
    authenticated: bool
    demo_mode: bool
    upstream: str

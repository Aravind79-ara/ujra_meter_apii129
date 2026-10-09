from __future__ import annotations

from datetime import datetime
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
    status: Optional[str] = None
    location: Optional[str] = None
    network: Dict[str, Optional[str]] = Field(default_factory=dict)
    source_url: Optional[str] = None


class MeterList(BaseModel):
    items: List[Meter]
    page: int = 1
    page_size: int = 20
    total: int


class Reading(BaseModel):
    timestamp: datetime
    value: float


class Consumption(BaseModel):
    meter_id: str
    unit: Optional[str] = None
    readings: List[Reading]


class HierarchyNode(BaseModel):
    id: str
    label: str
    kind: str
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



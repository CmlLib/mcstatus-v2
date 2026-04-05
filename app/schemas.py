from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ServerStatus(BaseModel):
    target: str
    status: str
    latency_ms: int | None = None
    timestamp: datetime
    data: dict[str, Any] | None = None


class HistoryRecord(BaseModel):
    id: int
    target: str
    status: str
    latency_ms: int | None = None
    timestamp: datetime
    data: dict[str, Any] | None = None


class HistoryResponse(BaseModel):
    target: str
    hours: int
    records: list[HistoryRecord]


class HealthResponse(BaseModel):
    api: str = "ok"
    redis: str
    database: str

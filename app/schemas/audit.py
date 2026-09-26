"""
app/schemas/audit.py
──────────────────────
Pydantic schemas for the Audit Log API.
"""
import csv
import io
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import Decision, EventType


class AuditLogResponse(BaseModel):
    """Single audit log entry as returned by the API."""
    id: int
    sequence_num: int
    event_id: str
    timestamp: datetime
    agent_id: str | None
    action_id: str | None
    event_type: str
    action: str | None
    amount: float | None
    currency: str | None
    decision: str | None
    reason_code: str | None
    metadata: dict[str, Any] | None = None
    previous_hash: str
    current_hash: str
    created_at: datetime


class AuditQueryParams(BaseModel):
    """Query parameters for filtering audit logs."""
    agent_id: str | None = None
    event_type: str | None = None
    decision: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)


class AuditListResponse(BaseModel):
    """Paginated list of audit entries."""
    total: int
    page: int
    page_size: int
    pages: int
    items: list[AuditLogResponse]


class AuditVerifyResponse(BaseModel):
    """Result of hash-chain verification."""
    valid: bool
    entries_checked: int
    first_invalid_entry: int | None = None  # sequence_num of first bad entry
    error: str | None = None
    message: str

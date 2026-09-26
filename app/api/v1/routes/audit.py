"""
app/api/v1/routes/audit.py
────────────────────────────
Audit Log API endpoints.

APPEND-ONLY NOTE: No PUT/PATCH/DELETE endpoints exist here.
Reading and verifying the chain is the only mutable-ish operation — verification.
"""
import csv
import io
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.audit import AuditListResponse, AuditLogResponse, AuditVerifyResponse
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get(
    "/logs",
    response_model=AuditListResponse,
    summary="Query audit logs with filtering and pagination",
)
def query_logs(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    decision: Optional[str] = Query(None, description="Filter by decision (ALLOW/DENY)"),
    start_time: Optional[datetime] = Query(None, description="Filter events after this time (ISO-8601)"),
    end_time: Optional[datetime] = Query(None, description="Filter events before this time (ISO-8601)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Results per page"),
    db: Session = Depends(get_db),
) -> AuditListResponse:
    """
    Paginated, filtered audit log query.
    All filter parameters are optional and combinable.
    Does not load the entire database into memory.
    """
    svc = AuditService(db)
    return svc.query_logs(
        agent_id=agent_id,
        event_type=event_type,
        decision=decision,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/logs/{event_id}",
    response_model=AuditLogResponse,
    summary="Get a specific audit log entry by event ID",
)
def get_log_entry(event_id: str, db: Session = Depends(get_db)) -> AuditLogResponse:
    svc = AuditService(db)
    entry = svc.get_by_event_id(event_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EVENT_NOT_FOUND", "message": f"Audit event '{event_id}' not found"},
        )
    return entry


@router.get(
    "/verify",
    response_model=AuditVerifyResponse,
    summary="Verify integrity of the entire audit hash chain",
)
def verify_chain(db: Session = Depends(get_db)) -> AuditVerifyResponse:
    """
    Re-computes every hash in the audit chain and verifies chain linkage.
    Returns the sequence number of the first invalid entry if tampering is detected.

    This is the core tamper-detection feature — run this after any suspected
    modification to confirm audit integrity.
    """
    svc = AuditService(db)
    return svc.verify_chain()


@router.get(
    "/export",
    summary="Export audit logs (JSON or CSV)",
    responses={
        200: {
            "description": "Audit log export",
            "content": {
                "application/json": {},
                "text/csv": {},
            },
        }
    },
)
def export_logs(
    fmt: str = Query("json", description="Export format: 'json' or 'csv'"),
    agent_id: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Export audit logs for compliance reporting.
    Includes: event_id, timestamp, agent, action, decision, reason,
              amount, currency, previous_hash, current_hash.
    """
    svc = AuditService(db)
    entries = svc.export_all(agent_id=agent_id, start_time=start_time, end_time=end_time)

    if fmt.lower() == "csv":
        output = io.StringIO()
        fieldnames = [
            "sequence_num", "event_id", "timestamp", "agent_id", "action_id",
            "event_type", "action", "amount", "currency", "decision",
            "reason_code", "previous_hash", "current_hash",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for e in entries:
            writer.writerow({
                "sequence_num": e.sequence_num,
                "event_id": e.event_id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else "",
                "agent_id": e.agent_id or "",
                "action_id": e.action_id or "",
                "event_type": e.event_type,
                "action": e.action or "",
                "amount": e.amount if e.amount is not None else "",
                "currency": e.currency or "",
                "decision": e.decision or "",
                "reason_code": e.reason_code or "",
                "previous_hash": e.previous_hash,
                "current_hash": e.current_hash,
            })
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_export.csv"},
        )

    # Default: JSON
    data = [e.model_dump(mode="json") for e in entries]
    return Response(
        content=json.dumps(data, default=str, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=audit_export.json"},
    )

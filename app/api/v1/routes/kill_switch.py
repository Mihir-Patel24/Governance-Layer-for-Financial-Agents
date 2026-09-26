"""
app/api/v1/routes/kill_switch.py
──────────────────────────────────
Kill Switch Service API endpoints.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.kill_switch import (
    AgentKillSwitchResponse,
    FleetKillSwitchResponse,
    KillSwitchRequest,
    KillSwitchStatusResponse,
)
from app.services.audit_service import AuditService
from app.services.kill_switch_service import KillSwitchService
from app.core.enums import Decision, EventType, ReasonCode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kill-switch", tags=["Kill Switch"])


@router.post(
    "/agent/{agent_id}",
    response_model=AgentKillSwitchResponse,
    summary="Halt a specific agent",
)
def halt_agent(
    agent_id: str,
    req: KillSwitchRequest,
    db: Session = Depends(get_db),
) -> AgentKillSwitchResponse:
    """
    Immediately halt the specified agent.
    The halt is persisted to PostgreSQL and propagated to Redis.
    Subsequent enforce() calls for this agent will be denied.
    """
    svc = KillSwitchService(db)
    audit = AuditService(db)
    try:
        result = svc.halt_agent(agent_id, req.reason, req.updated_by)
        audit.append_event(
            EventType.AGENT_HALTED,
            agent_id=agent_id,
            reason_code=ReasonCode.AGENT_HALTED,
            metadata={"reason": req.reason, "updated_by": req.updated_by},
        )
        db.commit()
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "AGENT_NOT_FOUND", "message": str(exc)},
        )


@router.post(
    "/agent/{agent_id}/resume",
    response_model=AgentKillSwitchResponse,
    summary="Resume a halted agent",
)
def resume_agent(
    agent_id: str,
    req: KillSwitchRequest,
    db: Session = Depends(get_db),
) -> AgentKillSwitchResponse:
    """Resume a previously halted agent."""
    svc = KillSwitchService(db)
    audit = AuditService(db)
    try:
        result = svc.resume_agent(agent_id, req.reason, req.updated_by)
        audit.append_event(
            EventType.AGENT_RESUMED,
            agent_id=agent_id,
            reason_code=None,
            metadata={"reason": req.reason, "updated_by": req.updated_by},
        )
        db.commit()
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "AGENT_NOT_FOUND", "message": str(exc)},
        )


@router.post(
    "/fleet",
    response_model=FleetKillSwitchResponse,
    summary="Halt the entire agent fleet",
)
def halt_fleet(
    req: KillSwitchRequest,
    db: Session = Depends(get_db),
) -> FleetKillSwitchResponse:
    """
    Emergency stop — halts ALL agents instantly.
    Individual agent status records are unchanged; the fleet-level halt
    takes precedence over all individual states.
    """
    svc = KillSwitchService(db)
    audit = AuditService(db)
    result = svc.halt_fleet(req.reason, req.updated_by)
    audit.append_event(
        EventType.FLEET_HALTED,
        reason_code=ReasonCode.FLEET_HALTED,
        metadata={"reason": req.reason, "updated_by": req.updated_by},
    )
    db.commit()
    return result


@router.post(
    "/fleet/resume",
    response_model=FleetKillSwitchResponse,
    summary="Resume the entire agent fleet",
)
def resume_fleet(
    req: KillSwitchRequest,
    db: Session = Depends(get_db),
) -> FleetKillSwitchResponse:
    """Resume all agents (fleet-level). Individual halts remain in effect."""
    svc = KillSwitchService(db)
    audit = AuditService(db)
    result = svc.resume_fleet(req.reason, req.updated_by)
    audit.append_event(
        EventType.FLEET_RESUMED,
        metadata={"reason": req.reason, "updated_by": req.updated_by},
    )
    db.commit()
    return result


@router.get(
    "/agent/{agent_id}",
    response_model=AgentKillSwitchResponse,
    summary="Get kill-switch state for a specific agent",
)
def get_agent_status(
    agent_id: str,
    db: Session = Depends(get_db),
) -> AgentKillSwitchResponse:
    svc = KillSwitchService(db)
    try:
        return svc.get_agent_status(agent_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "AGENT_NOT_FOUND", "message": str(exc)},
        )


@router.get(
    "/status",
    response_model=KillSwitchStatusResponse,
    summary="Get full kill-switch status (fleet + all agents)",
)
def get_full_status(db: Session = Depends(get_db)) -> KillSwitchStatusResponse:
    """Returns fleet status and per-agent halt state. Used by Person 4 dashboard."""
    svc = KillSwitchService(db)
    return svc.get_full_status()

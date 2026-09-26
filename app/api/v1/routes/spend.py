"""
app/api/v1/routes/spend.py
────────────────────────────
Spend Cap Service API endpoints.

All endpoints follow the Router → Service → Repository → DB pattern.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.spend import (
    BudgetConfigRequest,
    BudgetResetResponse,
    SpendCheckRequest,
    SpendCheckResponse,
    SpendReserveRequest,
    SpendStateResponse,
)
from app.schemas.action import EnforcementResult
from app.services.spend_cap_service import SpendCapService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/spend", tags=["Spend Cap"])


@router.get(
    "/{agent_id}",
    response_model=SpendStateResponse,
    summary="Get current budget state for an agent",
)
def get_spend_state(agent_id: str, db: Session = Depends(get_db)) -> SpendStateResponse:
    """Returns current spend, limit, and remaining budget for the agent."""
    svc = SpendCapService(db)
    result = svc.get_budget(agent_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BUDGET_NOT_FOUND", "message": f"No budget configured for agent '{agent_id}'"},
        )
    return result


@router.post(
    "/{agent_id}/configure",
    response_model=SpendStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Configure or update budget for an agent",
)
def configure_budget(
    agent_id: str,
    config: BudgetConfigRequest,
    db: Session = Depends(get_db),
) -> SpendStateResponse:
    """
    Set or update the spend limit for an agent.
    If a budget already exists, only the limit and currency are updated.
    """
    svc = SpendCapService(db)
    try:
        return svc.configure_budget(agent_id, config)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "AGENT_NOT_FOUND", "message": str(exc)},
        )


@router.post(
    "/check",
    response_model=SpendCheckResponse,
    summary="Check if a spend is within limits (non-destructive)",
)
def check_spend(
    req: SpendCheckRequest,
    db: Session = Depends(get_db),
) -> SpendCheckResponse:
    """Read-only check — does not consume budget. Used for pre-flight validation."""
    svc = SpendCapService(db)
    return svc.check_spend(req.agent_id, req.amount, req.currency)


@router.post(
    "/reserve",
    response_model=EnforcementResult,
    summary="Reserve (consume) spend for an agent",
)
def reserve_spend(
    req: SpendReserveRequest,
    db: Session = Depends(get_db),
) -> EnforcementResult:
    """
    Atomically check and consume budget. Idempotent on action_id.
    Note: This does NOT check kill-switch state. Use /enforce for full pipeline.
    """
    svc = SpendCapService(db)
    return svc.reserve_spend(
        agent_id=req.agent_id,
        action_id=req.action_id,
        amount=req.amount,
        currency=req.currency,
        action=req.action,
    )


@router.post(
    "/{agent_id}/reset",
    response_model=BudgetResetResponse,
    summary="Manually reset agent budget to a new period",
)
def reset_budget(
    agent_id: str,
    rollover_fraction: float = Query(0.0, ge=0.0, le=1.0,
                                     description="Fraction of unused budget to roll over (0.0 = no rollover)"),
    db: Session = Depends(get_db),
) -> BudgetResetResponse:
    """Force a budget period reset. Useful for operator actions and testing."""
    svc = SpendCapService(db)
    try:
        return svc.reset_budget(agent_id, rollover_fraction)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BUDGET_NOT_FOUND", "message": str(exc)},
        )

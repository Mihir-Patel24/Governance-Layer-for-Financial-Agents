"""
app/schemas/spend.py
──────────────────────
Pydantic schemas for the Spend Cap Service API.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import PeriodType


class SpendStateResponse(BaseModel):
    """Current budget status for an agent."""
    agent_id: str
    period_type: str
    period_start: datetime
    period_end: datetime
    limit_amount: float
    spent_amount: float
    remaining_amount: float
    currency: str
    rollover_amount: float
    reset_at: datetime | None = None
    updated_at: datetime


class BudgetConfigRequest(BaseModel):
    """Configure or update a budget for an agent."""
    limit_amount: float = Field(..., gt=0, description="Maximum spend for the period (must be > 0)")
    currency: str = Field("INR", description="ISO-4217 currency code")
    period_type: PeriodType = Field(PeriodType.DAILY, description="Budget reset period")
    rollover_amount: float = Field(0.0, ge=0, description="Amount carried over from previous period")

    model_config = {"json_schema_extra": {
        "example": {
            "limit_amount": 15000,
            "currency": "INR",
            "period_type": "DAILY",
            "rollover_amount": 0.0,
        }
    }}


class SpendCheckRequest(BaseModel):
    """Check if a spend is within limits (read-only, no state change)."""
    agent_id: str
    amount: float = Field(..., ge=0)
    currency: str = "INR"
    action_id: str | None = None


class SpendCheckResponse(BaseModel):
    """Result of a spend check (no state change)."""
    agent_id: str
    requested_amount: float
    currency: str
    allowed: bool
    remaining_budget: float
    reason: str | None = None


class SpendReserveRequest(BaseModel):
    """Reserve (consume) spend for an agent — causes state change."""
    agent_id: str
    action_id: str = Field(..., description="Idempotency key")
    amount: float = Field(..., ge=0)
    currency: str = "INR"
    action: str | None = None


class BudgetResetResponse(BaseModel):
    """Result of a manual budget reset."""
    agent_id: str
    old_spent: float
    new_spent: float
    period_start: datetime
    period_end: datetime
    message: str

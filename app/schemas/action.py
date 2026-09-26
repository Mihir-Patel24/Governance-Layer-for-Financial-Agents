"""
app/schemas/action.py
──────────────────────
Request/response models for action enforcement.
These are the shared API contracts between Person 1 (Policy Gateway)
and Person 2 (Enforcer), and between Person 2 and Person 4 (Dashboard).
"""
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.enums import Decision, ReasonCode

SUPPORTED_CURRENCIES = {"INR", "USD", "EUR", "GBP"}


class ActionRequest(BaseModel):
    """
    Payload that an agent sends to the governance system.
    Person 1 receives this and forwards the policy decision to Person 2.
    Person 2 also accepts this directly for spend/kill-switch enforcement.
    """
    agent_id: str = Field(..., description="Unique identifier of the requesting agent")
    action_id: str = Field(..., description="Unique idempotency key for this action")
    action: str = Field(..., description="Human-readable action name, e.g. BOOK_FLIGHT")
    amount: float = Field(..., ge=0, description="Amount in the specified currency")
    currency: str = Field("INR", description="ISO-4217 currency code")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        upper = v.upper()
        if upper not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency '{v}'. Supported: {SUPPORTED_CURRENCIES}")
        return upper

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v < 0:
            raise ValueError("amount must be non-negative")
        return v

    model_config = {"json_schema_extra": {
        "example": {
            "agent_id": "travel-agent",
            "action_id": "txn-001",
            "action": "BOOK_FLIGHT",
            "amount": 20000,
            "currency": "INR",
        }
    }}


class EnforcementResult(BaseModel):
    """
    Structured enforcement decision returned to the caller.
    Includes machine-readable reason_code so Person 4 can display specific UI.
    """
    allowed: bool
    reason_code: ReasonCode
    agent_id: str
    action_id: str
    requested_amount: float
    currency: str
    remaining_budget: float | None = None
    is_duplicate: bool = False
    metadata: dict[str, Any] | None = None

    model_config = {"json_schema_extra": {
        "example": {
            "allowed": False,
            "reason_code": "SPEND_CAP_EXCEEDED",
            "agent_id": "travel-agent",
            "action_id": "txn-001",
            "requested_amount": 20000,
            "currency": "INR",
            "remaining_budget": 3000,
            "is_duplicate": False,
        }
    }}

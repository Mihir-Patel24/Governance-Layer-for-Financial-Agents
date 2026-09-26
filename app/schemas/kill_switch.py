"""
app/schemas/kill_switch.py
────────────────────────────
Pydantic schemas for the Kill Switch Service API.
"""
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import AgentStatus, FleetStatus


class KillSwitchRequest(BaseModel):
    """Request body to halt or resume an agent."""
    reason: str = Field(..., min_length=1, max_length=512)
    updated_by: str = Field("operator", max_length=64)

    model_config = {"json_schema_extra": {
        "example": {
            "reason": "Security investigation — suspicious transaction pattern",
            "updated_by": "operator-1",
        }
    }}


class AgentKillSwitchResponse(BaseModel):
    """Current kill-switch state for a single agent."""
    agent_id: str
    status: AgentStatus
    reason: str | None
    updated_by: str | None
    updated_at: datetime
    effective_status: AgentStatus  # accounts for fleet halt


class FleetKillSwitchResponse(BaseModel):
    """Current fleet kill-switch state."""
    status: FleetStatus
    reason: str | None
    updated_by: str | None
    updated_at: datetime
    agents_affected: int


class KillSwitchStatusResponse(BaseModel):
    """Full kill-switch status (fleet + per-agent)."""
    fleet_status: FleetStatus
    fleet_reason: str | None
    fleet_updated_at: datetime | None
    agents: list[AgentKillSwitchResponse]

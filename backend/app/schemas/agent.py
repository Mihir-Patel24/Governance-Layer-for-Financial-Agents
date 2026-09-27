from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.enums import AgentStatusEnum

class AgentPolicyConfig(BaseModel):
    agent_id: str = Field(..., description="Unique agent key")
    agent_name: str = Field(..., description="Agent display name")
    agent_type: str = Field(..., description="Domain category e.g. banking, government")
    status: AgentStatusEnum = Field(AgentStatusEnum.ACTIVE)
    single_tx_limit: float = Field(10000.0, ge=0.0)
    daily_spend_cap: float = Field(50000.0, ge=0.0)
    monthly_spend_cap: float = Field(500000.0, ge=0.0)
    allowed_actions: List[str] = Field(default_factory=list)
    allowed_start_hour: int = Field(0, ge=0, le=24)
    allowed_end_hour: int = Field(24, ge=0, le=24)
    current_daily_spend: float = Field(0.0, ge=0.0)
    created_at: Optional[str] = None

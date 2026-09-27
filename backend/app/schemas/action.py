from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.core.enums import VerdictEnum

class RecipientInfo(BaseModel):
    id: str = Field(..., description="Unique recipient or beneficiary identifier")
    category: Optional[str] = Field("default", description="Classification e.g. individual, merchant")
    account_number: Optional[str] = Field(None, description="Account string")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ActionRequest(BaseModel):
    agent_id: str = Field(..., example="travel-agent-01")
    agent_type: str = Field(..., example="banking")
    action_type: str = Field(..., example="book_flight")
    amount: float = Field(0.0, ge=0.0, example=8000.0)
    currency: str = Field("INR", example="INR")
    recipient: Optional[RecipientInfo] = None
    description: Optional[str] = ""
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: Optional[str] = None

class ActionResponse(BaseModel):
    request_id: str
    agent_id: str
    verdict: VerdictEnum
    policy_passed: bool
    spend_cap_passed: bool
    ml_anomaly_score: float
    is_anomaly: bool
    reason: str
    llm_explanation: Optional[str] = None
    audit_hash: str
    timestamp: str
    execution_latency_ms: float = 0.0

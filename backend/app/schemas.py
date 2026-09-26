from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class VerdictEnum(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    HITL_REQUIRED = "HITL_REQUIRED"

class AgentStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    TERMINATED = "TERMINATED"

class RecipientInfo(BaseModel):
    id: str = Field(..., description="Unique recipient or beneficiary identifier")
    category: Optional[str] = Field("default", description="Recipient classification e.g. individual, merchant, relief_fund")
    account_number: Optional[str] = Field(None, description="Optional account/wallet string")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context metadata")

class ActionRequest(BaseModel):
    agent_id: str = Field(..., example="travel-agent-01", description="Unique agent instance identifier")
    agent_type: str = Field(..., example="banking", description="Domain classification e.g. banking, government, healthcare")
    action_type: str = Field(..., example="book_flight", description="Action name requested by agent")
    amount: float = Field(0.0, ge=0.0, example=8000.0, description="Transaction financial value")
    currency: str = Field("INR", example="INR", description="Currency ISO code")
    recipient: Optional[RecipientInfo] = Field(None, description="Target recipient information")
    description: Optional[str] = Field("", description="Human readable action rationale")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution environment context (IP, location, session)")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of request generation")

class AgentPolicyConfig(BaseModel):
    agent_id: str = Field(..., description="Unique agent identifier key")
    agent_name: str = Field(..., description="Human-readable agent display name")
    agent_type: str = Field(..., description="Domain category e.g. banking, government, healthcare")
    status: AgentStatusEnum = Field(AgentStatusEnum.ACTIVE, description="Agent operational status")
    single_tx_limit: float = Field(10000.0, ge=0.0, description="Maximum allowed amount per single transaction")
    daily_spend_cap: float = Field(50000.0, ge=0.0, description="Maximum rolling 24-hour spend cap")
    monthly_spend_cap: float = Field(500000.0, ge=0.0, description="Maximum monthly spend cap")
    allowed_actions: List[str] = Field(default_factory=list, description="Whitelist of action names allowed for this agent")
    allowed_start_hour: int = Field(0, ge=0, le=24, description="Daily execution window start hour (0-24)")
    allowed_end_hour: int = Field(24, ge=0, le=24, description="Daily execution window end hour (0-24)")
    max_requests_per_min: int = Field(60, ge=1, description="Rate limit max requests per minute")
    current_daily_spend: float = Field(0.0, ge=0.0, description="Current accumulated spend for today")
    created_at: Optional[str] = Field(None, description="Registration timestamp")

class ActionResponse(BaseModel):
    request_id: str = Field(..., description="Unique request tracing ID")
    agent_id: str = Field(..., description="Agent identifier evaluating request")
    verdict: VerdictEnum = Field(..., description="Final governance decision: ALLOW, BLOCK, or HITL_REQUIRED")
    policy_passed: bool = Field(..., description="Whether policy engine checks passed")
    spend_cap_passed: bool = Field(..., description="Whether spend cap limits passed")
    ml_anomaly_score: float = Field(..., description="Isolation Forest anomaly score between 0.0 and 1.0")
    is_anomaly: bool = Field(..., description="True if anomaly score exceeds threshold (>0.70)")
    reason: str = Field(..., description="Detailed governance evaluation rationale")
    llm_explanation: Optional[str] = Field(None, description="Plain-English LLM block explanation")
    audit_hash: str = Field(..., description="SHA-256 cryptographic hash block in audit chain")
    timestamp: str = Field(..., description="Evaluation completion timestamp")
    execution_latency_ms: float = Field(0.0, description="Inline governance evaluation latency in milliseconds")

class KillSwitchPayload(BaseModel):
    agent_id: Optional[str] = Field(None, description="If provided, kills specific agent. If None, triggers global fleet stop.")
    reason: str = Field("Manual Operator Intervention", description="Reason for triggering kill switch")

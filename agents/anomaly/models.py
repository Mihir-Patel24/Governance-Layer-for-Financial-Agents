from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AnomalyType(str, Enum):
    """Controlled set of behavioral anomaly classifications."""
    NORMAL = "NORMAL"
    SPENDING_SPIKE = "SPENDING_SPIKE"
    RAPID_ACTION_BURST = "RAPID_ACTION_BURST"
    UNAUTHORIZED_ACTION = "UNAUTHORIZED_ACTION"


class AnomalyResult(BaseModel):
    """
    Standardized data contract for anomaly detection outputs.
    Serves Person 4's dashboard interface and will remain identical when
    the dummy detector is replaced by real ML models (Isolation Forest / Z-score).
    """
    anomaly_id: str = Field(..., example="anom-001", description="Unique anomaly record identifier")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO timestamp of record")
    agent_id: str = Field(..., example="servicing-agent-01", description="Agent instance identifier")
    agent_type: str = Field("banking", example="banking", description="Domain classification e.g. banking")
    action_type: str = Field(..., example="fee_reversal", description="Name of action evaluated")
    amount: float = Field(0.0, ge=0.0, example=500.0, description="Financial transaction value")
    currency: str = Field("INR", example="INR", description="Currency ISO code")
    anomaly_score: float = Field(0.0, ge=0.0, le=1.0, example=0.91, description="Normalized score between 0.0 (normal) and 1.0 (anomalous)")
    is_anomaly: bool = Field(..., description="True if anomaly score exceeds detection threshold")
    anomaly_type: AnomalyType = Field(..., description="Behavioral classification label")
    reason: str = Field(..., description="Human-readable explanation of why the action was flagged")
    source: str = Field("dummy", description="Data source indicator ('dummy' for mid-sem, 'ml' for end-sem)")


class AnomalyResponse(BaseModel):
    """Top-level API payload contract for Person 4 dashboard consumption."""
    source: str = Field("dummy", description="Provider indicator")
    count: int = Field(..., description="Total number of records in feed")
    anomalies: List[AnomalyResult] = Field(default_factory=list, description="List of anomaly evaluation items")

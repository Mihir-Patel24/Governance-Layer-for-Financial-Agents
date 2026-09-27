from typing import List, Optional, Dict, Any
from datetime import datetime
from agents.anomaly.detector import BaseAnomalyDetector
from agents.anomaly.models import AnomalyResult, AnomalyType


class DummyAnomalyDetector(BaseAnomalyDetector):
    """
    Mid-Semester Anomaly Detection Data & Response Contract Provider.
    Produces a deterministic dummy anomaly feed for Person 4's dashboard integration.
    
    IMPORTANT:
    - Scores (0.0 = normal, 1.0 = highly anomalous) and anomaly labels are illustrative dummy data.
    - No ML models (Isolation Forest / Z-score) are used in this mid-sem module.
    - Preserves exact response contract for end-sem ML replacement.
    """

    def __init__(self):
        self._dataset: List[AnomalyResult] = self._build_deterministic_dataset()

    def _build_deterministic_dataset(self) -> List[AnomalyResult]:
        now = datetime.now().isoformat()
        return [
            # CASE 1: Normal Travel Booking
            AnomalyResult(
                anomaly_id="anom-dummy-001",
                timestamp=now,
                agent_id="travel-agent-01",
                agent_type="banking",
                action_type="book_flight",
                amount=8000.0,
                currency="INR",
                anomaly_score=0.05,
                is_anomaly=False,
                anomaly_type=AnomalyType.NORMAL,
                reason="Normal travel booking behavior.",
                source="dummy"
            ),
            # CASE 2: Travel Spending Spike
            AnomalyResult(
                anomaly_id="anom-dummy-002",
                timestamp=now,
                agent_id="travel-agent-01",
                agent_type="banking",
                action_type="book_flight",
                amount=25000.0,
                currency="INR",
                anomaly_score=0.88,
                is_anomaly=True,
                anomaly_type=AnomalyType.SPENDING_SPIKE,
                reason="Transaction amount is significantly higher than the simulated normal travel behavior.",
                source="dummy"
            ),
            # CASE 3: Normal Servicing Activity
            AnomalyResult(
                anomaly_id="anom-dummy-003",
                timestamp=now,
                agent_id="servicing-agent-01",
                agent_type="banking",
                action_type="fee_reversal",
                amount=500.0,
                currency="INR",
                anomaly_score=0.02,
                is_anomaly=False,
                anomaly_type=AnomalyType.NORMAL,
                reason="Normal servicing activity.",
                source="dummy"
            ),
            # CASE 4: Rapid Servicing Burst
            AnomalyResult(
                anomaly_id="anom-dummy-004",
                timestamp=now,
                agent_id="servicing-agent-01",
                agent_type="banking",
                action_type="fee_reversal",
                amount=500.0,
                currency="INR",
                anomaly_score=0.91,
                is_anomaly=True,
                anomaly_type=AnomalyType.RAPID_ACTION_BURST,
                reason="Multiple fee reversal actions occurred within a short interval.",
                source="dummy"
            ),
            # CASE 5: Normal Rewards Activity
            AnomalyResult(
                anomaly_id="anom-dummy-005",
                timestamp=now,
                agent_id="rewards-agent-01",
                agent_type="banking",
                action_type="redeem_points",
                amount=0.0,
                currency="INR",
                anomaly_score=0.01,
                is_anomaly=False,
                anomaly_type=AnomalyType.NORMAL,
                reason="Normal rewards activity.",
                source="dummy"
            ),
            # CASE 6: Unauthorized Rewards Action
            AnomalyResult(
                anomaly_id="anom-dummy-006",
                timestamp=now,
                agent_id="rewards-agent-01",
                agent_type="banking",
                action_type="cash_withdrawal",
                amount=5000.0,
                currency="INR",
                anomaly_score=0.95,
                is_anomaly=True,
                anomaly_type=AnomalyType.UNAUTHORIZED_ACTION,
                reason="The action type is outside the simulated Rewards Agent activity profile.",
                source="dummy"
            )
        ]

    def get_dummy_feed(self, agent_id: Optional[str] = None) -> List[AnomalyResult]:
        """Returns deterministic dummy feed filtered optionally by agent_id."""
        if agent_id:
            return [item for item in self._dataset if item.agent_id == agent_id]
        return list(self._dataset)

    def detect(self, records: Optional[List[Dict[str, Any]]] = None) -> List[AnomalyResult]:
        """
        Implementation of BaseAnomalyDetector contract.
        For mid-sem dummy detector, returns the deterministic dataset regardless of input records.
        """
        return self.get_dummy_feed()

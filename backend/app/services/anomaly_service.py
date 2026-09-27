import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Tuple, Dict, Any, Optional

class AnomalyDetectorService:
    """
    Person 3 Deliverable:
    Unsupervised ML Anomaly Detector using Isolation Forest.
    Evaluates real-time agent telemetry for out-of-distribution risks.
    """
    def __init__(self):
        self.model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        self._train_baseline()

    def _train_baseline(self):
        """Train Isolation Forest model on baseline telemetry data"""
        np.random.seed(42)
        normal_amounts = np.random.uniform(100, 5000, 1000)
        normal_hours = np.random.uniform(9, 18, 1000) # business hours
        normal_velocity = np.random.poisson(2, 1000)
        normal_ratios = normal_amounts / 15000.0

        X_train = np.column_stack((normal_amounts, normal_hours, normal_velocity, normal_ratios))
        self.model.fit(X_train)

    def predict_anomaly(
        self,
        amount: float,
        hour: int = 14,
        velocity: int = 1,
        limit: float = 15000.0,
        action_type: str = "default"
    ) -> Tuple[float, bool]:
        """
        Calculate anomaly score (0.0 to 1.0) and return (score, is_anomaly)
        Threshold > 0.70 triggers HITL_REQUIRED verdict.
        """
        ratio = amount / max(limit, 1.0)
        features = np.array([[amount, hour, velocity, ratio]])

        raw_score = self.model.decision_function(features)[0]
        # Normalize score to [0.0, 1.0] range
        anomaly_score = float(np.clip(0.5 - raw_score, 0.0, 1.0))

        # Contextual anomaly heuristics (off-hours execution or extreme limit ratio)
        if ratio > 0.85 or hour < 6 or hour > 23:
            anomaly_score = max(anomaly_score, 0.78)

        is_anomaly = anomaly_score > 0.70
        return round(anomaly_score, 3), is_anomaly

anomaly_service = AnomalyDetectorService()

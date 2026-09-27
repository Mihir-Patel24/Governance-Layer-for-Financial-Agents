"""
Person 3 Anomaly Detection Package.
Provides data models, detector interface contracts, and dummy/hardcoded detector
implementations for mid-semester dashboard integration.
"""

from agents.anomaly.models import AnomalyType, AnomalyResult, AnomalyResponse
from agents.anomaly.detector import BaseAnomalyDetector
from agents.anomaly.dummy_detector import DummyAnomalyDetector

__all__ = [
    "AnomalyType",
    "AnomalyResult",
    "AnomalyResponse",
    "BaseAnomalyDetector",
    "DummyAnomalyDetector",
]

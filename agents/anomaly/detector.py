from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from agents.anomaly.models import AnomalyResult


class BaseAnomalyDetector(ABC):
    """
    Abstract interface contract for Person 3 Anomaly Detection implementations.
    Guarantees seamless replacement of the mid-sem dummy detector with future ML detectors
    (Isolation Forest / Z-score) without altering the Person 4 API response format.
    """

    @abstractmethod
    def detect(self, records: Optional[List[Dict[str, Any]]] = None) -> List[AnomalyResult]:
        """
        Evaluates input action records and returns a list of AnomalyResult objects.
        
        Args:
            records: List of raw action dictionaries (e.g., from simulation history or stream)
            
        Returns:
            List of standardized AnomalyResult Pydantic objects.
        """
        pass

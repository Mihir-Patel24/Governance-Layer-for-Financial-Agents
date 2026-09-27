import os
from typing import Optional
from fastapi import FastAPI, Query, status
from fastapi.middleware.cors import CORSMiddleware

from agents.anomaly.dummy_detector import DummyAnomalyDetector
from agents.anomaly.models import AnomalyResponse

app = FastAPI(
    title="SentinelAI Person 3 Anomaly Detection Service",
    description="Mid-Semester Anomaly Detection Data Contract & Dummy Provider API for Person 4 Dashboard Integration.",
    version="1.0.0"
)

# Enable CORS for React frontend dashboard (Person 4 integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate mid-sem dummy detector
detector = DummyAnomalyDetector()


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Simple service health check endpoint for Person 4 dashboard verification."""
    return {
        "status": "ok",
        "service": "person3-anomaly-service",
        "mode": "dummy"
    }


@app.get("/api/anomalies", response_model=AnomalyResponse, status_code=status.HTTP_200_OK)
def list_anomalies(agent_id: Optional[str] = Query(None, description="Optional agent ID filter e.g. servicing-agent-01")):
    """
    Person 3 API Contract Endpoint:
    Returns the deterministic anomaly detection feed for dashboard visualization.
    Allows optional single-agent filtering via ?agent_id=...
    """
    anomalies = detector.get_dummy_feed(agent_id=agent_id)
    return AnomalyResponse(
        source="dummy",
        count=len(anomalies),
        anomalies=anomalies
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

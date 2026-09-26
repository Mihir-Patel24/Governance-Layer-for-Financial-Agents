import os
import uuid
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Try loading environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.schemas import (
    ActionRequest, ActionResponse, VerdictEnum, AgentPolicyConfig
)
from app.policy_engine import policy_engine

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
MAX_POLICY_TIMEOUT_MS = float(os.getenv("MAX_POLICY_TIMEOUT_MS", "20.0"))

app = FastAPI(
    title="SentinelAI Governance Engine",
    description="Person 1 API Gateway & Policy Engine for Autonomous Financial and Enterprise Agents.",
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

@app.get("/")
def read_root():
    """Health check endpoint showing backend system status and registered agents count"""
    return {
        "system": "SentinelAI Policy Gateway",
        "status": "ONLINE",
        "environment": ENVIRONMENT,
        "owner": "Person 1 - Policy Architect",
        "registered_agents_count": len(policy_engine.list_agents()),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/governance/evaluate", response_model=ActionResponse, status_code=status.HTTP_200_OK)
def evaluate_action(req: ActionRequest):
    """
    Person 1 Core Backend Route:
    Evaluates incoming ActionRequest against dynamic AgentPolicyConfig rules.
    Measures execution latency and guarantees Fail-Closed behavior.
    """
    start_time = time.perf_counter()
    request_id = f"req-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now().isoformat()

    # Step 1: Execute Person 1 Policy Engine Evaluation
    policy_passed, policy_reason = policy_engine.evaluate_policy(req, max_timeout_ms=MAX_POLICY_TIMEOUT_MS)

    # Step 2: Determine Verdict
    if policy_passed:
        verdict = VerdictEnum.ALLOW
        reason = policy_reason
    else:
        verdict = VerdictEnum.BLOCK
        reason = policy_reason

    # Calculate exact governance evaluation latency
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return ActionResponse(
        request_id=request_id,
        agent_id=req.agent_id,
        verdict=verdict,
        policy_passed=policy_passed,
        spend_cap_passed=True,  # Person 2 extension stub
        ml_anomaly_score=0.05,  # Person 3 extension stub
        is_anomaly=False,        # Person 3 extension stub
        reason=reason,
        llm_explanation=None,   # Person 3 extension stub
        audit_hash=f"hash-{uuid.uuid4().hex[:12]}", # Person 2 extension stub
        timestamp=timestamp,
        execution_latency_ms=round(elapsed_ms, 3)
    )

@app.get("/api/agents")
def list_registered_agents():
    """List all dynamically registered agent profiles"""
    return policy_engine.list_agents()

@app.post("/api/agents/register", status_code=status.HTTP_201_CREATED)
def register_agent_profile(config: AgentPolicyConfig):
    """Dynamically register a new agent policy profile (e.g., Government Subsidy Agent)"""
    policy_engine.register_agent(config)
    return {
        "message": f"Agent '{config.agent_id}' registered successfully.",
        "config": config
    }

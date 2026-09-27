from fastapi import APIRouter, status
from app.schemas.agent import AgentPolicyConfig
from app.services.policy_engine import policy_engine

router = APIRouter()

@router.get("/")
def list_agents():
    """List registered agent profiles"""
    return policy_engine.list_agents()

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_agent(config: AgentPolicyConfig):
    """Dynamically register a new agent policy profile (e.g. Government Subsidy Agent)"""
    policy_engine.register_agent(config)
    return {"message": f"Agent '{config.agent_id}' registered successfully.", "config": config}

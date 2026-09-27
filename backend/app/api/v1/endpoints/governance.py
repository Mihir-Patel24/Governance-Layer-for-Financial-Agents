from fastapi import APIRouter, status
from app.schemas.action import ActionRequest, ActionResponse
from app.services.governance_orchestrator import governance_orchestrator

router = APIRouter()

@router.post("/evaluate", response_model=ActionResponse, status_code=status.HTTP_200_OK)
def evaluate_action(req: ActionRequest):
    """
    Unified Inline Governance Endpoint:
    Integrates Person 1 Policy Engine with Person 2 Spend Caps, Circuit Breaker, & Audit Ledger.
    """
    return governance_orchestrator.evaluate_action_request(req)

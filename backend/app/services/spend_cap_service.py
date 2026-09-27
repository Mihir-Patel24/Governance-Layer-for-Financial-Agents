from typing import Tuple, Dict
from app.schemas.action import ActionRequest
from app.schemas.agent import AgentPolicyConfig

class SpendCapService:
    """Person 2 Deliverable: Multi-Window Rolling Spend Limit Tracker"""
    def __init__(self):
        self.daily_spend_ledger: Dict[str, float] = {}
        self.monthly_spend_ledger: Dict[str, float] = {}

    def check_and_reserve(self, req: ActionRequest, agent: AgentPolicyConfig) -> Tuple[bool, str, float]:
        current_daily = self.daily_spend_ledger.get(req.agent_id, 0.0)
        projected_daily = current_daily + req.amount

        if projected_daily > agent.daily_spend_cap:
            return False, (
                f"Daily spend cap breached! Attempted total ₹{projected_daily:,.2f} "
                f"exceeds limit of ₹{agent.daily_spend_cap:,.2f} "
                f"(Current spend today: ₹{current_daily:,.2f})."
            ), current_daily

        # Reserve spend amount
        self.daily_spend_ledger[req.agent_id] = projected_daily
        agent.current_daily_spend = projected_daily
        return True, f"Spend cap check passed. New daily total: ₹{projected_daily:,.2f}.", projected_daily

    def get_current_daily_spend(self, agent_id: str) -> float:
        return self.daily_spend_ledger.get(agent_id, 0.0)

spend_cap_service = SpendCapService()

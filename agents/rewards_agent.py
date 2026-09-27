from typing import Dict, Any, Optional, List
from agents.base_agent import BaseAgent
from agents.scenarios import ScenarioType, ScenarioGenerator
from agents.state import AgentState


class RewardsAgent(BaseAgent):
    """
    Simulated Autonomous Rewards Agent.
    Identity: rewards-agent-01 (banking domain)
    Supported Actions: redeem_points, transfer_points, apply_reward
    Auto-registers profile with backend using Person 1's POST /api/agents/register.
    """

    def __init__(self, governance_url: str = "http://localhost:8000", auto_register: bool = True):
        super().__init__(
            agent_id="rewards-agent-01",
            agent_type="banking",
            governance_url=governance_url
        )
        if auto_register:
            self.register_agent_profile()

    def register_agent_profile(self) -> Dict[str, Any]:
        """
        Registers rewards-agent-01 with Person 1's backend via POST /api/agents/register
        Conforms strictly to AgentPolicyConfig schema.
        """
        config = {
            "agent_id": self.agent_id,
            "agent_name": "Rewards & Loyalty Concierge",
            "agent_type": self.agent_type,
            "status": "ACTIVE",
            "single_tx_limit": 5000.0,
            "daily_spend_cap": 20000.0,
            "monthly_spend_cap": 100000.0,
            "allowed_actions": ["redeem_points", "transfer_points", "apply_reward"],
            "allowed_start_hour": 0,
            "allowed_end_hour": 24,
            "max_requests_per_min": 60,
            "current_daily_spend": 0.0
        }
        res = self.governance_client.register_agent(config)
        return res

    def redeem_points(
        self,
        amount: float = 0.0,
        currency: str = "INR",
        description: str = "Redeem loyalty reward points",
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        action = self.generate_action(
            action_type="redeem_points",
            amount=amount,
            currency=currency,
            description=description,
            context=context or {}
        )
        return self.submit_action(action)

    def transfer_points(
        self,
        amount: float = 0.0,
        currency: str = "INR",
        description: str = "Transfer points to partner account",
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        action = self.generate_action(
            action_type="transfer_points",
            amount=amount,
            currency=currency,
            description=description,
            context=context or {}
        )
        return self.submit_action(action)

    def apply_reward(
        self,
        amount: float = 0.0,
        currency: str = "INR",
        description: str = "Apply reward code or promotional credit",
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        action = self.generate_action(
            action_type="apply_reward",
            amount=amount,
            currency=currency,
            description=description,
            context=context or {}
        )
        return self.submit_action(action)

    def run_scenario(self, scenario_type: ScenarioType) -> List[AgentState]:
        """
        Executes a predefined scenario sequence through Person 1's governance backend.
        """
        actions = ScenarioGenerator.get_rewards_scenario(scenario_type)
        results = []
        for act_spec in actions:
            action = self.generate_action(
                action_type=act_spec["action_type"],
                amount=act_spec.get("amount", 0.0),
                currency=act_spec.get("currency", "INR"),
                recipient=act_spec.get("recipient"),
                description=act_spec.get("description", ""),
                context=act_spec.get("context", {})
            )
            state = self.submit_action(action)
            results.append(state)
            self._print_execution_feedback(state)
        return results

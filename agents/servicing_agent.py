from typing import Dict, Any, Optional, List
from agents.base_agent import BaseAgent
from agents.scenarios import ScenarioType, ScenarioGenerator
from agents.state import AgentState


class ServicingAgent(BaseAgent):
    """
    Simulated Autonomous Customer Servicing Agent.
    Identity: servicing-agent-01 (banking domain)
    Supported Actions: fee_reversal, issue_credit, update_address
    """

    def __init__(self, governance_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="servicing-agent-01",
            agent_type="banking",
            governance_url=governance_url
        )

    def fee_reversal(
        self,
        amount: float = 500.0,
        currency: str = "INR",
        description: str = "Reverse service fee for customer",
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        action = self.generate_action(
            action_type="fee_reversal",
            amount=amount,
            currency=currency,
            description=description,
            context=context or {}
        )
        return self.submit_action(action)

    def issue_credit(
        self,
        amount: float = 300.0,
        currency: str = "INR",
        description: str = "Issue customer service credit",
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        action = self.generate_action(
            action_type="issue_credit",
            amount=amount,
            currency=currency,
            description=description,
            context=context or {}
        )
        return self.submit_action(action)

    def update_address(
        self,
        description: str = "Update customer address",
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        action = self.generate_action(
            action_type="update_address",
            amount=0.0,
            currency="INR",
            description=description,
            context=context or {}
        )
        return self.submit_action(action)

    def run_scenario(self, scenario_type: ScenarioType) -> List[AgentState]:
        """
        Executes a predefined scenario sequence through Person 1's governance backend.
        """
        actions = ScenarioGenerator.get_servicing_scenario(scenario_type)
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

    def _print_execution_feedback(self, state: AgentState):
        verdict = state.get("verdict")
        action = state.get("current_action", {})
        act_type = action.get("action_type")

        if verdict == "ALLOW":
            print(f"  [EXECUTION] Simulated Servicing Action '{act_type}' COMPLETED successfully.")
        elif verdict == "BLOCK":
            print(f"  [GOVERNANCE BLOCK] Servicing Action '{act_type}' BLOCKED by governance policy.")
        elif verdict == "HITL_REQUIRED":
            print(f"  [HITL REQUIRED] Servicing Action '{act_type}' PENDING HUMAN APPROVAL.")
        else:
            print(f"  [ERROR] Servicing Action '{act_type}' FAILED execution.")

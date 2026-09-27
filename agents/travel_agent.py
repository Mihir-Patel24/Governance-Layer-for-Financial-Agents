from typing import Dict, Any, Optional, List
from agents.base_agent import BaseAgent
from agents.scenarios import ScenarioType, ScenarioGenerator
from agents.state import AgentState


class TravelAgent(BaseAgent):
    """
    Simulated Autonomous Travel Agent.
    Identity: travel-agent-01 (banking domain)
    Supported Actions: book_flight, book_hotel, cancel_booking
    """

    def __init__(self, governance_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="travel-agent-01",
            agent_type="banking",
            governance_url=governance_url
        )

    def book_flight(
        self,
        amount: float = 8000.0,
        currency: str = "INR",
        recipient: Optional[Dict[str, Any]] = None,
        description: str = "Book flight for customer",
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        action = self.generate_action(
            action_type="book_flight",
            amount=amount,
            currency=currency,
            recipient=recipient or {"id": "airline-default", "category": "airline"},
            description=description,
            context=context or {}
        )
        return self.submit_action(action)

    def book_hotel(
        self,
        amount: float = 5000.0,
        currency: str = "INR",
        recipient: Optional[Dict[str, Any]] = None,
        description: str = "Book hotel for customer",
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        action = self.generate_action(
            action_type="book_hotel",
            amount=amount,
            currency=currency,
            recipient=recipient or {"id": "hotel-default", "category": "hotel"},
            description=description,
            context=context or {}
        )
        return self.submit_action(action)

    def cancel_booking(
        self,
        amount: float = 0.0,
        currency: str = "INR",
        recipient: Optional[Dict[str, Any]] = None,
        description: str = "Cancel existing travel booking",
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        action = self.generate_action(
            action_type="cancel_booking",
            amount=amount,
            currency=currency,
            recipient=recipient,
            description=description,
            context=context or {}
        )
        return self.submit_action(action)

    def run_scenario(self, scenario_type: ScenarioType) -> List[AgentState]:
        """
        Executes a predefined scenario sequence through Person 1's governance backend.
        """
        actions = ScenarioGenerator.get_travel_scenario(scenario_type)
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
            print(f"  [EXECUTION] Simulated Travel Action '{act_type}' COMPLETED successfully.")
        elif verdict == "BLOCK":
            print(f"  [GOVERNANCE BLOCK] Travel Action '{act_type}' BLOCKED by governance policy.")
        elif verdict == "HITL_REQUIRED":
            print(f"  [HITL REQUIRED] Travel Action '{act_type}' PENDING HUMAN APPROVAL.")
        else:
            print(f"  [ERROR] Travel Action '{act_type}' FAILED execution.")

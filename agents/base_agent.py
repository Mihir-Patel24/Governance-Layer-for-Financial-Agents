from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.governance_client import GovernanceClient
from agents.state import AgentState
from agents.workflow import create_governance_workflow


class BaseAgent:
    """
    Reusable Base Agent abstraction for simulated autonomous financial agents.
    Provides common functionality for action generation, governance client invocation,
    and LangGraph workflow execution. Specialized agents (Travel, Servicing, Rewards)
    will inherit from this base class.
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        governance_url: str = "http://localhost:8000",
        governance_client: Optional[GovernanceClient] = None
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.governance_client = governance_client or GovernanceClient(base_url=governance_url)
        self.workflow = create_governance_workflow(self.governance_client)
        self.history: List[Dict[str, Any]] = []

    def generate_action(
        self,
        action_type: str,
        amount: float = 0.0,
        currency: str = "INR",
        recipient: Optional[Dict[str, Any]] = None,
        description: Optional[str] = "",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Helper method to construct a valid dictionary strictly conforming to Person 1's ActionRequest schema.
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "action_type": action_type,
            "amount": float(amount),
            "currency": currency,
            "recipient": recipient,
            "description": description or "",
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }

    def submit_action(self, action_request: Dict[str, Any]) -> AgentState:
        """
        Submits an action request payload through the LangGraph workflow.
        Returns the final state containing governance response and execution status.
        """
        initial_state: AgentState = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "current_action": action_request,
            "governance_response": None,
            "verdict": None,
            "execution_status": "INIT",
            "error": None,
            "history": list(self.history)
        }

        # Invoke the compiled LangGraph workflow
        final_state: AgentState = self.workflow.invoke(initial_state)

        # Update local history
        if final_state.get("history"):
            self.history = final_state["history"]

        return final_state

    def _print_execution_feedback(self, state: AgentState):
        """
        Helper method to print explicit, unambiguous execution feedback for each action.
        """
        verdict = state.get("verdict")
        action = state.get("current_action", {})
        act_type = action.get("action_type")
        amount = action.get("amount", 0.0)

        if verdict == "ALLOW":
            exec_str = "EXECUTED"
        elif verdict == "BLOCK":
            exec_str = "NOT EXECUTED / BLOCKED"
        elif verdict == "HITL_REQUIRED":
            exec_str = "PENDING APPROVAL"
        else:
            exec_str = "FAILED"

        print(f"  Action     : {act_type}")
        print(f"  Amount     : Rs.{amount:,.2f}")
        print(f"  Governance : {verdict}")
        print(f"  Execution  : {exec_str}\n")

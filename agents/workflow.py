from datetime import datetime
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END

from agents.state import AgentState
from agents.governance_client import GovernanceClient


def create_governance_workflow(governance_client: GovernanceClient):
    """
    Factory function that builds and compiles a reusable LangGraph workflow.
    Orchestrates the lifecycle of an action through validation, governance check,
    verdict evaluation (ALLOW / BLOCK / HITL_REQUIRED), and simulated execution.
    """

    def prepare_action_node(state: AgentState) -> Dict[str, Any]:
        """Ensures action payload conforms to Person 1 ActionRequest schema defaults."""
        action = dict(state.get("current_action") or {})
        action.setdefault("agent_id", state.get("agent_id", "unknown-agent"))
        action.setdefault("agent_type", state.get("agent_type", "banking"))
        action.setdefault("action_type", "generic_action")
        action.setdefault("amount", 0.0)
        action.setdefault("currency", "INR")
        action.setdefault("description", "")
        action.setdefault("context", {})
        if not action.get("timestamp"):
            action["timestamp"] = datetime.now().isoformat()

        return {
            "current_action": action,
            "execution_status": "PENDING_GOVERNANCE"
        }

    def evaluate_governance_node(state: AgentState) -> Dict[str, Any]:
        """Calls Person 1's FastAPI POST /api/governance/evaluate endpoint."""
        action = state["current_action"]
        resp = governance_client.evaluate_action(action)
        verdict = resp.get("verdict", "BLOCK")
        error_msg = resp.get("error")

        return {
            "governance_response": resp,
            "verdict": verdict,
            "error": error_msg
        }

    def route_verdict(state: AgentState) -> str:
        """Determines graph execution path based strictly on governance verdict."""
        verdict = state.get("verdict")
        if verdict == "ALLOW":
            return "execute_action"
        elif verdict == "BLOCK":
            return "record_block"
        elif verdict == "HITL_REQUIRED":
            return "record_hitl"
        else:
            return "record_error"

    def execute_action_node(state: AgentState) -> Dict[str, Any]:
        """Simulates action execution for ALLOW verdict."""
        history = list(state.get("history", []))
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": state.get("current_action"),
            "governance_response": state.get("governance_response"),
            "execution_status": "EXECUTED"
        }
        history.append(entry)
        return {
            "execution_status": "EXECUTED",
            "history": history
        }

    def record_block_node(state: AgentState) -> Dict[str, Any]:
        """Records blocked status without executing the action."""
        history = list(state.get("history", []))
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": state.get("current_action"),
            "governance_response": state.get("governance_response"),
            "execution_status": "BLOCKED"
        }
        history.append(entry)
        return {
            "execution_status": "BLOCKED",
            "history": history
        }

    def record_hitl_node(state: AgentState) -> Dict[str, Any]:
        """Records pending human approval status without automatically executing."""
        history = list(state.get("history", []))
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": state.get("current_action"),
            "governance_response": state.get("governance_response"),
            "execution_status": "PENDING_APPROVAL"
        }
        history.append(entry)
        return {
            "execution_status": "PENDING_APPROVAL",
            "history": history
        }

    def record_error_node(state: AgentState) -> Dict[str, Any]:
        """Handles unexpected governance response or client errors."""
        history = list(state.get("history", []))
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": state.get("current_action"),
            "governance_response": state.get("governance_response"),
            "execution_status": "FAILED",
            "error": state.get("error", "Governance evaluation failed")
        }
        history.append(entry)
        return {
            "execution_status": "FAILED",
            "history": history
        }

    # Construct LangGraph StateGraph
    builder = StateGraph(AgentState)

    # Add Nodes
    builder.add_node("prepare_action", prepare_action_node)
    builder.add_node("evaluate_governance", evaluate_governance_node)
    builder.add_node("execute_action", execute_action_node)
    builder.add_node("record_block", record_block_node)
    builder.add_node("record_hitl", record_hitl_node)
    builder.add_node("record_error", record_error_node)

    # Add Edges
    builder.add_edge(START, "prepare_action")
    builder.add_edge("prepare_action", "evaluate_governance")

    # Conditional Router Edge
    builder.add_conditional_edges(
        "evaluate_governance",
        route_verdict,
        {
            "execute_action": "execute_action",
            "record_block": "record_block",
            "record_hitl": "record_hitl",
            "record_error": "record_error"
        }
    )

    builder.add_edge("execute_action", END)
    builder.add_edge("record_block", END)
    builder.add_edge("record_hitl", END)
    builder.add_edge("record_error", END)

    return builder.compile()

from typing import TypedDict, Optional, Dict, Any, List


class AgentState(TypedDict):
    """
    Shared state schema passed through LangGraph workflow nodes.
    Tracks action evaluation lifecycle from generation to governance and execution.
    """
    agent_id: str
    agent_type: str
    current_action: Optional[Dict[str, Any]]
    governance_response: Optional[Dict[str, Any]]
    verdict: Optional[str]
    execution_status: str  # INIT, PENDING_GOVERNANCE, EXECUTED, BLOCKED, PENDING_APPROVAL, FAILED
    error: Optional[str]
    history: List[Dict[str, Any]]

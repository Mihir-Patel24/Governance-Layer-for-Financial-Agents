from typing import Dict, Any, Optional
from app.core.enums import AgentStatusEnum

class KillSwitchService:
    """Person 2 Deliverable: Circuit Breaker Emergency Kill Switch"""
    def __init__(self):
        self.global_emergency_stop: bool = False

    def trigger_global_kill(self, reason: str = "Global Emergency Stop Triggered") -> Dict[str, Any]:
        self.global_emergency_stop = True
        return {"status": "GLOBAL_KILL_ACTIVE", "message": reason}

    def is_global_killed(self) -> bool:
        return self.global_emergency_stop

kill_switch_service = KillSwitchService()

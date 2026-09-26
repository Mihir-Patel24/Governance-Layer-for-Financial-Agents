import os
import time
from datetime import datetime
from typing import Tuple, Dict, Optional, List
from app.schemas import ActionRequest, AgentPolicyConfig, AgentStatusEnum

# Try loading environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_TIMEOUT_MS = float(os.getenv("MAX_POLICY_TIMEOUT_MS", "20.0"))

class DynamicPolicyEngine:
    """
    Person 1 Core Deliverable:
    100% Dynamic, Fail-Closed Policy Engine.
    Evaluates ActionRequests against dynamic AgentPolicyConfigs without hardcoded rules.
    """
    def __init__(self):
        # Dynamic policy registry (In-memory + hooked into PostgreSQL via Person 2)
        self.agents: Dict[str, AgentPolicyConfig] = {}
        self._initialize_default_agents()

    def _initialize_default_agents(self):
        """Seed initial multi-domain agent configurations dynamically"""
        defaults = [
            AgentPolicyConfig(
                agent_id="travel-agent-01",
                agent_name="Corporate Travel Booking Assistant",
                agent_type="banking",
                status=AgentStatusEnum.ACTIVE,
                single_tx_limit=15000.0,
                daily_spend_cap=50000.0,
                monthly_spend_cap=500000.0,
                allowed_actions=["book_flight", "book_hotel", "cancel_booking"],
                allowed_start_hour=0,
                allowed_end_hour=24,
                max_requests_per_min=30
            ),
            AgentPolicyConfig(
                agent_id="servicing-agent-01",
                agent_name="Customer Support Concierge",
                agent_type="banking",
                status=AgentStatusEnum.ACTIVE,
                single_tx_limit=1000.0,
                daily_spend_cap=5000.0,
                monthly_spend_cap=50000.0,
                allowed_actions=["fee_reversal", "issue_credit", "update_address"],
                allowed_start_hour=8,
                allowed_end_hour=20, # Business hours only
                max_requests_per_min=20
            ),
            AgentPolicyConfig(
                agent_id="subsidy-agent-01",
                agent_name="Government Direct Subsidy Disbursement Agent",
                agent_type="government",
                status=AgentStatusEnum.ACTIVE,
                single_tx_limit=25000.0,
                daily_spend_cap=50000.0,
                monthly_spend_cap=1000000.0,
                allowed_actions=["release_subsidy", "flag_discrepancy", "verify_beneficiary"],
                allowed_start_hour=0,
                allowed_end_hour=24,
                max_requests_per_min=50
            )
        ]
        for cfg in defaults:
            self.agents[cfg.agent_id] = cfg

    def register_agent(self, config: AgentPolicyConfig):
        """Dynamically add or update an agent policy config at runtime"""
        self.agents[config.agent_id] = config

    def get_agent(self, agent_id: str) -> Optional[AgentPolicyConfig]:
        return self.agents.get(agent_id)

    def list_agents(self) -> List[AgentPolicyConfig]:
        return list(self.agents.values())

    def evaluate_policy(self, req: ActionRequest, max_timeout_ms: Optional[float] = None) -> Tuple[bool, str]:
        """
        Phase 3: Fail-Closed Evaluation Engine
        Wraps rule checks in a strict execution timer & exception guardrail.
        If latency exceeds max_timeout_ms or any error occurs -> VERDICT: BLOCK (Fail-Closed).
        """
        if max_timeout_ms is None:
            max_timeout_ms = DEFAULT_TIMEOUT_MS

        start_time = time.perf_counter()

        try:
            # 1. Agent Existence & Status Check
            agent = self.get_agent(req.agent_id)
            if not agent:
                return False, f"Unknown agent ID '{req.agent_id}'. Request rejected."

            if agent.status == AgentStatusEnum.TERMINATED:
                return False, f"Agent '{req.agent_id}' is TERMINATED by emergency kill switch."

            if agent.status == AgentStatusEnum.PAUSED:
                return False, f"Agent '{req.agent_id}' is PAUSED."

            # 2. Whitelist Action Check
            if req.action_type not in agent.allowed_actions:
                return False, (
                    f"Action '{req.action_type}' is NOT permitted for agent '{req.agent_id}'. "
                    f"Allowed actions: {agent.allowed_actions}."
                )

            # 3. Single Transaction Limit Check
            if req.amount > agent.single_tx_limit:
                return False, (
                    f"Requested amount ₹{req.amount:,.2f} exceeds single transaction limit "
                    f"of ₹{agent.single_tx_limit:,.2f} for agent '{req.agent_id}'."
                )

            # 4. Time-of-Day Window Check
            current_hour = datetime.now().hour
            if not (agent.allowed_start_hour <= current_hour <= agent.allowed_end_hour):
                return False, (
                    f"Action execution restricted. Current hour ({current_hour}:00) is outside "
                    f"allowed operating window ({agent.allowed_start_hour}:00 - {agent.allowed_end_hour}:00)."
                )

            # Latency Timeout Guardrail Check (Fail-Closed)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            if elapsed_ms > max_timeout_ms:
                return False, f"Fail-Closed Guardrail: Policy evaluation exceeded timeout threshold ({elapsed_ms:.2f}ms > {max_timeout_ms}ms)."

            return True, "Dynamic policy checks passed successfully."

        except Exception as e:
            # Fail-Closed Fallback on unexpected errors
            return False, f"Fail-Closed Security Triggered: Policy evaluation exception - {str(e)}"

policy_engine = DynamicPolicyEngine()

import requests
from typing import Dict, Any, Optional
from datetime import datetime


class GovernanceClientError(Exception):
    """Custom exception raised for unrecoverable governance client failures."""
    pass


class GovernanceClient:
    """
    Dedicated client for communicating with Person 1's FastAPI Governance Gateway.
    Target Endpoint: POST /api/governance/evaluate
    Registration Endpoint: POST /api/agents/register
    """
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.evaluate_url = f"{self.base_url}/api/governance/evaluate"
        self.agents_url = f"{self.base_url}/api/agents"
        self.register_url = f"{self.base_url}/api/agents/register"
        self.timeout = timeout

    def evaluate_action(self, action_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends an ActionRequest dictionary to Person 1's governance endpoint.
        Guarantees fail-closed behavior (BLOCK) if connection fails or unexpected errors occur.
        """
        # Ensure timestamp is set if missing
        payload = dict(action_request)
        if not payload.get("timestamp"):
            payload["timestamp"] = datetime.now().isoformat()

        # Enforce default schema values if omitted
        payload.setdefault("amount", 0.0)
        payload.setdefault("currency", "INR")
        payload.setdefault("description", "")
        payload.setdefault("context", {})

        try:
            response = requests.post(
                self.evaluate_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )

            # Check HTTP Status Codes
            if response.status_code != 200:
                error_msg = f"Governance API HTTP {response.status_code}: {response.text}"
                return self._create_fail_closed_response(
                    agent_id=payload.get("agent_id", "unknown"),
                    reason=f"Governance Gateway Error: HTTP {response.status_code}",
                    error_details=error_msg
                )

            res_data = response.json()

            # Validate mandatory response fields
            verdict = res_data.get("verdict")
            if verdict not in ["ALLOW", "BLOCK", "HITL_REQUIRED"]:
                return self._create_fail_closed_response(
                    agent_id=payload.get("agent_id", "unknown"),
                    reason=f"Invalid governance verdict received: '{verdict}'",
                    error_details=f"Unexpected verdict value: {verdict}"
                )

            return res_data

        except requests.exceptions.ConnectionError as e:
            return self._create_fail_closed_response(
                agent_id=payload.get("agent_id", "unknown"),
                reason="Fail-Closed Security Trigger: Governance Backend unavailable (Connection Refused).",
                error_details=str(e)
            )
        except requests.exceptions.Timeout as e:
            return self._create_fail_closed_response(
                agent_id=payload.get("agent_id", "unknown"),
                reason=f"Fail-Closed Security Trigger: Governance evaluation request timed out (> {self.timeout}s).",
                error_details=str(e)
            )
        except requests.exceptions.RequestException as e:
            return self._create_fail_closed_response(
                agent_id=payload.get("agent_id", "unknown"),
                reason=f"Governance client request exception: {str(e)}",
                error_details=str(e)
            )
        except ValueError as e: # JSON decode error
            return self._create_fail_closed_response(
                agent_id=payload.get("agent_id", "unknown"),
                reason="Governance API returned non-JSON invalid payload.",
                error_details=str(e)
            )
        except Exception as e:
            return self._create_fail_closed_response(
                agent_id=payload.get("agent_id", "unknown"),
                reason=f"Unexpected client exception: {str(e)}",
                error_details=str(e)
            )

    def register_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registers a new agent policy profile via Person 1's POST /api/agents/register endpoint.
        """
        try:
            resp = requests.post(
                self.register_url,
                json=agent_config,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            if resp.status_code in [200, 201]:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"error": str(e)}

    def check_agent_exists(self, agent_id: str) -> bool:
        """
        Optional helper to verify agent registration against GET /api/agents
        """
        try:
            resp = requests.get(self.agents_url, timeout=self.timeout)
            if resp.status_code == 200:
                agents = resp.json()
                return any(a.get("agent_id") == agent_id for a in agents)
            return False
        except Exception:
            return False

    def _create_fail_closed_response(self, agent_id: str, reason: str, error_details: str) -> Dict[str, Any]:
        """Creates a standardized ActionResponse dict enforcing verdict=BLOCK when errors occur."""
        return {
            "request_id": "req-error-failclosed",
            "agent_id": agent_id,
            "verdict": "BLOCK",
            "policy_passed": False,
            "spend_cap_passed": False,
            "ml_anomaly_score": 1.0,
            "is_anomaly": True,
            "reason": reason,
            "llm_explanation": None,
            "audit_hash": "error-block-hash",
            "timestamp": datetime.now().isoformat(),
            "execution_latency_ms": 0.0,
            "error": error_details
        }

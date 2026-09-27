import os
import sys
from typing import Dict, Any

# Ensure stdout handles UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.base_agent import BaseAgent
from agents.governance_client import GovernanceClient


def print_separator(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def safe_print_str(text: str) -> str:
    """Sanitizes text for safe terminal display on Windows cp1252 if needed."""
    try:
        return str(text)
    except Exception:
        return str(text).encode("ascii", "replace").decode("ascii")


def run_foundation_tests():
    backend_url = os.getenv("GOVERNANCE_URL", "http://localhost:8000")

    print_separator("Governance Layer Agent Foundation Integration Test")
    print(f"Connecting to Governance Gateway: {backend_url}/api/governance/evaluate")

    client = GovernanceClient(base_url=backend_url)

    # Check backend connectivity
    is_connected = client.check_agent_exists("travel-agent-01")
    if not is_connected:
        print("[WARN] Warning: Backend API ping returned false or backend is offline.")
        print("       Test will proceed to verify fail-closed handling against the gateway.")
    else:
        print("[OK] Governance Backend connection verified successfully.")

    # Instantiate Base Agent representing Travel Agent
    agent = BaseAgent(
        agent_id="travel-agent-01",
        agent_type="banking",
        governance_url=backend_url
    )

    # -------------------------------------------------------------
    # Test 1: Valid Action Request (Expected: ALLOW -> EXECUTED)
    # -------------------------------------------------------------
    print_separator("Test Case 1: Standard Valid Action (Flight Booking Rs.8,000)")
    action1 = agent.generate_action(
        action_type="book_flight",
        amount=8000.0,
        currency="INR",
        description="Corporate flight booking to Bangalore",
        context={"location": "IN-KA", "user_role": "employee"}
    )
    print(f"Agent ID    : {action1['agent_id']}")
    print(f"Action Type : {action1['action_type']}")
    print(f"Amount      : Rs.{action1['amount']:,.2f}")

    final_state1 = agent.submit_action(action1)
    gov_resp1 = final_state1.get("governance_response") or {}

    print(f"\n[Result]")
    print(f"Governance Verdict : {final_state1.get('verdict')}")
    print(f"Policy Passed      : {gov_resp1.get('policy_passed')}")
    print(f"Reason             : {safe_print_str(gov_resp1.get('reason'))}")
    print(f"Execution Status   : {final_state1.get('execution_status')}")

    # -------------------------------------------------------------
    # Test 2: Excessive Amount Request (Expected: BLOCK -> BLOCKED)
    # -------------------------------------------------------------
    print_separator("Test Case 2: Exceeding Single Tx Limit (Flight Booking Rs.99,000)")
    action2 = agent.generate_action(
        action_type="book_flight",
        amount=99000.0,
        currency="INR",
        description="First class international flight",
        context={"location": "IN-MH"}
    )
    print(f"Agent ID    : {action2['agent_id']}")
    print(f"Action Type : {action2['action_type']}")
    print(f"Amount      : Rs.{action2['amount']:,.2f}")

    final_state2 = agent.submit_action(action2)
    gov_resp2 = final_state2.get("governance_response") or {}

    print(f"\n[Result]")
    print(f"Governance Verdict : {final_state2.get('verdict')}")
    print(f"Policy Passed      : {gov_resp2.get('policy_passed')}")
    print(f"Reason             : {safe_print_str(gov_resp2.get('reason'))}")
    print(f"Execution Status   : {final_state2.get('execution_status')}")

    # -------------------------------------------------------------
    # Test 3: Unauthorized Action Request (Expected: BLOCK -> BLOCKED)
    # -------------------------------------------------------------
    print_separator("Test Case 3: Unauthorized Action (Direct Wire Transfer)")
    action3 = agent.generate_action(
        action_type="wire_transfer",
        amount=500.0,
        currency="INR",
        description="Attempted unauthorized wire transfer"
    )
    print(f"Agent ID    : {action3['agent_id']}")
    print(f"Action Type : {action3['action_type']}")

    final_state3 = agent.submit_action(action3)
    gov_resp3 = final_state3.get("governance_response") or {}

    print(f"\n[Result]")
    print(f"Governance Verdict : {final_state3.get('verdict')}")
    print(f"Policy Passed      : {gov_resp3.get('policy_passed')}")
    print(f"Reason             : {safe_print_str(gov_resp3.get('reason'))}")
    print(f"Execution Status   : {final_state3.get('execution_status')}")

    # -------------------------------------------------------------
    # Test 4: Offline Backend / Invalid Host (Expected: Fail-Closed BLOCK)
    # -------------------------------------------------------------
    print_separator("Test Case 4: Fail-Closed Safety (Invalid Gateway Host)")
    offline_agent = BaseAgent(
        agent_id="travel-agent-01",
        agent_type="banking",
        governance_url="http://localhost:9999"  # Non-existent port
    )
    action4 = offline_agent.generate_action(action_type="book_flight", amount=100.0)
    final_state4 = offline_agent.submit_action(action4)
    gov_resp4 = final_state4.get("governance_response") or {}

    print(f"\n[Result]")
    print(f"Governance Verdict : {final_state4.get('verdict')}")
    print(f"Reason             : {safe_print_str(gov_resp4.get('reason'))}")
    print(f"Execution Status   : {final_state4.get('execution_status')}")

    print_separator("Agent Foundation Integration Test Summary")
    print(f"Total agent history records logged: {len(agent.history)}")
    print("Foundation verification completed.")


if __name__ == "__main__":
    run_foundation_tests()

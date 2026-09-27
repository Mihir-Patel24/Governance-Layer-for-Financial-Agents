import os
import sys
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure stdout handles UTF-8 on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.llm_explainer import LLMExplainer, LLMExplainerConfigError


def print_separator(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_llm_explainer_tests():
    print_separator("Person 3 AI Layer: Groq LLM Explainer Integration Test")

    # Verify GROQ_API_KEY presence
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[ERROR] GROQ_API_KEY environment variable is missing!")
        print("        Please set GROQ_API_KEY in your .env file or environment.")
        print("        Example in .env file: GROQ_API_KEY=gsk_your_key_here")
        sys.exit(1)

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    print(f"[OK] GROQ_API_KEY detected.")
    print(f"[OK] Using Groq Model: {model_name}")

    explainer = LLMExplainer(api_key=api_key, model=model_name)

    # -------------------------------------------------------------
    # TEST 1: Travel Agent Allowed Flight Booking
    # -------------------------------------------------------------
    print_separator("TEST 1: Travel Agent Allowed Flight Booking (Rs.6,000)")
    resp1 = {
        "request_id": "req-test-001",
        "agent_id": "travel-agent-01",
        "verdict": "ALLOW",
        "policy_passed": True,
        "spend_cap_passed": True,
        "ml_anomaly_score": 0.05,
        "is_anomaly": False,
        "reason": "Policy checks passed",
        "execution_latency_ms": 1.2
    }
    act1 = {
        "agent_id": "travel-agent-01",
        "action_type": "book_flight",
        "amount": 6000.0,
        "currency": "INR",
        "description": "Domestic flight booking"
    }

    explanation1 = explainer.generate_explanation(resp1, act1)
    print(f"Verdict        : {resp1['verdict']}")
    print(f"Governance Msg : {resp1['reason']}")
    print(f"\n[Groq Generated Explanation]\n{explanation1}")

    # -------------------------------------------------------------
    # TEST 2: Travel Agent Blocked Flight Booking (Spike)
    # -------------------------------------------------------------
    print_separator("TEST 2: Travel Agent Blocked Flight Booking (Rs.25,000)")
    resp2 = {
        "request_id": "req-test-002",
        "agent_id": "travel-agent-01",
        "verdict": "BLOCK",
        "policy_passed": False,
        "spend_cap_passed": False,
        "ml_anomaly_score": 0.05,
        "is_anomaly": False,
        "reason": "Requested amount Rs.25,000.00 exceeds single transaction limit of Rs.15,000.00",
        "execution_latency_ms": 1.5
    }
    act2 = {
        "agent_id": "travel-agent-01",
        "action_type": "book_flight",
        "amount": 25000.0,
        "currency": "INR",
        "description": "First class international flight"
    }

    explanation2 = explainer.generate_explanation(resp2, act2)
    print(f"Verdict        : {resp2['verdict']}")
    print(f"Governance Msg : {resp2['reason']}")
    print(f"\n[Groq Generated Explanation]\n{explanation2}")

    # -------------------------------------------------------------
    # TEST 3: Servicing Agent Allowed Fee Reversal
    # -------------------------------------------------------------
    print_separator("TEST 3: Servicing Agent Allowed Fee Reversal (Rs.500)")
    resp3 = {
        "request_id": "req-test-003",
        "agent_id": "servicing-agent-01",
        "verdict": "ALLOW",
        "policy_passed": True,
        "spend_cap_passed": True,
        "ml_anomaly_score": 0.02,
        "is_anomaly": False,
        "reason": "Policy checks passed",
        "execution_latency_ms": 1.1
    }
    act3 = {
        "agent_id": "servicing-agent-01",
        "action_type": "fee_reversal",
        "amount": 500.0,
        "currency": "INR",
        "description": "Monthly fee reversal"
    }

    explanation3 = explainer.generate_explanation(resp3, act3)
    print(f"Verdict        : {resp3['verdict']}")
    print(f"Governance Msg : {resp3['reason']}")
    print(f"\n[Groq Generated Explanation]\n{explanation3}")

    # -------------------------------------------------------------
    # TEST 4: Rewards Agent Blocked Cash Withdrawal
    # -------------------------------------------------------------
    print_separator("TEST 4: Rewards Agent Blocked Cash Withdrawal (Rs.5,000)")
    resp4 = {
        "request_id": "req-test-004",
        "agent_id": "rewards-agent-01",
        "verdict": "BLOCK",
        "policy_passed": False,
        "spend_cap_passed": True,
        "ml_anomaly_score": 0.05,
        "is_anomaly": False,
        "reason": "Action 'cash_withdrawal' is NOT permitted for agent 'rewards-agent-01'.",
        "execution_latency_ms": 1.4
    }
    act4 = {
        "agent_id": "rewards-agent-01",
        "action_type": "cash_withdrawal",
        "amount": 5000.0,
        "currency": "INR",
        "description": "Unauthorized cash withdrawal attempt"
    }

    explanation4 = explainer.generate_explanation(resp4, act4)
    print(f"Verdict        : {resp4['verdict']}")
    print(f"Governance Msg : {resp4['reason']}")
    print(f"\n[Groq Generated Explanation]\n{explanation4}")

    print_separator("Groq LLM Explainer Test Summary")
    print("[SUCCESS] All 4 explanation generation tests completed successfully.")


if __name__ == "__main__":
    run_llm_explainer_tests()

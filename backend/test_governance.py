import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.schemas.action import ActionRequest
from app.services.governance_orchestrator import governance_orchestrator
from app.services.audit_service import audit_service

def clean_str(text: str) -> str:
    """Strip unicode characters for clean Windows console printing"""
    if not text:
        return ""
    return text.replace("\u26a0\ufe0f", "[!]").replace("\u26a0", "[!]").replace("\u20b9", "INR ")

def run_tests():
    print("=" * 80)
    print("SENTINEL AI GOVERNANCE ENGINE - INTEGRATED TEST SUITE")
    print("Testing Person 1 (Policy) + Person 2 (Caps & Audit) + Person 3 (ML Anomaly & LLM)")
    print("=" * 80)

    scenarios = [
        {
            "name": "Scenario 1: Valid Normal Flight Booking",
            "agent_id": "travel-agent-01",
            "agent_type": "banking",
            "action_type": "book_flight",
            "amount": 8000.0
        },
        {
            "name": "Scenario 2: Policy Violation (Disallowed Crypto Transfer)",
            "agent_id": "travel-agent-01",
            "agent_type": "banking",
            "action_type": "transfer_crypto",
            "amount": 5000.0
        },
        {
            "name": "Scenario 3: Spend Cap Violation (Exceeds Daily Cap INR 50,000)",
            "agent_id": "travel-agent-01",
            "agent_type": "banking",
            "action_type": "book_flight",
            "amount": 45000.0
        },
        {
            "name": "Scenario 4: ML Anomaly Flagged (High Value Near Limit INR 24,000)",
            "agent_id": "subsidy-agent-01",
            "agent_type": "government",
            "action_type": "release_subsidy",
            "amount": 24000.0
        }
    ]

    for idx, sc in enumerate(scenarios, 1):
        print(f"\n[Test {idx}/4] {sc['name']}")
        req = ActionRequest(
            agent_id=sc["agent_id"],
            agent_type=sc["agent_type"],
            action_type=sc["action_type"],
            amount=sc["amount"],
            description=sc["name"]
        )

        resp = governance_orchestrator.evaluate_action_request(req)

        if resp.verdict == "ALLOW":
            symbol = "[ALLOWED]"
        elif resp.verdict == "BLOCK":
            symbol = "[BLOCKED]"
        else:
            symbol = "[HITL REQUIRED]"

        print(f"   Verdict:          {symbol}")
        print(f"   Reason:           {clean_str(resp.reason)}")
        print(f"   ML Anomaly Score: {resp.ml_anomaly_score} (Is Anomaly: {resp.is_anomaly})")
        print(f"   Latency:          {resp.execution_latency_ms} ms")
        print(f"   Audit Block Hash: {resp.audit_hash[:16]}...")

    print("\n" + "=" * 80)
    print("AUDIT LEDGER INTEGRITY CHECK:")
    verified = audit_service.verify_integrity()
    print(f"   Cryptographic SHA-256 Hash Chain Verified: {'[PASSED]' if verified else '[FAILED]'}")
    print(f"   Total Immutable Audit Ledger Blocks:        {len(audit_service.get_ledger())}")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()

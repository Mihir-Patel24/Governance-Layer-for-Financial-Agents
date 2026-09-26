"""
scripts/demo.py
────────────────
Runs the complete Round 1 demo scenario against the live API.

DEMO STEPS
──────────
Step 1: Travel Agent is running. Current: ₹12,000 / ₹15,000
Step 2: Travel Agent requests ₹20,000
Step 3: System returns DENIED — SPEND_CAP_EXCEEDED
Step 4: Audit log contains the denial
Step 5: Run audit verification → VALID
Step 6: Operator halts Travel Agent
Step 7: Travel Agent attempts action → DENIED — AGENT_HALTED
Step 8: Verify audit chain → VALID
Step 9: Demonstrate tamper detection (requires manual DB manipulation)

Run from backend/ directory:
  python scripts/demo.py
"""
import json
import os
import sys
import time

import httpx

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
AGENT_ID = "travel-agent"

client = httpx.Client(base_url=BASE_URL, timeout=10.0)


def print_step(step: int, title: str):
    print(f"\n{'='*60}")
    print(f"DEMO STEP {step}: {title}")
    print("="*60)


def check(resp: httpx.Response, label: str):
    print(f"\n[{label}] Status: {resp.status_code}")
    try:
        data = resp.json()
        print(json.dumps(data, indent=2, default=str))
    except Exception:
        print(resp.text)
    return resp


def main():
    print("\n" + "★"*60)
    print("  GOVERNANCE LAYER — Person 2 Demo (Round 1)")
    print("★"*60)

    # ── Step 0: Health check ──────────────────────────────────────────────
    print_step(0, "Health check")
    resp = client.get("/health")
    check(resp, "GET /health")

    # ── Step 0b: Seed travel-agent with ₹12,000 already spent ────────────
    print_step(0, "Setup: Travel Agent at ₹12,000 / ₹15,000")
    # Reserve ₹12,000 as a setup transaction
    resp = client.post("/api/v1/spend/reserve", json={
        "agent_id": AGENT_ID,
        "action_id": "setup-txn-001",
        "amount": 12000,
        "currency": "INR",
        "action": "DEMO_SETUP",
    })
    check(resp, "POST /api/v1/spend/reserve (setup ₹12,000)")

    # Show current state
    resp = client.get(f"/api/v1/spend/{AGENT_ID}")
    check(resp, f"GET /api/v1/spend/{AGENT_ID}")

    # ── Step 1: Show current status ───────────────────────────────────────
    print_step(1, "Travel Agent is RUNNING | Budget: ₹12,000 / ₹15,000")
    resp = client.get(f"/api/v1/kill-switch/agent/{AGENT_ID}")
    check(resp, "Agent status")

    # ── Step 2-3: Request ₹20,000 → DENY ────────────────────────────────
    print_step(2, "Travel Agent requests ₹20,000 booking")
    resp = client.post("/api/v1/enforce", json={
        "agent_id": AGENT_ID,
        "action_id": "txn-demo-flight-001",
        "action": "BOOK_FLIGHT",
        "amount": 20000,
        "currency": "INR",
    })
    result = check(resp, "POST /api/v1/enforce")
    result_data = resp.json()
    assert not result_data["allowed"], "Expected DENY but got ALLOW"
    assert result_data["reason_code"] == "SPEND_CAP_EXCEEDED", f"Wrong reason: {result_data['reason_code']}"
    print("\n✓ CORRECTLY DENIED — SPEND_CAP_EXCEEDED")

    # ── Step 4: Audit log contains denial ────────────────────────────────
    print_step(4, "Audit log contains the denial")
    resp = client.get("/api/v1/audit/logs", params={
        "agent_id": AGENT_ID,
        "decision": "DENY",
    })
    check(resp, "GET /api/v1/audit/logs?agent_id=travel-agent&decision=DENY")

    # ── Step 5: Chain verification ────────────────────────────────────────
    print_step(5, "Audit chain verification → should be VALID")
    resp = client.get("/api/v1/audit/verify")
    verify = check(resp, "GET /api/v1/audit/verify")
    verify_data = resp.json()
    assert verify_data["valid"], f"Chain invalid! {verify_data}"
    print("\n✓ AUDIT CHAIN VALID")

    # ── Step 6: Halt travel-agent ─────────────────────────────────────────
    print_step(6, "Operator halts Travel Agent")
    resp = client.post(f"/api/v1/kill-switch/agent/{AGENT_ID}", json={
        "reason": "Security investigation — suspicious transaction pattern",
        "updated_by": "operator-1",
    })
    check(resp, f"POST /api/v1/kill-switch/agent/{AGENT_ID}")

    # ── Step 7: Halted agent rejects action ───────────────────────────────
    print_step(7, "Travel Agent attempts action → DENIED — AGENT_HALTED")
    resp = client.post("/api/v1/enforce", json={
        "agent_id": AGENT_ID,
        "action_id": "txn-demo-hotel-001",
        "action": "BOOK_HOTEL",
        "amount": 5000,
        "currency": "INR",
    })
    result = check(resp, "POST /api/v1/enforce")
    result_data = resp.json()
    assert not result_data["allowed"], "Expected DENY but got ALLOW"
    assert result_data["reason_code"] == "AGENT_HALTED", f"Wrong reason: {result_data['reason_code']}"
    print("\n✓ CORRECTLY DENIED — AGENT_HALTED")

    # ── Step 8: Verify chain again ────────────────────────────────────────
    print_step(8, "Audit chain verification after halt → should still be VALID")
    resp = client.get("/api/v1/audit/verify")
    verify_data = resp.json()
    check(resp, "GET /api/v1/audit/verify")
    assert verify_data["valid"], f"Chain invalid after halt! {verify_data}"
    print("\n✓ AUDIT CHAIN STILL VALID")
    print(f"   Entries checked: {verify_data['entries_checked']}")

    # ── Step 9: Tamper detection (guidance only — requires direct DB access) ──
    print_step(9, "Tamper detection (manual step)")
    print("""
To demonstrate tamper detection:
  1. Connect to PostgreSQL directly:
       psql postgresql://govuser:govpass@localhost:5432/govdb

  2. Modify any audit record:
       UPDATE audit_log
       SET decision = 'ALLOW'
       WHERE sequence_num = 1;

  3. Then call:
       GET /api/v1/audit/verify

  4. You will see:
       { "valid": false, "first_invalid_entry": 1, "error": "HASH_MISMATCH" }

  OR run the automated tamper test:
       cd backend && pytest tests/unit/test_audit_service.py -k tamper -v
""")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "★"*60)
    print("  DEMO COMPLETE")
    print("★"*60)
    print(f"""
All demo steps passed:
  ✓ Spend cap enforced (₹20,000 > ₹3,000 remaining)
  ✓ Denial logged in audit
  ✓ Audit chain valid
  ✓ Agent halted by operator
  ✓ Halted agent rejected (AGENT_HALTED)
  ✓ Audit chain valid after halt
""")


if __name__ == "__main__":
    main()

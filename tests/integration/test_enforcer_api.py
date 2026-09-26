"""
tests/integration/test_enforcer_api.py
────────────────────────────────────────
Integration tests using the FastAPI TestClient.
Tests the full request lifecycle including EnforcerService precedence.
"""
from app.core.enums import ReasonCode


def test_enforce_valid_spend(client):
    req = {
        "agent_id": "travel-agent",
        "action_id": "txn-int-001",
        "action": "BOOK_FLIGHT",
        "amount": 5000,
        "currency": "INR",
    }
    resp = client.post("/api/v1/enforce", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is True
    assert data["reason_code"] == ReasonCode.ALLOWED
    assert data["remaining_budget"] == 10000


def test_enforce_spend_cap_exceeded(client):
    req = {
        "agent_id": "travel-agent",
        "action_id": "txn-int-002",
        "action": "BOOK_FLIGHT",
        "amount": 25000,
        "currency": "INR",
    }
    resp = client.post("/api/v1/enforce", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is False
    assert data["reason_code"] == ReasonCode.SPEND_CAP_EXCEEDED
    assert data["remaining_budget"] == 15000  # unchanged


def test_enforce_policy_denied(client):
    req = {
        "agent_id": "travel-agent",
        "action_id": "txn-int-003",
        "action": "BOOK_FLIGHT",
        "amount": 1000,
        "currency": "INR",
    }
    # Pass opa_allowed=False as query param
    resp = client.post("/api/v1/enforce?opa_allowed=false", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is False
    assert data["reason_code"] == ReasonCode.POLICY_DENIED


def test_enforce_agent_halted(client):
    # Halt agent
    client.post("/api/v1/kill-switch/agent/travel-agent", json={
        "reason": "Test", "updated_by": "Test"
    })
    
    req = {
        "agent_id": "travel-agent",
        "action_id": "txn-int-004",
        "action": "BOOK_FLIGHT",
        "amount": 1000,
        "currency": "INR",
    }
    resp = client.post("/api/v1/enforce", json=req)
    data = resp.json()
    assert data["allowed"] is False
    assert data["reason_code"] == ReasonCode.AGENT_HALTED


def test_audit_logs_created(client):
    # Valid spend
    client.post("/api/v1/enforce", json={
        "agent_id": "travel-agent", "action_id": "txn-int-005", "action": "X", "amount": 1000, "currency": "INR"
    })
    
    # Over spend
    client.post("/api/v1/enforce", json={
        "agent_id": "travel-agent", "action_id": "txn-int-006", "action": "X", "amount": 99999, "currency": "INR"
    })
    
    resp = client.get("/api/v1/audit/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    
    # Verify chain
    verify = client.get("/api/v1/audit/verify")
    assert verify.json()["valid"] is True

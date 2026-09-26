"""
tests/unit/test_audit_service.py
──────────────────────────────────
Tests for AuditService invariants (hash chain, tampering).
"""
import pytest
from sqlalchemy import text

from app.core.enums import Decision, EventType, ReasonCode
from app.services.audit_service import AuditService, GENESIS_HASH


def test_first_event_genesis(db):
    svc = AuditService(db)
    
    event1 = svc.append_event(
        EventType.ACTION_ALLOWED,
        agent_id="travel-agent",
        action_id="txn-001",
        amount=5000,
        currency="INR",
        decision=Decision.ALLOW,
    )
    db.commit()
    
    assert event1.sequence_num == 1
    assert event1.previous_hash == GENESIS_HASH
    assert len(event1.current_hash) == 64  # SHA-256 hex


def test_hash_chain_verification(db):
    svc = AuditService(db)
    
    # Add multiple events
    svc.append_event(EventType.ACTION_ALLOWED, decision=Decision.ALLOW)
    svc.append_event(EventType.ACTION_DENIED, decision=Decision.DENY)
    svc.append_event(EventType.SPEND_CAP_EXCEEDED, decision=Decision.DENY)
    db.commit()
    
    verify_res = svc.verify_chain()
    assert verify_res.valid is True
    assert verify_res.entries_checked == 3
    assert verify_res.first_invalid_entry is None


def test_tamper_detection(db):
    svc = AuditService(db)
    
    svc.append_event(EventType.ACTION_ALLOWED, amount=100.0, decision=Decision.ALLOW)
    svc.append_event(EventType.ACTION_ALLOWED, amount=200.0, decision=Decision.ALLOW)
    db.commit()
    
    # Verify OK
    assert svc.verify_chain().valid is True
    
    # TAMPER: directly modify the DB (simulate malicious actor)
    db.execute(text("UPDATE audit_log SET amount = 999.0 WHERE sequence_num = 1"))
    db.commit()
    
    # Verify Fails
    verify_res = svc.verify_chain()
    assert verify_res.valid is False
    assert verify_res.error == "HASH_MISMATCH"
    assert verify_res.first_invalid_entry == 1


def test_previous_hash_tamper_detection(db):
    svc = AuditService(db)
    
    svc.append_event(EventType.ACTION_ALLOWED, amount=100.0, decision=Decision.ALLOW)
    svc.append_event(EventType.ACTION_ALLOWED, amount=200.0, decision=Decision.ALLOW)
    db.commit()
    
    # Verify OK
    assert svc.verify_chain().valid is True
    
    # TAMPER: directly modify the previous_hash link
    db.execute(text("UPDATE audit_log SET previous_hash = 'bogus' WHERE sequence_num = 2"))
    db.commit()
    
    # Verify Fails
    verify_res = svc.verify_chain()
    assert verify_res.valid is False
    assert verify_res.error == "PREVIOUS_HASH_MISMATCH"
    assert verify_res.first_invalid_entry == 2

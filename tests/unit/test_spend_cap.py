"""
tests/unit/test_spend_cap.py
──────────────────────────────
Tests for SpendCapService invariants.
"""
from datetime import datetime, timedelta, timezone

from app.core.enums import ReasonCode, PeriodType
from app.schemas.action import ActionRequest
from app.services.spend_cap_service import SpendCapService


def test_under_limit_request(db_with_budgets):
    svc = SpendCapService(db_with_budgets)
    result = svc.reserve_spend("travel-agent", "txn-001", 5000)
    assert result.allowed is True
    assert result.reason_code == ReasonCode.ALLOWED
    assert result.remaining_budget == 10000

    state = svc.get_budget("travel-agent")
    assert state.spent_amount == 5000


def test_exact_limit_request(db_with_budgets):
    svc = SpendCapService(db_with_budgets)
    result = svc.reserve_spend("travel-agent", "txn-002", 15000)
    assert result.allowed is True
    assert result.remaining_budget == 0

    state = svc.get_budget("travel-agent")
    assert state.spent_amount == 15000


def test_over_limit_request_denied_and_does_not_modify_balance(db_with_budgets):
    svc = SpendCapService(db_with_budgets)
    # spend 10000 first
    svc.reserve_spend("travel-agent", "txn-003", 10000)
    
    # Try 6000 (would make it 16000)
    result = svc.reserve_spend("travel-agent", "txn-004", 6000)
    assert result.allowed is False
    assert result.reason_code == ReasonCode.SPEND_CAP_EXCEEDED
    assert result.remaining_budget == 5000

    # Verify balance was NOT modified
    state = svc.get_budget("travel-agent")
    assert state.spent_amount == 10000


def test_duplicate_action(db_with_budgets):
    svc = SpendCapService(db_with_budgets)
    # First request
    res1 = svc.reserve_spend("travel-agent", "txn-005", 5000)
    assert res1.allowed is True

    # Second request with SAME action_id
    res2 = svc.reserve_spend("travel-agent", "txn-005", 5000)
    assert res2.is_duplicate is True
    assert res2.allowed is True
    assert res2.remaining_budget == 10000

    # Balance should only be deducted once
    state = svc.get_budget("travel-agent")
    assert state.spent_amount == 5000


def test_duplicate_denial(db_with_budgets):
    svc = SpendCapService(db_with_budgets)
    # Try 20000 (over limit)
    res1 = svc.reserve_spend("travel-agent", "txn-006", 20000)
    assert res1.allowed is False

    # Second request with SAME action_id
    res2 = svc.reserve_spend("travel-agent", "txn-006", 20000)
    assert res2.is_duplicate is True
    assert res2.allowed is False


def test_budget_reset(db_with_budgets):
    svc = SpendCapService(db_with_budgets)
    svc.reserve_spend("travel-agent", "txn-007", 10000)
    
    state = svc.get_budget("travel-agent")
    assert state.spent_amount == 10000

    svc.reset_budget("travel-agent", rollover_fraction=0.0)
    
    state2 = svc.get_budget("travel-agent")
    assert state2.spent_amount == 0.0
    assert state2.limit_amount == 15000


def test_rollover(db_with_budgets):
    svc = SpendCapService(db_with_budgets)
    svc.reserve_spend("travel-agent", "txn-008", 5000)
    
    # 10000 remaining. Rollover 10% (1000)
    svc.reset_budget("travel-agent", rollover_fraction=0.1)
    
    state = svc.get_budget("travel-agent")
    assert state.spent_amount == 1000.0
    assert state.rollover_amount == 1000.0
    assert state.limit_amount == 15000
    assert state.remaining_amount == 14000.0

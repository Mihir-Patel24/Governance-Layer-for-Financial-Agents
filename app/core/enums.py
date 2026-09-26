
"""
app/core/enums.py
─────────────────
Shared enumerations used across the Person 2 Enforcer subsystem.
These are the canonical machine-readable codes — do NOT use free-form strings.
"""
from enum import Enum


class ReasonCode(str, Enum):
    """Reason codes for governance enforcement decisions."""
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_HALTED = "AGENT_HALTED"
    FLEET_HALTED = "FLEET_HALTED"
    SPEND_CAP_EXCEEDED = "SPEND_CAP_EXCEEDED"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_CURRENCY = "INVALID_CURRENCY"
    DUPLICATE_ACTION = "DUPLICATE_ACTION"
    AUDIT_CHAIN_INVALID = "AUDIT_CHAIN_INVALID"
    POLICY_DENIED = "POLICY_DENIED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    ALLOWED = "ALLOWED"


class Decision(str, Enum):
    """Final governance decision for an action."""
    ALLOW = "ALLOW"
    DENY = "DENY"


class AgentStatus(str, Enum):
    """Operational status of an individual agent."""
    RUNNING = "RUNNING"
    HALTED = "HALTED"


class FleetStatus(str, Enum):
    """Operational status of the entire fleet."""
    RUNNING = "RUNNING"
    HALTED = "HALTED"


class PeriodType(str, Enum):
    """Budget period granularity."""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class EventType(str, Enum):
    """Types of events recorded in the audit log."""
    ACTION_ALLOWED = "ACTION_ALLOWED"
    ACTION_DENIED = "ACTION_DENIED"
    SPEND_CAP_EXCEEDED = "SPEND_CAP_EXCEEDED"
    AGENT_HALTED = "AGENT_HALTED"
    AGENT_RESUMED = "AGENT_RESUMED"
    FLEET_HALTED = "FLEET_HALTED"
    FLEET_RESUMED = "FLEET_RESUMED"
    BUDGET_RESET = "BUDGET_RESET"
    BUDGET_CONFIGURED = "BUDGET_CONFIGURED"

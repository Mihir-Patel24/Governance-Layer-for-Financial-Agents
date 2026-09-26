"""
app/services/enforcer_service.py
──────────────────────────────────
Person 2's central enforcement orchestrator.

This service implements the complete enforcement pipeline for an incoming
action request.  It is the integration point between:
  - Person 1 (Policy Gateway) — calls enforce() after OPA check
  - Person 2 (Enforcer) — owns all logic in this module
  - Person 3 (Agents) — agents' requests arrive here via the gateway
  - Person 4 (Dashboard) — enforcement decisions appear in audit log

ENFORCEMENT PRECEDENCE
───────────────────────
Step 1: Validate request fields (amount, currency)
Step 2: Check fleet halt
Step 3: Check agent halt
Step 4: Check policy decision (from Person 1 OPA, if provided)
Step 5: Check duplicate action_id
Step 6: Check spend cap
Step 7: Reserve spend and record ALLOWED

At each step, a DENY terminates the pipeline and audits the denial.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.enums import Decision, EventType, ReasonCode
from app.repositories.agent_repository import AgentRepository
from app.schemas.action import ActionRequest, EnforcementResult
from app.services.audit_service import AuditService
from app.services.kill_switch_service import KillSwitchService
from app.services.spend_cap_service import SpendCapService

logger = logging.getLogger(__name__)


class EnforcerService:
    """
    Central enforcement pipeline.

    Usage (from FastAPI route or Person 1 gateway):
        result = EnforcerService(db).enforce(action_request, opa_allowed=True)
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._agent_repo = AgentRepository(db)
        self._ks_service = KillSwitchService(db)
        self._spend_service = SpendCapService(db)
        self._audit_service = AuditService(db)

    def enforce(
        self,
        request: ActionRequest,
        *,
        opa_allowed: Optional[bool] = None,
        opa_reason: Optional[str] = None,
    ) -> EnforcementResult:
        """
        Run the full enforcement pipeline.

        Parameters
        ----------
        request     : The action request from the agent.
        opa_allowed : OPA policy decision (True=allow, False=deny, None=skip OPA step).
                      When Person 1 is integrated, pass the OPA decision here.
        opa_reason  : Textual reason from OPA if denied.

        Returns
        -------
        EnforcementResult with allowed=True/False and a stable reason_code.
        """
        now = datetime.now(timezone.utc)

        # ── Step 1: Validate fields ────────────────────────────────────────
        if request.amount < 0:
            result = self._deny(
                request, ReasonCode.INVALID_AMOUNT, now,
                "Amount cannot be negative"
            )
            return result

        # ── Step 2: Fleet halt check ───────────────────────────────────────
        fleet_halted, fleet_reason = self._ks_service.is_agent_effectively_halted(
            "__fleet__"  # special sentinel; is_agent_effectively_halted checks fleet first
        )
        # Actually: call a dedicated fleet check
        from app.repositories.kill_switch_repository import KillSwitchRepository
        from app.core.redis_client import redis_client
        from app.core.enums import AgentStatus

        ks_repo = KillSwitchRepository(self._db)
        fleet_state = ks_repo.get_fleet()
        fleet_is_halted = fleet_state.status == AgentStatus.HALTED.value

        # Fast path via Redis
        redis_fleet = redis_client.is_fleet_halted()
        if redis_fleet is not None:
            fleet_is_halted = redis_fleet

        if fleet_is_halted:
            result = self._deny(
                request, ReasonCode.FLEET_HALTED, now,
                f"Fleet halted: {fleet_state.reason}",
            )
            return result

        # ── Step 3: Agent halt check ───────────────────────────────────────
        if not self._agent_repo.exists(request.agent_id):
            result = self._deny(request, ReasonCode.AGENT_NOT_FOUND, now, "Agent not registered")
            return result

        agent_halted_redis = redis_client.is_agent_halted(request.agent_id)
        if agent_halted_redis is None:
            ks = ks_repo.get_agent(request.agent_id)
            agent_halted_redis = (ks is not None and ks.status == AgentStatus.HALTED.value)

        if agent_halted_redis:
            ks = ks_repo.get_agent(request.agent_id)
            reason = ks.reason if ks else "Agent halted"
            result = self._deny(request, ReasonCode.AGENT_HALTED, now, reason)
            return result

        # ── Step 4: OPA policy check (Person 1 integration) ───────────────
        if opa_allowed is not None and not opa_allowed:
            result = self._deny(
                request, ReasonCode.POLICY_DENIED, now,
                opa_reason or "OPA policy denied the action",
            )
            return result

        # ── Steps 5-6: Spend cap check + reserve (handles duplicate too) ──
        spend_result = self._spend_service.reserve_spend(
            agent_id=request.agent_id,
            action_id=request.action_id,
            amount=request.amount,
            currency=request.currency,
            action=request.action,
        )

        # Audit the result
        if spend_result.is_duplicate:
            # Don't re-audit duplicates — just return cached result
            logger.info(
                "Duplicate action skipped audit agent=%s action_id=%s",
                request.agent_id, request.action_id,
            )
            return spend_result

        if spend_result.allowed:
            self._audit_service.append_event(
                EventType.ACTION_ALLOWED,
                agent_id=request.agent_id,
                action_id=request.action_id,
                action=request.action,
                amount=request.amount,
                currency=request.currency,
                decision=Decision.ALLOW,
                reason_code=ReasonCode.ALLOWED,
                timestamp=now,
                metadata={"remaining_budget": spend_result.remaining_budget},
            )
            self._db.commit()
        else:
            event_type = (
                EventType.SPEND_CAP_EXCEEDED
                if spend_result.reason_code == ReasonCode.SPEND_CAP_EXCEEDED
                else EventType.ACTION_DENIED
            )
            self._audit_service.append_event(
                event_type,
                agent_id=request.agent_id,
                action_id=request.action_id,
                action=request.action,
                amount=request.amount,
                currency=request.currency,
                decision=Decision.DENY,
                reason_code=spend_result.reason_code,
                timestamp=now,
                metadata={"remaining_budget": spend_result.remaining_budget},
            )
            self._db.commit()

        return spend_result

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _deny(
        self,
        request: ActionRequest,
        reason_code: ReasonCode,
        timestamp: datetime,
        detail: str,
    ) -> EnforcementResult:
        """Create denial result and append audit entry atomically."""
        result = EnforcementResult(
            allowed=False,
            reason_code=reason_code,
            agent_id=request.agent_id,
            action_id=request.action_id,
            requested_amount=request.amount,
            currency=request.currency,
        )

        event_map = {
            ReasonCode.FLEET_HALTED: EventType.ACTION_DENIED,
            ReasonCode.AGENT_HALTED: EventType.ACTION_DENIED,
            ReasonCode.POLICY_DENIED: EventType.ACTION_DENIED,
            ReasonCode.AGENT_NOT_FOUND: EventType.ACTION_DENIED,
            ReasonCode.INVALID_AMOUNT: EventType.ACTION_DENIED,
        }
        event_type = event_map.get(reason_code, EventType.ACTION_DENIED)

        try:
            self._audit_service.append_event(
                event_type,
                agent_id=request.agent_id,
                action_id=request.action_id,
                action=request.action,
                amount=request.amount,
                currency=request.currency,
                decision=Decision.DENY,
                reason_code=reason_code,
                timestamp=timestamp,
                metadata={"detail": detail},
            )
            self._db.commit()
        except Exception as exc:
            logger.error("Audit write failed for denial: %s", exc)
            self._db.rollback()

        logger.info(
            "ACTION_DENIED agent=%s action_id=%s reason=%s detail=%s",
            request.agent_id, request.action_id, reason_code.value, detail,
        )
        return result

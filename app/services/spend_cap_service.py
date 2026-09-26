"""
app/services/spend_cap_service.py
────────────────────────────────────
Spend Cap business logic.

DECISION PRECEDENCE (enforced in check_and_enforce):
  1. Agent not found → AGENT_NOT_FOUND
  2. Duplicate action_id → return cached result (DUPLICATE_ACTION)
  3. Amount validation → INVALID_AMOUNT
  4. Period expired → auto-reset, continue
  5. Spend check → SPEND_CAP_EXCEEDED or ALLOWED

CONCURRENCY
────────────
`reserve_spend()` uses SELECT FOR UPDATE on the SpendState row.
See SpendRepository for the detailed concurrency documentation.

ROLLOVER POLICY
───────────────
By default rollover_fraction=0.0 — no unused budget rolls over.
If configured, the fraction of unused budget is added to the next period's
starting spend (not to the limit).  Example:
  limit=15000, spent=9000, rollover_fraction=0.1
  unused=6000, rollover=600
  new period: spent_amount=600, limit still=15000
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import Decision, EventType, PeriodType, ReasonCode
from app.repositories.agent_repository import AgentRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.spend_repository import SpendRepository
from app.schemas.action import ActionRequest, EnforcementResult
from app.schemas.spend import (
    BudgetConfigRequest,
    BudgetResetResponse,
    SpendCheckResponse,
    SpendStateResponse,
)

logger = logging.getLogger(__name__)


class SpendCapService:

    def __init__(self, db: Session) -> None:
        self._db = db
        self._spend_repo = SpendRepository(db)
        self._agent_repo = AgentRepository(db)
        self._idem_repo = IdempotencyRepository(db)

    # ── Configuration ────────────────────────────────────────────────────────

    def configure_budget(
        self, agent_id: str, config: BudgetConfigRequest
    ) -> SpendStateResponse:
        """Create or replace the budget configuration for an agent."""
        if not self._agent_repo.exists(agent_id):
            raise ValueError(f"Agent '{agent_id}' not found")

        existing = self._spend_repo.get_for_agent(agent_id)
        if existing is not None:
            # Update limit in-place, preserving current period
            existing.limit_amount = config.limit_amount
            existing.currency = config.currency
            self._db.commit()
            logger.info("Budget updated for agent=%s limit=%s %s",
                        agent_id, config.limit_amount, config.currency)
            return self._to_response(existing)

        state = self._spend_repo.create(
            agent_id=agent_id,
            limit_amount=config.limit_amount,
            currency=config.currency,
            period_type=config.period_type,
            rollover_amount=config.rollover_amount,
        )
        self._db.commit()
        logger.info("Budget created for agent=%s limit=%s %s",
                    agent_id, config.limit_amount, config.currency)
        return self._to_response(state)

    # ── Read ─────────────────────────────────────────────────────────────────

    def get_budget(self, agent_id: str) -> Optional[SpendStateResponse]:
        state = self._spend_repo.get_for_agent(agent_id)
        if state is None:
            return None
        return self._to_response(state)

    # ── Check (read-only) ─────────────────────────────────────────────────────

    def check_spend(
        self, agent_id: str, amount: float, currency: str = "INR"
    ) -> SpendCheckResponse:
        """Non-destructive check — does not consume budget."""
        state = self._spend_repo.get_for_agent(agent_id)
        if state is None:
            return SpendCheckResponse(
                agent_id=agent_id,
                requested_amount=amount,
                currency=currency,
                allowed=False,
                remaining_budget=0,
                reason="No budget configured for agent",
            )

        remaining = state.limit_amount - state.spent_amount
        allowed = (state.spent_amount + amount) <= state.limit_amount
        return SpendCheckResponse(
            agent_id=agent_id,
            requested_amount=amount,
            currency=currency,
            allowed=allowed,
            remaining_budget=max(0, remaining),
            reason=None if allowed else "Requested amount exceeds remaining budget",
        )

    # ── Reserve (state-changing) ──────────────────────────────────────────────

    def reserve_spend(
        self, agent_id: str, action_id: str, amount: float, currency: str = "INR",
        action: Optional[str] = None,
    ) -> EnforcementResult:
        """
        Atomically check and reserve spend.
        Uses SELECT FOR UPDATE to prevent race conditions.
        Uses idempotency keys to prevent duplicate charges.
        """
        # ── Idempotency check (before acquiring DB lock) ──────────────────
        existing_key = self._idem_repo.get(agent_id, action_id)
        if existing_key is not None:
            cached = json.loads(existing_key.cached_result_json)
            result = EnforcementResult(**cached)
            result.is_duplicate = True
            logger.info("Duplicate action detected agent=%s action_id=%s", agent_id, action_id)
            return result

        # ── Validation ───────────────────────────────────────────────────
        if amount < 0:
            return EnforcementResult(
                allowed=False,
                reason_code=ReasonCode.INVALID_AMOUNT,
                agent_id=agent_id,
                action_id=action_id,
                requested_amount=amount,
                currency=currency,
            )

        # ── Acquire row-level lock ────────────────────────────────────────
        try:
            state = self._spend_repo.get_for_agent_locked(agent_id)
        except Exception as exc:
            logger.error("DB error acquiring lock for agent=%s: %s", agent_id, exc)
            return EnforcementResult(
                allowed=False,
                reason_code=ReasonCode.INTERNAL_ERROR,
                agent_id=agent_id,
                action_id=action_id,
                requested_amount=amount,
                currency=currency,
            )

        if state is None:
            result = EnforcementResult(
                allowed=False,
                reason_code=ReasonCode.AGENT_NOT_FOUND,
                agent_id=agent_id,
                action_id=action_id,
                requested_amount=amount,
                currency=currency,
                remaining_budget=0,
            )
            self._db.rollback()
            return result

        # ── Auto-reset expired period ─────────────────────────────────────
        now = datetime.now(timezone.utc)
        period_end = state.period_end
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)
        if now >= period_end:
            logger.info("Budget period expired for agent=%s — auto-resetting", agent_id)
            self._spend_repo.reset_period(state)

        # ── Spend check ───────────────────────────────────────────────────
        new_total = state.spent_amount + amount
        remaining = state.limit_amount - state.spent_amount

        if new_total > state.limit_amount:
            result = EnforcementResult(
                allowed=False,
                reason_code=ReasonCode.SPEND_CAP_EXCEEDED,
                agent_id=agent_id,
                action_id=action_id,
                requested_amount=amount,
                currency=currency,
                remaining_budget=max(0, remaining),
            )
            # Do NOT update spend state for denied requests
            # Store idempotency key for the denial so repeat denials are consistent
            try:
                self._idem_repo.store(agent_id, action_id, result.model_dump_json())
                self._db.commit()
            except IntegrityError:
                self._db.rollback()
                existing = self._idem_repo.get(agent_id, action_id)
                if existing:
                    cached = json.loads(existing.cached_result_json)
                    return EnforcementResult(**cached)
            logger.info(
                "SPEND_CAP_EXCEEDED agent=%s action_id=%s requested=%.2f remaining=%.2f",
                agent_id, action_id, amount, remaining,
            )
            return result

        # ── Reserve ───────────────────────────────────────────────────────
        self._spend_repo.update_spend(state, new_total)
        result = EnforcementResult(
            allowed=True,
            reason_code=ReasonCode.ALLOWED,
            agent_id=agent_id,
            action_id=action_id,
            requested_amount=amount,
            currency=currency,
            remaining_budget=max(0, state.limit_amount - new_total),
        )
        try:
            self._idem_repo.store(agent_id, action_id, result.model_dump_json())
            self._db.commit()
        except IntegrityError:
            # Race: another request committed first — rollback and return cached
            self._db.rollback()
            existing = self._idem_repo.get(agent_id, action_id)
            if existing:
                cached = json.loads(existing.cached_result_json)
                res = EnforcementResult(**cached)
                res.is_duplicate = True
                return res
            # Very unlikely: integrity error but no existing key → internal error
            return EnforcementResult(
                allowed=False,
                reason_code=ReasonCode.INTERNAL_ERROR,
                agent_id=agent_id,
                action_id=action_id,
                requested_amount=amount,
                currency=currency,
            )

        logger.info(
            "SPEND_ALLOWED agent=%s action_id=%s amount=%.2f new_total=%.2f",
            agent_id, action_id, amount, new_total,
        )
        return result

    # ── Budget reset ──────────────────────────────────────────────────────────

    def reset_budget(self, agent_id: str, rollover_fraction: float = 0.0) -> BudgetResetResponse:
        """Manually reset budget to a new period (e.g., operator action)."""
        state = self._spend_repo.get_for_agent_locked(agent_id)
        if state is None:
            raise ValueError(f"No budget configured for agent '{agent_id}'")

        old_spent = state.spent_amount
        self._spend_repo.reset_period(state, rollover_fraction)
        self._db.commit()

        logger.info("Budget reset agent=%s old_spent=%.2f new_spent=%.2f",
                    agent_id, old_spent, state.spent_amount)
        return BudgetResetResponse(
            agent_id=agent_id,
            old_spent=old_spent,
            new_spent=state.spent_amount,
            period_start=state.period_start,
            period_end=state.period_end,
            message=f"Budget reset. New period: {state.period_start} – {state.period_end}",
        )

    # ── Internal ─────────────────────────────────────────────────────────────

    @staticmethod
    def _to_response(state) -> SpendStateResponse:
        return SpendStateResponse(
            agent_id=state.agent_id,
            period_type=state.period_type,
            period_start=state.period_start,
            period_end=state.period_end,
            limit_amount=state.limit_amount,
            spent_amount=state.spent_amount,
            remaining_amount=max(0, state.limit_amount - state.spent_amount),
            currency=state.currency,
            rollover_amount=state.rollover_amount,
            reset_at=state.reset_at,
            updated_at=state.updated_at,
        )

"""
app/repositories/spend_repository.py
──────────────────────────────────────
Data-access layer for SpendState.

CONCURRENCY CONTRACT
────────────────────
`reserve_spend()` uses SELECT FOR UPDATE to acquire a row-level lock before
reading and writing the spend balance.  This ensures that two concurrent
requests for the same agent cannot both observe the same pre-update balance
and both succeed when only one should.

Timeline example (without lock → BUG):
  Thread A: SELECT spent=10000  \
  Thread B: SELECT spent=10000   > both see 10000, both pass check
  Thread A: UPDATE spent=14000  /
  Thread B: UPDATE spent=13000  → last write wins: 13000, not 17000 but A's 4000 was silently lost

Timeline with SELECT FOR UPDATE (CORRECT):
  Thread A: SELECT FOR UPDATE spent=10000, limit=15000 → acquires row lock
  Thread B: SELECT FOR UPDATE → BLOCKED until A commits
  Thread A: 10000+4000=14000 ≤ 15000 → UPDATE spent=14000, COMMIT → releases lock
  Thread B: SELECT FOR UPDATE → NOW sees spent=14000
  Thread B: 14000+3000=17000 > 15000 → DENY (lock released, no update)
  Final: spent=14000, limit respected.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.spend_state import SpendState
from app.core.enums import PeriodType

logger = logging.getLogger(__name__)


class SpendRepository:

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_agent(self, agent_id: str) -> Optional[SpendState]:
        """Fetch current spend state (no lock)."""
        stmt = select(SpendState).where(SpendState.agent_id == agent_id)
        return self._db.scalars(stmt).first()

    def get_for_agent_locked(self, agent_id: str) -> Optional[SpendState]:
        """
        Fetch current spend state with a pessimistic row-level lock.
        The lock is held until the surrounding transaction commits/rolls back.
        MUST be called inside an active transaction.
        """
        stmt = (
            select(SpendState)
            .where(SpendState.agent_id == agent_id)
            .with_for_update()
        )
        return self._db.scalars(stmt).first()

    def create(self, agent_id: str, limit_amount: float, currency: str,
               period_type: PeriodType, rollover_amount: float = 0.0) -> SpendState:
        """Create a new spend state for the current period."""
        now = datetime.now(timezone.utc)
        period_start, period_end = self._period_bounds(now, period_type)

        state = SpendState(
            agent_id=agent_id,
            period_type=period_type.value,
            period_start=period_start,
            period_end=period_end,
            limit_amount=limit_amount,
            currency=currency,
            spent_amount=rollover_amount,
            rollover_amount=rollover_amount,
        )
        self._db.add(state)
        self._db.flush()  # obtain id without committing
        return state

    def update_spend(self, state: SpendState, new_spent: float) -> None:
        """Update the spent_amount on an already-locked row."""
        state.spent_amount = new_spent
        state.updated_at = datetime.now(timezone.utc)
        self._db.flush()

    def reset_period(self, state: SpendState, rollover_fraction: float = 0.0) -> None:
        """
        Begin a new budget period.
        rollover_fraction: fraction of unused budget to carry to next period.
        Per project spec: simple daily reset with no rollover by default.
        """
        now = datetime.now(timezone.utc)
        period_type = PeriodType(state.period_type)
        period_start, period_end = self._period_bounds(now, period_type)

        unused = max(0.0, state.limit_amount - state.spent_amount)
        rollover = round(unused * rollover_fraction, 4)

        state.period_start = period_start
        state.period_end = period_end
        state.rollover_amount = rollover
        state.spent_amount = rollover
        state.reset_at = now
        self._db.flush()

    @staticmethod
    def _period_bounds(now: datetime, period_type: PeriodType) -> tuple[datetime, datetime]:
        if period_type == PeriodType.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period_type == PeriodType.WEEKLY:
            day_of_week = now.weekday()  # Monday=0
            start = (now - timedelta(days=day_of_week)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end = start + timedelta(weeks=1)
        elif period_type == PeriodType.MONTHLY:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # First day of next month
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1)
            else:
                end = start.replace(month=now.month + 1)
        else:
            raise ValueError(f"Unsupported period_type: {period_type}")
        return start, end

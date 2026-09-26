"""
app/models/spend_state.py
──────────────────────────
Spend Cap persistent state per agent per budget period.

Concurrency note:
  The critical section (validate + reserve) uses SELECT FOR UPDATE at the
  database level, which serialises concurrent updates to a single agent's row.
  This prevents double-spending under simultaneous requests.
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import PeriodType


class SpendState(Base):
    __tablename__ = "spend_state"

    __table_args__ = (
        # One active budget per agent per period
        UniqueConstraint("agent_id", "period_type", name="uq_spend_agent_period"),
    )

    # ── Primary key ────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Foreign key ─────────────────────────────────────────────────────────
    agent_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False
    )

    # ── Budget definition ───────────────────────────────────────────────────
    period_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PeriodType.DAILY.value
    )
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    limit_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")

    # ── Spend tracking ──────────────────────────────────────────────────────
    spent_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rollover_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Timestamps ─────────────────────────────────────────────────────────
    reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ───────────────────────────────────────────────────────
    agent: Mapped["Agent"] = relationship("Agent", back_populates="spend_state")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<SpendState agent={self.agent_id!r} "
            f"spent={self.spent_amount}/{self.limit_amount} {self.currency}>"
        )

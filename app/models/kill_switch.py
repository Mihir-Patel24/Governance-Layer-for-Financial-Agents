"""
app/models/kill_switch.py
──────────────────────────
Kill Switch persistent state.

Dual-layer design:
  1. PostgreSQL (source of truth) — persists halt state across restarts.
  2. Redis cache — enables fast reads without DB round-trips.

If Redis is unavailable, the system reads directly from PostgreSQL.
The DB is always updated FIRST before Redis, so a crash after DB write
but before Redis write leaves the system in a consistent state (Redis
will be corrected on next read via DB fallback path).
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import AgentStatus


class KillSwitchState(Base):
    __tablename__ = "kill_switch_state"

    # ── Primary key ────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Foreign key ─────────────────────────────────────────────────────────
    agent_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("agents.agent_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # ── State ──────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=AgentStatus.RUNNING.value
    )
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── Timestamps ─────────────────────────────────────────────────────────
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ───────────────────────────────────────────────────────
    agent: Mapped["Agent"] = relationship("Agent", back_populates="kill_switch")  # noqa: F821

    def __repr__(self) -> str:
        return f"<KillSwitchState agent={self.agent_id!r} status={self.status!r}>"


class FleetKillSwitchState(Base):
    """
    Fleet-level kill switch (singleton row with id=1).
    Uses a separate table so it survives agent table truncations.
    """
    __tablename__ = "fleet_kill_switch_state"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=AgentStatus.RUNNING.value
    )
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<FleetKillSwitchState status={self.status!r}>"

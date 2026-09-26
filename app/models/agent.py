"""
app/models/agent.py
────────────────────
Agent table — master registry of all governed agents.
Person 1 will also read this table for policy lookups.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    # ── Primary key ────────────────────────────────────────────────────────
    agent_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # ── Descriptive ────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ── Timestamps ─────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────
    spend_state: Mapped["SpendState"] = relationship(  # noqa: F821
        "SpendState", back_populates="agent", uselist=False
    )
    kill_switch: Mapped["KillSwitchState"] = relationship(  # noqa: F821
        "KillSwitchState", back_populates="agent", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Agent id={self.agent_id!r} name={self.name!r}>"

"""
app/models/idempotency_key.py
──────────────────────────────
Records processed action_ids so duplicate submissions are safely detected.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IdempotencyKey(Base):
    """
    Persisted idempotency store.
    Once an action_id is committed here, a second submission is detected
    before any spend is applied, and the original decision is returned.
    """
    __tablename__ = "idempotency_keys"

    __table_args__ = (
        UniqueConstraint("agent_id", "action_id", name="uq_idempotency_agent_action"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action_id: Mapped[str] = mapped_column(String(128), nullable=False)

    # Serialised JSON of the original EnforcementResult
    cached_result_json: Mapped[str] = mapped_column("cached_result_json", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<IdempotencyKey agent={self.agent_id!r} action={self.action_id!r}>"

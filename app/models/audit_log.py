"""
app/models/audit_log.py
────────────────────────
Hash-chained append-only audit log table.

TAMPER-EVIDENCE DESIGN
───────────────────────
Each row stores:
  • previous_hash  — the current_hash of the immediately preceding row (or
                     'GENESIS' for the first row)
  • current_hash   — SHA-256 of a canonical JSON serialisation of this row's
                     data concatenated with previous_hash

The canonical payload includes (in deterministic key order):
  event_id, timestamp (ISO-8601 UTC), agent_id, action_id, event_type,
  action, amount, currency, decision, reason_code, metadata, previous_hash

Any modification to any of these fields after the row is written will cause
verification to compute a different hash, making tampering detectable.

APPEND-ONLY CONTRACT
─────────────────────
No normal application route exposes UPDATE or DELETE on this table.
The audit verification endpoint detects broken chains.
"""
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    __table_args__ = (
        Index("ix_audit_agent_id", "agent_id"),
        Index("ix_audit_event_type", "event_type"),
        Index("ix_audit_decision", "decision"),
        Index("ix_audit_timestamp", "timestamp"),
        Index("ix_audit_sequence", "sequence_num"),
    )

    # ── Database identity ───────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sequence_num: Mapped[int] = mapped_column(nullable=False, unique=True)

    # ── Business identity ───────────────────────────────────────────────────
    event_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, default=lambda: str(uuid.uuid4())
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # ── Event data ──────────────────────────────────────────────────────────
    agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── Flexible metadata (JSON string) ─────────────────────────────────────
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Hash chain ──────────────────────────────────────────────────────────
    previous_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    current_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    # ── Row creation timestamp (server-side) ────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def canonical_payload(self) -> str:
        """
        Produce a deterministic JSON string of the auditable fields.
        Key order is fixed to ensure reproducible hashes.
        Timestamp is always ISO-8601 UTC with 'Z' suffix.
        """
        ts = self.timestamp
        # SQLite can sometimes strip tzinfo or return strings depending on type decorators
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts = ts.astimezone(timezone.utc)
        timestamp_str = ts.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

        payload = {
            "event_id": self.event_id,
            "sequence_num": self.sequence_num,
            "timestamp": timestamp_str,
            "agent_id": self.agent_id,
            "action_id": self.action_id,
            "event_type": self.event_type,
            "action": self.action,
            "amount": self.amount,
            "currency": self.currency,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "metadata": self.metadata_json,
            "previous_hash": self.previous_hash,
        }
        # json.dumps with sort_keys=True guarantees order
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def __repr__(self) -> str:
        return (
            f"<AuditLog seq={self.sequence_num} "
            f"event={self.event_type!r} agent={self.agent_id!r} "
            f"decision={self.decision!r}>"
        )

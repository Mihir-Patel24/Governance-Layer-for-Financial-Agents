"""
app/repositories/audit_repository.py
──────────────────────────────────────
Data-access layer for the hash-chained AuditLog.

APPEND-ONLY CONTRACT
────────────────────
This repository only provides methods to INSERT and READ audit entries.
No UPDATE or DELETE methods are exposed.  The application enforces this
at the repository level — not just at the HTTP layer.
"""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditRepository:

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_last_entry(self) -> Optional[AuditLog]:
        """Return the most recently appended audit entry (by sequence_num)."""
        stmt = select(AuditLog).order_by(AuditLog.sequence_num.desc()).limit(1)
        return self._db.scalars(stmt).first()

    def get_next_sequence(self) -> int:
        """Get the next sequence number (max + 1, or 1 if empty)."""
        result = self._db.execute(
            select(func.max(AuditLog.sequence_num))
        ).scalar()
        return (result or 0) + 1

    def append(self, entry: AuditLog) -> AuditLog:
        """
        Append a new entry to the audit log.
        sequence_num and hash fields must already be set by the service layer.
        """
        self._db.add(entry)
        self._db.flush()  # populate id without committing
        return entry

    # ── Query (read-only) ────────────────────────────────────────────────────

    def query(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        decision: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[int, list[AuditLog]]:
        """
        Filtered, paginated query.
        Returns (total_count, items_for_page).
        Does NOT load the entire table into memory.
        """
        stmt = select(AuditLog)

        if agent_id:
            stmt = stmt.where(AuditLog.agent_id == agent_id)
        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        if decision:
            stmt = stmt.where(AuditLog.decision == decision)
        if start_time:
            stmt = stmt.where(AuditLog.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(AuditLog.timestamp <= end_time)

        # Count without loading rows
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self._db.execute(count_stmt).scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        stmt = stmt.order_by(AuditLog.sequence_num).offset(offset).limit(page_size)
        items = list(self._db.scalars(stmt).all())

        return total, items

    def get_by_event_id(self, event_id: str) -> Optional[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.event_id == event_id)
        return self._db.scalars(stmt).first()

    def get_all_ordered(self) -> list[AuditLog]:
        """
        Load all entries in sequence order — used ONLY for chain verification.
        In production use the query() paginated method for large exports.
        """
        stmt = select(AuditLog).order_by(AuditLog.sequence_num)
        return list(self._db.scalars(stmt).all())

    def get_entry_by_sequence(self, sequence_num: int) -> Optional[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.sequence_num == sequence_num)
        return self._db.scalars(stmt).first()

    def count_all(self) -> int:
        result = self._db.execute(select(func.count(AuditLog.id))).scalar()
        return result or 0

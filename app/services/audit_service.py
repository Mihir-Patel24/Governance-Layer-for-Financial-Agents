"""
app/services/audit_service.py
──────────────────────────────
Hash-chained audit log service.

HASH ALGORITHM
──────────────
Algorithm: SHA-256 (configurable via AUDIT_HASH_ALGORITHM env var)

For each entry:
  canonical_data  = deterministic JSON of event fields (see AuditLog.canonical_payload())
  current_hash    = SHA256(canonical_data)
                    (previous_hash is embedded inside canonical_data,
                     so the chain is captured in the hash itself)

First entry:
  previous_hash = "GENESIS"

Every subsequent entry:
  previous_hash = previous_entry.current_hash

VERIFICATION ALGORITHM
───────────────────────
For each entry e[i] in sequence order:
  1. expected_previous = "GENESIS" if i==0 else e[i-1].current_hash
  2. Verify e[i].previous_hash == expected_previous         → linkage check
  3. Recompute hash from e[i].canonical_payload()
  4. Verify recomputed == e[i].current_hash                 → content check
  5. If any check fails → return first_invalid_entry = e[i].sequence_num
"""
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import Decision, EventType, ReasonCode
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditListResponse, AuditLogResponse, AuditVerifyResponse

logger = logging.getLogger(__name__)

GENESIS_HASH = "GENESIS"


def _compute_hash(canonical_payload: str, algorithm: str = "sha256") -> str:
    """Compute hex digest of canonical_payload using the configured algorithm."""
    h = hashlib.new(algorithm)
    h.update(canonical_payload.encode("utf-8"))
    return h.hexdigest()


class AuditService:

    def __init__(self, db: Session) -> None:
        self._repo = AuditRepository(db)
        self._algo = settings.audit_hash_algorithm

    # ── Append ──────────────────────────────────────────────────────────────

    def append_event(
        self,
        event_type: EventType,
        *,
        agent_id: Optional[str] = None,
        action_id: Optional[str] = None,
        action: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        decision: Optional[Decision] = None,
        reason_code: Optional[ReasonCode] = None,
        metadata: Optional[dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> AuditLog:
        """
        Create and append a new audit entry.
        The hash chain is computed inside this method — callers never set hashes.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Determine previous hash
        last = self._repo.get_last_entry()
        previous_hash = GENESIS_HASH if last is None else last.current_hash
        sequence_num = self._repo.get_next_sequence()

        metadata_json: Optional[str] = None
        if metadata:
            metadata_json = json.dumps(metadata, sort_keys=True, separators=(",", ":"))

        # Build the entry (without current_hash — we need canonical_payload first)
        entry = AuditLog(
            event_id=str(uuid.uuid4()),
            sequence_num=sequence_num,
            timestamp=timestamp,
            agent_id=agent_id,
            action_id=action_id,
            event_type=event_type.value,
            action=action,
            amount=amount,
            currency=currency,
            decision=decision.value if decision else None,
            reason_code=reason_code.value if reason_code else None,
            metadata_json=metadata_json,
            previous_hash=previous_hash,
            current_hash="PENDING",  # placeholder
        )

        # Compute canonical payload (previous_hash is embedded)
        canonical = entry.canonical_payload()
        entry.current_hash = _compute_hash(canonical, self._algo)

        stored = self._repo.append(entry)
        logger.info(
            "Audit appended seq=%d event=%s agent=%s decision=%s hash=%s...",
            sequence_num,
            event_type.value,
            agent_id,
            decision.value if decision else None,
            stored.current_hash[:16],
        )
        return stored

    # ── Verification ─────────────────────────────────────────────────────────

    def verify_chain(self) -> AuditVerifyResponse:
        """
        Verify the entire hash chain from start to end.
        Loads all entries in sequence order and checks every hash link.
        """
        entries = self._repo.get_all_ordered()

        if not entries:
            return AuditVerifyResponse(
                valid=True,
                entries_checked=0,
                first_invalid_entry=None,
                error=None,
                message="Audit log is empty — chain is trivially valid.",
            )

        expected_previous = GENESIS_HASH

        for i, entry in enumerate(entries):
            # Check 1: previous_hash linkage
            if entry.previous_hash != expected_previous:
                logger.warning(
                    "Audit chain BROKEN at seq=%d: expected previous_hash=%s..., got=%s...",
                    entry.sequence_num,
                    expected_previous[:16],
                    entry.previous_hash[:16],
                )
                return AuditVerifyResponse(
                    valid=False,
                    entries_checked=i + 1,
                    first_invalid_entry=entry.sequence_num,
                    error="PREVIOUS_HASH_MISMATCH",
                    message=f"Chain broken at sequence {entry.sequence_num}: "
                            f"previous_hash does not match preceding entry.",
                )

            # Check 2: content hash
            recomputed = _compute_hash(entry.canonical_payload(), self._algo)
            if recomputed != entry.current_hash:
                logger.warning(
                    "Audit TAMPERED at seq=%d: stored_hash=%s..., computed=%s...",
                    entry.sequence_num,
                    entry.current_hash[:16],
                    recomputed[:16],
                )
                return AuditVerifyResponse(
                    valid=False,
                    entries_checked=i + 1,
                    first_invalid_entry=entry.sequence_num,
                    error="HASH_MISMATCH",
                    message=f"Hash mismatch at sequence {entry.sequence_num}: "
                            f"entry may have been tampered with.",
                )

            expected_previous = entry.current_hash

        return AuditVerifyResponse(
            valid=True,
            entries_checked=len(entries),
            first_invalid_entry=None,
            error=None,
            message=f"Chain verified successfully. {len(entries)} entries checked.",
        )

    # ── Query ────────────────────────────────────────────────────────────────

    def query_logs(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        decision: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AuditListResponse:
        total, items = self._repo.query(
            agent_id=agent_id,
            event_type=event_type,
            decision=decision,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size,
        )
        import math
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        return AuditListResponse(
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            items=[self._to_response(e) for e in items],
        )

    def get_by_event_id(self, event_id: str) -> Optional[AuditLogResponse]:
        entry = self._repo.get_by_event_id(event_id)
        if entry is None:
            return None
        return self._to_response(entry)

    def export_all(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[AuditLogResponse]:
        """Return all matching entries for export (used by export endpoints)."""
        # For large datasets this should be streamed; semester project loads all
        total, _ = self._repo.query(
            agent_id=agent_id, start_time=start_time, end_time=end_time,
            page=1, page_size=1,
        )
        if total == 0:
            return []
        _, items = self._repo.query(
            agent_id=agent_id, start_time=start_time, end_time=end_time,
            page=1, page_size=min(total, 10000),
        )
        return [self._to_response(e) for e in items]

    # ── Internal ─────────────────────────────────────────────────────────────

    @staticmethod
    def _to_response(entry: AuditLog) -> AuditLogResponse:
        metadata: Optional[dict] = None
        if entry.metadata_json:
            try:
                metadata = json.loads(entry.metadata_json)
            except Exception:
                metadata = {"raw": entry.metadata_json}

        return AuditLogResponse(
            id=entry.id,
            sequence_num=entry.sequence_num,
            event_id=entry.event_id,
            timestamp=entry.timestamp,
            agent_id=entry.agent_id,
            action_id=entry.action_id,
            event_type=entry.event_type,
            action=entry.action,
            amount=entry.amount,
            currency=entry.currency,
            decision=entry.decision,
            reason_code=entry.reason_code,
            metadata=metadata,
            previous_hash=entry.previous_hash,
            current_hash=entry.current_hash,
            created_at=entry.created_at,
        )

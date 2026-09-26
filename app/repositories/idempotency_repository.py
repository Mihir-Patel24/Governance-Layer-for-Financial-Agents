"""
app/repositories/idempotency_repository.py
────────────────────────────────────────────
Persistent idempotency key store.
"""
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.idempotency_key import IdempotencyKey

logger = logging.getLogger(__name__)


class IdempotencyRepository:

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, agent_id: str, action_id: str) -> Optional[IdempotencyKey]:
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.agent_id == agent_id,
            IdempotencyKey.action_id == action_id,
        )
        return self._db.scalars(stmt).first()

    def store(self, agent_id: str, action_id: str, result_json: str) -> IdempotencyKey:
        """
        Store the result for an action_id. On concurrent duplicate, IntegrityError
        is raised by the DB (unique constraint); caller should re-read existing key.
        """
        key = IdempotencyKey(
            agent_id=agent_id,
            action_id=action_id,
            cached_result_json=result_json,
        )
        self._db.add(key)
        self._db.flush()
        return key

    def exists(self, agent_id: str, action_id: str) -> bool:
        return self.get(agent_id, action_id) is not None

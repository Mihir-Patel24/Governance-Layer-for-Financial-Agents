"""
app/core/redis_client.py
────────────────────────
Redis client (synchronous, using redis-py).
Redis is used as a fast-path cache for kill-switch state.
PostgreSQL remains the source of truth — if Redis is unavailable the
system falls back to the database automatically.
"""
import logging
from typing import Optional

import redis as redis_lib

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Thin wrapper around redis.Redis with graceful degradation."""

    def __init__(self) -> None:
        self._client: Optional[redis_lib.Redis] = None

    def _get_client(self) -> Optional[redis_lib.Redis]:
        if self._client is None:
            try:
                self._client = redis_lib.Redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                self._client.ping()
            except Exception as exc:
                logger.warning("Redis unavailable: %s — using DB-only mode", exc)
                self._client = None
        return self._client

    # ── Fleet halt ──────────────────────────────────────────────────────────
    def set_fleet_halted(self, halted: bool) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            if halted:
                client.set(settings.redis_fleet_halt_key, "1")
            else:
                client.delete(settings.redis_fleet_halt_key)
        except Exception as exc:
            logger.warning("Redis set_fleet_halted failed: %s", exc)

    def is_fleet_halted(self) -> Optional[bool]:
        """Returns True/False if Redis has state, None if Redis is unavailable."""
        client = self._get_client()
        if client is None:
            return None
        try:
            val = client.get(settings.redis_fleet_halt_key)
            return val == "1"
        except Exception as exc:
            logger.warning("Redis is_fleet_halted failed: %s", exc)
            return None

    # ── Agent halt ──────────────────────────────────────────────────────────
    def set_agent_halted(self, agent_id: str, halted: bool) -> None:
        client = self._get_client()
        if client is None:
            return
        key = settings.redis_agent_halt_prefix + agent_id
        try:
            if halted:
                client.set(key, "1")
            else:
                client.delete(key)
        except Exception as exc:
            logger.warning("Redis set_agent_halted failed: %s", exc)

    def is_agent_halted(self, agent_id: str) -> Optional[bool]:
        """Returns True/False if Redis has state, None if Redis is unavailable."""
        client = self._get_client()
        if client is None:
            return None
        key = settings.redis_agent_halt_prefix + agent_id
        try:
            val = client.get(key)
            return val == "1"
        except Exception as exc:
            logger.warning("Redis is_agent_halted failed: %s", exc)
            return None

    def ping(self) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            return client.ping()
        except Exception:
            return False


# Singleton instance
redis_client = RedisClient()

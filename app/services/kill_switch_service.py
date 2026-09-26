"""
app/services/kill_switch_service.py
──────────────────────────────────────
Kill Switch business logic.

EFFECTIVE STATUS RULES
──────────────────────
fleet_status == HALTED  →  ALL agents are effectively HALTED,
                           regardless of individual agent status.

agent_status == HALTED  →  that agent is HALTED even if fleet is RUNNING.

agent_status == RUNNING AND fleet_status == RUNNING  →  RUNNING.

PERSISTENCE STRATEGY
─────────────────────
  1. Write to PostgreSQL first (source of truth).
  2. Update Redis cache (fast-path for enforcement checks).
  3. If Redis is unavailable, only PostgreSQL is updated.
     Enforcement checks fall back to DB on Redis miss.
     Consistency is maintained — availability is slightly degraded.

INSTANT PROPAGATION
───────────────────
After a halt command, the next enforcement check for any agent will see
the updated Redis value (sub-millisecond read) or the PostgreSQL value
(millisecond read if Redis is unavailable).
There is no polling delay.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.enums import AgentStatus, FleetStatus
from app.core.redis_client import redis_client
from app.repositories.agent_repository import AgentRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.kill_switch_repository import KillSwitchRepository
from app.schemas.kill_switch import (
    AgentKillSwitchResponse,
    FleetKillSwitchResponse,
    KillSwitchStatusResponse,
)

logger = logging.getLogger(__name__)


class KillSwitchService:

    def __init__(self, db: Session) -> None:
        self._db = db
        self._ks_repo = KillSwitchRepository(db)
        self._agent_repo = AgentRepository(db)

    # ── Agent Halt / Resume ──────────────────────────────────────────────────

    def halt_agent(
        self,
        agent_id: str,
        reason: str,
        updated_by: str = "operator",
    ) -> AgentKillSwitchResponse:
        """Halt a specific agent."""
        if not self._agent_repo.exists(agent_id):
            raise ValueError(f"Agent '{agent_id}' not found")

        ks = self._ks_repo.upsert_agent(
            agent_id=agent_id,
            status=AgentStatus.HALTED,
            reason=reason,
            updated_by=updated_by,
        )
        self._db.commit()

        # Propagate to Redis (after DB commit so DB is consistent on crash)
        redis_client.set_agent_halted(agent_id, True)

        logger.info("AGENT_HALTED agent=%s by=%s reason=%s", agent_id, updated_by, reason)
        return self._agent_response(ks)

    def resume_agent(
        self,
        agent_id: str,
        reason: str = "operator resumed",
        updated_by: str = "operator",
    ) -> AgentKillSwitchResponse:
        """Resume a halted agent."""
        if not self._agent_repo.exists(agent_id):
            raise ValueError(f"Agent '{agent_id}' not found")

        ks = self._ks_repo.upsert_agent(
            agent_id=agent_id,
            status=AgentStatus.RUNNING,
            reason=reason,
            updated_by=updated_by,
        )
        self._db.commit()

        redis_client.set_agent_halted(agent_id, False)

        logger.info("AGENT_RESUMED agent=%s by=%s", agent_id, updated_by)
        return self._agent_response(ks)

    # ── Fleet Halt / Resume ──────────────────────────────────────────────────

    def halt_fleet(
        self,
        reason: str,
        updated_by: str = "operator",
    ) -> FleetKillSwitchResponse:
        """Halt the entire agent fleet."""
        fleet = self._ks_repo.update_fleet(
            status=AgentStatus.HALTED,
            reason=reason,
            updated_by=updated_by,
        )
        self._db.commit()

        redis_client.set_fleet_halted(True)

        agents = self._ks_repo.get_all_agents()
        logger.info("FLEET_HALTED by=%s reason=%s agents=%d", updated_by, reason, len(agents))
        return FleetKillSwitchResponse(
            status=FleetStatus.HALTED,
            reason=fleet.reason,
            updated_by=fleet.updated_by,
            updated_at=fleet.updated_at,
            agents_affected=len(agents),
        )

    def resume_fleet(
        self,
        reason: str = "operator resumed fleet",
        updated_by: str = "operator",
    ) -> FleetKillSwitchResponse:
        """Resume the entire fleet."""
        fleet = self._ks_repo.update_fleet(
            status=AgentStatus.RUNNING,
            reason=reason,
            updated_by=updated_by,
        )
        self._db.commit()

        redis_client.set_fleet_halted(False)

        agents = self._ks_repo.get_all_agents()
        logger.info("FLEET_RESUMED by=%s agents=%d", updated_by, len(agents))
        return FleetKillSwitchResponse(
            status=FleetStatus.RUNNING,
            reason=fleet.reason,
            updated_by=fleet.updated_by,
            updated_at=fleet.updated_at,
            agents_affected=len(agents),
        )

    # ── Enforcement check ────────────────────────────────────────────────────

    def is_agent_effectively_halted(self, agent_id: str) -> tuple[bool, Optional[str]]:
        """
        Returns (is_halted, reason_description).
        Checks fleet first (Redis → DB fallback), then agent.
        """
        # 1. Check fleet halt (Redis fast path)
        fleet_halted = redis_client.is_fleet_halted()
        if fleet_halted is None:
            # Redis unavailable — fall back to DB
            fleet = self._ks_repo.get_fleet()
            fleet_halted = fleet.status == AgentStatus.HALTED.value

        if fleet_halted:
            fleet = self._ks_repo.get_fleet()
            return True, f"Fleet halted: {fleet.reason}"

        # 2. Check agent halt (Redis fast path)
        agent_halted = redis_client.is_agent_halted(agent_id)
        if agent_halted is None:
            ks = self._ks_repo.get_agent(agent_id)
            agent_halted = (ks is not None and ks.status == AgentStatus.HALTED.value)

        if agent_halted:
            ks = self._ks_repo.get_agent(agent_id)
            reason = ks.reason if ks else "Agent halted"
            return True, reason

        return False, None

    # ── Status queries ───────────────────────────────────────────────────────

    def get_agent_status(self, agent_id: str) -> AgentKillSwitchResponse:
        if not self._agent_repo.exists(agent_id):
            raise ValueError(f"Agent '{agent_id}' not found")

        ks = self._ks_repo.get_agent(agent_id)
        if ks is None:
            # No explicit record → create default RUNNING state
            ks = self._ks_repo.upsert_agent(
                agent_id=agent_id,
                status=AgentStatus.RUNNING,
                reason=None,
                updated_by=None,
            )
            self._db.commit()

        return self._agent_response(ks)

    def get_full_status(self) -> KillSwitchStatusResponse:
        fleet = self._ks_repo.get_fleet()
        all_agents_ks = self._ks_repo.get_all_agents()
        fleet_halted = fleet.status == AgentStatus.HALTED.value

        return KillSwitchStatusResponse(
            fleet_status=FleetStatus(fleet.status),
            fleet_reason=fleet.reason,
            fleet_updated_at=fleet.updated_at,
            agents=[
                AgentKillSwitchResponse(
                    agent_id=ks.agent_id,
                    status=AgentStatus(ks.status),
                    reason=ks.reason,
                    updated_by=ks.updated_by,
                    updated_at=ks.updated_at,
                    effective_status=(
                        AgentStatus.HALTED if fleet_halted or ks.status == AgentStatus.HALTED.value
                        else AgentStatus.RUNNING
                    ),
                )
                for ks in all_agents_ks
            ],
        )

    # ── Internal ─────────────────────────────────────────────────────────────

    def _agent_response(self, ks) -> AgentKillSwitchResponse:
        fleet = self._ks_repo.get_fleet()
        fleet_halted = fleet.status == AgentStatus.HALTED.value
        effective = (
            AgentStatus.HALTED
            if fleet_halted or ks.status == AgentStatus.HALTED.value
            else AgentStatus.RUNNING
        )
        return AgentKillSwitchResponse(
            agent_id=ks.agent_id,
            status=AgentStatus(ks.status),
            reason=ks.reason,
            updated_by=ks.updated_by,
            updated_at=ks.updated_at,
            effective_status=effective,
        )

"""
app/repositories/kill_switch_repository.py
────────────────────────────────────────────
Data-access layer for KillSwitchState and FleetKillSwitchState.
"""
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.kill_switch import FleetKillSwitchState, KillSwitchState
from app.core.enums import AgentStatus

logger = logging.getLogger(__name__)

_FLEET_ROW_ID = 1  # Singleton fleet row id


class KillSwitchRepository:

    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Agent level ─────────────────────────────────────────────────────────

    def get_agent(self, agent_id: str) -> Optional[KillSwitchState]:
        stmt = select(KillSwitchState).where(KillSwitchState.agent_id == agent_id)
        return self._db.scalars(stmt).first()

    def get_all_agents(self) -> list[KillSwitchState]:
        stmt = select(KillSwitchState)
        return list(self._db.scalars(stmt).all())

    def upsert_agent(
        self,
        agent_id: str,
        status: AgentStatus,
        reason: Optional[str],
        updated_by: Optional[str],
    ) -> KillSwitchState:
        """Create or update kill switch state for an agent."""
        existing = self.get_agent(agent_id)
        if existing is None:
            existing = KillSwitchState(agent_id=agent_id)
            self._db.add(existing)

        existing.status = status.value
        existing.reason = reason
        existing.updated_by = updated_by
        self._db.flush()
        return existing

    # ── Fleet level ─────────────────────────────────────────────────────────

    def get_fleet(self) -> FleetKillSwitchState:
        """Get fleet state, creating the singleton row if it doesn't exist."""
        stmt = select(FleetKillSwitchState).where(
            FleetKillSwitchState.id == _FLEET_ROW_ID
        )
        fleet = self._db.scalars(stmt).first()
        if fleet is None:
            fleet = FleetKillSwitchState(id=_FLEET_ROW_ID, status=AgentStatus.RUNNING.value)
            self._db.add(fleet)
            self._db.flush()
        return fleet

    def update_fleet(
        self,
        status: AgentStatus,
        reason: Optional[str],
        updated_by: Optional[str],
    ) -> FleetKillSwitchState:
        fleet = self.get_fleet()
        fleet.status = status.value
        fleet.reason = reason
        fleet.updated_by = updated_by
        self._db.flush()
        return fleet

"""
app/repositories/agent_repository.py
──────────────────────────────────────
Data-access layer for the Agent table.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent


class AgentRepository:

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, agent_id: str) -> Optional[Agent]:
        stmt = select(Agent).where(Agent.agent_id == agent_id)
        return self._db.scalars(stmt).first()

    def get_all(self) -> list[Agent]:
        stmt = select(Agent)
        return list(self._db.scalars(stmt).all())

    def create(self, agent_id: str, name: str, description: Optional[str] = None) -> Agent:
        agent = Agent(agent_id=agent_id, name=name, description=description)
        self._db.add(agent)
        self._db.flush()
        return agent

    def exists(self, agent_id: str) -> bool:
        return self.get(agent_id) is not None

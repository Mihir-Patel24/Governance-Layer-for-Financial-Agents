"""
app/api/v1/routes/agents.py
────────────────────────────
Agent management endpoints.
Used to register agents and query agent list.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.agent_repository import AgentRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentCreateRequest(BaseModel):
    agent_id: str
    name: str
    description: Optional[str] = None


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    description: Optional[str]


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent",
)
def create_agent(req: AgentCreateRequest, db: Session = Depends(get_db)) -> AgentResponse:
    repo = AgentRepository(db)
    if repo.exists(req.agent_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "AGENT_EXISTS", "message": f"Agent '{req.agent_id}' already registered"},
        )
    agent = repo.create(req.agent_id, req.name, req.description)
    db.commit()
    return AgentResponse(agent_id=agent.agent_id, name=agent.name, description=agent.description)


@router.get(
    "",
    response_model=list[AgentResponse],
    summary="List all registered agents",
)
def list_agents(db: Session = Depends(get_db)) -> list[AgentResponse]:
    repo = AgentRepository(db)
    agents = repo.get_all()
    return [AgentResponse(agent_id=a.agent_id, name=a.name, description=a.description)
            for a in agents]


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get a specific agent",
)
def get_agent(agent_id: str, db: Session = Depends(get_db)) -> AgentResponse:
    repo = AgentRepository(db)
    agent = repo.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "AGENT_NOT_FOUND", "message": f"Agent '{agent_id}' not found"},
        )
    return AgentResponse(agent_id=agent.agent_id, name=agent.name, description=agent.description)

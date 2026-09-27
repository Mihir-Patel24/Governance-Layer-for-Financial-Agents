from fastapi import APIRouter
from app.api.v1.endpoints import governance, agents, kill_switch, audit

api_router = APIRouter()
api_router.include_router(governance.router, prefix="/governance", tags=["Governance"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(kill_switch.router, prefix="/kill-switch", tags=["Kill Switch"])
api_router.include_router(audit.router, tags=["Audit & Compliance"])

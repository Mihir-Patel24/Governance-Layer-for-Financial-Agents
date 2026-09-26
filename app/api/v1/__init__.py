"""
app/api/v1/__init__.py
──────────────────────
v1 API router — assembles all sub-routers.
"""
from fastapi import APIRouter

from app.api.v1.routes import agents, audit, enforce, kill_switch, spend

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(agents.router)
api_router.include_router(spend.router)
api_router.include_router(kill_switch.router)
api_router.include_router(audit.router)
api_router.include_router(enforce.router)

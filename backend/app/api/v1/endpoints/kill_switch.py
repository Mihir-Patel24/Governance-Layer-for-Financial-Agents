from fastapi import APIRouter
from app.services.kill_switch_service import kill_switch_service

router = APIRouter()

@router.post("/global")
def trigger_global_kill():
    """Trigger master emergency stop for all fleet agents"""
    return kill_switch_service.trigger_global_kill("Master Circuit Breaker Activated")

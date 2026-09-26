"""
tests/unit/test_kill_switch.py
────────────────────────────────
Tests for KillSwitchService invariants.
"""
from app.core.enums import AgentStatus, FleetStatus
from app.services.kill_switch_service import KillSwitchService


def test_agent_halt(db_with_agents):
    svc = KillSwitchService(db_with_agents)
    
    # Check default status
    status = svc.get_agent_status("travel-agent")
    assert status.effective_status == AgentStatus.RUNNING

    # Halt
    res = svc.halt_agent("travel-agent", "Test halt")
    assert res.status == AgentStatus.HALTED
    assert res.effective_status == AgentStatus.HALTED

    # Check
    halted, reason = svc.is_agent_effectively_halted("travel-agent")
    assert halted is True
    assert reason == "Test halt"


def test_agent_resume(db_with_agents):
    svc = KillSwitchService(db_with_agents)
    svc.halt_agent("travel-agent", "Test halt")
    
    res = svc.resume_agent("travel-agent", "Test resume")
    assert res.status == AgentStatus.RUNNING
    
    halted, _ = svc.is_agent_effectively_halted("travel-agent")
    assert halted is False


def test_fleet_halt_overrides_agent(db_with_agents):
    svc = KillSwitchService(db_with_agents)
    
    # Agent is running individually
    status = svc.get_agent_status("travel-agent")
    assert status.status == AgentStatus.RUNNING

    # Halt fleet
    svc.halt_fleet("Fleet test halt")
    
    # Agent should now be effectively halted
    halted, reason = svc.is_agent_effectively_halted("travel-agent")
    assert halted is True
    assert "Fleet halted:" in reason
    
    # Get status API should reflect effective halt
    status2 = svc.get_agent_status("travel-agent")
    assert status2.status == AgentStatus.RUNNING  # Individually still running
    assert status2.effective_status == AgentStatus.HALTED  # But effectively halted

    # Resume fleet
    svc.resume_fleet("Resume")
    
    halted2, _ = svc.is_agent_effectively_halted("travel-agent")
    assert halted2 is False

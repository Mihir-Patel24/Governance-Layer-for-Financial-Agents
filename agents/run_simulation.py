import os
import sys
import json
import csv
from datetime import datetime
from typing import List, Dict, Any

# Ensure stdout handles UTF-8 on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.governance_client import GovernanceClient
from agents.scenarios import ScenarioType
from agents.travel_agent import TravelAgent
from agents.servicing_agent import ServicingAgent
from agents.rewards_agent import RewardsAgent


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    print("\n" + "-" * 50)
    print(f"  --> {title}")
    print("-" * 50)


def safe_str(val: Any) -> str:
    """Safely converts values to string for terminal printing."""
    try:
        return str(val)
    except Exception:
        return str(val).encode("ascii", "replace").decode("ascii")


def export_action_stream(history_records: List[Dict[str, Any]], output_dir: str) -> Dict[str, str]:
    """
    Exports collected raw agent history stream into JSON and CSV files.
    Preserves raw event timestamps, metadata, and governance decisions for future ML pipeline.
    """
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "simulation_actions.json")
    csv_path = os.path.join(output_dir, "simulation_actions.csv")

    flattened_records = []
    for item in history_records:
        action = item.get("action") or {}
        gov_resp = item.get("governance_response") or {}

        record = {
            "timestamp": item.get("timestamp", datetime.now().isoformat()),
            "request_id": gov_resp.get("request_id", "N/A"),
            "agent_id": action.get("agent_id", "unknown"),
            "agent_type": action.get("agent_type", "banking"),
            "action_type": action.get("action_type", "unknown"),
            "amount": float(action.get("amount", 0.0)),
            "currency": action.get("currency", "INR"),
            "governance_verdict": item.get("verdict") or gov_resp.get("verdict", "UNKNOWN"),
            "policy_passed": gov_resp.get("policy_passed", False),
            "execution_status": item.get("execution_status", "UNKNOWN"),
            "reason": gov_resp.get("reason", ""),
            "audit_hash": gov_resp.get("audit_hash", ""),
            "execution_latency_ms": float(gov_resp.get("execution_latency_ms", 0.0)),
            "description": action.get("description", ""),
            "context_json": json.dumps(action.get("context", {}))
        }
        flattened_records.append(record)

    # Export to JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(flattened_records, f, indent=2)

    # Export to CSV
    if flattened_records:
        fieldnames = list(flattened_records[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_records)

    return {"json": json_path, "csv": csv_path}


def run_full_simulation():
    backend_url = os.getenv("GOVERNANCE_URL", "http://localhost:8000")

    print_header("GOVERNANCE LAYER SIMULATION RUNNER")
    print(f"Backend Gateway : {backend_url}/api/governance/evaluate")

    client = GovernanceClient(base_url=backend_url)

    # 1. Connection Check
    print_section("Backend Connection & Profile Setup")
    if not client.check_agent_exists("travel-agent-01"):
        print("[WARN] Governance Gateway offline or ping failed. Simulation will run in Fail-Closed mode.")
    else:
        print("[OK] Connected to Governance Backend successfully.")

    # Instantiate Agents
    travel_agent = TravelAgent(governance_url=backend_url)
    servicing_agent = ServicingAgent(governance_url=backend_url)
    rewards_agent = RewardsAgent(governance_url=backend_url, auto_register=True)

    print("[OK] Travel Agent identity    : travel-agent-01")
    print("[OK] Servicing Agent identity : servicing-agent-01")
    print("[OK] Rewards Agent identity   : rewards-agent-01 (Registered via POST /api/agents/register)")

    # 2. Normal Scenarios
    print_header("NORMAL SCENARIOS")

    print_section("Travel Agent - Normal Operations")
    travel_agent.run_scenario(ScenarioType.NORMAL)

    print_section("Servicing Agent - Normal Operations")
    servicing_agent.run_scenario(ScenarioType.NORMAL)

    print_section("Rewards Agent - Normal Operations")
    rewards_agent.run_scenario(ScenarioType.NORMAL)

    # 3. Unusual Scenarios (For future anomaly detection ingest)
    print_header("UNUSUAL BEHAVIOR SCENARIOS")

    print_section("Travel Agent - Spending Spike Scenario (Rs.25,000 > Rs.15,000 limit)")
    travel_agent.run_scenario(ScenarioType.SPENDING_SPIKE)

    print_section("Servicing Agent - Rapid Repeated Action Scenario (5 consecutive fee reversals)")
    servicing_agent.run_scenario(ScenarioType.BURST)

    print_section("Rewards Agent - Repeated Redemptions & Policy Limit Attempt")
    rewards_agent.run_scenario(ScenarioType.BURST)
    rewards_agent.run_scenario(ScenarioType.POLICY_LIMIT_ATTEMPT)

    # 4. Collect Action Streams & Calculate Stats
    all_history = travel_agent.history + servicing_agent.history + rewards_agent.history

    allowed_count = sum(1 for h in all_history if h.get("execution_status") == "EXECUTED")
    blocked_count = sum(1 for h in all_history if h.get("execution_status") == "BLOCKED")
    hitl_count = sum(1 for h in all_history if h.get("execution_status") == "PENDING_APPROVAL")
    error_count = sum(1 for h in all_history if h.get("execution_status") == "FAILED")
    total_count = len(all_history)

    # 5. Export Action Stream Data
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "output"))
    export_paths = export_action_stream(all_history, output_dir)

    # 6. Summary Display
    print_header("SIMULATION SUMMARY")
    print(f"  Total Actions Evaluated : {total_count}")
    print(f"  - ALLOWED (Executed)    : {allowed_count}")
    print(f"  - BLOCKED (Governance)  : {blocked_count}")
    print(f"  - HITL (Pending)        : {hitl_count}")
    print(f"  - ERRORS / FAIL-CLOSED  : {error_count}")
    print("\n  Action Stream Exported To:")
    print(f"  - JSON : {export_paths['json']}")
    print(f"  - CSV  : {export_paths['csv']}")
    print("=" * 70)


if __name__ == "__main__":
    run_full_simulation()

"""
scripts/seed.py
────────────────
Seed the database with demo agents and budget configurations.

Agents seeded:
  travel-agent     — Daily limit: ₹15,000  (matches demo spec exactly)
  servicing-agent  — Daily limit: ₹20,000
  rewards-agent    — Daily limit: ₹10,000

Run from backend/ directory:
  python scripts/seed.py
"""
import os
import sys

# Ensure the backend/ directory is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.enums import PeriodType
from app.repositories.agent_repository import AgentRepository
from app.repositories.kill_switch_repository import KillSwitchRepository
from app.schemas.spend import BudgetConfigRequest
from app.services.spend_cap_service import SpendCapService

AGENTS = [
    {
        "agent_id": "travel-agent",
        "name": "Travel Agent",
        "description": "Manages travel bookings and transportation expenses",
        "limit": 15000.0,
    },
    {
        "agent_id": "servicing-agent",
        "name": "Servicing Agent",
        "description": "Handles service and maintenance fee processing",
        "limit": 20000.0,
    },
    {
        "agent_id": "rewards-agent",
        "name": "Rewards Agent",
        "description": "Manages reward point redemptions and cashback",
        "limit": 10000.0,
    },
]


def seed():
    print("Seeding database...")
    db = SessionLocal()
    try:
        agent_repo = AgentRepository(db)
        ks_repo = KillSwitchRepository(db)

        for a in AGENTS:
            if not agent_repo.exists(a["agent_id"]):
                agent_repo.create(a["agent_id"], a["name"], a["description"])
                db.commit()
                print(f"  ✓ Created agent: {a['agent_id']}")
            else:
                print(f"  - Agent already exists: {a['agent_id']}")

            # Ensure fleet row exists
            ks_repo.get_fleet()
            db.commit()

        for a in AGENTS:
            svc = SpendCapService(db)
            existing = svc.get_budget(a["agent_id"])
            if existing is None:
                svc.configure_budget(
                    a["agent_id"],
                    BudgetConfigRequest(
                        limit_amount=a["limit"],
                        currency="INR",
                        period_type=PeriodType.DAILY,
                        rollover_amount=0.0,
                    ),
                )
                print(f"  ✓ Budget configured: {a['agent_id']} limit=₹{a['limit']:,.0f}")
            else:
                print(f"  - Budget already exists: {a['agent_id']} limit=₹{existing.limit_amount:,.0f}")

        print("\nSeed complete!")
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

"""
tests/conftest.py
──────────────────
Shared pytest fixtures.
Uses SQLite in-memory database for fast, dependency-free testing.
PostgreSQL-specific features (SELECT FOR UPDATE) are mocked/skipped in unit tests
and tested separately via integration tests.
"""
import os

# Point to testing environment BEFORE importing app modules
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("AUDIT_HASH_ALGORITHM", "sha256")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

import app.models  # Ensure models are loaded before Base.metadata.create_all
from app.core.database import Base


# ── SQLite test engine ───────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)

# Enable WAL mode and foreign keys for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db() -> Session:
    """
    Provide a clean in-memory SQLite session for each test.
    Tables are created fresh and dropped after each test.
    """
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_with_agents(db: Session):
    """Pre-seeded database with the 3 demo agents."""
    from app.repositories.agent_repository import AgentRepository
    from app.repositories.kill_switch_repository import KillSwitchRepository

    repo = AgentRepository(db)
    repo.create("travel-agent", "Travel Agent")
    repo.create("servicing-agent", "Servicing Agent")
    repo.create("rewards-agent", "Rewards Agent")

    ks_repo = KillSwitchRepository(db)
    ks_repo.get_fleet()  # ensure singleton exists
    db.commit()
    return db


@pytest.fixture(scope="function")
def db_with_budgets(db_with_agents: Session):
    """Agents + budgets configured."""
    from app.schemas.spend import BudgetConfigRequest
    from app.services.spend_cap_service import SpendCapService
    from app.core.enums import PeriodType

    svc = SpendCapService(db_with_agents)
    svc.configure_budget("travel-agent", BudgetConfigRequest(
        limit_amount=15000.0, currency="INR", period_type=PeriodType.DAILY
    ))
    svc.configure_budget("servicing-agent", BudgetConfigRequest(
        limit_amount=20000.0, currency="INR", period_type=PeriodType.DAILY
    ))
    svc.configure_budget("rewards-agent", BudgetConfigRequest(
        limit_amount=10000.0, currency="INR", period_type=PeriodType.DAILY
    ))
    return db_with_agents


# ── FastAPI test client ────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def client(db_with_budgets: Session):
    """FastAPI TestClient with overridden DB dependency."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db

    def override_get_db():
        yield db_with_budgets

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

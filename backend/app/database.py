import os
import json
from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Try loading environment variables from .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Environment Configurable Primary Database URL: PostgreSQL
POSTGRES_DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sentinelai_db")
SQLITE_FALLBACK_URL = "sqlite:///./sentinelai.db"

# Try initializing PostgreSQL engine first; fallback to local SQLite if Postgres server is offline
try:
    if POSTGRES_DB_URL.startswith("postgresql"):
        engine = create_engine(POSTGRES_DB_URL, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            pass
    else:
        engine = create_engine(POSTGRES_DB_URL)
except Exception as e:
    print(f"⚠️ PostgreSQL connection offline ({e}). Utilizing fallback database: {SQLITE_FALLBACK_URL}")
    engine = create_engine(SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# Person 2 Database Entities (3 Core Tables)
# ==========================================

class AgentModel(Base):
    """Stores dynamic agent profiles and policy constraints"""
    __tablename__ = "agents"

    agent_id = Column(String(64), primary_key=True, index=True)
    agent_name = Column(String(128), nullable=False)
    agent_type = Column(String(64), nullable=False) # e.g. banking, government, healthcare
    status = Column(String(32), default="ACTIVE")  # ACTIVE, PAUSED, TERMINATED
    single_tx_limit = Column(Float, default=10000.0)
    daily_spend_cap = Column(Float, default=50000.0)
    monthly_spend_cap = Column(Float, default=500000.0)
    allowed_actions_json = Column(Text, nullable=False) # Serialized JSON list e.g. ["book_flight","book_hotel"]
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def allowed_actions(self):
        try:
            return json.loads(self.allowed_actions_json)
        except Exception:
            return []

    @allowed_actions.setter
    def allowed_actions(self, value: list):
        self.allowed_actions_json = json.dumps(value)


class SpendRecordModel(Base):
    """Tracks accumulated agent spend per rolling time window (Daily, Weekly, Monthly)"""
    __tablename__ = "spend_records"

    id = Column(String(64), primary_key=True, index=True)
    agent_id = Column(String(64), index=True, nullable=False)
    window_type = Column(String(32), default="DAILY") # DAILY, WEEKLY, MONTHLY
    accumulated_spend = Column(Float, default=0.0)
    window_reset_at = Column(DateTime, default=datetime.utcnow)


class AuditLedgerModel(Base):
    """Stores immutable cryptographic SHA-256 block hash records"""
    __tablename__ = "audit_ledger"

    block_id = Column(String(64), primary_key=True, index=True)
    request_id = Column(String(64), index=True, nullable=False)
    agent_id = Column(String(64), index=True, nullable=False)
    action_type = Column(String(64), nullable=False)
    amount = Column(Float, default=0.0)
    verdict = Column(String(32), nullable=False) # ALLOW, BLOCK, HITL_REQUIRED
    reason = Column(Text, nullable=False)
    ml_anomaly_score = Column(Float, default=0.0)
    previous_hash = Column(String(128), nullable=False)
    block_hash = Column(String(128), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ==========================================
# Database Initialization & Session Utilities
# ==========================================

def init_db():
    """Create all database tables and seed initial default agent records"""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if default agents exist, if not seed them
        if not db.query(AgentModel).filter(AgentModel.agent_id == "travel-agent-01").first():
            travel_agent = AgentModel(
                agent_id="travel-agent-01",
                agent_name="Corporate Travel Booking Assistant",
                agent_type="banking",
                status="ACTIVE",
                single_tx_limit=15000.0,
                daily_spend_cap=50000.0,
                monthly_spend_cap=500000.0,
                allowed_actions_json=json.dumps(["book_flight", "book_hotel", "cancel_booking"])
            )
            servicing_agent = AgentModel(
                agent_id="servicing-agent-01",
                agent_name="Customer Support Concierge",
                agent_type="banking",
                status="ACTIVE",
                single_tx_limit=1000.0,
                daily_spend_cap=5000.0,
                monthly_spend_cap=50000.0,
                allowed_actions_json=json.dumps(["fee_reversal", "issue_credit", "update_address"])
            )
            subsidy_agent = AgentModel(
                agent_id="subsidy-agent-01",
                agent_name="Government Direct Subsidy Disbursement Agent",
                agent_type="government",
                status="ACTIVE",
                single_tx_limit=25000.0,
                daily_spend_cap=50000.0,
                monthly_spend_cap=1000000.0,
                allowed_actions_json=json.dumps(["release_subsidy", "flag_discrepancy", "verify_beneficiary"])
            )
            db.add_all([travel_agent, servicing_agent, subsidy_agent])
            db.commit()
    finally:
        db.close()

def get_db() -> Generator[Session, None, None]:
    """Dependency injection helper for FastAPI database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

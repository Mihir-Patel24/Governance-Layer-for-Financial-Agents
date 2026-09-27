from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text
from app.core.database import Base

class AuditLedgerModel(Base):
    """PostgreSQL entity for SHA-256 cryptographic hash-chained audit log"""
    __tablename__ = "audit_ledger"

    block_id = Column(String(64), primary_key=True, index=True)
    request_id = Column(String(64), index=True, nullable=False)
    agent_id = Column(String(64), index=True, nullable=False)
    action_type = Column(String(64), nullable=False)
    amount = Column(Float, default=0.0)
    verdict = Column(String(32), nullable=False)
    reason = Column(Text, nullable=False)
    ml_anomaly_score = Column(Float, default=0.0)
    previous_hash = Column(String(128), nullable=False)
    block_hash = Column(String(128), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

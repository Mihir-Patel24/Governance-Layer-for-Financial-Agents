from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime
from app.core.database import Base
from app.core.enums import WindowTypeEnum

class SpendRecordModel(Base):
    """PostgreSQL entity for multi-window rolling spend caps"""
    __tablename__ = "spend_records"

    id = Column(String(64), primary_key=True, index=True)
    agent_id = Column(String(64), index=True, nullable=False)
    window_type = Column(String(32), default=WindowTypeEnum.DAILY.value)
    accumulated_spend = Column(Float, default=0.0)
    window_reset_at = Column(DateTime, default=datetime.utcnow)

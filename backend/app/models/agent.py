import json
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text
from app.core.database import Base
from app.core.enums import AgentStatusEnum

class AgentModel(Base):
    """PostgreSQL Agent Entity storing policy constraints and status"""
    __tablename__ = "agents"

    agent_id = Column(String(64), primary_key=True, index=True)
    agent_name = Column(String(128), nullable=False)
    agent_type = Column(String(64), nullable=False)
    status = Column(String(32), default=AgentStatusEnum.ACTIVE.value)
    single_tx_limit = Column(Float, default=10000.0)
    daily_spend_cap = Column(Float, default=50000.0)
    monthly_spend_cap = Column(Float, default=500000.0)
    allowed_actions_json = Column(Text, nullable=False)
    allowed_start_hour = Column(Float, default=0.0)
    allowed_end_hour = Column(Float, default=24.0)
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

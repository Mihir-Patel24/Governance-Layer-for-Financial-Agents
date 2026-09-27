from enum import Enum

class VerdictEnum(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    HITL_REQUIRED = "HITL_REQUIRED"

class AgentStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    TERMINATED = "TERMINATED"

class WindowTypeEnum(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

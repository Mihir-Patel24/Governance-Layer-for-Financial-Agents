"""
app/core/config.py
──────────────────
Central settings loaded from environment variables via pydantic-settings.
All application code should import `settings` from here.
"""
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────
    app_env: Literal["development", "testing", "production"] = "development"
    app_name: str = "Governance Layer"
    app_version: str = "1.0.0"
    debug: bool = True

    # ── Database ───────────────────────────────────────────────────────
    database_url: str = "postgresql://govuser:govpass@localhost:5432/govdb"
    database_url_async: str = (
        "postgresql+asyncpg://govuser:govpass@localhost:5432/govdb"
    )

    # ── Redis ──────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_fleet_halt_key: str = "fleet:halted"
    redis_agent_halt_prefix: str = "agent:halted:"

    # ── Audit ──────────────────────────────────────────────────────────
    audit_hash_algorithm: str = "sha256"

    # ── OPA (Person 1) ────────────────────────────────────────────────
    opa_url: str = "http://localhost:8181"
    opa_policy_path: str = "/v1/data/governance/allow"

    # ── Agent budget defaults (INR) ───────────────────────────────────
    travel_agent_daily_limit: float = 15000.0
    servicing_agent_daily_limit: float = 20000.0
    rewards_agent_daily_limit: float = 10000.0

    @field_validator("audit_hash_algorithm")
    @classmethod
    def validate_hash_algo(cls, v: str) -> str:
        import hashlib
        if v not in hashlib.algorithms_available:
            raise ValueError(f"Unsupported hash algorithm: {v}")
        return v.lower()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()


# Convenience alias used throughout the codebase
settings = get_settings()

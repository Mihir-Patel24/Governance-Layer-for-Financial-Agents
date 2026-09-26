"""
app/core/database.py
──────────────────────
SQLAlchemy synchronous engine + session factory.
We use synchronous SQLAlchemy because the ORM row-level locking (SELECT FOR UPDATE)
pattern is simpler and safer than async for the concurrency requirements of
the Spend Cap Service.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


# ── Engine ─────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # discard dead connections
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

# ── Session factory ────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── Declarative base shared by all models ─────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ─────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """Yield a database session and guarantee closure after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Try loading environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Primary Database Connection: PostgreSQL (with zero-crash SQLite fallback)
POSTGRES_DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sentinelai_db")
SQLITE_FALLBACK_URL = "sqlite:///./sentinelai.db"

try:
    if POSTGRES_DB_URL.startswith("postgresql"):
        engine = create_engine(POSTGRES_DB_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
    else:
        engine = create_engine(POSTGRES_DB_URL)
except Exception as e:
    print(f"⚠️ PostgreSQL connection offline ({e}). Utilizing fallback database: {SQLITE_FALLBACK_URL}")
    engine = create_engine(SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency injection helper for FastAPI database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

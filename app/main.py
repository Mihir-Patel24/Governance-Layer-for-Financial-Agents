"""
app/main.py
────────────
FastAPI application entry point.

Person 1 will integrate their Policy Gateway into this same application
by adding their own router.  Do NOT create a second FastAPI instance.
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ── Application lifespan ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s (env=%s)", settings.app_name, settings.app_version, settings.app_env)
    yield
    logger.info("Shutting down %s", settings.app_name)


# ── FastAPI instance ───────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## Governance Layer for Financial Agents

**Person 2 — The Enforcer** subsystem API.

### Components
- **Spend Cap Service** — real-time budget enforcement per agent
- **Kill Switch Service** — instant agent / fleet halt
- **Audit Log** — hash-chained, tamper-evident event log

### Integration Points
- Person 1 (Policy Gateway): `POST /api/v1/enforce?opa_allowed=true|false`
- Person 4 (Dashboard): `/api/v1/kill-switch/status`, `/api/v1/audit/logs`
- Person 3 (Agents): `POST /api/v1/enforce`
""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS (for Person 4 React dashboard) ───────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s %s → %s", request.method, request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Check server logs.",
            }
        },
    )


# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, Any]:
    """Health check endpoint. Returns service status and version."""
    from app.core.redis_client import redis_client
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "redis": "ok" if redis_client.ping() else "unavailable",
    }


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.app_name} API",
        "docs": "/docs",
        "version": settings.app_version,
    }

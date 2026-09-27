import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Try loading environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.api.v1.router import api_router

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    title="SentinelAI Governance Engine",
    description="Unified Governance Engine interlocking Person 1 Policy Gateway with Person 2 Spend Caps, Circuit Breaker, & Cryptographic Audit Ledger.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "system": "SentinelAI Integrated Governance Gateway",
        "status": "ONLINE",
        "environment": ENVIRONMENT,
        "integrated_roles": ["Person 1 - Policy Architect", "Person 2 - The Enforcer"],
        "timestamp": datetime.now().isoformat()
    }

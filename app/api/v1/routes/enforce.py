"""
app/api/v1/routes/enforce.py
──────────────────────────────
Person 1 integration endpoint — central action enforcement.

Person 1 (Policy Gateway) calls POST /enforce after OPA decides.
Agents can also call this directly if Person 1 is not yet integrated.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.action import ActionRequest, EnforcementResult
from app.services.enforcer_service import EnforcerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enforce", tags=["Enforcement"])


@router.post(
    "",
    response_model=EnforcementResult,
    summary="Full governance enforcement pipeline (Person 1 integration point)",
)
def enforce_action(
    request: ActionRequest,
    opa_allowed: Optional[bool] = Query(
        None,
        description="OPA policy decision (True=allow, False=deny). "
                    "Pass None to skip OPA step (enforcement only).",
    ),
    opa_reason: Optional[str] = Query(
        None,
        description="Reason from OPA if opa_allowed=False.",
    ),
    db: Session = Depends(get_db),
) -> EnforcementResult:
    """
    Run the complete Person 2 enforcement pipeline:

    1. Validate request fields
    2. Fleet halt check
    3. Agent halt check
    4. OPA policy check (if opa_allowed provided)
    5. Duplicate action detection
    6. Spend cap check
    7. Reserve spend (if allowed)
    8. Audit event

    Person 1 (Policy Gateway) calls this endpoint after OPA decision.
    Person 3 (Agents) can call this directly for standalone testing.
    """
    svc = EnforcerService(db)
    return svc.enforce(request, opa_allowed=opa_allowed, opa_reason=opa_reason)

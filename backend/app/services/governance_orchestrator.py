import uuid
import time
from datetime import datetime
from app.schemas.action import ActionRequest, ActionResponse
from app.core.enums import VerdictEnum
from app.services.policy_engine import policy_engine
from app.services.spend_cap_service import spend_cap_service
from app.services.kill_switch_service import kill_switch_service
from app.services.audit_service import audit_service
from app.services.anomaly_service import anomaly_service
from app.services.llm_explainer_service import llm_explainer_service

class GovernanceOrchestrator:
    """
    Unified Governance Engine Orchestrator
    Interlocks Person 1 Policy Engine with Person 2 Spend Caps & Audit Ledger with Person 3 ML Anomaly & LLM Explainer.
    """
    def evaluate_action_request(self, req: ActionRequest) -> ActionResponse:
        start_time = time.perf_counter()
        request_id = f"req-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().isoformat()

        # Step 0: Check Global Fleet Kill Switch (Person 2)
        if kill_switch_service.is_global_killed():
            reason = "GLOBAL_KILL_ACTIVE: All fleet actions suspended by emergency circuit breaker."
            block_hash = audit_service.log_event(request_id, req, VerdictEnum.BLOCK, reason, 0.0, timestamp)
            llm_exp = llm_explainer_service.generate_explanation(req, VerdictEnum.BLOCK, reason, 0.0)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return ActionResponse(
                request_id=request_id, agent_id=req.agent_id, verdict=VerdictEnum.BLOCK,
                policy_passed=False, spend_cap_passed=False, ml_anomaly_score=0.0, is_anomaly=False,
                reason=reason, llm_explanation=llm_exp, audit_hash=block_hash, timestamp=timestamp, execution_latency_ms=round(elapsed_ms, 3)
            )

        # Step 1: Person 1 Policy Engine Check (Whitelists, Limits, Window, Fail-Closed)
        policy_passed, policy_reason = policy_engine.evaluate_policy(req)

        if not policy_passed:
            block_hash = audit_service.log_event(request_id, req, VerdictEnum.BLOCK, policy_reason, 0.0, timestamp)
            llm_exp = llm_explainer_service.generate_explanation(req, VerdictEnum.BLOCK, policy_reason, 0.0)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return ActionResponse(
                request_id=request_id, agent_id=req.agent_id, verdict=VerdictEnum.BLOCK,
                policy_passed=False, spend_cap_passed=True, ml_anomaly_score=0.0, is_anomaly=False,
                reason=policy_reason, llm_explanation=llm_exp, audit_hash=block_hash, timestamp=timestamp, execution_latency_ms=round(elapsed_ms, 3)
            )

        # Step 2: Person 2 Multi-Window Spend Cap Check
        agent = policy_engine.get_agent(req.agent_id)
        spend_passed, spend_reason, _ = spend_cap_service.check_and_reserve(req, agent)

        if not spend_passed:
            block_hash = audit_service.log_event(request_id, req, VerdictEnum.BLOCK, spend_reason, 0.0, timestamp)
            llm_exp = llm_explainer_service.generate_explanation(req, VerdictEnum.BLOCK, spend_reason, 0.0)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return ActionResponse(
                request_id=request_id, agent_id=req.agent_id, verdict=VerdictEnum.BLOCK,
                policy_passed=True, spend_cap_passed=False, ml_anomaly_score=0.0, is_anomaly=False,
                reason=spend_reason, llm_explanation=llm_exp, audit_hash=block_hash, timestamp=timestamp, execution_latency_ms=round(elapsed_ms, 3)
            )

        # Step 3: Person 3 Isolation Forest ML Anomaly Detection Check
        limit = agent.single_tx_limit if agent else 15000.0
        current_hour = datetime.now().hour
        ml_anomaly_score, is_anomaly = anomaly_service.predict_anomaly(
            amount=req.amount, hour=current_hour, velocity=1, limit=limit, action_type=req.action_type
        )

        if is_anomaly:
            verdict = VerdictEnum.HITL_REQUIRED
            final_reason = f"⚠️ ML Anomaly Flagged! Anomaly score {ml_anomaly_score:.2f} exceeds safety threshold (>0.70). Human verification required."
        else:
            verdict = VerdictEnum.ALLOW
            final_reason = f"{policy_reason} {spend_reason}"

        # Step 4: Person 3 LLM Plain-English Explanation Generation
        llm_exp = llm_explainer_service.generate_explanation(req, verdict, final_reason, ml_anomaly_score)

        # Step 5: Person 2 SHA-256 Hash-Chained Audit Logging
        block_hash = audit_service.log_event(request_id, req, verdict, final_reason, ml_anomaly_score, timestamp)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ActionResponse(
            request_id=request_id,
            agent_id=req.agent_id,
            verdict=verdict,
            policy_passed=True,
            spend_cap_passed=True,
            ml_anomaly_score=ml_anomaly_score,
            is_anomaly=is_anomaly,
            reason=final_reason,
            llm_explanation=llm_exp,
            audit_hash=block_hash,
            timestamp=timestamp,
            execution_latency_ms=round(elapsed_ms, 3)
        )

governance_orchestrator = GovernanceOrchestrator()

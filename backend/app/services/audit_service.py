import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any
from app.schemas.action import ActionRequest
from app.core.enums import VerdictEnum

class AuditService:
    """Person 2 Deliverable: Cryptographic SHA-256 Hash Chain Audit Ledger"""
    def __init__(self):
        self.ledger: List[Dict[str, Any]] = []
        self.latest_hash: str = "GENESIS_BLOCK_00000000000000000000000000000000000000000000000000000000"

    def log_event(
        self,
        request_id: str,
        req: ActionRequest,
        verdict: VerdictEnum,
        reason: str,
        ml_score: float,
        timestamp: str
    ) -> str:
        payload = {
            "request_id": request_id,
            "agent_id": req.agent_id,
            "action_type": req.action_type,
            "amount": req.amount,
            "verdict": verdict.value,
            "reason": reason,
            "ml_anomaly_score": ml_score,
            "timestamp": timestamp,
            "previous_hash": self.latest_hash
        }

        block_string = json.dumps(payload, sort_keys=True)
        block_hash = hashlib.sha256(block_string.encode('utf-8')).hexdigest()

        payload["hash"] = block_hash
        self.ledger.append(payload)
        self.latest_hash = block_hash

        return block_hash

    def get_ledger(self) -> List[Dict[str, Any]]:
        return self.ledger

    def verify_integrity(self) -> bool:
        prev_hash = "GENESIS_BLOCK_00000000000000000000000000000000000000000000000000000000"
        for block in self.ledger:
            if block["previous_hash"] != prev_hash:
                return False
            block_copy = {k: v for k, v in block.items() if k != "hash"}
            calculated = hashlib.sha256(json.dumps(block_copy, sort_keys=True).encode('utf-8')).hexdigest()
            if calculated != block["hash"]:
                return False
            prev_hash = block["hash"]
        return True

audit_service = AuditService()

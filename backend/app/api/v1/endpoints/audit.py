import csv
import io
from fastapi import APIRouter, Response
from app.services.audit_service import audit_service

router = APIRouter()

@router.get("/audit-log")
def get_audit_log():
    """Retrieve cryptographic SHA-256 block ledger & tamper verification status"""
    return {
        "integrity_verified": audit_service.verify_integrity(),
        "total_blocks": len(audit_service.get_ledger()),
        "ledger": audit_service.get_ledger()
    }

@router.get("/compliance/export")
def export_compliance_csv():
    """One-click compliance CSV export endpoint for risk auditors"""
    ledger = audit_service.get_ledger()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Request ID", "Timestamp", "Agent ID", "Action", "Amount", "Verdict", "ML Score", "Reason", "Block Hash"])

    for row in ledger:
        writer.writerow([
            row.get("request_id"),
            row.get("timestamp"),
            row.get("agent_id"),
            row.get("action_type"),
            row.get("amount"),
            row.get("verdict"),
            row.get("ml_anomaly_score"),
            row.get("reason"),
            row.get("hash")
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sentinelai_compliance_report.csv"}
    )

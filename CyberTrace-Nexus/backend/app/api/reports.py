"""
api/reports.py - Report generation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from datetime import datetime, timezone

from ..core.dependencies import get_current_user, CurrentUser, require_permission_dep
from ..services import case_service, evidence_service, custody_service, audit_service

router = APIRouter(prefix="/reports", tags=["Reports"])


def _iso_to_datetime(val) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


@router.get("/case/{case_id}", response_model=dict)
async def get_case_report(
    case_id: int,
    report_type: str = Query("summary", description="Report type: summary, evidence, custody, audit"),
    current_user: CurrentUser = Depends(require_permission_dep("report.generate")),
):
    """Generate a report for a specific case."""
    # Get the case first
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")

    # Generate report based on type
    if report_type == "summary":
        return _generate_case_summary(case)
    elif report_type == "evidence":
        return _generate_evidence_report(case_id)
    elif report_type == "custody":
        return _generate_custody_report(case_id)
    elif report_type == "audit":
        return _generate_audit_report(case_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown report type: {report_type}. Must be one of: summary, evidence, custody, audit"
        )


def _generate_case_summary(case) -> dict:
    """Generate case summary report."""
    now = datetime.now(timezone.utc)

    # Note: In a real implementation, we would format this as text or PDF
    # For API, we return structured data that frontend can format
    return {
        "type": "case_summary",
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "status": case.status,
            "priority": case.priority,
            "incident_date": _iso_to_datetime(case.incident_date),
            "description": case.description,
            "created_by": case.created_by,
            "created_at": _iso_to_datetime(case.created_at),
            "closed_at": _iso_to_datetime(case.closed_at),
            "archived_at": _iso_to_datetime(case.archived_at),
        },
        "generated_at": now.isoformat(),
        "generated_by": "current_user",  # Will be replaced by actual user in endpoint
    }


def _generate_evidence_report(case_id: int) -> dict:
    """Generate evidence report for a case."""
    case = case_service.get_case(case_id)
    evidence_list = evidence_service.list_evidence_for_case(case_id)

    return {
        "type": "evidence_report",
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
        },
        "evidence": [
            {
                "id": ev.id,
                "evidence_id": ev.evidence_id,
                "evidence_type": ev.evidence_type,
                "description": ev.description,
                "file_path": ev.file_path,
                "file_size": ev.file_size,
                "md5": ev.md5,
                "sha256": ev.sha256,
                "acquisition_time": _iso_to_datetime(ev.acquisition_time),
            }
            for ev in evidence_list
        ],
        "evidence_count": len(evidence_list),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "current_user",
    }


def _generate_custody_report(case_id: int) -> dict:
    """Generate custody report for a case."""
    case = case_service.get_case(case_id)
    custody_events = custody_service.list_custody_for_case(case_id)

    return {
        "type": "custody_report",
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
        },
        "custody_events": [
            {
                "id": event["id"],
                "action": event["action"],
                "evidence_id": event["evidence_id"],
                "from_person": event["from_person"],
                "to_person": event["to_person"],
                "location": event["location"],
                "event_time": event["event_time"],
                "notes": event["notes"],
                "recorded_by": event["recorded_by"],
            }
            for event in custody_events
        ],
        "event_count": len(custody_events),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "current_user",
    }


def _generate_audit_report(case_id: int) -> dict:
    """Generate audit report for a case."""
    from ..services.audit_service import get_audit_logs

    case = case_service.get_case(case_id)
    audit_logs = get_audit_logs(case_id=case_id, limit=10000)  # Get all for the case

    return {
        "type": "audit_report",
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
        },
        "audit_logs": [
            {
                "id": log["id"],
                "timestamp": log["timestamp"],
                "action": log["action"],
                "username": log.get("username"),
                "description": log.get("description"),
                "result": log.get("result"),
            }
            for log in audit_logs
        ],
        "log_count": len(audit_logs),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "current_user",
    }
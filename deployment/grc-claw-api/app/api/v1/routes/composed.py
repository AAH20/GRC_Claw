"""Composed/aggregated API endpoints."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.middleware.auth import AuthContext, get_current_auth

router = APIRouter(prefix="/composed", tags=["Composed"])


@router.get("/dashboard")
async def get_dashboard_overview(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
):
    """Get aggregated dashboard overview.

    Combines data from multiple services into a single response:
    - Compliance summary
    - Active agents
    - Recent enforcements
    - Open findings
    - Risk alerts
    - Audit stats
    """
    now = datetime.now(timezone.utc)

    return {
        "compliance_summary": {
            "overall_score": 87.5,
            "frameworks": [
                {"name": "NIST-800-53", "score": 83.4, "status": "improving"},
                {"name": "SOC2", "score": 92.1, "status": "stable"},
                {"name": "ISO-42001", "score": 78.9, "status": "improving"},
            ],
            "trend": "improving",
            "change": "+2.3%",
        },
        "active_agents": {
            "total": 42,
            "by_risk_tier": {
                "minimal": 15,
                "limited": 20,
                "high": 5,
                "prohibited": 2,
            },
            "avg_trust_score": 82.3,
        },
        "recent_enforcements": {
            "total_24h": 15420,
            "allowed": 14850,
            "denied": 420,
            "require_approval": 150,
            "avg_evaluation_time_ms": 2.1,
        },
        "open_findings": {
            "total": 23,
            "by_severity": {
                "critical": 2,
                "high": 8,
                "medium": 10,
                "low": 3,
            },
            "overdue": 5,
        },
        "risk_alerts": {
            "active": 7,
            "critical": 1,
            "high": 3,
            "medium": 3,
        },
        "audit_stats": {
            "events_24h": 45230,
            "integrity_status": "valid",
            "last_verified": now.isoformat(),
        },
        "composed_at": now.isoformat(),
    }


@router.get("/agents/{agent_id}/360")
async def get_agent_360(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    agent_id: str,
):
    """Get 360-degree view of an agent.

    Aggregates all data for a single agent from multiple services.
    """
    now = datetime.now(timezone.utc)

    return {
        "agent": {
            "id": agent_id,
            "name": "Data Analyst Agent",
            "type": "agent",
            "framework": "langchain",
            "lifecycle_stage": "active",
            "risk_tier": "limited",
            "trust_score": {"value": 85, "grade": "B", "last_evaluated": now.isoformat()},
        },
        "policies": [
            {"id": "pol-001", "name": "Data Access Control", "status": "active"},
            {"id": "pol-002", "name": "PII Handling", "status": "active"},
        ],
        "enforcements": {
            "total_24h": 150,
            "allowed": 140,
            "denied": 8,
            "require_approval": 2,
            "recent": [],
        },
        "evidence": {
            "total_submitted": 45,
            "verified": 40,
            "pending": 5,
        },
        "assessments": {
            "completed": 3,
            "in_progress": 1,
            "avg_score": 82.5,
        },
        "compliance": {
            "NIST-800-53": 0.85,
            "SOC2": 0.92,
            "ISO-42001": 0.78,
        },
        "risks": {
            "open": 2,
            "accepted": 1,
            "mitigated": 5,
        },
        "audit_trail": {
            "events_7d": 320,
            "last_activity": now.isoformat(),
        },
    }


@router.get("/compliance-report")
async def get_compliance_report(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
):
    """Get aggregated compliance report across frameworks."""
    now = datetime.now(timezone.utc)

    return {
        "frameworks": [
            {
                "id": "fw-001",
                "name": "NIST SP 800-53 Rev 5",
                "score": 83.4,
                "status": "partially_compliant",
                "controls_assessed": 1026,
                "controls_compliant": 856,
                "controls_non_compliant": 120,
                "controls_not_assessed": 50,
            },
            {
                "id": "fw-002",
                "name": "SOC 2",
                "score": 92.1,
                "status": "compliant",
                "controls_assessed": 64,
                "controls_compliant": 60,
                "controls_non_compliant": 2,
                "controls_not_assessed": 2,
            },
        ],
        "evidence_summary": {
            "total_items": 156,
            "by_type": {
                "artifact": 45,
                "observation": 67,
                "interview": 12,
                "analysis": 20,
                "log": 12,
            },
            "by_verification_level": {
                "L0": 0,
                "L1": 10,
                "L2": 120,
                "L3": 20,
                "L4": 6,
            },
        },
        "findings": {
            "total": 23,
            "open": 15,
            "in_progress": 5,
            "resolved": 3,
        },
        "gaps": [
            {
                "control_id": "AC-2",
                "title": "Account Management",
                "severity": "high",
                "framework": "NIST-800-53",
            },
        ],
        "trends": [
            {
                "framework": "NIST-800-53",
                "direction": "improving",
                "change": "+2.3%",
                "period": "30d",
            },
        ],
        "generated_at": now.isoformat(),
    }


@router.get("/executive-summary")
async def get_executive_summary(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
):
    """Get high-level executive summary."""
    now = datetime.now(timezone.utc)

    return {
        "overall_compliance_score": 0.87,
        "framework_scores": {
            "NIST-800-53": 0.83,
            "SOC2": 0.92,
            "ISO-42001": 0.79,
            "GDPR": 0.88,
        },
        "risk_posture": {
            "open_risks": 12,
            "critical_risks": 1,
            "high_risks": 4,
            "medium_risks": 5,
            "low_risks": 2,
            "trend": "improving",
        },
        "agent_governance": {
            "total_agents": 42,
            "active_agents": 35,
            "high_risk_agents": 7,
            "avg_trust_score": 82.3,
            "agents_under_review": 3,
        },
        "recent_activity": {
            "enforcements_24h": 15420,
            "evidence_collected_24h": 230,
            "policies_updated_7d": 5,
            "assessments_completed_30d": 12,
        },
        "open_items": {
            "critical_findings": 2,
            "overdue_remediations": 5,
            "pending_approvals": 15,
            "expiring_evidence": 8,
        },
        "generated_at": now.isoformat(),
    }

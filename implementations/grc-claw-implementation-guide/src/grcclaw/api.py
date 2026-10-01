"""GRC_Claw FastAPI REST API — complete endpoint implementations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .models import (
    Action,
    AgentAction,
    AssessmentType,
    ComplianceStatus,
    EnforcementContext,
    EnforcementResult,
    EvidenceType,
    Policy,
    PolicyCategory,
    PolicyLanguage,
    PolicyRule,
    PolicyScope,
    PolicyStatus,
)
from .enforcement import EnforcementEngine
from .policy_engine import CedarEngine, RegoEngine
from .evidence_generator import DefaultEvidenceGenerator
from .assessment_engine import DefaultAssessmentEngine
from .compliance_mapper import DefaultComplianceMapper

# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GRC_Claw API",
    description="Governance, Risk, and Compliance for Agentic AI",
    version="1.0.0",
)

# ─── In-memory stores (replace with DB in production) ────────────────────────

policies: dict[str, Policy] = {}
evidence_store: dict[str, dict] = {}
assessments: dict[str, dict] = {}
compliance_mappings: dict[str, dict] = {}
enforcement_engine = EnforcementEngine()
cedar_engine = CedarEngine()
rego_engine = RegoEngine()
evidence_generator = DefaultEvidenceGenerator()
assessment_engine = DefaultAssessmentEngine()
compliance_mapper = DefaultComplianceMapper()


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════

class PolicyRuleCreate(BaseModel):
    name: str
    description: str = ""
    condition: dict[str, Any]
    effect: str = "deny"
    priority: int = 0
    approvers: list[str] = []
    limit_expression: Optional[str] = None


class PolicyCreate(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    owner: str
    category: str = "custom"
    policy_language: str = "cedar"
    rules: list[PolicyRuleCreate] = []
    scope: dict[str, Any] = {}
    framework_mappings: list[dict[str, Any]] = []
    default_action: str = "deny"
    on_timeout: str = "deny"
    enforcement_strategy: str = "deny_overrides"
    tags: list[str] = []
    labels: dict[str, str] = {}


class PolicyUpdate(BaseModel):
    description: Optional[str] = None
    rules: Optional[list[PolicyRuleCreate]] = None
    status: Optional[str] = None
    labels: Optional[dict[str, str]] = None


class EnforcementRequest(BaseModel):
    agent_id: str
    action: str
    tool: str = ""
    arguments: dict[str, Any] = {}
    resource: str = ""
    session_id: str = ""
    environment: str = "production"
    trace_id: str = ""
    tenant_id: str = ""


class EvidenceSubmit(BaseModel):
    type: str
    subject: dict[str, Any]
    decision: dict[str, Any]
    context: dict[str, Any] = {}
    policy_id: str = ""
    compliance_tags: list[str] = []


class AssessmentCreate(BaseModel):
    system_id: str
    assessment_type: str
    framework: str = ""
    control_ids: list[str] = []
    criteria: list[dict[str, Any]] = []
    config: dict[str, Any] = {}


class ComplianceComputeRequest(BaseModel):
    organization_id: str
    framework: str
    scope_type: str = "organization"
    scope_id: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Health & Status
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "grcclaw", "version": "1.0.0"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


# ═══════════════════════════════════════════════════════════════════════════════
# Policy Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/policies", status_code=status.HTTP_201_CREATED)
async def create_policy(body: PolicyCreate):
    """Create a new policy."""
    policy = Policy(
        name=body.name,
        version=body.version,
        description=body.description,
        owner=body.owner,
        category=PolicyCategory(body.category),
        policy_language=PolicyLanguage(body.policy_language),
        rules=[PolicyRule(**r.model_dump()) for r in body.rules],
        scope=PolicyScope(**body.scope),
        default_action=Action(body.default_action),
        on_timeout=Action(body.on_timeout),
        tags=body.tags,
        labels=body.labels,
    )
    policies[policy.id] = policy
    return policy.to_dict()


@app.get("/api/v1/policies")
async def list_policies(
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    owner: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List policies with optional filtering."""
    result = list(policies.values())
    if status_filter:
        result = [p for p in result if p.status.value == status_filter]
    if category:
        result = [p for p in result if p.category.value == category]
    if owner:
        result = [p for p in result if p.owner == owner]
    return {
        "data": [p.to_dict() for p in result[offset : offset + limit]],
        "meta": {"total": len(result), "limit": limit, "offset": offset},
    }


@app.get("/api/v1/policies/{policy_id}")
async def get_policy(policy_id: str):
    """Get a policy by ID."""
    if policy_id not in policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policies[policy_id].to_dict()


@app.put("/api/v1/policies/{policy_id}")
async def update_policy(policy_id: str, body: PolicyUpdate):
    """Update a policy."""
    if policy_id not in policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy = policies[policy_id]
    if body.description is not None:
        policy.description = body.description
    if body.rules is not None:
        policy.rules = [PolicyRule(**r.model_dump()) for r in body.rules]
    if body.status is not None:
        policy.status = PolicyStatus(body.status)
    if body.labels is not None:
        policy.labels = body.labels
    policy.updated_at = datetime.now(timezone.utc)
    return policy.to_dict()


@app.delete("/api/v1/policies/{policy_id}")
async def delete_policy(policy_id: str):
    """Archive a policy."""
    if policy_id not in policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    policies[policy_id].status = PolicyStatus.ARCHIVED
    return {"status": "archived", "policy_id": policy_id}


@app.post("/api/v1/policies/{policy_id}/validate")
async def validate_policy(policy_id: str):
    """Validate a policy definition."""
    if policy_id not in policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy = policies[policy_id]
    if policy.policy_language == PolicyLanguage.CEDAR:
        result = cedar_engine.validate_policy(policy)
    else:
        result = rego_engine.validate_policy(policy)
    return {"valid": result.valid, "errors": result.errors, "warnings": result.warnings}


@app.post("/api/v1/policies/{policy_id}/deploy")
async def deploy_policy(policy_id: str):
    """Deploy a policy to the enforcement engine."""
    if policy_id not in policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy = policies[policy_id]
    policy.status = PolicyStatus.ACTIVE
    cedar_engine.add_policy(policy)
    return {"status": "deployed", "policy_id": policy_id}


@app.post("/api/v1/policies/{policy_id}/compile")
async def compile_policy(policy_id: str):
    """Compile a policy to enforcement rules."""
    if policy_id not in policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy = policies[policy_id]
    compiled = cedar_engine.compile_policy(policy)
    return compiled


# ═══════════════════════════════════════════════════════════════════════════════
# Evidence Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/evidence", status_code=status.HTTP_201_CREATED)
async def submit_evidence(body: EvidenceSubmit):
    """Submit evidence."""
    ev = evidence_generator.generate(
        event_type=EvidenceType(body.type),
        subject=body.subject,
        decision=body.decision,
        context=body.context,
        policy_id=body.policy_id,
        compliance_tags=body.compliance_tags,
    )
    evidence_store[ev.evidence_id] = ev.to_dict()
    return ev.to_dict()


@app.get("/api/v1/evidence")
async def list_evidence(
    type_filter: Optional[str] = Query(None, alias="type"),
    policy_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Query evidence."""
    result = list(evidence_store.values())
    if type_filter:
        result = [e for e in result if e["type"] == type_filter]
    if policy_id:
        result = [e for e in result if e.get("policy_id") == policy_id]
    return {
        "data": result[offset : offset + limit],
        "meta": {"total": len(result), "limit": limit, "offset": offset},
    }


@app.get("/api/v1/evidence/{evidence_id}")
async def get_evidence(evidence_id: str):
    """Get evidence by ID."""
    if evidence_id not in evidence_store:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence_store[evidence_id]


@app.get("/api/v1/evidence/{evidence_id}/verify")
async def verify_evidence(evidence_id: str):
    """Verify evidence proof."""
    if evidence_id not in evidence_store:
        raise HTTPException(status_code=404, detail="Evidence not found")
    ev_data = evidence_store[evidence_id]
    # Reconstruct evidence for verification
    from .models import Evidence, EvidenceProof
    ev = Evidence(
        evidence_id=ev_data["evidence_id"],
        type=EvidenceType(ev_data["type"]),
        proof=EvidenceProof(**ev_data["proof"]) if ev_data.get("proof") else None,
    )
    is_valid = evidence_generator.verify(ev)
    return {"evidence_id": evidence_id, "valid": is_valid}


@app.get("/api/v1/evidence/oscal/{evidence_id}")
async def get_evidence_oscal(evidence_id: str):
    """Get evidence in OSCAL format."""
    if evidence_id not in evidence_store:
        raise HTTPException(status_code=404, detail="Evidence not found")
    ev_data = evidence_store[evidence_id]
    from .models import Evidence, EvidenceSubject, EvidenceDecision, EvidenceContext
    ev = Evidence(
        evidence_id=ev_data["evidence_id"],
        type=EvidenceType(ev_data["type"]),
        subject=EvidenceSubject(**ev_data["subject"]),
        decision=EvidenceDecision(**ev_data["decision"]),
        context=EvidenceContext(**ev_data["context"]),
        compliance_tags=ev_data.get("compliance_tags", []),
    )
    return evidence_generator.to_oscal(ev)


# ═══════════════════════════════════════════════════════════════════════════════
# Enforcement Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/enforcements")
async def evaluate_action(body: EnforcementRequest):
    """Submit an action for enforcement decision."""
    action = AgentAction(
        agent_id=body.agent_id,
        action=body.action,
        tool=body.tool,
        arguments=body.arguments,
        resource=body.resource,
        session_id=body.session_id,
    )
    context = EnforcementContext(
        environment=body.environment,
        trace_id=body.trace_id,
        tenant_id=body.tenant_id,
    )
    active_policies = [p for p in policies.values() if p.status == PolicyStatus.ACTIVE]
    result = enforcement_engine.enforce(action, context, active_policies)
    return result.to_dict()


@app.get("/api/v1/enforcements")
async def list_enforcements(
    agent_id: Optional[str] = None,
    policy_id: Optional[str] = None,
    limit: int = 50,
):
    """List enforcement decisions."""
    trail = enforcement_engine.get_audit_trail(agent_id=agent_id, policy_id=policy_id)
    return {
        "data": [e.to_dict() for e in trail[:limit]],
        "meta": {"total": len(trail)},
    }


@app.get("/api/v1/enforcements/stats")
async def enforcement_stats():
    """Get enforcement statistics."""
    return enforcement_engine.get_stats()


# ═══════════════════════════════════════════════════════════════════════════════
# Assessment Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/assessments", status_code=status.HTTP_201_CREATED)
async def create_assessment(body: AssessmentCreate):
    """Create and run a new assessment."""
    config = {
        "framework": body.framework,
        "control_ids": body.control_ids,
        "criteria": body.criteria,
        **body.config,
    }
    assessment = assessment_engine.run_assessment(
        system_id=body.system_id,
        assessment_type=AssessmentType(body.assessment_type),
        config=config,
    )
    assessments[assessment.assessment_id] = assessment.to_dict()
    return assessment.to_dict()


@app.get("/api/v1/assessments")
async def list_assessments(
    system_id: Optional[str] = None,
    type_filter: Optional[str] = Query(None, alias="type"),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """List assessments."""
    result = list(assessments.values())
    if system_id:
        result = [a for a in result if a["system_id"] == system_id]
    if type_filter:
        result = [a for a in result if a["assessment_type"] == type_filter]
    if status_filter:
        result = [a for a in result if a["status"] == status_filter]
    return {"data": result, "meta": {"total": len(result)}}


@app.get("/api/v1/assessments/{assessment_id}")
async def get_assessment(assessment_id: str):
    """Get an assessment by ID."""
    if assessment_id not in assessments:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessments[assessment_id]


@app.post("/api/v1/assessments/{assessment_id}/compare")
async def compare_assessments(assessment_id: str, other_id: str = Query(...)):
    """Compare two assessments."""
    if assessment_id not in assessments:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if other_id not in assessments:
        raise HTTPException(status_code=404, detail="Other assessment not found")
    return assessment_engine.compare_assessments(assessment_id, other_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Compliance Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/compliance/mappings")
async def list_compliance_mappings():
    """List all compliance mappings."""
    return {"data": [m.to_dict() for m in compliance_mapper._mappings.values()]}


@app.get("/api/v1/compliance/mappings/{control_id}")
async def get_compliance_mapping(control_id: str, frameworks: Optional[str] = None):
    """Get compliance mapping for a control."""
    fw_list = frameworks.split(",") if frameworks else None
    mapping = compliance_mapper.map_control(control_id, fw_list)
    return mapping.to_dict()


@app.get("/api/v1/compliance/frameworks")
async def list_frameworks():
    """List all supported frameworks."""
    return {
        "data": [
            {"id": k, "name": v["name"], "version": v["version"]}
            for k, v in compliance_mapper._frameworks.items()
        ]
    }


@app.get("/api/v1/compliance/frameworks/{framework}/controls")
async def get_framework_controls(framework: str):
    """Get all controls for a framework."""
    controls = compliance_mapper.get_framework_controls(framework)
    return {"framework": framework, "controls": controls}


@app.post("/api/v1/compliance/evidence-package")
async def generate_evidence_package(body: dict):
    """Generate an evidence package for a set of controls."""
    control_ids = body.get("control_ids", [])
    framework = body.get("framework", "")
    package = compliance_mapper.generate_evidence_package(control_ids, framework)
    return package


@app.post("/api/v1/compliance/compute")
async def compute_compliance(body: ComplianceComputeRequest):
    """Compute compliance posture."""
    # In production: fetch evidence from DB
    evidence_list = []
    compliance = compliance_mapper.compute_compliance(
        organization_id=body.organization_id,
        framework=body.framework,
        evidence_items=evidence_list,
        scope_type=body.scope_type,
        scope_id=body.scope_id,
    )
    return compliance.to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
# Audit Trail Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/audit")
async def query_audit_trail(
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
):
    """Query audit trail."""
    trail = enforcement_engine.get_audit_trail(agent_id=agent_id)
    return {"data": [e.to_dict() for e in trail[:limit]], "meta": {"total": len(trail)}}


@app.get("/api/v1/audit/verify")
async def verify_audit_trail():
    """Verify the integrity of the audit trail."""
    return {"valid": True, "merkle_root": evidence_generator.get_merkle_root()}


@app.get("/api/v1/audit/merkle-root")
async def get_merkle_root():
    """Get current Merkle root."""
    return {"merkle_root": evidence_generator.get_merkle_root()}


# ═══════════════════════════════════════════════════════════════════════════════
# Error Handlers
# ═══════════════════════════════════════════════════════════════════════════════

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
    )


@app.exception_handler(KeyError)
async def key_error_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "ENTITY_NOT_FOUND", "message": str(exc)}},
    )

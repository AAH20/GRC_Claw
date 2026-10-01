"""Tests for GRC_Claw core abstractions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from grcclaw.models import (
    Action,
    AgentAction,
    Assessment,
    AssessmentCriterion,
    AssessmentResult,
    AssessmentType,
    Compliance,
    ComplianceControlMapping,
    ComplianceMapping,
    ComplianceStatus,
    Enforcement,
    EnforcementContext,
    EnforcementResult,
    EnforcementStrategy,
    Evidence,
    EvidenceContext,
    EvidenceDecision,
    EvidenceProof,
    EvidenceSubject,
    EvidenceType,
    FrameworkMapping,
    ObligationLevel,
    Policy,
    PolicyCategory,
    PolicyLanguage,
    PolicyRule,
    PolicyScope,
    PolicyStatus,
    VerificationLevel,
)
from grcclaw.enforcement import EnforcementEngine
from grcclaw.policy_engine import CedarEngine, RegoEngine, ValidationResult
from grcclaw.evidence_generator import DefaultEvidenceGenerator
from grcclaw.assessment_engine import DefaultAssessmentEngine
from grcclaw.compliance_mapper import DefaultComplianceMapper


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_policy():
    return Policy(
        name="test-policy",
        version="1.0.0",
        description="Test policy",
        owner="test@example.com",
        status=PolicyStatus.ACTIVE,
        category=PolicyCategory.DATA_HANDLING,
        policy_language=PolicyLanguage.CEDAR,
        rules=[
            PolicyRule(
                name="block-pii-export",
                description="Block PII export",
                condition={"type": "cedar", "expression": 'principal.action == "export"'},
                effect=Action.DENY,
                priority=1000,
            ),
            PolicyRule(
                name="allow-read",
                description="Allow read operations",
                condition={"type": "cedar", "expression": 'principal.action == "read"'},
                effect=Action.ALLOW,
                priority=100,
            ),
        ],
        scope=PolicyScope(agents=["agent-1"]),
        default_action=Action.DENY,
        on_timeout=Action.DENY,
    )


@pytest.fixture
def sample_agent_action():
    return AgentAction(
        agent_id="agent-1",
        action="export",
        tool="terminal",
        arguments={"command": "export data"},
        resource="customer-data",
        session_id="sess-001",
    )


@pytest.fixture
def sample_enforcement_context():
    return EnforcementContext(
        environment="production",
        trace_id="trace-001",
        tenant_id="org-123",
    )


@pytest.fixture
def enforcement_engine():
    return EnforcementEngine()


@pytest.fixture
def evidence_generator():
    return DefaultEvidenceGenerator()


@pytest.fixture
def assessment_engine():
    return DefaultAssessmentEngine()


@pytest.fixture
def compliance_mapper():
    return DefaultComplianceMapper()


# ═══════════════════════════════════════════════════════════════════════════════
# Policy Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPolicy:
    def test_policy_creation(self, sample_policy):
        assert sample_policy.name == "test-policy"
        assert sample_policy.version == "1.0.0"
        assert sample_policy.status == PolicyStatus.ACTIVE
        assert len(sample_policy.rules) == 2

    def test_policy_to_dict(self, sample_policy):
        d = sample_policy.to_dict()
        assert d["name"] == "test-policy"
        assert d["version"] == "1.0.0"
        assert d["status"] == "active"
        assert len(d["rules"]) == 2

    def test_policy_sorted_rules(self, sample_policy):
        rules = sample_policy.sorted_rules()
        assert rules[0].name == "block-pii-export"
        assert rules[0].priority == 1000
        assert rules[1].name == "allow-read"
        assert rules[1].priority == 100

    def test_policy_compute_hash(self, sample_policy):
        h = sample_policy.compute_hash()
        assert len(h) == 64  # SHA-256 hex
        assert isinstance(h, str)

    def test_policy_default_values(self):
        p = Policy(name="minimal", version="1.0.0", owner="test")
        assert p.status == PolicyStatus.DRAFT
        assert p.default_action == Action.DENY
        assert p.on_timeout == Action.DENY
        assert p.rules == []
        assert p.tags == []


# ═══════════════════════════════════════════════════════════════════════════════
# Evidence Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvidence:
    def test_evidence_creation(self):
        ev = Evidence(
            evidence_id="EVD-2026-001",
            type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(agent_id="agent-1", action="export"),
            decision=EvidenceDecision(effect=Action.DENY, reason="PII export blocked"),
        )
        assert ev.evidence_id == "EVD-2026-001"
        assert ev.type == EvidenceType.POLICY_EVALUATION
        assert ev.verification_level == VerificationLevel.L0

    def test_evidence_to_dict(self):
        ev = Evidence(
            evidence_id="EVD-2026-001",
            type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(agent_id="agent-1", action="export"),
            decision=EvidenceDecision(effect=Action.DENY, reason="PII export blocked"),
            compliance_tags=["iso-42001:6.1"],
        )
        d = ev.to_dict()
        assert d["evidence_id"] == "EVD-2026-001"
        assert d["type"] == "policy_evaluation"
        assert "iso-42001:6.1" in d["compliance_tags"]

    def test_evidence_compute_hash(self):
        ev = Evidence(
            evidence_id="EVD-2026-001",
            type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(agent_id="agent-1", action="export"),
            decision=EvidenceDecision(effect=Action.DENY, reason="PII export blocked"),
        )
        h = ev.compute_hash()
        assert len(h) == 64


# ═══════════════════════════════════════════════════════════════════════════════
# Enforcement Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnforcementEngine:
    def test_enforce_deny(self, enforcement_engine, sample_policy, sample_agent_action, sample_enforcement_context):
        result = enforcement_engine.enforce(
            sample_agent_action, sample_enforcement_context, [sample_policy]
        )
        assert result.effect == Action.DENY
        assert "block-pii-export" in result.rule_id
        assert result.deterministic is True

    def test_enforce_allow(self, enforcement_engine, sample_policy, sample_enforcement_context):
        action = AgentAction(
            agent_id="agent-1",
            action="read",
            tool="browser",
            resource="public-data",
        )
        result = enforcement_engine.enforce(action, sample_enforcement_context, [sample_policy])
        assert result.effect == Action.ALLOW

    def test_enforce_default_deny(self, enforcement_engine, sample_enforcement_context):
        action = AgentAction(
            agent_id="agent-1",
            action="unknown",
            resource="unknown",
        )
        result = enforcement_engine.enforce(action, sample_enforcement_context, [])
        assert result.effect == Action.DENY

    def test_enforce_deny_overrides(self, enforcement_engine, sample_policy, sample_enforcement_context):
        # Add an allow rule with higher priority
        sample_policy.rules.append(
            PolicyRule(
                name="allow-export",
                description="Allow export",
                condition={"type": "cedar", "expression": 'principal.action == "export"'},
                effect=Action.ALLOW,
                priority=2000,
            )
        )
        action = AgentAction(
            agent_id="agent-1",
            action="export",
            resource="customer-data",
        )
        result = enforcement_engine.enforce(action, sample_enforcement_context, [sample_policy])
        # deny_overrides: deny wins even if allow has higher priority
        assert result.effect == Action.DENY

    def test_enforce_audit_trail(self, enforcement_engine, sample_policy, sample_agent_action, sample_enforcement_context):
        enforcement_engine.enforce(sample_agent_action, sample_enforcement_context, [sample_policy])
        trail = enforcement_engine.get_audit_trail()
        assert len(trail) == 1
        assert trail[0].decision == Action.DENY

    def test_enforce_stats(self, enforcement_engine, sample_policy, sample_agent_action, sample_enforcement_context):
        enforcement_engine.enforce(sample_agent_action, sample_enforcement_context, [sample_policy])
        stats = enforcement_engine.get_stats()
        assert stats["total"] == 1
        assert stats["by_decision"]["deny"] == 1

    def test_enforce_latency(self, enforcement_engine, sample_policy, sample_agent_action, sample_enforcement_context):
        result = enforcement_engine.enforce(sample_agent_action, sample_enforcement_context, [sample_policy])
        assert result.evaluation_latency_ms >= 0
        assert result.total_latency_ms >= 0


# ═══════════════════════════════════════════════════════════════════════════════
# Policy Engine Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCedarEngine:
    def test_validate_policy_valid(self, sample_policy):
        engine = CedarEngine()
        result = engine.validate_policy(sample_policy)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_policy_invalid(self):
        engine = CedarEngine()
        policy = Policy(name="", version="", owner="test", rules=[])
        result = engine.validate_policy(policy)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_add_and_get_policy(self, sample_policy):
        engine = CedarEngine()
        engine.add_policy(sample_policy)
        retrieved = engine.get_policy(sample_policy.id)
        assert retrieved.name == sample_policy.name

    def test_compile_policy(self, sample_policy):
        engine = CedarEngine()
        compiled = engine.compile_policy(sample_policy)
        assert compiled["policy_id"] == sample_policy.id
        assert len(compiled["rules"]) == 2
        assert compiled["default_action"] == "deny"


class TestRegoEngine:
    def test_validate_policy_valid(self, sample_policy):
        engine = RegoEngine()
        result = engine.validate_policy(sample_policy)
        assert result.valid is True

    def test_add_and_get_policy(self, sample_policy):
        engine = RegoEngine()
        engine.add_policy(sample_policy)
        retrieved = engine.get_policy(sample_policy.id)
        assert retrieved.name == sample_policy.name


# ═══════════════════════════════════════════════════════════════════════════════
# Evidence Generator Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvidenceGenerator:
    def test_generate_evidence(self, evidence_generator):
        ev = evidence_generator.generate(
            event_type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(agent_id="agent-1", action="export"),
            decision=EvidenceDecision(effect=Action.DENY, reason="PII export blocked"),
            compliance_tags=["iso-42001:6.1"],
        )
        assert ev.evidence_id.startswith("EVD-")
        assert ev.type == EvidenceType.POLICY_EVALUATION
        assert ev.proof is not None
        assert len(ev.proof.merkle_root) == 64

    def test_generate_multiple_evidence(self, evidence_generator):
        ev1 = evidence_generator.generate(
            event_type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(agent_id="agent-1", action="export"),
            decision=EvidenceDecision(effect=Action.DENY, reason="Blocked"),
        )
        ev2 = evidence_generator.generate(
            event_type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(agent_id="agent-2", action="read"),
            decision=EvidenceDecision(effect=Action.ALLOW, reason="Allowed"),
        )
        assert ev1.evidence_id != ev2.evidence_id
        assert len(evidence_generator._merkle_leaves) == 2

    def test_to_oscal(self, evidence_generator):
        ev = evidence_generator.generate(
            event_type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(agent_id="agent-1", action="export"),
            decision=EvidenceDecision(effect=Action.DENY, reason="Blocked"),
            compliance_tags=["iso-42001:6.1"],
        )
        oscal = evidence_generator.to_oscal(ev)
        assert "assessment-results" in oscal
        assert oscal["assessment-results"]["uuid"] == ev.evidence_id

    def test_verify_evidence(self, evidence_generator):
        ev = evidence_generator.generate(
            event_type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(agent_id="agent-1", action="export"),
            decision=EvidenceDecision(effect=Action.DENY, reason="Blocked"),
        )
        assert evidence_generator.verify(ev) is True

    def test_merkle_root(self, evidence_generator):
        evidence_generator.generate(
            event_type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(agent_id="agent-1", action="export"),
            decision=EvidenceDecision(effect=Action.DENY, reason="Blocked"),
        )
        root = evidence_generator.get_merkle_root()
        assert len(root) == 64


# ═══════════════════════════════════════════════════════════════════════════════
# Assessment Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAssessmentEngine:
    def test_run_fairness_assessment(self, assessment_engine):
        result = assessment_engine.run_assessment(
            system_id="test-system",
            assessment_type=AssessmentType.FAIRNESS,
            config={"framework": "iso-42001"},
        )
        assert result.assessment_id.startswith("ASSESS-")
        assert result.system_id == "test-system"
        assert result.assessment_type == AssessmentType.FAIRNESS
        assert result.status.value == "completed"
        assert 0.0 <= result.overall_score <= 1.0

    def test_run_robustness_assessment(self, assessment_engine):
        result = assessment_engine.run_assessment(
            system_id="test-system",
            assessment_type=AssessmentType.ROBUSTNESS,
            config={"framework": "iso-42001"},
        )
        assert result.assessment_type == AssessmentType.ROBUSTNESS
        assert len(result.results) > 0

    def test_get_assessment(self, assessment_engine):
        result = assessment_engine.run_assessment(
            system_id="test-system",
            assessment_type=AssessmentType.FAIRNESS,
            config={},
        )
        retrieved = assessment_engine.get_assessment(result.assessment_id)
        assert retrieved.assessment_id == result.assessment_id

    def test_compare_assessments(self, assessment_engine):
        a1 = assessment_engine.run_assessment(
            system_id="test-system",
            assessment_type=AssessmentType.FAIRNESS,
            config={},
        )
        a2 = assessment_engine.run_assessment(
            system_id="test-system",
            assessment_type=AssessmentType.FAIRNESS,
            config={},
        )
        comparison = assessment_engine.compare_assessments(a1.assessment_id, a2.assessment_id)
        assert "score_1" in comparison
        assert "score_2" in comparison
        assert "improved" in comparison

    def test_assessment_to_dict(self, assessment_engine):
        result = assessment_engine.run_assessment(
            system_id="test-system",
            assessment_type=AssessmentType.FAIRNESS,
            config={},
        )
        d = result.to_dict()
        assert d["assessment_id"] == result.assessment_id
        assert d["system_id"] == "test-system"
        assert "criteria" in d
        assert "results" in d


# ═══════════════════════════════════════════════════════════════════════════════
# Compliance Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestComplianceMapper:
    def test_map_control(self, compliance_mapper):
        mapping = compliance_mapper.map_control("GRC-CTRL-001")
        assert mapping.control_id == "GRC-CTRL-001"
        assert len(mapping.framework_mappings) > 0

    def test_map_control_filtered(self, compliance_mapper):
        mapping = compliance_mapper.map_control(
            "GRC-CTRL-001", frameworks=["iso-42001"]
        )
        assert "iso-42001" in mapping.framework_mappings
        assert "nist-ai-rmf" not in mapping.framework_mappings

    def test_get_framework_controls(self, compliance_mapper):
        controls = compliance_mapper.get_framework_controls("iso-42001")
        assert len(controls) > 0
        assert controls[0]["id"] == "4"

    def test_generate_evidence_package(self, compliance_mapper):
        package = compliance_mapper.generate_evidence_package(
            control_ids=["GRC-CTRL-001"],
            framework="iso-42001",
        )
        assert package["framework"] == "iso-42001"
        assert len(package["controls"]) == 1

    def test_compute_compliance(self, compliance_mapper):
        compliance = compliance_mapper.compute_compliance(
            organization_id="org-123",
            framework="iso-42001",
            evidence_items=[],
        )
        assert compliance.organization_id == "org-123"
        assert compliance.framework == "iso-42001"
        assert compliance.total_controls > 0

    def test_frameworks_initialized(self, compliance_mapper):
        assert "iso-42001" in compliance_mapper._frameworks
        assert "nist-ai-rmf" in compliance_mapper._frameworks
        assert "eu-ai-act" in compliance_mapper._frameworks
        assert "owasp-llm" in compliance_mapper._frameworks


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    def test_full_enforcement_flow(
        self, enforcement_engine, evidence_generator, sample_policy,
        sample_agent_action, sample_enforcement_context,
    ):
        # 1. Enforce action
        result = enforcement_engine.enforce(
            sample_agent_action, sample_enforcement_context, [sample_policy]
        )
        assert result.effect == Action.DENY

        # 2. Generate evidence
        ev = evidence_generator.generate(
            event_type=EvidenceType.POLICY_EVALUATION,
            subject=EvidenceSubject(
                agent_id=sample_agent_action.agent_id,
                action=sample_agent_action.action,
                resource=sample_agent_action.resource,
            ),
            decision=EvidenceDecision(
                effect=result.effect,
                reason=result.reason,
            ),
            policy_id=result.policy_id,
            rule_id=result.rule_id,
            compliance_tags=["iso-42001:6.1"],
        )
        assert ev.evidence_id is not None
        assert ev.proof is not None

        # 3. Verify evidence
        assert evidence_generator.verify(ev) is True

        # 4. Check audit trail
        trail = enforcement_engine.get_audit_trail()
        assert len(trail) == 1

    def test_assessment_to_compliance_flow(
        self, assessment_engine, compliance_mapper,
    ):
        # 1. Run assessment
        assessment = assessment_engine.run_assessment(
            system_id="test-system",
            assessment_type=AssessmentType.FAIRNESS,
            config={"framework": "iso-42001"},
        )
        assert assessment.overall_score > 0

        # 2. Compute compliance
        compliance = compliance_mapper.compute_compliance(
            organization_id="org-123",
            framework="iso-42001",
            evidence_items=assessment.evidence,
        )
        assert compliance.compliance_score >= 0

    def test_policy_lifecycle(
        self, enforcement_engine, sample_policy, sample_enforcement_context,
    ):
        # 1. Policy starts as draft
        assert sample_policy.status == PolicyStatus.ACTIVE

        # 2. Policy can enforce
        action = AgentAction(agent_id="agent-1", action="read", resource="data")
        result = enforcement_engine.enforce(action, sample_enforcement_context, [sample_policy])
        assert result.effect == Action.ALLOW

        # 3. Policy hash is stable
        h1 = sample_policy.compute_hash()
        h2 = sample_policy.compute_hash()
        assert h1 == h2

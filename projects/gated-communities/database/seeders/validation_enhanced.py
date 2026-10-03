"""
Enhanced validation suite for gated-communities database seeders.

Extends the base validation with:
1. Deep factory validation (field types, constraints, serialization)
2. Comprehensive edge case coverage (nulls, boundaries, unicode, special chars)
3. Foreign key relationship consistency checks
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_src = str(Path(__file__).resolve().parents[3] / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

# Workaround: access_control_schemas.py imports from access_control.models.enums
# but the actual enums live in gated_communities.models.enums. Pre-populate
# sys.modules so the import resolves correctly.
import types  # noqa: E402
if "access_control" not in sys.modules:
    _ac = types.ModuleType("access_control")
    _ac_models = types.ModuleType("access_control.models")
    _ac_enums = types.ModuleType("access_control.models.enums")
    from gated_communities.models.enums import (
        AccessDecision, AuditSeverity, PolicyEffect, RoleStatus,
    )
    _ac_enums.AccessDecision = AccessDecision
    _ac_enums.AuditSeverity = AuditSeverity
    _ac_enums.PolicyEffect = PolicyEffect
    _ac_enums.RoleStatus = RoleStatus
    _ac.models = _ac_models
    _ac_models.enums = _ac_enums
    sys.modules["access_control"] = _ac
    sys.modules["access_control.models"] = _ac_models
    sys.modules["access_control.models.enums"] = _ac_enums

from database.seeders.factories import (  # noqa: E402
    AccessAuditFactory,
    AccessPolicyFactory,
    AccessRecommendationFactory,
    AccessRequestFactory,
    AccessResultFactory,
    AnalyticsSummaryFactory,
    AuditReportFactory,
    BadgeFactory,
    BenefitFactory,
    ChurnPredictionFactory,
    CompliancePolicyFactory,
    ComplianceReportFactory,
    ComplianceScoreFactory,
    DisputeFactory,
    DisputeResolutionFactory,
    DocumentDataFactory,
    DocumentVerificationResultFactory,
    EngagementMetricsFactory,
    EscalationAnalysisFactory,
    EscalationFactory,
    FraudReportFactory,
    GovernanceActionFactory,
    GovernanceAnalyticsFactory,
    GovernanceHealthScoreFactory,
    GovernancePolicyFactory,
    GovernanceSummaryFactory,
    GrowthAnalysisFactory,
    HealthExplanationFactory,
    HealthScoreFactory,
    IdentityDataFactory,
    ModerationAnalyticsFactory,
    ModerationEscalationFactory,
    ModerationItemFactory,
    ModerationPredictionFactory,
    ModeratorPerformanceFactory,
    PermissionFactory,
    PolicyEffectivenessFactory,
    PriorityAssessmentFactory,
    PriorityFactory,
    PriorityScoreFactory,
    QueueFactory,
    QueueMetricsFactory,
    RemediationActionFactory,
    ReputationExplanationFactory,
    ReputationHistoryFactory,
    ReputationScoreFactory,
    ResolutionFactory,
    ReviewDecisionFactory,
    RoleFactory,
    RuleEnforcementResultFactory,
    RuleFactory,
    SLABreachFactory,
    SLAFactory,
    TierAnalyticsFactory,
    TierEvaluationFactory,
    TierFactory,
    ToxicityReportFactory,
    TrendFactory,
    TrendReportFactory,
    TrustScoreFactory,
    TrustTierFactory,
    UpgradeRequestFactory,
    VerificationExplanationFactory,
    VerificationRequestFactory,
    VerificationResultFactory,
    ViolationFactory,
)
from database.seeders.seeders import seed_all  # noqa: E402

ALL_FACTORIES = [
    TierFactory,
    TierEvaluationFactory,
    UpgradeRequestFactory,
    AccessPolicyFactory,
    BenefitFactory,
    TierAnalyticsFactory,
    GovernancePolicyFactory,
    RuleFactory,
    RuleEnforcementResultFactory,
    DisputeFactory,
    DisputeResolutionFactory,
    GovernanceActionFactory,
    GovernanceHealthScoreFactory,
    GovernanceAnalyticsFactory,
    GovernanceSummaryFactory,
    EscalationFactory,
    ResolutionFactory,
    SLAFactory,
    SLABreachFactory,
    PriorityFactory,
    PriorityAssessmentFactory,
    EscalationAnalysisFactory,
    TrendReportFactory,
    PermissionFactory,
    RoleFactory,
    AccessRequestFactory,
    AccessResultFactory,
    AccessAuditFactory,
    AccessRecommendationFactory,
    ReputationScoreFactory,
    BadgeFactory,
    TrustTierFactory,
    ReputationHistoryFactory,
    ReputationExplanationFactory,
    CompliancePolicyFactory,
    ViolationFactory,
    AuditReportFactory,
    ComplianceScoreFactory,
    ComplianceReportFactory,
    RemediationActionFactory,
    IdentityDataFactory,
    DocumentDataFactory,
    VerificationRequestFactory,
    VerificationResultFactory,
    TrustScoreFactory,
    FraudReportFactory,
    DocumentVerificationResultFactory,
    VerificationExplanationFactory,
    ModerationItemFactory,
    QueueFactory,
    PriorityScoreFactory,
    ReviewDecisionFactory,
    ModerationEscalationFactory,
    QueueMetricsFactory,
    ModerationAnalyticsFactory,
    TrendFactory,
    ModeratorPerformanceFactory,
    PolicyEffectivenessFactory,
    ModerationPredictionFactory,
    AnalyticsSummaryFactory,
    EngagementMetricsFactory,
    ToxicityReportFactory,
    GrowthAnalysisFactory,
    ChurnPredictionFactory,
    HealthScoreFactory,
    HealthExplanationFactory,
]


def validate_factories_deep() -> dict[str, Any]:
    """Validate all factories produce valid, serializable data with correct types."""
    results = {"passed": 0, "failed": 0, "errors": [], "details": []}
    for factory in ALL_FACTORIES:
        try:
            obj = factory()
            assert obj is not None
            dumped = obj.model_dump()
            assert isinstance(dumped, dict)
            json.dumps(dumped, default=str)
            results["passed"] += 1
            results["details"].append(
                {
                    "factory": factory.__name__,
                    "fields": len(dumped),
                    "sample_keys": list(dumped.keys())[:5],
                }
            )
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(
                {
                    "factory": factory.__name__,
                    "error": str(e),
                }
            )
    return results


def generate_edge_cases() -> dict[str, Any]:
    """Generate comprehensive edge case data."""
    edge_cases = {}

    # Null values for optional fields
    try:
        tier = TierFactory(
            name="Test Tier",
            description=None,
            max_members=None,
            metadata={},
        )
        assert tier.description is None
        assert tier.max_members is None
        edge_cases["null_optional_fields"] = {"status": "passed", "example": tier.name}
    except Exception as e:
        edge_cases["null_optional_fields"] = {"status": "failed", "error": str(e)}

    # Boundary values - minimum
    try:
        tier = TierFactory(
            name="A",
            max_members=1,
            monthly_fee=0.0,
        )
        assert len(tier.name) == 1
        assert tier.max_members == 1
        assert tier.monthly_fee == 0.0
        edge_cases["boundary_min"] = {
            "status": "passed",
            "example": f"name={tier.name}, max_members={tier.max_members}",
        }
    except Exception as e:
        edge_cases["boundary_min"] = {"status": "failed", "error": str(e)}

    # Boundary values - maximum
    try:
        tier = TierFactory(
            name="X" * 100,
            max_members=10000,
            monthly_fee=500.0,
        )
        assert len(tier.name) == 100
        edge_cases["boundary_max"] = {
            "status": "passed",
            "example": f"name_len={len(tier.name)}, max_members={tier.max_members}",
        }
    except Exception as e:
        edge_cases["boundary_max"] = {"status": "failed", "error": str(e)}

    # Unicode strings
    try:
        tier = TierFactory(
            name="Tier 名称 🚀",
            description="Description with émojis 🎉 and ünïcödé",
        )
        assert "🚀" in tier.name
        edge_cases["unicode"] = {"status": "passed", "example": tier.name}
    except Exception as e:
        edge_cases["unicode"] = {"status": "failed", "error": str(e)}

    # Empty/whitespace strings (should fail validation)
    try:
        tier = TierFactory(name="   ")
        edge_cases["whitespace_only"] = {
            "status": "unexpected_pass",
            "example": repr(tier.name),
        }
    except Exception as e:
        edge_cases["whitespace_only"] = {
            "status": "expected_failure",
            "error": str(e)[:80],
        }

    # Special characters and XSS patterns
    try:
        tier = TierFactory(
            name="Tier <script>alert('xss')</script>",
            description="Description with 'quotes' and \"double quotes\"",
        )
        edge_cases["special_chars"] = {"status": "passed", "example": tier.name[:30]}
    except Exception as e:
        edge_cases["special_chars"] = {"status": "failed", "error": str(e)}

    # Very long strings (exceeds max_length)
    try:
        tier = TierFactory(name="T" * 1000)
        edge_cases["long_strings"] = {
            "status": "unexpected_pass",
            "example": f"name_len={len(tier.name)}",
        }
    except Exception as e:
        edge_cases["long_strings"] = {
            "status": "expected_failure",
            "error": str(e)[:80],
        }

    # Negative values (should fail for ge=0 fields)
    try:
        tier = TierFactory(monthly_fee=-1.0)
        edge_cases["negative_values"] = {
            "status": "unexpected_pass",
            "example": f"fee={tier.monthly_fee}",
        }
    except Exception as e:
        edge_cases["negative_values"] = {
            "status": "expected_failure",
            "error": str(e)[:80],
        }

    # Zero values for nullable integer fields
    try:
        benefit = BenefitFactory(usage_limit=0)
        edge_cases["zero_usage_limit"] = {
            "status": "unexpected_pass",
            "example": f"usage_limit={benefit.usage_limit}",
        }
    except Exception as e:
        edge_cases["zero_usage_limit"] = {
            "status": "expected_failure",
            "error": str(e)[:80],
        }

    # Empty lists and dicts
    try:
        tier = TierFactory(benefits=[], requirements={})
        assert tier.benefits == []
        assert tier.requirements == {}
        edge_cases["empty_collections"] = {
            "status": "passed",
            "example": f"benefits={tier.benefits}",
        }
    except Exception as e:
        edge_cases["empty_collections"] = {"status": "failed", "error": str(e)}

    # Nested model with unicode
    try:
        verification = VerificationRequestFactory()
        verification.identity.full_name = "José García Márquez"
        edge_cases["nested_unicode"] = {
            "status": "passed",
            "example": verification.identity.full_name,
        }
    except Exception as e:
        edge_cases["nested_unicode"] = {"status": "failed", "error": str(e)}

    # Boundary float values
    try:
        tier_eval = TierEvaluationFactory(score=0.0, confidence=0.0)
        assert tier_eval.score == 0.0
        assert tier_eval.confidence == 0.0
        edge_cases["float_zero"] = {
            "status": "passed",
            "example": f"score={tier_eval.score}, confidence={tier_eval.confidence}",
        }
    except Exception as e:
        edge_cases["float_zero"] = {"status": "failed", "error": str(e)}

    try:
        tier_eval = TierEvaluationFactory(score=100.0, confidence=1.0)
        assert tier_eval.score == 100.0
        assert tier_eval.confidence == 1.0
        edge_cases["float_max"] = {
            "status": "passed",
            "example": f"score={tier_eval.score}, confidence={tier_eval.confidence}",
        }
    except Exception as e:
        edge_cases["float_max"] = {"status": "failed", "error": str(e)}

    return edge_cases


def check_foreign_key_consistency() -> dict[str, Any]:
    """Verify foreign key relationships and referential integrity."""
    checks = {}

    # Tier -> AccessPolicy relationship
    try:
        tiers = TierFactory.create_batch(3)
        tier_ids = {t.id for t in tiers}
        policies = [AccessPolicyFactory(tier_id=tid) for tid in tier_ids]
        for policy in policies:
            assert policy.tier_id in tier_ids
        checks["tier_to_access_policy"] = {
            "status": "passed",
            "detail": f"{len(policies)} policies reference valid tiers",
        }
    except Exception as e:
        checks["tier_to_access_policy"] = {"status": "failed", "error": str(e)}

    # Tier -> Benefit relationship (many-to-many via tier_ids)
    try:
        tiers = TierFactory.create_batch(3)
        tier_ids = [t.id for t in tiers]
        benefit = BenefitFactory(tier_ids=tier_ids)
        for tid in benefit.tier_ids:
            assert tid in tier_ids
        checks["tier_to_benefit"] = {
            "status": "passed",
            "detail": f"Benefit references {len(tier_ids)} valid tiers",
        }
    except Exception as e:
        checks["tier_to_benefit"] = {"status": "failed", "error": str(e)}

    # Escalation -> Resolution relationship
    try:
        escalation = EscalationFactory()
        resolution = ResolutionFactory(escalation_id=escalation.id)
        assert resolution.escalation_id == escalation.id
        checks["escalation_to_resolution"] = {
            "status": "passed",
            "detail": "Resolution references valid escalation",
        }
    except Exception as e:
        checks["escalation_to_resolution"] = {"status": "failed", "error": str(e)}

    # Escalation -> SLA relationship
    try:
        escalation = EscalationFactory()
        sla = SLAFactory(escalation_id=escalation.id)
        assert sla.escalation_id == escalation.id
        checks["escalation_to_sla"] = {
            "status": "passed",
            "detail": "SLA references valid escalation",
        }
    except Exception as e:
        checks["escalation_to_sla"] = {"status": "failed", "error": str(e)}

    # SLA -> SLABreach relationship
    try:
        sla = SLAFactory()
        breach = SLABreachFactory(sla_id=sla.id, escalation_id=sla.escalation_id)
        assert breach.sla_id == sla.id
        checks["sla_to_breach"] = {
            "status": "passed",
            "detail": "Breach references valid SLA",
        }
    except Exception as e:
        checks["sla_to_breach"] = {"status": "failed", "error": str(e)}

    # Escalation -> PriorityAssessment relationship
    try:
        escalation = EscalationFactory()
        assessment = PriorityAssessmentFactory(escalation_id=escalation.id)
        assert assessment.escalation_id == escalation.id
        checks["escalation_to_assessment"] = {
            "status": "passed",
            "detail": "Assessment references valid escalation",
        }
    except Exception as e:
        checks["escalation_to_assessment"] = {"status": "failed", "error": str(e)}

    # CompliancePolicy -> Violation relationship
    try:
        policy = CompliancePolicyFactory()
        violation = ViolationFactory(policy_id=policy.id)
        assert violation.policy_id == policy.id
        checks["policy_to_violation"] = {
            "status": "passed",
            "detail": "Violation references valid policy",
        }
    except Exception as e:
        checks["policy_to_violation"] = {"status": "failed", "error": str(e)}

    # Violation -> RemediationAction relationship
    try:
        violation = ViolationFactory()
        action = RemediationActionFactory(violation_id=violation.id)
        assert action.violation_id == violation.id
        checks["violation_to_remediation"] = {
            "status": "passed",
            "detail": "Remediation references valid violation",
        }
    except Exception as e:
        checks["violation_to_remediation"] = {"status": "failed", "error": str(e)}

    # Rule -> RuleEnforcementResult relationship
    try:
        rule = RuleFactory()
        result = RuleEnforcementResultFactory(rule_id=rule.id)
        assert result.rule_id == rule.id
        checks["rule_to_enforcement"] = {
            "status": "passed",
            "detail": "Enforcement result references valid rule",
        }
    except Exception as e:
        checks["rule_to_enforcement"] = {"status": "failed", "error": str(e)}

    # ModerationItem -> ReviewDecision relationship
    try:
        item = ModerationItemFactory()
        decision = ReviewDecisionFactory(item_id=item.id)
        assert decision.item_id == item.id
        checks["item_to_decision"] = {
            "status": "passed",
            "detail": "Decision references valid moderation item",
        }
    except Exception as e:
        checks["item_to_decision"] = {"status": "failed", "error": str(e)}

    # ModerationItem -> ModerationEscalation relationship
    try:
        item = ModerationItemFactory()
        escalation = ModerationEscalationFactory(item_id=item.id)
        assert escalation.item_id == item.id
        checks["item_to_escalation"] = {
            "status": "passed",
            "detail": "Escalation references valid moderation item",
        }
    except Exception as e:
        checks["item_to_escalation"] = {"status": "failed", "error": str(e)}

    # Queue -> QueueMetrics relationship
    try:
        queue = QueueFactory()
        metrics = QueueMetricsFactory(queue_id=queue.id)
        assert metrics.queue_id == queue.id
        checks["queue_to_metrics"] = {
            "status": "passed",
            "detail": "Metrics reference valid queue",
        }
    except Exception as e:
        checks["queue_to_metrics"] = {"status": "failed", "error": str(e)}

    # ModerationItem -> PriorityScore relationship
    try:
        item = ModerationItemFactory()
        score = PriorityScoreFactory(item_id=item.id)
        assert score.item_id == item.id
        checks["item_to_priority_score"] = {
            "status": "passed",
            "detail": "Priority score references valid item",
        }
    except Exception as e:
        checks["item_to_priority_score"] = {"status": "failed", "error": str(e)}

    # VerificationRequest -> VerificationResult relationship
    try:
        request = VerificationRequestFactory()
        result = VerificationResultFactory(
            request_id=request.request_id, member_id=request.member_id
        )
        assert result.request_id == request.request_id
        assert result.member_id == request.member_id
        checks["request_to_result"] = {
            "status": "passed",
            "detail": "Result references valid request",
        }
    except Exception as e:
        checks["request_to_result"] = {"status": "failed", "error": str(e)}

    # AccessRequest -> AccessResult relationship (SubFactory)
    try:
        result = AccessResultFactory()
        assert result.request is not None
        assert result.request.principal_id is not None
        checks["access_request_result"] = {
            "status": "passed",
            "detail": "AccessResult contains valid AccessRequest",
        }
    except Exception as e:
        checks["access_request_result"] = {"status": "failed", "error": str(e)}

    # GovernanceAnalytics -> GovernanceHealthScore (SubFactory)
    try:
        analytics = GovernanceAnalyticsFactory()
        assert analytics.health_score is not None
        assert 0 <= analytics.health_score.overall_score <= 100
        checks["analytics_to_health_score"] = {
            "status": "passed",
            "detail": "Analytics contains valid health score",
        }
    except Exception as e:
        checks["analytics_to_health_score"] = {"status": "failed", "error": str(e)}

    # AnalyticsSummary -> nested models (SubFactory)
    try:
        summary = AnalyticsSummaryFactory()
        assert summary.analytics is not None
        assert len(summary.trends) > 0
        assert len(summary.top_moderators) > 0
        checks["summary_nested"] = {
            "status": "passed",
            "detail": "Summary contains valid nested models",
        }
    except Exception as e:
        checks["summary_nested"] = {"status": "failed", "error": str(e)}

    # Unique ID generation
    try:
        tiers = TierFactory.create_batch(10)
        ids = [t.id for t in tiers]
        assert len(set(ids)) == 10, "All IDs should be unique"
        checks["unique_ids"] = {
            "status": "passed",
            "detail": "All generated IDs are unique",
        }
    except Exception as e:
        checks["unique_ids"] = {"status": "failed", "error": str(e)}

    # seed_all completeness
    try:
        data = seed_all()
        expected_count = 66
        assert (
            len(data) == expected_count
        ), f"Expected {expected_count} entity types, got {len(data)}"
        checks["seed_all_completeness"] = {
            "status": "passed",
            "detail": f"All {expected_count} entity types present",
        }
    except Exception as e:
        checks["seed_all_completeness"] = {"status": "failed", "error": str(e)}

    return checks


def run_enhanced_validation() -> dict[str, Any]:
    """Run all enhanced validations."""
    print("Running deep factory validation...")
    factory_results = validate_factories_deep()

    print("Generating edge cases...")
    edge_case_results = generate_edge_cases()

    print("Checking foreign key consistency...")
    fk_results = check_foreign_key_consistency()

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "factory_validation": factory_results,
        "edge_cases": edge_case_results,
        "foreign_key_consistency": fk_results,
    }


if __name__ == "__main__":
    results = run_enhanced_validation()
    print(json.dumps(results, indent=2, default=str))

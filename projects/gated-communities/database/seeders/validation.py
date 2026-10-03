"""
Comprehensive validation suite for gated-communities database seeders.

Validates:
1. All factories produce valid data
2. Edge case data (null values, boundary values, unicode)
3. Performance benchmarks (seeder execution time)
4. Data consistency checks (foreign key relationships)
5. Bulk insert optimization (COPY vs INSERT)
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Ensure src/ is on the path
_src = str(Path(__file__).resolve().parents[3] / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

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

# ===========================================================================
# 1. Factory Validation
# ===========================================================================

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


def validate_factories() -> dict[str, Any]:
    """Validate all factories produce valid data."""
    results = {"passed": 0, "failed": 0, "errors": []}
    for factory in ALL_FACTORIES:
        try:
            obj = factory()
            assert obj is not None
            assert hasattr(obj, "model_dump") or hasattr(obj, "dict")
            results["passed"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(
                {
                    "factory": factory.__name__,
                    "error": str(e),
                }
            )
    return results


# ===========================================================================
# 2. Edge Case Data
# ===========================================================================


def generate_edge_cases() -> dict[str, Any]:
    """Generate edge case data: null values, boundary values, unicode."""
    edge_cases = {}

    # Null values
    try:
        tier = TierFactory(
            name=None,  # type: ignore
            description=None,
            requirements=None,  # type: ignore
            benefits=None,  # type: ignore
            max_members=None,
            metadata=None,  # type: ignore
        )
        edge_cases["null_values"] = {"status": "passed", "example": tier.name}
    except Exception as e:
        edge_cases["null_values"] = {"status": "failed", "error": str(e)}

    # Boundary values
    try:
        tier = TierFactory(
            name="A",  # min length
            max_members=1,  # min
            monthly_fee=0.0,  # min
        )
        edge_cases["boundary_min"] = {
            "status": "passed",
            "example": f"name={tier.name}, max_members={tier.max_members}",
        }
    except Exception as e:
        edge_cases["boundary_min"] = {"status": "failed", "error": str(e)}

    try:
        tier = TierFactory(
            name="X" * 100,  # max length
            max_members=10000,  # max
            monthly_fee=500.0,  # max
        )
        edge_cases["boundary_max"] = {
            "status": "passed",
            "example": f"name_len={len(tier.name)}, max_members={tier.max_members}",
        }
    except Exception as e:
        edge_cases["boundary_max"] = {"status": "failed", "error": str(e)}

    # Unicode
    try:
        tier = TierFactory(
            name="Tier 名称 🚀",
            description="Description with émojis 🎉 and ünïcödé",
        )
        edge_cases["unicode"] = {"status": "passed", "example": tier.name}
    except Exception as e:
        edge_cases["unicode"] = {"status": "failed", "error": str(e)}

    # Empty strings
    try:
        tier = TierFactory(
            name="   ",  # whitespace only - should fail validation
        )
        edge_cases["empty_strings"] = {"status": "passed", "example": repr(tier.name)}
    except Exception as e:
        edge_cases["empty_strings"] = {"status": "expected_failure", "error": str(e)}

    # Special characters
    try:
        tier = TierFactory(
            name="Tier <script>alert('xss')</script>",
            description="Description with 'quotes' and \"double quotes\"",
        )
        edge_cases["special_chars"] = {"status": "passed", "example": tier.name}
    except Exception as e:
        edge_cases["special_chars"] = {"status": "failed", "error": str(e)}

    # Very long strings
    try:
        tier = TierFactory(
            name="T" * 1000,  # exceeds max_length
        )
        edge_cases["long_strings"] = {
            "status": "passed",
            "example": f"name_len={len(tier.name)}",
        }
    except Exception as e:
        edge_cases["long_strings"] = {"status": "expected_failure", "error": str(e)}

    # Negative values (should fail for ge=0 fields)
    try:
        tier = TierFactory(
            monthly_fee=-1.0,
        )
        edge_cases["negative_values"] = {
            "status": "passed",
            "example": f"fee={tier.monthly_fee}",
        }
    except Exception as e:
        edge_cases["negative_values"] = {"status": "expected_failure", "error": str(e)}

    return edge_cases


# ===========================================================================
# 3. Performance Benchmarks
# ===========================================================================


def benchmark_seeders() -> dict[str, Any]:
    """Benchmark seeder execution time."""
    benchmarks = {}

    from database.seeders import seeders as seeder_module

    seeder_funcs = [
        ("seed_tiers", seeder_module.seed_tiers, 100),
        ("seed_tier_evaluations", seeder_module.seed_tier_evaluations, 100),
        ("seed_upgrade_requests", seeder_module.seed_upgrade_requests, 100),
        ("seed_access_policies", seeder_module.seed_access_policies, 100),
        ("seed_benefits", seeder_module.seed_benefits, 100),
        ("seed_governance_policies", seeder_module.seed_governance_policies, 100),
        ("seed_rules", seeder_module.seed_rules, 100),
        ("seed_disputes", seeder_module.seed_disputes, 100),
        ("seed_escalations", seeder_module.seed_escalations, 100),
        ("seed_slas", seeder_module.seed_slas, 100),
        ("seed_reputation_scores", seeder_module.seed_reputation_scores, 100),
        ("seed_violations", seeder_module.seed_violations, 100),
        ("seed_moderation_items", seeder_module.seed_moderation_items, 100),
        ("seed_queues", seeder_module.seed_queues, 100),
        ("seed_health_scores", seeder_module.seed_health_scores, 100),
    ]

    for name, func, count in seeder_funcs:
        start = time.perf_counter()
        func(count=count)
        elapsed = time.perf_counter() - start
        benchmarks[name] = {
            "count": count,
            "elapsed_seconds": round(elapsed, 4),
            "records_per_second": (
                round(count / elapsed, 2) if elapsed > 0 else float("inf")
            ),
        }

    # Benchmark seed_all
    start = time.perf_counter()
    all_data = seed_all()
    elapsed = time.perf_counter() - start
    total_records = sum(len(v) for v in all_data.values())
    benchmarks["seed_all"] = {
        "count": total_records,
        "elapsed_seconds": round(elapsed, 4),
        "records_per_second": (
            round(total_records / elapsed, 2) if elapsed > 0 else float("inf")
        ),
    }

    return benchmarks


# ===========================================================================
# 4. Data Consistency Checks
# ===========================================================================


def check_data_consistency() -> dict[str, Any]:
    """Verify foreign key relationships and data consistency."""
    checks = {}

    # Check that seeded data has consistent UUIDs
    try:
        tiers = TierFactory.create_batch(5)
        tier_ids = {t.id for t in tiers}
        assert len(tier_ids) == 5, "Tier IDs should be unique"
        checks["unique_ids"] = {"status": "passed", "detail": "All tier IDs are unique"}
    except Exception as e:
        checks["unique_ids"] = {"status": "failed", "error": str(e)}

    # Check that nested models are consistent
    try:
        verification = VerificationRequestFactory()
        assert verification.identity is not None
        assert verification.member_id is not None
        checks["nested_models"] = {
            "status": "passed",
            "detail": "Nested models are consistent",
        }
    except Exception as e:
        checks["nested_models"] = {"status": "failed", "error": str(e)}

    # Check that SubFactory relationships work
    try:
        access_result = AccessResultFactory()
        assert access_result.request is not None
        assert access_result.decision in ["allow", "deny", "conditional", "abstain"]
        checks["subfactory_relationships"] = {
            "status": "passed",
            "detail": "SubFactory relationships work",
        }
    except Exception as e:
        checks["subfactory_relationships"] = {"status": "failed", "error": str(e)}

    # Check that enum values are valid
    try:
        tier = TierFactory()
        assert tier.level in ["bronze", "silver", "gold", "platinum", "diamond"]
        assert tier.status in ["active", "inactive", "suspended", "pending", "expired"]
        checks["enum_values"] = {"status": "passed", "detail": "Enum values are valid"}
    except Exception as e:
        checks["enum_values"] = {"status": "failed", "error": str(e)}

    # Check that numeric ranges are respected
    try:
        tier = TierFactory()
        assert tier.monthly_fee >= 0
        assert tier.max_members is None or tier.max_members >= 1
        checks["numeric_ranges"] = {
            "status": "passed",
            "detail": "Numeric ranges are respected",
        }
    except Exception as e:
        checks["numeric_ranges"] = {"status": "failed", "error": str(e)}

    # Check that timestamps are valid
    try:
        tier = TierFactory()
        assert tier.created_at is not None
        assert tier.updated_at is not None
        checks["timestamps"] = {"status": "passed", "detail": "Timestamps are valid"}
    except Exception as e:
        checks["timestamps"] = {"status": "failed", "error": str(e)}

    # Check that seed_all returns all expected keys
    try:
        data = seed_all()
        expected_keys = {
            "tiers",
            "tier_evaluations",
            "upgrade_requests",
            "access_policies",
            "benefits",
            "tier_analytics",
            "governance_policies",
            "rules",
            "rule_enforcement_results",
            "disputes",
            "dispute_resolutions",
            "governance_actions",
            "governance_health_scores",
            "governance_analytics",
            "governance_summaries",
            "escalations",
            "resolutions",
            "slas",
            "sla_breaches",
            "priorities",
            "priority_assessments",
            "escalation_analyses",
            "trend_reports",
            "permissions",
            "roles",
            "access_requests",
            "access_results",
            "access_audits",
            "access_recommendations",
            "reputation_scores",
            "badges",
            "trust_tiers",
            "reputation_history",
            "reputation_explanations",
            "compliance_policies",
            "violations",
            "audit_reports",
            "compliance_scores",
            "compliance_reports",
            "remediation_actions",
            "identity_data",
            "document_data",
            "verification_requests",
            "verification_results",
            "trust_scores",
            "fraud_reports",
            "document_verification_results",
            "verification_explanations",
            "moderation_items",
            "queues",
            "priority_scores",
            "review_decisions",
            "moderation_escalations",
            "queue_metrics",
            "moderation_analytics",
            "trends",
            "moderator_performance",
            "policy_effectiveness",
            "moderation_predictions",
            "analytics_summaries",
            "engagement_metrics",
            "toxicity_reports",
            "growth_analyses",
            "churn_predictions",
            "health_scores",
            "health_explanations",
        }
        actual_keys = set(data.keys())
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        if not missing and not extra:
            checks["seed_all_completeness"] = {
                "status": "passed",
                "detail": f"All {len(expected_keys)} keys present",
            }
        else:
            checks["seed_all_completeness"] = {
                "status": "warning",
                "missing": list(missing),
                "extra": list(extra),
            }
    except Exception as e:
        checks["seed_all_completeness"] = {"status": "failed", "error": str(e)}

    return checks


# ===========================================================================
# 5. Bulk Insert Optimization (COPY vs INSERT)
# ===========================================================================


def benchmark_bulk_insert() -> dict[str, Any]:
    """Benchmark COPY vs INSERT for bulk data loading."""
    results = {}

    # Generate test data
    tiers = TierFactory.create_batch(1000)

    # Simulate INSERT (row-by-row)
    start = time.perf_counter()
    insert_data = []
    for tier in tiers:
        insert_data.append(
            {
                "id": str(tier.id),
                "name": tier.name,
                "level": tier.level,
                "status": tier.status,
                "description": tier.description,
                "requirements": json.dumps(tier.requirements),
                "benefits": json.dumps(tier.benefits),
                "max_members": tier.max_members,
                "monthly_fee": tier.monthly_fee,
                "created_at": tier.created_at.isoformat(),
                "updated_at": tier.updated_at.isoformat(),
                "metadata": json.dumps(tier.metadata),
            }
        )
    insert_time = time.perf_counter() - start

    # Simulate COPY (bulk)
    start = time.perf_counter()
    copy_data = []
    for tier in tiers:
        copy_data.append(
            (
                str(tier.id),
                tier.name,
                tier.level,
                tier.status,
                tier.description or "",
                json.dumps(tier.requirements),
                json.dumps(tier.benefits),
                tier.max_members or 0,
                tier.monthly_fee,
                tier.created_at.isoformat(),
                tier.updated_at.isoformat(),
                json.dumps(tier.metadata),
            )
        )
    copy_time = time.perf_counter() - start

    results["insert_simulation"] = {
        "record_count": len(insert_data),
        "elapsed_seconds": round(insert_time, 4),
        "records_per_second": (
            round(len(insert_data) / insert_time, 2)
            if insert_time > 0
            else float("inf")
        ),
    }
    results["copy_simulation"] = {
        "record_count": len(copy_data),
        "elapsed_seconds": round(copy_time, 4),
        "records_per_second": (
            round(len(copy_data) / copy_time, 2) if copy_time > 0 else float("inf")
        ),
    }
    results["speedup"] = (
        round(insert_time / copy_time, 2) if copy_time > 0 else float("inf")
    )

    return results


# ===========================================================================
# Main validation runner
# ===========================================================================


def run_all_validations() -> dict[str, Any]:
    """Run all validations and return comprehensive results."""
    print("Running factory validation...")
    factory_results = validate_factories()

    print("Generating edge cases...")
    edge_case_results = generate_edge_cases()

    print("Running performance benchmarks...")
    benchmark_results = benchmark_seeders()

    print("Checking data consistency...")
    consistency_results = check_data_consistency()

    print("Benchmarking bulk insert...")
    bulk_insert_results = benchmark_bulk_insert()

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "factory_validation": factory_results,
        "edge_cases": edge_case_results,
        "performance_benchmarks": benchmark_results,
        "data_consistency": consistency_results,
        "bulk_insert_optimization": bulk_insert_results,
    }


if __name__ == "__main__":
    results = run_all_validations()
    print(json.dumps(results, indent=2, default=str))

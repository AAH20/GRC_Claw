"""
Seeder scripts for generating realistic test data.

Each seeder function returns a list of Pydantic model instances ready
to be persisted to your database of choice.  The seeders use
factory_boy factories defined in ``factories.py`` and Faker for
realistic fake data.

Usage
-----
>>> from database.seeders.seeders import seed_tiers, seed_members
>>> tiers = seed_tiers(count=5)
>>> members = seed_members(count=10)
>>>
>>> # Or seed everything:
>>> from database.seeders.seeders import seed_all
>>> data = seed_all()
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from .factories import (
    AccessAuditFactory,
    AccessPolicyFactory,
    AccessRecommendationFactory,
    AccessRequestFactory,
    AccessResultFactory,
    ActionStatus,
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
    QueueFactory,
    QueueMetricsFactory,
    RecommendationFactory,
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


# ===========================================================================
# Tier Management seeders
# ===========================================================================


def seed_tiers(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed membership tiers.

    Args:
        count: Number of tiers to create.
        **kwargs: Override any TierFactory field.

    Returns:
        List of Tier instances.
    """
    return TierFactory.create_batch(count, **kwargs)


def seed_tier_evaluations(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed tier evaluations."""
    return TierEvaluationFactory.create_batch(count, **kwargs)


def seed_upgrade_requests(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed upgrade requests."""
    return UpgradeRequestFactory.create_batch(count, **kwargs)


def seed_access_policies(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed access policies (tier management)."""
    return AccessPolicyFactory.create_batch(count, **kwargs)


def seed_benefits(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed benefits."""
    return BenefitFactory.create_batch(count, **kwargs)


def seed_tier_analytics(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed tier analytics."""
    return TierAnalyticsFactory.create_batch(count, **kwargs)


# ===========================================================================
# Community Governance seeders
# ===========================================================================


def seed_governance_policies(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed governance policies."""
    return GovernancePolicyFactory.create_batch(count, **kwargs)


def seed_rules(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed governance rules."""
    return RuleFactory.create_batch(count, **kwargs)


def seed_rule_enforcement_results(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed rule enforcement results."""
    return RuleEnforcementResultFactory.create_batch(count, **kwargs)


def seed_disputes(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed disputes."""
    return DisputeFactory.create_batch(count, **kwargs)


def seed_dispute_resolutions(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed dispute resolutions."""
    return DisputeResolutionFactory.create_batch(count, **kwargs)


def seed_governance_actions(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed governance actions."""
    return GovernanceActionFactory.create_batch(count, **kwargs)


def seed_governance_health_scores(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed governance health scores."""
    return GovernanceHealthScoreFactory.create_batch(count, **kwargs)


def seed_governance_analytics(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed governance analytics."""
    return GovernanceAnalyticsFactory.create_batch(count, **kwargs)


def seed_governance_summaries(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed governance summaries."""
    return GovernanceSummaryFactory.create_batch(count, **kwargs)


# ===========================================================================
# Escalation Workflow seeders
# ===========================================================================


def seed_escalations(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed escalations."""
    return EscalationFactory.create_batch(count, **kwargs)


def seed_resolutions(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed resolutions."""
    return ResolutionFactory.create_batch(count, **kwargs)


def seed_slas(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed SLAs."""
    return SLAFactory.create_batch(count, **kwargs)


def seed_sla_breaches(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed SLA breaches."""
    return SLABreachFactory.create_batch(count, **kwargs)


def seed_priorities(count: int = 4, **kwargs: Any) -> list[Any]:
    """Seed priority configurations."""
    return PriorityFactory.create_batch(count, **kwargs)


def seed_priority_assessments(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed priority assessments."""
    return PriorityAssessmentFactory.create_batch(count, **kwargs)


def seed_escalation_analyses(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed escalation analyses."""
    return EscalationAnalysisFactory.create_batch(count, **kwargs)


def seed_trend_reports(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed trend reports."""
    return TrendReportFactory.create_batch(count, **kwargs)


# ===========================================================================
# Access Control seeders
# ===========================================================================


def seed_permissions(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed permissions."""
    return PermissionFactory.create_batch(count, **kwargs)


def seed_roles(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed roles."""
    return RoleFactory.create_batch(count, **kwargs)


def seed_access_requests(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed access requests."""
    return AccessRequestFactory.create_batch(count, **kwargs)


def seed_access_results(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed access results."""
    return AccessResultFactory.create_batch(count, **kwargs)


def seed_access_audits(count: int = 50, **kwargs: Any) -> list[Any]:
    """Seed access audit entries."""
    return AccessAuditFactory.create_batch(count, **kwargs)


def seed_access_recommendations(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed access recommendations."""
    return AccessRecommendationFactory.create_batch(count, **kwargs)


# ===========================================================================
# Reputation System seeders
# ===========================================================================


def seed_reputation_scores(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed reputation scores."""
    return ReputationScoreFactory.create_batch(count, **kwargs)


def seed_badges(count: int = 15, **kwargs: Any) -> list[Any]:
    """Seed badges."""
    return BadgeFactory.create_batch(count, **kwargs)


def seed_trust_tiers(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed trust tiers."""
    return TrustTierFactory.create_batch(count, **kwargs)


def seed_reputation_history(count: int = 50, **kwargs: Any) -> list[Any]:
    """Seed reputation history entries."""
    return ReputationHistoryFactory.create_batch(count, **kwargs)


def seed_reputation_explanations(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed reputation explanations."""
    return ReputationExplanationFactory.create_batch(count, **kwargs)


# ===========================================================================
# Compliance Monitor seeders
# ===========================================================================


def seed_compliance_policies(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed compliance policies."""
    return CompliancePolicyFactory.create_batch(count, **kwargs)


def seed_violations(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed violations."""
    return ViolationFactory.create_batch(count, **kwargs)


def seed_audit_reports(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed audit reports."""
    return AuditReportFactory.create_batch(count, **kwargs)


def seed_compliance_scores(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed compliance scores."""
    return ComplianceScoreFactory.create_batch(count, **kwargs)


def seed_compliance_reports(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed compliance reports."""
    return ComplianceReportFactory.create_batch(count, **kwargs)


def seed_remediation_actions(count: int = 15, **kwargs: Any) -> list[Any]:
    """Seed remediation actions."""
    return RemediationActionFactory.create_batch(count, **kwargs)


# ===========================================================================
# Member Verification seeders
# ===========================================================================


def seed_identity_data(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed identity data."""
    return IdentityDataFactory.create_batch(count, **kwargs)


def seed_document_data(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed document data."""
    return DocumentDataFactory.create_batch(count, **kwargs)


def seed_verification_requests(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed verification requests."""
    return VerificationRequestFactory.create_batch(count, **kwargs)


def seed_verification_results(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed verification results."""
    return VerificationResultFactory.create_batch(count, **kwargs)


def seed_trust_scores(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed trust scores."""
    return TrustScoreFactory.create_batch(count, **kwargs)


def seed_fraud_reports(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed fraud reports."""
    return FraudReportFactory.create_batch(count, **kwargs)


def seed_document_verification_results(count: int = 20, **kwargs: Any) -> list[Any]:
    """Seed document verification results."""
    return DocumentVerificationResultFactory.create_batch(count, **kwargs)


def seed_verification_explanations(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed verification explanations."""
    return VerificationExplanationFactory.create_batch(count, **kwargs)


# ===========================================================================
# Moderation Queue seeders
# ===========================================================================


def seed_moderation_items(count: int = 50, **kwargs: Any) -> list[Any]:
    """Seed moderation items."""
    return ModerationItemFactory.create_batch(count, **kwargs)


def seed_queues(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed moderation queues."""
    return QueueFactory.create_batch(count, **kwargs)


def seed_priority_scores(count: int = 50, **kwargs: Any) -> list[Any]:
    """Seed priority scores."""
    return PriorityScoreFactory.create_batch(count, **kwargs)


def seed_review_decisions(count: int = 30, **kwargs: Any) -> list[Any]:
    """Seed review decisions."""
    return ReviewDecisionFactory.create_batch(count, **kwargs)


def seed_moderation_escalations(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed moderation escalations."""
    return ModerationEscalationFactory.create_batch(count, **kwargs)


def seed_queue_metrics(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed queue metrics."""
    return QueueMetricsFactory.create_batch(count, **kwargs)


# ===========================================================================
# Moderation Analytics seeders
# ===========================================================================


def seed_moderation_analytics(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed moderation analytics."""
    return ModerationAnalyticsFactory.create_batch(count, **kwargs)


def seed_trends(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed trends."""
    return TrendFactory.create_batch(count, **kwargs)


def seed_moderator_performance(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed moderator performance records."""
    return ModeratorPerformanceFactory.create_batch(count, **kwargs)


def seed_policy_effectiveness(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed policy effectiveness records."""
    return PolicyEffectivenessFactory.create_batch(count, **kwargs)


def seed_moderation_predictions(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed moderation predictions."""
    return ModerationPredictionFactory.create_batch(count, **kwargs)


def seed_analytics_summaries(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed analytics summaries."""
    return AnalyticsSummaryFactory.create_batch(count, **kwargs)


# ===========================================================================
# Community Health Scorer seeders
# ===========================================================================


def seed_engagement_metrics(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed engagement metrics."""
    return EngagementMetricsFactory.create_batch(count, **kwargs)


def seed_toxicity_reports(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed toxicity reports."""
    return ToxicityReportFactory.create_batch(count, **kwargs)


def seed_growth_analyses(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed growth analyses."""
    return GrowthAnalysisFactory.create_batch(count, **kwargs)


def seed_churn_predictions(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed churn predictions."""
    return ChurnPredictionFactory.create_batch(count, **kwargs)


def seed_health_scores(count: int = 10, **kwargs: Any) -> list[Any]:
    """Seed health scores."""
    return HealthScoreFactory.create_batch(count, **kwargs)


def seed_health_explanations(count: int = 5, **kwargs: Any) -> list[Any]:
    """Seed health explanations."""
    return HealthExplanationFactory.create_batch(count, **kwargs)


# ===========================================================================
# Full-database seeder
# ===========================================================================


def seed_all(
    tiers: int = 5,
    evaluations: int = 10,
    upgrade_requests: int = 10,
    access_policies: int = 10,
    benefits: int = 10,
    tier_analytics: int = 5,
    governance_policies: int = 5,
    rules: int = 10,
    enforcement_results: int = 10,
    disputes: int = 10,
    dispute_resolutions: int = 5,
    governance_actions: int = 20,
    health_scores: int = 5,
    governance_analytics: int = 5,
    governance_summaries: int = 5,
    escalations: int = 10,
    resolutions: int = 5,
    slas: int = 10,
    sla_breaches: int = 5,
    priorities: int = 4,
    priority_assessments: int = 10,
    escalation_analyses: int = 5,
    trend_reports: int = 5,
    permissions: int = 20,
    roles: int = 10,
    access_requests: int = 20,
    access_results: int = 20,
    access_audits: int = 50,
    access_recommendations: int = 10,
    reputation_scores: int = 20,
    badges: int = 15,
    trust_tiers: int = 5,
    reputation_history: int = 50,
    reputation_explanations: int = 10,
    compliance_policies: int = 10,
    violations: int = 20,
    audit_reports: int = 5,
    compliance_scores: int = 10,
    compliance_reports: int = 5,
    remediation_actions: int = 15,
    identity_data: int = 20,
    document_data: int = 20,
    verification_requests: int = 20,
    verification_results: int = 20,
    trust_scores: int = 20,
    fraud_reports: int = 10,
    document_verification_results: int = 20,
    verification_explanations: int = 10,
    moderation_items: int = 50,
    queues: int = 5,
    priority_scores: int = 50,
    review_decisions: int = 30,
    moderation_escalations: int = 10,
    queue_metrics: int = 5,
    moderation_analytics: int = 5,
    trends: int = 10,
    moderator_performance: int = 10,
    policy_effectiveness: int = 10,
    moderation_predictions: int = 10,
    analytics_summaries: int = 5,
    engagement_metrics: int = 10,
    toxicity_reports: int = 10,
    growth_analyses: int = 10,
    churn_predictions: int = 10,
    health_score_records: int = 10,
    health_explanations: int = 5,
) -> dict[str, list[Any]]:
    """Seed all entities with realistic test data.

    Returns:
        A dictionary mapping entity names to lists of model instances.
    """
    return {
        # Tier Management
        "tiers": seed_tiers(tiers),
        "tier_evaluations": seed_tier_evaluations(evaluations),
        "upgrade_requests": seed_upgrade_requests(upgrade_requests),
        "access_policies": seed_access_policies(access_policies),
        "benefits": seed_benefits(benefits),
        "tier_analytics": seed_tier_analytics(tier_analytics),
        # Community Governance
        "governance_policies": seed_governance_policies(governance_policies),
        "rules": seed_rules(rules),
        "rule_enforcement_results": seed_rule_enforcement_results(enforcement_results),
        "disputes": seed_disputes(disputes),
        "dispute_resolutions": seed_dispute_resolutions(dispute_resolutions),
        "governance_actions": seed_governance_actions(governance_actions),
        "governance_health_scores": seed_governance_health_scores(health_scores),
        "governance_analytics": seed_governance_analytics(governance_analytics),
        "governance_summaries": seed_governance_summaries(governance_summaries),
        # Escalation Workflow
        "escalations": seed_escalations(escalations),
        "resolutions": seed_resolutions(resolutions),
        "slas": seed_slas(slas),
        "sla_breaches": seed_sla_breaches(sla_breaches),
        "priorities": seed_priorities(priorities),
        "priority_assessments": seed_priority_assessments(priority_assessments),
        "escalation_analyses": seed_escalation_analyses(escalation_analyses),
        "trend_reports": seed_trend_reports(trend_reports),
        # Access Control
        "permissions": seed_permissions(permissions),
        "roles": seed_roles(roles),
        "access_requests": seed_access_requests(access_requests),
        "access_results": seed_access_results(access_results),
        "access_audits": seed_access_audits(access_audits),
        "access_recommendations": seed_access_recommendations(access_recommendations),
        # Reputation System
        "reputation_scores": seed_reputation_scores(reputation_scores),
        "badges": seed_badges(badges),
        "trust_tiers": seed_trust_tiers(trust_tiers),
        "reputation_history": seed_reputation_history(reputation_history),
        "reputation_explanations": seed_reputation_explanations(reputation_explanations),
        # Compliance Monitor
        "compliance_policies": seed_compliance_policies(compliance_policies),
        "violations": seed_violations(violations),
        "audit_reports": seed_audit_reports(audit_reports),
        "compliance_scores": seed_compliance_scores(compliance_scores),
        "compliance_reports": seed_compliance_reports(compliance_reports),
        "remediation_actions": seed_remediation_actions(remediation_actions),
        # Member Verification
        "identity_data": seed_identity_data(identity_data),
        "document_data": seed_document_data(document_data),
        "verification_requests": seed_verification_requests(verification_requests),
        "verification_results": seed_verification_results(verification_results),
        "trust_scores": seed_trust_scores(trust_scores),
        "fraud_reports": seed_fraud_reports(fraud_reports),
        "document_verification_results": seed_document_verification_results(document_verification_results),
        "verification_explanations": seed_verification_explanations(verification_explanations),
        # Moderation Queue
        "moderation_items": seed_moderation_items(moderation_items),
        "queues": seed_queues(queues),
        "priority_scores": seed_priority_scores(priority_scores),
        "review_decisions": seed_review_decisions(review_decisions),
        "moderation_escalations": seed_moderation_escalations(moderation_escalations),
        "queue_metrics": seed_queue_metrics(queue_metrics),
        # Moderation Analytics
        "moderation_analytics": seed_moderation_analytics(moderation_analytics),
        "trends": seed_trends(trends),
        "moderator_performance": seed_moderator_performance(moderator_performance),
        "policy_effectiveness": seed_policy_effectiveness(policy_effectiveness),
        "moderation_predictions": seed_moderation_predictions(moderation_predictions),
        "analytics_summaries": seed_analytics_summaries(analytics_summaries),
        # Community Health Scorer
        "engagement_metrics": seed_engagement_metrics(engagement_metrics),
        "toxicity_reports": seed_toxicity_reports(toxicity_reports),
        "growth_analyses": seed_growth_analyses(growth_analyses),
        "churn_predictions": seed_churn_predictions(churn_predictions),
        "health_scores": seed_health_scores(health_score_records),
        "health_explanations": seed_health_explanations(health_explanations),
    }


# ===========================================================================
# CLI entry point
# ===========================================================================


def main() -> None:
    """Run all seeders and print a summary."""
    data = seed_all()
    total = sum(len(v) for v in data.values())
    print(f"Seeded {total} records across {len(data)} entity types:")
    for name, records in data.items():
        print(f"  {name}: {len(records)}")


if __name__ == "__main__":
    main()

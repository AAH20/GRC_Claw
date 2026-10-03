"""
Pytest fixtures for database testing.

These fixtures provide pre-configured factory_boy factories and seed
functions for use in test suites.  Import them in your test modules
or use them via conftest.py.

Usage
-----
# In conftest.py:
from database.seeders.conftest import *  # noqa: F401,F403

# In test files:
def test_tier_creation(tier_factory):
    tier = tier_factory()
    assert tier.name
"""

from __future__ import annotations

from typing import Any

import pytest

from .factories import (
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
from .seeders import (
    seed_access_audits,
    seed_access_policies,
    seed_access_recommendations,
    seed_access_requests,
    seed_access_results,
    seed_analytics_summaries,
    seed_audit_reports,
    seed_badges,
    seed_benefits,
    seed_churn_predictions,
    seed_compliance_policies,
    seed_compliance_reports,
    seed_compliance_scores,
    seed_dispute_resolutions,
    seed_disputes,
    seed_document_data,
    seed_document_verification_results,
    seed_engagement_metrics,
    seed_escalation_analyses,
    seed_escalations,
    seed_fraud_reports,
    seed_governance_actions,
    seed_governance_analytics,
    seed_governance_health_scores,
    seed_governance_policies,
    seed_governance_summaries,
    seed_growth_analyses,
    seed_health_explanations,
    seed_health_scores,
    seed_identity_data,
    seed_moderation_analytics,
    seed_moderation_escalations,
    seed_moderation_items,
    seed_moderation_predictions,
    seed_moderator_performance,
    seed_permissions,
    seed_policy_effectiveness,
    seed_priority_assessments,
    seed_priority_scores,
    seed_queue_metrics,
    seed_queues,
    seed_remediation_actions,
    seed_reputation_explanations,
    seed_reputation_history,
    seed_reputation_scores,
    seed_resolutions,
    seed_review_decisions,
    seed_roles,
    seed_rule_enforcement_results,
    seed_rules,
    seed_sla_breaches,
    seed_slas,
    seed_tier_analytics,
    seed_tier_evaluations,
    seed_tiers,
    seed_toxicity_reports,
    seed_trend_reports,
    seed_trends,
    seed_trust_scores,
    seed_trust_tiers,
    seed_upgrade_requests,
    seed_verification_explanations,
    seed_verification_requests,
    seed_verification_results,
    seed_violations,
)

# ===========================================================================
# Factory fixtures – one per factory
# ===========================================================================


@pytest.fixture
def tier_factory():
    """Return the TierFactory class."""
    return TierFactory


@pytest.fixture
def tier_evaluation_factory():
    return TierEvaluationFactory


@pytest.fixture
def upgrade_request_factory():
    return UpgradeRequestFactory


@pytest.fixture
def access_policy_factory():
    return AccessPolicyFactory


@pytest.fixture
def benefit_factory():
    return BenefitFactory


@pytest.fixture
def tier_analytics_factory():
    return TierAnalyticsFactory


@pytest.fixture
def governance_policy_factory():
    return GovernancePolicyFactory


@pytest.fixture
def rule_factory():
    return RuleFactory


@pytest.fixture
def rule_enforcement_result_factory():
    return RuleEnforcementResultFactory


@pytest.fixture
def dispute_factory():
    return DisputeFactory


@pytest.fixture
def dispute_resolution_factory():
    return DisputeResolutionFactory


@pytest.fixture
def governance_action_factory():
    return GovernanceActionFactory


@pytest.fixture
def governance_health_score_factory():
    return GovernanceHealthScoreFactory


@pytest.fixture
def governance_analytics_factory():
    return GovernanceAnalyticsFactory


@pytest.fixture
def governance_summary_factory():
    return GovernanceSummaryFactory


@pytest.fixture
def escalation_factory():
    return EscalationFactory


@pytest.fixture
def resolution_factory():
    return ResolutionFactory


@pytest.fixture
def sla_factory():
    return SLAFactory


@pytest.fixture
def sla_breach_factory():
    return SLABreachFactory


@pytest.fixture
def priority_factory():
    return PriorityFactory


@pytest.fixture
def priority_assessment_factory():
    return PriorityAssessmentFactory


@pytest.fixture
def escalation_analysis_factory():
    return EscalationAnalysisFactory


@pytest.fixture
def trend_report_factory():
    return TrendReportFactory


@pytest.fixture
def permission_factory():
    return PermissionFactory


@pytest.fixture
def role_factory():
    return RoleFactory


@pytest.fixture
def access_request_factory():
    return AccessRequestFactory


@pytest.fixture
def access_result_factory():
    return AccessResultFactory


@pytest.fixture
def access_audit_factory():
    return AccessAuditFactory


@pytest.fixture
def access_recommendation_factory():
    return AccessRecommendationFactory


@pytest.fixture
def reputation_score_factory():
    return ReputationScoreFactory


@pytest.fixture
def badge_factory():
    return BadgeFactory


@pytest.fixture
def trust_tier_factory():
    return TrustTierFactory


@pytest.fixture
def reputation_history_factory():
    return ReputationHistoryFactory


@pytest.fixture
def reputation_explanation_factory():
    return ReputationExplanationFactory


@pytest.fixture
def compliance_policy_factory():
    return CompliancePolicyFactory


@pytest.fixture
def violation_factory():
    return ViolationFactory


@pytest.fixture
def audit_report_factory():
    return AuditReportFactory


@pytest.fixture
def compliance_score_factory():
    return ComplianceScoreFactory


@pytest.fixture
def compliance_report_factory():
    return ComplianceReportFactory


@pytest.fixture
def remediation_action_factory():
    return RemediationActionFactory


@pytest.fixture
def identity_data_factory():
    return IdentityDataFactory


@pytest.fixture
def document_data_factory():
    return DocumentDataFactory


@pytest.fixture
def verification_request_factory():
    return VerificationRequestFactory


@pytest.fixture
def verification_result_factory():
    return VerificationResultFactory


@pytest.fixture
def trust_score_factory():
    return TrustScoreFactory


@pytest.fixture
def fraud_report_factory():
    return FraudReportFactory


@pytest.fixture
def document_verification_result_factory():
    return DocumentVerificationResultFactory


@pytest.fixture
def verification_explanation_factory():
    return VerificationExplanationFactory


@pytest.fixture
def moderation_item_factory():
    return ModerationItemFactory


@pytest.fixture
def queue_factory():
    return QueueFactory


@pytest.fixture
def priority_score_factory():
    from .factories import PriorityScoreFactory
    return PriorityScoreFactory


@pytest.fixture
def review_decision_factory():
    return ReviewDecisionFactory


@pytest.fixture
def moderation_escalation_factory():
    return ModerationEscalationFactory


@pytest.fixture
def queue_metrics_factory():
    return QueueMetricsFactory


@pytest.fixture
def moderation_analytics_factory():
    return ModerationAnalyticsFactory


@pytest.fixture
def trend_factory():
    return TrendFactory


@pytest.fixture
def moderator_performance_factory():
    return ModeratorPerformanceFactory


@pytest.fixture
def policy_effectiveness_factory():
    return PolicyEffectivenessFactory


@pytest.fixture
def moderation_prediction_factory():
    return ModerationPredictionFactory


@pytest.fixture
def analytics_summary_factory():
    return AnalyticsSummaryFactory


@pytest.fixture
def engagement_metrics_factory():
    return EngagementMetricsFactory


@pytest.fixture
def toxicity_report_factory():
    return ToxicityReportFactory


@pytest.fixture
def growth_analysis_factory():
    return GrowthAnalysisFactory


@pytest.fixture
def churn_prediction_factory():
    return ChurnPredictionFactory


@pytest.fixture
def health_score_factory():
    return HealthScoreFactory


@pytest.fixture
def health_explanation_factory():
    return HealthExplanationFactory


# ===========================================================================
# Seeder fixtures – pre-built batches
# ===========================================================================


@pytest.fixture
def tiers():
    """Pre-built list of Tier instances."""
    return seed_tiers()


@pytest.fixture
def tier_evaluations():
    return seed_tier_evaluations()


@pytest.fixture
def upgrade_requests():
    return seed_upgrade_requests()


@pytest.fixture
def access_policies():
    return seed_access_policies()


@pytest.fixture
def benefits():
    return seed_benefits()


@pytest.fixture
def tier_analytics():
    return seed_tier_analytics()


@pytest.fixture
def governance_policies():
    return seed_governance_policies()


@pytest.fixture
def rules():
    return seed_rules()


@pytest.fixture
def rule_enforcement_results():
    return seed_rule_enforcement_results()


@pytest.fixture
def disputes():
    return seed_disputes()


@pytest.fixture
def dispute_resolutions():
    return seed_dispute_resolutions()


@pytest.fixture
def governance_actions():
    return seed_governance_actions()


@pytest.fixture
def governance_health_scores():
    return seed_governance_health_scores()


@pytest.fixture
def governance_analytics():
    return seed_governance_analytics()


@pytest.fixture
def governance_summaries():
    return seed_governance_summaries()


@pytest.fixture
def escalations():
    return seed_escalations()


@pytest.fixture
def resolutions():
    return seed_resolutions()


@pytest.fixture
def slas():
    return seed_slas()


@pytest.fixture
def sla_breaches():
    return seed_sla_breaches()


@pytest.fixture
def priorities():
    from .seeders import seed_priorities
    return seed_priorities()


@pytest.fixture
def priority_assessments():
    return seed_priority_assessments()


@pytest.fixture
def escalation_analyses():
    return seed_escalation_analyses()


@pytest.fixture
def trend_reports():
    return seed_trend_reports()


@pytest.fixture
def permissions():
    return seed_permissions()


@pytest.fixture
def roles():
    return seed_roles()


@pytest.fixture
def access_requests():
    return seed_access_requests()


@pytest.fixture
def access_results():
    return seed_access_results()


@pytest.fixture
def access_audits():
    return seed_access_audits()


@pytest.fixture
def access_recommendations():
    return seed_access_recommendations()


@pytest.fixture
def reputation_scores():
    return seed_reputation_scores()


@pytest.fixture
def badges():
    return seed_badges()


@pytest.fixture
def trust_tiers():
    return seed_trust_tiers()


@pytest.fixture
def reputation_history():
    return seed_reputation_history()


@pytest.fixture
def reputation_explanations():
    return seed_reputation_explanations()


@pytest.fixture
def compliance_policies():
    return seed_compliance_policies()


@pytest.fixture
def violations():
    return seed_violations()


@pytest.fixture
def audit_reports():
    return seed_audit_reports()


@pytest.fixture
def compliance_scores():
    return seed_compliance_scores()


@pytest.fixture
def compliance_reports():
    return seed_compliance_reports()


@pytest.fixture
def remediation_actions():
    return seed_remediation_actions()


@pytest.fixture
def identity_data():
    return seed_identity_data()


@pytest.fixture
def document_data():
    return seed_document_data()


@pytest.fixture
def verification_requests():
    return seed_verification_requests()


@pytest.fixture
def verification_results():
    return seed_verification_results()


@pytest.fixture
def trust_scores():
    return seed_trust_scores()


@pytest.fixture
def fraud_reports():
    return seed_fraud_reports()


@pytest.fixture
def document_verification_results():
    return seed_document_verification_results()


@pytest.fixture
def verification_explanations():
    return seed_verification_explanations()


@pytest.fixture
def moderation_items():
    return seed_moderation_items()


@pytest.fixture
def queues():
    return seed_queues()


@pytest.fixture
def priority_scores():
    return seed_priority_scores()


@pytest.fixture
def review_decisions():
    return seed_review_decisions()


@pytest.fixture
def moderation_escalations():
    return seed_moderation_escalations()


@pytest.fixture
def queue_metrics():
    return seed_queue_metrics()


@pytest.fixture
def moderation_analytics():
    return seed_moderation_analytics()


@pytest.fixture
def trends():
    return seed_trends()


@pytest.fixture
def moderator_performance():
    return seed_moderator_performance()


@pytest.fixture
def policy_effectiveness():
    return seed_policy_effectiveness()


@pytest.fixture
def moderation_predictions():
    return seed_moderation_predictions()


@pytest.fixture
def analytics_summaries():
    return seed_analytics_summaries()


@pytest.fixture
def engagement_metrics():
    return seed_engagement_metrics()


@pytest.fixture
def toxicity_reports():
    return seed_toxicity_reports()


@pytest.fixture
def growth_analyses():
    return seed_growth_analyses()


@pytest.fixture
def churn_predictions():
    return seed_churn_predictions()


@pytest.fixture
def health_scores():
    return seed_health_scores()


@pytest.fixture
def health_explanations():
    return seed_health_explanations()


# ===========================================================================
# Full-database fixture
# ===========================================================================


@pytest.fixture
def seeded_database() -> dict[str, list[Any]]:
    """Seed all entities and return as a dictionary.

    Returns:
        Dictionary mapping entity names to lists of model instances.
    """
    from .seeders import seed_all

    return seed_all()

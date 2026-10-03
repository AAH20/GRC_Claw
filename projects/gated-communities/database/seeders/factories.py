"""
factory_boy factories for all gated-communities Pydantic models.

Each factory generates a valid Pydantic model instance with realistic
fake data.  Use ``factory_boy``'s ``PydanticModelFactory`` so that the
output is always a validated model instance, not a raw dict.

Usage
-----
>>> from database.seeders.factories import TierFactory
>>> tier = TierFactory()
>>> tier.name
'Gold Tier'
>>>
>>> # Override any field:
>>> tier = TierFactory(level="platinum", monthly_fee=99.99)
>>>
>>> # Create a batch:
>>> tiers = TierFactory.create_batch(5)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import factory
from factory import Faker, LazyFunction, Sequence, SubFactory
from factory.fuzzy import FuzzyChoice, FuzzyFloat, FuzzyInteger

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid4())


# ===========================================================================
# Tier Management  (tier_management.models.schemas)
# ===========================================================================


class TierFactory(factory.Factory):
    """Factory for :class:`Tier`."""

    class Meta:
        model = Any  # Pydantic model – set at bottom of file

    id = LazyFunction(uuid4)
    name = Sequence(lambda n: f"Tier {n}")
    level = FuzzyChoice(["bronze", "silver", "gold", "platinum", "diamond"])
    status = FuzzyChoice(["active", "inactive", "suspended", "pending", "expired"])
    description = Faker("sentence", nb_words=8)
    requirements = LazyFunction(lambda: {"min_score": FuzzyInteger(0, 100).fuzz()})
    benefits = Faker("words", nb=3)
    max_members = FuzzyInteger(10, 10_000)
    monthly_fee = FuzzyFloat(0.0, 500.0)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    metadata = LazyFunction(dict)


class TierEvaluationFactory(factory.Factory):
    """Factory for :class:`TierEvaluation`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    member_id = LazyFunction(uuid4)
    current_tier_id = LazyFunction(uuid4)
    target_tier_id = LazyFunction(uuid4)
    eligible = Faker("boolean")
    score = FuzzyFloat(0.0, 100.0)
    criteria_results = LazyFunction(dict)
    gaps = Faker("words", nb=2)
    recommendations = Faker("sentences", nb=2)
    evaluated_at = LazyFunction(_utcnow)
    evaluated_by = "TierEvaluatorAgent"
    confidence = FuzzyFloat(0.0, 1.0)


class UpgradeRequestFactory(factory.Factory):
    """Factory for :class:`UpgradeRequest`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    member_id = LazyFunction(uuid4)
    current_tier_id = LazyFunction(uuid4)
    target_tier_id = LazyFunction(uuid4)
    reason = Faker("sentence", nb_words=10)
    eligibility = FuzzyChoice(
        ["eligible", "not_eligible", "pending", "cooldown", "max_tier"]
    )
    status = "pending"
    requested_at = LazyFunction(_utcnow)
    processed_at = None
    processed_by = None
    denial_reason = None


class AccessPolicyFactory(factory.Factory):
    """Factory for :class:`AccessPolicy` (tier management)."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    name = Sequence(lambda n: f"Access Policy {n}")
    tier_id = LazyFunction(uuid4)
    resource = Faker("word")
    action = FuzzyChoice(["read", "write", "delete", "admin"])
    effect = FuzzyChoice(["granted", "denied", "pending_review", "conditional"])
    conditions = LazyFunction(dict)
    priority = FuzzyInteger(0, 100)
    enabled = True
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    expires_at = None


class BenefitFactory(factory.Factory):
    """Factory for :class:`Benefit`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    name = Sequence(lambda n: f"Benefit {n}")
    benefit_type = FuzzyChoice(
        [
            "percentage_discount",
            "fixed_discount",
            "free_shipping",
            "priority_support",
            "exclusive_access",
            "bonus_credits",
        ]
    )
    description = Faker("sentence", nb_words=6)
    value = FuzzyFloat(0.0, 100.0)
    tier_ids = LazyFunction(lambda: [uuid4()])
    active = True
    start_date = None
    end_date = None
    usage_limit = FuzzyInteger(1, 100)
    metadata = LazyFunction(dict)


class TierAnalyticsFactory(factory.Factory):
    """Factory for :class:`TierAnalytics`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    tier_id = LazyFunction(uuid4)
    period_start = LazyFunction(lambda: _utcnow() - timedelta(days=30))
    period_end = LazyFunction(_utcnow)
    total_members = FuzzyInteger(0, 10_000)
    active_members = FuzzyInteger(0, 5_000)
    new_members = FuzzyInteger(0, 500)
    churned_members = FuzzyInteger(0, 200)
    upgrade_requests = FuzzyInteger(0, 100)
    downgrade_requests = FuzzyInteger(0, 50)
    avg_engagement_score = FuzzyFloat(0.0, 100.0)
    revenue = FuzzyFloat(0.0, 100_000.0)
    metrics = LazyFunction(dict)
    insights = Faker("sentences", nb=2)
    generated_at = LazyFunction(_utcnow)
    generated_by = "TierAnalyticsAgent"


# ===========================================================================
# Community Governance  (community_governance.models)
# ===========================================================================


class GovernancePolicyFactory(factory.Factory):
    """Factory for :class:`Policy` (community governance)."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    name = Sequence(lambda n: f"Governance Policy {n}")
    description = Faker("paragraph", nb_sentences=2)
    status = FuzzyChoice(["draft", "active", "under_review", "deprecated", "archived"])
    scope = FuzzyChoice(["global", "community", "category", "user", "custom"])
    scope_target = None
    rules = LazyFunction(lambda: [uuid4()])
    guidelines = Faker("sentences", nb=3)
    enforcement_level = "standard"
    effective_date = None
    expiration_date = None
    metadata = LazyFunction(dict)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    created_by = None
    version = FuzzyInteger(1, 10)


class RuleFactory(factory.Factory):
    """Factory for :class:`Rule`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    name = Sequence(lambda n: f"Rule {n}")
    description = Faker("sentence", nb_words=8)
    category = FuzzyChoice(
        [
            "content_moderation",
            "user_conduct",
            "privacy",
            "security",
            "access_control",
            "compliance",
            "custom",
        ]
    )
    severity = FuzzyChoice(["low", "medium", "high", "critical"])
    conditions = LazyFunction(dict)
    actions = Faker("words", nb=3)
    is_active = True
    priority = FuzzyInteger(0, 100)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    created_by = None
    version = FuzzyInteger(1, 10)


class RuleEnforcementResultFactory(factory.Factory):
    """Factory for :class:`RuleEnforcementResult`."""

    class Meta:
        model = Any

    rule_id = LazyFunction(uuid4)
    rule_name = Sequence(lambda n: f"Rule {n}")
    action_id = LazyFunction(uuid4)
    is_violation = Faker("boolean")
    severity = FuzzyChoice(["low", "medium", "high", "critical"])
    message = Faker("sentence", nb_words=10)
    details = LazyFunction(dict)
    enforced_at = LazyFunction(_utcnow)
    recommended_actions = Faker("words", nb=2)


class DisputeFactory(factory.Factory):
    """Factory for :class:`Dispute`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    title = Faker("sentence", nb_words=6)
    description = Faker("paragraph", nb_sentences=2)
    status = FuzzyChoice(
        ["open", "under_review", "mediation", "resolved", "closed", "escalated"]
    )
    priority = FuzzyChoice(["low", "medium", "high", "urgent"])
    category = Faker("word")
    initiator_id = LazyFunction(_uuid)
    respondent_id = LazyFunction(_uuid)
    assigned_mediator_id = None
    related_action_id = None
    resolution = None
    metadata = LazyFunction(dict)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    resolved_at = None


class DisputeResolutionFactory(factory.Factory):
    """Factory for :class:`DisputeResolution`."""

    class Meta:
        model = Any

    resolution_type = FuzzyChoice(
        ["mediation", "arbitration", "vote", "admin_decision"]
    )
    outcome = Faker("sentence", nb_words=8)
    rationale = Faker("paragraph", nb_sentences=2)
    conditions = Faker("words", nb=3)
    resolved_by = LazyFunction(_uuid)
    resolved_at = LazyFunction(_utcnow)
    follow_up_required = Faker("boolean")
    follow_up_date = None


class GovernanceActionFactory(factory.Factory):
    """Factory for :class:`GovernanceAction`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    action_type = FuzzyChoice(
        [
            "create",
            "update",
            "delete",
            "approve",
            "reject",
            "flag",
            "escalate",
            "resolve",
        ]
    )
    target_id = LazyFunction(_uuid)
    target_type = Faker("word")
    actor_id = LazyFunction(_uuid)
    reason = Faker("sentence", nb_words=8)
    metadata = LazyFunction(dict)
    status = FuzzyChoice(
        ["pending", "in_review", "approved", "rejected", "escalated", "resolved"]
    )
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    resolved_at = None
    resolution_notes = None


class GovernanceHealthScoreFactory(factory.Factory):
    """Factory for :class:`GovernanceHealthScore`."""

    class Meta:
        model = Any

    overall_score = FuzzyFloat(0.0, 100.0)
    rule_compliance_rate = FuzzyFloat(0.0, 100.0)
    dispute_resolution_rate = FuzzyFloat(0.0, 100.0)
    policy_adherence_rate = FuzzyFloat(0.0, 100.0)
    average_resolution_time_hours = FuzzyFloat(0.0, 72.0)
    active_violations_count = FuzzyInteger(0, 100)
    pending_disputes_count = FuzzyInteger(0, 50)
    calculated_at = LazyFunction(_utcnow)


class GovernanceAnalyticsFactory(factory.Factory):
    """Factory for :class:`GovernanceAnalytics`."""

    class Meta:
        model = Any

    period_start = LazyFunction(lambda: _utcnow() - timedelta(days=30))
    period_end = LazyFunction(_utcnow)
    total_actions = FuzzyInteger(0, 10_000)
    total_rules = FuzzyInteger(0, 100)
    total_disputes = FuzzyInteger(0, 500)
    total_policies = FuzzyInteger(0, 50)
    violations_by_category = LazyFunction(dict)
    disputes_by_status = LazyFunction(dict)
    actions_by_type = LazyFunction(dict)
    top_violated_rules = LazyFunction(list)
    resolution_time_trend = LazyFunction(list)
    health_score = SubFactory(GovernanceHealthScoreFactory)
    recommendations = Faker("sentences", nb=2)
    generated_at = LazyFunction(_utcnow)


class GovernanceSummaryFactory(factory.Factory):
    """Factory for :class:`GovernanceSummary`."""

    class Meta:
        model = Any

    total_active_rules = FuzzyInteger(0, 100)
    total_active_policies = FuzzyInteger(0, 50)
    open_disputes = FuzzyInteger(0, 100)
    pending_actions = FuzzyInteger(0, 200)
    violations_last_24h = FuzzyInteger(0, 50)
    health_score = FuzzyFloat(0.0, 100.0)
    last_updated = LazyFunction(_utcnow)


# ===========================================================================
# Escalation Workflow  (escalation_workflow.models)
# ===========================================================================


class EscalationFactory(factory.Factory):
    """Factory for :class:`Escalation`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    title = Faker("sentence", nb_words=8)
    description = Faker("paragraph", nb_sentences=3)
    status = FuzzyChoice(
        [
            "pending",
            "routed",
            "in_progress",
            "waiting",
            "resolved",
            "closed",
            "cancelled",
        ]
    )
    priority = FuzzyChoice(["critical", "high", "medium", "low"])
    category = Faker("word")
    source = FuzzyChoice(["api", "webhook", "manual", "system"])
    assignee = None
    requester = LazyFunction(_uuid)
    tags = Faker("words", nb=3)
    metadata = LazyFunction(dict)
    sla_id = None
    resolution_id = None
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    resolved_at = None
    due_at = None


class ResolutionFactory(factory.Factory):
    """Factory for :class:`Resolution`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    escalation_id = LazyFunction(uuid4)
    title = Faker("sentence", nb_words=8)
    description = Faker("paragraph", nb_sentences=2)
    status = FuzzyChoice(
        [
            "proposed",
            "approved",
            "in_progress",
            "implemented",
            "verified",
            "rejected",
            "rolled_back",
        ]
    )
    resolution_type = FuzzyChoice(["manual", "automated", "hybrid"])
    root_cause = Faker("sentence", nb_words=10)
    steps = Faker("sentences", nb=3)
    automated = Faker("boolean")
    confidence = FuzzyFloat(0.0, 1.0)
    verified_by = None
    verified_at = None
    metadata = LazyFunction(dict)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    completed_at = None


class SLAFactory(factory.Factory):
    """Factory for :class:`SLA`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    escalation_id = LazyFunction(uuid4)
    priority = FuzzyChoice(["critical", "high", "medium", "low"])
    response_time_minutes = FuzzyInteger(1, 1440)
    resolution_time_minutes = FuzzyInteger(1, 10_080)
    status = FuzzyChoice(["active", "at_risk", "breached", "met", "paused"])
    started_at = LazyFunction(_utcnow)
    response_deadline = LazyFunction(lambda: _utcnow() + timedelta(hours=1))
    resolution_deadline = LazyFunction(lambda: _utcnow() + timedelta(hours=4))
    responded_at = None
    resolved_at = None
    elapsed_minutes = FuzzyFloat(0.0, 1000.0)
    remaining_minutes = FuzzyFloat(0.0, 1000.0)
    breach_count = FuzzyInteger(0, 5)
    breaches = LazyFunction(list)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)


class SLABreachFactory(factory.Factory):
    """Factory for :class:`SLABreach`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    sla_id = LazyFunction(uuid4)
    escalation_id = LazyFunction(uuid4)
    breached_at = LazyFunction(_utcnow)
    minutes_overdue = FuzzyFloat(0.0, 1440.0)
    severity = FuzzyChoice(["low", "medium", "high", "critical"])
    acknowledged = False
    acknowledged_by = None
    acknowledged_at = None
    notes = ""


class PriorityFactory(factory.Factory):
    """Factory for :class:`Priority`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    level = FuzzyChoice(["critical", "high", "medium", "low"])
    name = Sequence(lambda n: f"Priority {n}")
    description = Faker("sentence", nb_words=6)
    sla_minutes = FuzzyInteger(1, 1440)
    escalation_threshold = FuzzyInteger(1, 10)
    notification_channels = Faker("words", nb=2)
    routing_rules = LazyFunction(dict)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)


class PriorityAssessmentFactory(factory.Factory):
    """Factory for :class:`PriorityAssessment`."""

    class Meta:
        model = Any

    escalation_id = LazyFunction(uuid4)
    assessed_priority = FuzzyChoice(["critical", "high", "medium", "low"])
    confidence = FuzzyFloat(0.0, 1.0)
    reasoning = Faker("sentence", nb_words=10)
    factors = LazyFunction(dict)
    recommended_sla_minutes = FuzzyInteger(1, 1440)
    assessed_at = LazyFunction(_utcnow)


class EscalationAnalysisFactory(factory.Factory):
    """Factory for :class:`EscalationAnalysis`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    escalation_id = None
    analysis_type = FuzzyChoice(["single", "batch", "trend"])
    summary = Faker("paragraph", nb_sentences=2)
    patterns = LazyFunction(
        lambda: [
            FuzzyChoice(
                [
                    "recurring",
                    "seasonal",
                    "dependency",
                    "capacity",
                    "configuration",
                    "external",
                ]
            ).fuzz()
            for _ in range(FuzzyInteger(1, 3).fuzz())
        ]
    )
    risk_score = FuzzyFloat(0.0, 1.0)
    impact_assessment = Faker("sentence", nb_words=10)
    recommendations = Faker("sentences", nb=2)
    related_escalations = LazyFunction(lambda: [uuid4()])
    metrics = LazyFunction(dict)
    analyzed_at = LazyFunction(_utcnow)
    created_at = LazyFunction(_utcnow)


class TrendReportFactory(factory.Factory):
    """Factory for :class:`TrendReport`."""

    class Meta:
        model = Any

    period_start = LazyFunction(lambda: _utcnow() - timedelta(days=30))
    period_end = LazyFunction(_utcnow)
    total_escalations = FuzzyInteger(0, 10_000)
    resolved_count = FuzzyInteger(0, 5_000)
    breached_count = FuzzyInteger(0, 500)
    avg_resolution_minutes = FuzzyFloat(0.0, 10_000.0)
    top_categories = LazyFunction(dict)
    priority_distribution = LazyFunction(dict)
    pattern_summary = LazyFunction(dict)


# ===========================================================================
# Access Control  (access_control.models)
# ===========================================================================


class PermissionFactory(factory.Factory):
    """Factory for :class:`Permission`."""

    class Meta:
        model = Any

    resource = Faker("word")
    action = FuzzyChoice(["read", "write", "delete", "admin"])
    conditions = LazyFunction(dict)
    effect = FuzzyChoice(["allow", "deny"])


class RoleFactory(factory.Factory):
    """Factory for :class:`Role`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    name = Sequence(lambda n: f"Role {n}")
    description = Faker("sentence", nb_words=6)
    permissions = LazyFunction(lambda: [PermissionFactory()])
    status = FuzzyChoice(["active", "inactive", "deprecated", "pending"])
    metadata = LazyFunction(dict)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)


class AccessRequestFactory(factory.Factory):
    """Factory for :class:`AccessRequest`."""

    class Meta:
        model = Any

    principal_id = LazyFunction(_uuid)
    resource = Faker("word")
    action = FuzzyChoice(["read", "write", "delete", "admin"])
    context = LazyFunction(dict)
    roles = LazyFunction(lambda: [str(uuid4())])


class AccessResultFactory(factory.Factory):
    """Factory for :class:`AccessResult`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    request = SubFactory(AccessRequestFactory)
    decision = FuzzyChoice(["allow", "deny", "conditional", "abstain"])
    reason = Faker("sentence", nb_words=8)
    obligations = Faker("words", nb=2)
    evaluated_at = LazyFunction(_utcnow)
    policy_ids = LazyFunction(lambda: [str(uuid4())])
    confidence = FuzzyFloat(0.0, 1.0)


class AccessAuditFactory(factory.Factory):
    """Factory for :class:`AccessAudit`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    principal_id = LazyFunction(_uuid)
    action = FuzzyChoice(["read", "write", "delete", "admin"])
    resource = Faker("word")
    decision = FuzzyChoice(["allow", "deny", "conditional", "abstain"])
    severity = FuzzyChoice(["info", "warning", "error", "critical"])
    details = LazyFunction(dict)
    ip_address = Faker("ipv4")
    user_agent = Faker("user_agent")
    timestamp = LazyFunction(_utcnow)


class AccessRecommendationFactory(factory.Factory):
    """Factory for :class:`AccessRecommendation`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    principal_id = LazyFunction(_uuid)
    resource = Faker("word")
    action = FuzzyChoice(["read", "write", "delete", "admin"])
    recommendation = FuzzyChoice(["grant", "revoke", "modify", "review"])
    reason = Faker("sentence", nb_words=8)
    confidence = FuzzyFloat(0.0, 1.0)
    created_at = LazyFunction(_utcnow)


# ===========================================================================
# Reputation System  (reputation_system.models)
# ===========================================================================


class ReputationScoreFactory(factory.Factory):
    """Factory for :class:`ReputationScore`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    member_id = LazyFunction(_uuid)
    score = FuzzyInteger(0, 1000)
    trust_tier = FuzzyChoice(["bronze", "silver", "gold", "platinum", "diamond"])
    badge_count = FuzzyInteger(0, 50)
    total_contributions = FuzzyInteger(0, 10_000)
    positive_feedback = FuzzyInteger(0, 5_000)
    negative_feedback = FuzzyInteger(0, 1_000)
    last_activity_at = LazyFunction(_utcnow)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    metadata = LazyFunction(dict)


class BadgeFactory(factory.Factory):
    """Factory for :class:`Badge`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    name = Sequence(lambda n: f"Badge {n}")
    description = Faker("sentence", nb_words=8)
    category = FuzzyChoice(
        ["contribution", "quality", "community", "expertise", "special"]
    )
    icon_url = None
    criteria = LazyFunction(dict)
    points = FuzzyInteger(0, 100)
    is_active = True
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)


class TrustTierFactory(factory.Factory):
    """Factory for :class:`TrustTier`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    level = FuzzyChoice(["bronze", "silver", "gold", "platinum", "diamond"])
    name = Sequence(lambda n: f"Trust Tier {n}")
    description = Faker("sentence", nb_words=8)
    min_score = FuzzyInteger(0, 500)
    max_score = FuzzyInteger(501, 1000)
    benefits = Faker("words", nb=3)
    requirements = LazyFunction(dict)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)


class ReputationHistoryFactory(factory.Factory):
    """Factory for :class:`ReputationHistory`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    member_id = LazyFunction(_uuid)
    action = Faker("word")
    score_change = FuzzyInteger(-100, 100)
    previous_score = FuzzyInteger(0, 1000)
    new_score = FuzzyInteger(0, 1000)
    badge_id = None
    reason = Faker("sentence", nb_words=8)
    metadata = LazyFunction(dict)
    created_at = LazyFunction(_utcnow)


class ReputationExplanationFactory(factory.Factory):
    """Factory for :class:`ReputationExplanation`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    member_id = LazyFunction(_uuid)
    explanation = Faker("paragraph", nb_sentences=2)
    factors = LazyFunction(list)
    recommendations = Faker("sentences", nb=2)
    confidence = FuzzyFloat(0.0, 1.0)
    created_at = LazyFunction(_utcnow)


# ===========================================================================
# Compliance Monitor  (compliance_monitor.models)
# ===========================================================================


class CompliancePolicyFactory(factory.Factory):
    """Factory for :class:`Policy` (compliance monitor)."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    name = Sequence(lambda n: f"Compliance Policy {n}")
    description = Faker("paragraph", nb_sentences=2)
    category = Faker("word")
    status = FuzzyChoice(["draft", "active", "suspended", "archived"])
    version = "1.0.0"
    effective_date = LazyFunction(_utcnow)
    rules = Faker("words", nb=3)
    metadata = LazyFunction(dict)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)


class ViolationFactory(factory.Factory):
    """Factory for :class:`Violation`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    policy_id = LazyFunction(uuid4)
    title = Faker("sentence", nb_words=8)
    description = Faker("paragraph", nb_sentences=2)
    severity = FuzzyChoice(["low", "medium", "high", "critical"])
    status = FuzzyChoice(
        ["open", "acknowledged", "in_remediation", "resolved", "closed"]
    )
    detected_at = LazyFunction(_utcnow)
    resolved_at = None
    evidence = Faker("sentences", nb=2)
    remediation_actions = LazyFunction(lambda: [uuid4()])
    assignee = None
    metadata = LazyFunction(dict)


class AuditReportFactory(factory.Factory):
    """Factory for :class:`AuditReport`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    title = Faker("sentence", nb_words=8)
    description = Faker("paragraph", nb_sentences=2)
    period_start = LazyFunction(lambda: _utcnow() - timedelta(days=30))
    period_end = LazyFunction(_utcnow)
    findings = Faker("sentences", nb=3)
    policies_reviewed = LazyFunction(lambda: [uuid4()])
    violations_found = LazyFunction(lambda: [uuid4()])
    overall_score = FuzzyFloat(0.0, 100.0)
    recommendations = Faker("sentences", nb=2)
    generated_at = LazyFunction(_utcnow)
    generated_by = "AuditReporterAgent"


class ComplianceScoreFactory(factory.Factory):
    """Factory for :class:`ComplianceScore`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    policy_id = LazyFunction(uuid4)
    domain = Faker("word")
    score = FuzzyFloat(0.0, 100.0)
    max_score = 100.0
    factors = LazyFunction(dict)
    computed_at = LazyFunction(_utcnow)
    trend = FuzzyChoice(["improving", "declining", "stable"])
    previous_score = None


class ComplianceReportFactory(factory.Factory):
    """Factory for :class:`ComplianceReport`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    organization = Faker("company")
    period_start = LazyFunction(lambda: _utcnow() - timedelta(days=30))
    period_end = LazyFunction(_utcnow)
    policies = LazyFunction(list)
    violations = LazyFunction(list)
    scores = LazyFunction(list)
    audit_reports = LazyFunction(lambda: [uuid4()])
    overall_compliance_score = FuzzyFloat(0.0, 100.0)
    risk_level = FuzzyChoice(["low", "medium", "high", "critical"])
    executive_summary = Faker("paragraph", nb_sentences=2)
    generated_at = LazyFunction(_utcnow)


class RemediationActionFactory(factory.Factory):
    """Factory for :class:`RemediationAction`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    violation_id = LazyFunction(uuid4)
    action_type = Faker("word")
    description = Faker("sentence", nb_words=10)
    status = FuzzyChoice(["pending", "in_progress", "completed", "failed"])
    executed_at = None
    result = None
    error_message = None


# ===========================================================================
# Member Verification  (member_verification.models)
# ===========================================================================


class IdentityDataFactory(factory.Factory):
    """Factory for :class:`IdentityData`."""

    class Meta:
        model = Any

    full_name = Faker("name")
    date_of_birth = LazyFunction(
        lambda: f"{FuzzyInteger(1935, 2007).fuzz()}-{FuzzyInteger(1, 12).fuzz():02d}-{FuzzyInteger(1, 28).fuzz():02d}"
    )
    email = Faker("email")
    phone = Faker("phone_number")
    address = Faker("address")
    government_id = None


class DocumentDataFactory(factory.Factory):
    """Factory for :class:`DocumentData`."""

    class Meta:
        model = Any

    document_type = FuzzyChoice(
        [
            "passport",
            "drivers_license",
            "national_id",
            "utility_bill",
            "bank_statement",
        ]
    )
    document_number = Faker("bothify", text="??-########")
    issuing_country = Faker("country_code")
    issue_date = None
    expiry_date = None
    document_hash = None


class VerificationRequestFactory(factory.Factory):
    """Factory for :class:`VerificationRequest`."""

    class Meta:
        model = Any

    request_id = LazyFunction(uuid4)
    member_id = LazyFunction(_uuid)
    identity = SubFactory(IdentityDataFactory)
    documents = LazyFunction(lambda: [DocumentDataFactory()])
    metadata = LazyFunction(dict)
    callback_url = None
    priority = FuzzyChoice(["low", "normal", "high", "urgent"])


class VerificationResultFactory(factory.Factory):
    """Factory for :class:`VerificationResult`."""

    class Meta:
        model = Any

    request_id = LazyFunction(uuid4)
    member_id = LazyFunction(_uuid)
    status = FuzzyChoice(
        ["pending", "in_progress", "verified", "rejected", "needs_review", "expired"]
    )
    confidence = FuzzyFloat(0.0, 1.0)
    trust_score = FuzzyFloat(0.0, 1.0)
    fraud_risk = FuzzyFloat(0.0, 1.0)
    risk_level = FuzzyChoice(["low", "medium", "high", "critical"])
    verified_at = LazyFunction(_utcnow)
    expires_at = None
    checks_performed = Faker("words", nb=3)
    failure_reasons = LazyFunction(list)
    metadata = LazyFunction(dict)


class TrustScoreFactory(factory.Factory):
    """Factory for :class:`TrustScore`."""

    class Meta:
        model = Any

    member_id = LazyFunction(_uuid)
    score = FuzzyFloat(0.0, 1.0)
    level = FuzzyChoice(["low", "medium", "high", "critical"])
    factors = LazyFunction(dict)
    history = LazyFunction(list)
    calculated_at = LazyFunction(_utcnow)
    next_review_at = None


class FraudReportFactory(factory.Factory):
    """Factory for :class:`FraudReport`."""

    class Meta:
        model = Any

    member_id = LazyFunction(_uuid)
    risk_score = FuzzyFloat(0.0, 1.0)
    risk_level = FuzzyChoice(["low", "medium", "high", "critical"])
    flags = LazyFunction(list)
    matched_patterns = Faker("words", nb=2)
    recommendation = FuzzyChoice(["allow", "review", "block"])
    checked_at = LazyFunction(_utcnow)
    check_depth = FuzzyChoice(["basic", "standard", "deep"])


class DocumentVerificationResultFactory(factory.Factory):
    """Factory for :class:`DocumentVerificationResult`."""

    class Meta:
        model = Any

    document_type = FuzzyChoice(
        [
            "passport",
            "drivers_license",
            "national_id",
            "utility_bill",
            "bank_statement",
        ]
    )
    is_authentic = Faker("boolean")
    confidence = FuzzyFloat(0.0, 1.0)
    tampering_detected = False
    expiry_status = FuzzyChoice(["valid", "expired", "expiring_soon", "unknown"])
    cross_reference_match = None
    issues = LazyFunction(list)
    verified_at = LazyFunction(_utcnow)


class VerificationExplanationFactory(factory.Factory):
    """Factory for :class:`VerificationExplanation`."""

    class Meta:
        model = Any

    request_id = LazyFunction(uuid4)
    summary = Faker("paragraph", nb_sentences=2)
    factors = LazyFunction(list)
    recommendations = Faker("sentences", nb=2)
    appeal_process = None
    generated_at = LazyFunction(_utcnow)
    detail_level = FuzzyChoice(["summary", "detailed", "technical"])


# ===========================================================================
# Moderation Queue  (moderation_queue.models)
# ===========================================================================


class ModerationItemFactory(factory.Factory):
    """Factory for :class:`ModerationItem`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    content = Faker("paragraph", nb_sentences=3)
    content_type = FuzzyChoice(
        ["text", "image", "video", "audio", "comment", "post", "message"]
    )
    author_id = LazyFunction(_uuid)
    status = FuzzyChoice(
        ["pending", "in_review", "approved", "rejected", "escalated", "auto_moderated"]
    )
    queue_id = None
    priority_score = None
    priority_level = None
    metadata = LazyFunction(dict)
    tags = Faker("words", nb=3)
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)
    reviewed_at = None
    reviewer_id = None
    review_notes = None


class QueueFactory(factory.Factory):
    """Factory for :class:`Queue`."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    name = Sequence(lambda n: f"Queue {n}")
    description = Faker("sentence", nb_words=8)
    content_types = LazyFunction(
        lambda: [
            FuzzyChoice(
                ["text", "image", "video", "audio", "comment", "post", "message"]
            ).fuzz()
            for _ in range(FuzzyInteger(1, 4).fuzz())
        ]
    )
    max_size = FuzzyInteger(100, 10_000)
    priority_weights = LazyFunction(dict)
    assigned_reviewers = LazyFunction(lambda: [_uuid()])
    is_active = True
    created_at = LazyFunction(_utcnow)
    updated_at = LazyFunction(_utcnow)


class PriorityScoreFactory(factory.Factory):
    """Factory for :class:`PriorityScore`."""

    class Meta:
        model = Any

    item_id = LazyFunction(uuid4)
    score = FuzzyFloat(0.0, 1.0)
    level = FuzzyChoice(["low", "medium", "high", "critical"])
    factors = LazyFunction(dict)
    reasoning = Faker("sentence", nb_words=10)
    confidence = FuzzyFloat(0.0, 1.0)
    scored_at = LazyFunction(_utcnow)
    model_version = "1.0"


class ReviewDecisionFactory(factory.Factory):
    """Factory for :class:`ReviewDecision`."""

    class Meta:
        model = Any

    item_id = LazyFunction(uuid4)
    reviewer_id = LazyFunction(_uuid)
    decision = FuzzyChoice(["approve", "reject", "escalate", "request_info"])
    confidence = FuzzyFloat(0.0, 1.0)
    notes = Faker("sentence", nb_words=8)
    categories = Faker("words", nb=2)
    created_at = LazyFunction(_utcnow)


class ModerationEscalationFactory(factory.Factory):
    """Factory for :class:`Escalation` (moderation queue)."""

    class Meta:
        model = Any

    id = LazyFunction(uuid4)
    item_id = LazyFunction(uuid4)
    reason = Faker("sentence", nb_words=10)
    from_queue_id = None
    to_queue_id = None
    assigned_to = None
    priority = FuzzyChoice(["low", "medium", "high", "critical"])
    status = FuzzyChoice(["open", "in_progress", "resolved", "closed"])
    metadata = LazyFunction(dict)
    created_at = LazyFunction(_utcnow)
    resolved_at = None


class QueueMetricsFactory(factory.Factory):
    """Factory for :class:`QueueMetrics`."""

    class Meta:
        model = Any

    queue_id = LazyFunction(uuid4)
    total_items = FuzzyInteger(0, 10_000)
    pending_items = FuzzyInteger(0, 5_000)
    in_review_items = FuzzyInteger(0, 1_000)
    resolved_items = FuzzyInteger(0, 5_000)
    avg_resolution_time_seconds = FuzzyFloat(0.0, 10_000.0)
    oldest_item_age_seconds = FuzzyFloat(0.0, 100_000.0)
    updated_at = LazyFunction(_utcnow)


# ===========================================================================
# Moderation Analytics  (moderation_analytics.models)
# ===========================================================================


class ModerationAnalyticsFactory(factory.Factory):
    """Factory for :class:`ModerationAnalytics`."""

    class Meta:
        model = Any

    total_events = FuzzyInteger(0, 100_000)
    total_actions = FuzzyInteger(0, 50_000)
    action_breakdown = LazyFunction(dict)
    severity_distribution = LazyFunction(dict)
    average_response_time_seconds = FuzzyFloat(0.0, 10_000.0)
    period_start = LazyFunction(lambda: _utcnow() - timedelta(days=30))
    period_end = LazyFunction(_utcnow)
    metadata = LazyFunction(dict)


class TrendFactory(factory.Factory):
    """Factory for :class:`Trend`."""

    class Meta:
        model = Any

    metric_name = Faker("word")
    direction = FuzzyChoice(["increasing", "decreasing", "stable", "volatile"])
    change_percentage = FuzzyFloat(-100.0, 100.0)
    confidence = FuzzyFloat(0.0, 1.0)
    data_points = LazyFunction(
        lambda: [FuzzyFloat(0.0, 100.0).fuzz() for _ in range(5)]
    )
    start_date = LazyFunction(lambda: _utcnow() - timedelta(days=30))
    end_date = LazyFunction(_utcnow)
    description = Faker("sentence", nb_words=8)


class ModeratorPerformanceFactory(factory.Factory):
    """Factory for :class:`ModeratorPerformance`."""

    class Meta:
        model = Any

    moderator_id = LazyFunction(_uuid)
    moderator_name = Faker("name")
    total_reviews = FuzzyInteger(0, 10_000)
    accuracy = FuzzyFloat(0.0, 1.0)
    average_response_time_seconds = FuzzyFloat(0.0, 10_000.0)
    consistency_score = FuzzyFloat(0.0, 1.0)
    escalation_rate = FuzzyFloat(0.0, 1.0)
    period_start = LazyFunction(lambda: _utcnow() - timedelta(days=30))
    period_end = LazyFunction(_utcnow)
    strengths = Faker("sentences", nb=2)
    weaknesses = Faker("sentences", nb=2)
    recommendations = Faker("sentences", nb=2)


class PolicyEffectivenessFactory(factory.Factory):
    """Factory for :class:`PolicyEffectiveness`."""

    class Meta:
        model = Any

    policy_id = LazyFunction(_uuid)
    policy_name = Sequence(lambda n: f"Policy {n}")
    policy_version = "1.0.0"
    total_violations = FuzzyInteger(0, 10_000)
    total_enforcements = FuzzyInteger(0, 5_000)
    detection_rate = FuzzyFloat(0.0, 1.0)
    false_positive_rate = FuzzyFloat(0.0, 1.0)
    false_negative_rate = FuzzyFloat(0.0, 1.0)
    user_appeal_rate = FuzzyFloat(0.0, 1.0)
    appeal_success_rate = FuzzyFloat(0.0, 1.0)
    period_start = LazyFunction(lambda: _utcnow() - timedelta(days=30))
    period_end = LazyFunction(_utcnow)
    effectiveness_score = FuzzyFloat(0.0, 1.0)
    recommendations = Faker("sentences", nb=2)


class ModerationPredictionFactory(factory.Factory):
    """Factory for :class:`ModerationPrediction`."""

    class Meta:
        model = Any

    prediction_type = FuzzyChoice(["workload", "risk", "trend"])
    target_date = LazyFunction(lambda: _utcnow() + timedelta(days=7))
    predicted_value = FuzzyFloat(0.0, 10_000.0)
    confidence_interval = LazyFunction(
        lambda: (FuzzyFloat(0.0, 50.0).fuzz(), FuzzyFloat(50.0, 100.0).fuzz())
    )
    confidence = FuzzyFloat(0.0, 1.0)
    factors = Faker("words", nb=3)
    model_version = "v1"
    created_at = LazyFunction(_utcnow)


class AnalyticsSummaryFactory(factory.Factory):
    """Factory for :class:`AnalyticsSummary`."""

    class Meta:
        model = Any

    analytics = SubFactory(ModerationAnalyticsFactory)
    trends = LazyFunction(lambda: [TrendFactory()])
    top_moderators = LazyFunction(lambda: [ModeratorPerformanceFactory()])
    policy_scores = LazyFunction(lambda: [PolicyEffectivenessFactory()])
    predictions = LazyFunction(lambda: [ModerationPredictionFactory()])
    generated_at = LazyFunction(_utcnow)
    summary_text = Faker("paragraph", nb_sentences=2)


# ===========================================================================
# Community Health Scorer  (community_health_scorer.models)
# ===========================================================================


class EngagementMetricsFactory(factory.Factory):
    """Factory for :class:`EngagementMetrics`."""

    class Meta:
        model = Any

    dau = FuzzyInteger(0, 10_000)
    mau = FuzzyInteger(10_001, 100_000)
    avg_session_duration_minutes = FuzzyFloat(0.0, 120.0)
    avg_sessions_per_user = FuzzyFloat(0.0, 10.0)
    interaction_depth = FuzzyFloat(0.0, 1.0)
    content_creation_rate = FuzzyFloat(0.0, 1.0)
    response_rate = FuzzyFloat(0.0, 1.0)
    retention_rate_7d = FuzzyFloat(0.0, 1.0)
    retention_rate_30d = FuzzyFloat(0.0, 1.0)
    engagement_level = FuzzyChoice(
        [
            "highly_engaged",
            "engaged",
            "moderately_engaged",
            "low_engagement",
            "disengaged",
        ]
    )
    score = FuzzyFloat(0.0, 100.0)


class ToxicityReportFactory(factory.Factory):
    """Factory for :class:`ToxicityReport`."""

    class Meta:
        model = Any

    overall_toxicity_score = FuzzyFloat(0.0, 100.0)
    toxicity_level = FuzzyChoice(["none", "low", "moderate", "high", "severe"])
    toxic_content_count = FuzzyInteger(0, 1_000)
    total_content_analyzed = FuzzyInteger(1_001, 100_000)
    toxic_user_count = FuzzyInteger(0, 100)
    total_users = FuzzyInteger(101, 10_000)
    toxicity_categories = LazyFunction(dict)
    flagged_content = LazyFunction(list)
    recommendations = Faker("sentences", nb=2)
    score = FuzzyFloat(0.0, 100.0)


class GrowthAnalysisFactory(factory.Factory):
    """Factory for :class:`GrowthAnalysis`."""

    class Meta:
        model = Any

    current_members = FuzzyInteger(0, 100_000)
    new_members_7d = FuzzyInteger(0, 1_000)
    new_members_30d = FuzzyInteger(0, 5_000)
    churned_members_7d = FuzzyInteger(0, 500)
    churned_members_30d = FuzzyInteger(0, 2_000)
    growth_rate_7d = FuzzyFloat(-100.0, 100.0)
    growth_rate_30d = FuzzyFloat(-100.0, 100.0)
    net_growth_rate = FuzzyFloat(-100.0, 100.0)
    growth_trend = FuzzyChoice(
        [
            "rapid_growth",
            "steady_growth",
            "stable",
            "slow_decline",
            "rapid_decline",
        ]
    )
    projected_members_30d = FuzzyInteger(0, 150_000)
    projected_members_90d = FuzzyInteger(0, 200_000)
    acquisition_channels = LazyFunction(dict)
    score = FuzzyFloat(0.0, 100.0)


class ChurnPredictionFactory(factory.Factory):
    """Factory for :class:`ChurnPrediction`."""

    class Meta:
        model = Any

    overall_churn_risk = FuzzyChoice(
        ["very_low", "low", "moderate", "high", "very_high"]
    )
    churn_probability = FuzzyFloat(0.0, 1.0)
    at_risk_members = FuzzyInteger(0, 5_000)
    total_members = FuzzyInteger(5_001, 100_000)
    risk_factors = LazyFunction(list)
    protective_factors = LazyFunction(list)
    predicted_churn_rate_30d = FuzzyFloat(0.0, 1.0)
    predicted_churn_rate_90d = FuzzyFloat(0.0, 1.0)
    segment_risk = LazyFunction(dict)
    recommendations = Faker("sentences", nb=2)
    score = FuzzyFloat(0.0, 100.0)


class HealthScoreFactory(factory.Factory):
    """Factory for :class:`HealthScore`."""

    class Meta:
        model = Any

    community_id = LazyFunction(_uuid)
    overall_score = FuzzyFloat(0.0, 100.0)
    category = None
    engagement_score = FuzzyFloat(0.0, 100.0)
    toxicity_score = FuzzyFloat(0.0, 100.0)
    growth_score = FuzzyFloat(0.0, 100.0)
    churn_score = FuzzyFloat(0.0, 100.0)
    engagement_weight = 0.30
    toxicity_weight = 0.25
    growth_weight = 0.25
    churn_weight = 0.20
    timestamp = LazyFunction(_utcnow)
    period_start = None
    period_end = None
    metadata = LazyFunction(dict)


class HealthExplanationFactory(factory.Factory):
    """Factory for :class:`HealthExplanation`."""

    class Meta:
        model = Any

    community_id = LazyFunction(_uuid)
    summary = Faker("paragraph", nb_sentences=2)
    engagement_summary = Faker("sentence", nb_words=10)
    toxicity_summary = Faker("sentence", nb_words=10)
    growth_summary = Faker("sentence", nb_words=10)
    churn_summary = Faker("sentence", nb_words=10)
    key_strengths = Faker("sentences", nb=2)
    key_concerns = Faker("sentences", nb=2)
    actionable_recommendations = LazyFunction(list)
    generated_at = LazyFunction(_utcnow)
    model_used = "gpt-4o-mini"


# ===========================================================================
# Wire up Pydantic model classes
# ---------------------------------------------------------------------------
# The factories above use ``model = Any`` as a placeholder.  Below we
# import the real Pydantic models and assign them to each factory's Meta.
# This avoids circular imports at module load time.
# ===========================================================================


def _wire_models() -> None:
    """Assign real Pydantic model classes to factory Meta.model."""
    import sys
    from pathlib import Path

    # Ensure src/ is on the path for model imports
    src_path = str(Path(__file__).resolve().parents[3] / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from gated_communities.models.access_control_schemas import (
        AccessAudit,
        AccessRecommendation,
        AccessRequest,
        AccessResult,
        Permission,
        Role,
    )
    from gated_communities.models.analysis import EscalationAnalysis, TrendReport
    from gated_communities.models.analytics import (
        GovernanceAnalytics,
        GovernanceHealthScore,
        GovernanceSummary,
    )
    from gated_communities.models.community_health_scorer___init__ import (
        ChurnPrediction,
        EngagementMetrics,
        GrowthAnalysis,
        HealthExplanation,
        HealthScore,
        ToxicityReport,
    )
    from gated_communities.models.compliance_monitor_schemas import (
        AuditReport,
        ComplianceReport,
        ComplianceScore,
        RemediationAction,
        Violation,
    )
    from gated_communities.models.compliance_monitor_schemas import Policy as CompliancePolicy
    from gated_communities.models.dispute import Dispute, DisputeResolution
    from gated_communities.models.escalation import Escalation
    from gated_communities.models.governance_action import GovernanceAction
    from gated_communities.models.member_verification_schemas import (
        DocumentData,
        DocumentVerificationResult,
        FraudReport,
        IdentityData,
        TrustScore,
        VerificationExplanation,
        VerificationRequest,
        VerificationResult,
    )
    from gated_communities.models.moderation_analytics___init__ import (
        AnalyticsSummary,
        ModerationAnalytics,
        ModerationPrediction,
        ModeratorPerformance,
        PolicyEffectiveness,
        Trend,
    )
    from gated_communities.models.moderation_queue___init__ import (
        Escalation as ModerationEscalation,
    )
    from gated_communities.models.moderation_queue___init__ import (
        ModerationItem,
        PriorityScore,
        Queue,
        QueueMetrics,
        ReviewDecision,
    )
    from gated_communities.models.policy import Policy as GovernancePolicy
    from gated_communities.models.priority import Priority, PriorityAssessment
    from gated_communities.models.reputation_system_schemas import (
        Badge,
        ReputationExplanation,
        ReputationHistory,
        ReputationScore,
        TrustTier,
    )
    from gated_communities.models.resolution import Resolution
    from gated_communities.models.rule import Rule, RuleEnforcementResult
    from gated_communities.models.schemas import (
        AccessPolicy,
        Benefit,
        Tier,
        TierAnalytics,
        TierEvaluation,
        UpgradeRequest,
    )
    from gated_communities.models.sla import SLA, SLABreach

    # Tier Management
    TierFactory._meta.model = Tier
    TierEvaluationFactory._meta.model = TierEvaluation
    UpgradeRequestFactory._meta.model = UpgradeRequest
    AccessPolicyFactory._meta.model = AccessPolicy
    BenefitFactory._meta.model = Benefit
    TierAnalyticsFactory._meta.model = TierAnalytics

    # Community Governance
    GovernancePolicyFactory._meta.model = GovernancePolicy
    RuleFactory._meta.model = Rule
    RuleEnforcementResultFactory._meta.model = RuleEnforcementResult
    DisputeFactory._meta.model = Dispute
    DisputeResolutionFactory._meta.model = DisputeResolution
    GovernanceActionFactory._meta.model = GovernanceAction
    GovernanceHealthScoreFactory._meta.model = GovernanceHealthScore
    GovernanceAnalyticsFactory._meta.model = GovernanceAnalytics
    GovernanceSummaryFactory._meta.model = GovernanceSummary

    # Escalation Workflow
    EscalationFactory._meta.model = Escalation
    ResolutionFactory._meta.model = Resolution
    SLAFactory._meta.model = SLA
    SLABreachFactory._meta.model = SLABreach
    PriorityFactory._meta.model = Priority
    PriorityAssessmentFactory._meta.model = PriorityAssessment
    EscalationAnalysisFactory._meta.model = EscalationAnalysis
    TrendReportFactory._meta.model = TrendReport

    # Access Control
    PermissionFactory._meta.model = Permission
    RoleFactory._meta.model = Role
    AccessRequestFactory._meta.model = AccessRequest
    AccessResultFactory._meta.model = AccessResult
    AccessAuditFactory._meta.model = AccessAudit
    AccessRecommendationFactory._meta.model = AccessRecommendation

    # Reputation System
    ReputationScoreFactory._meta.model = ReputationScore
    BadgeFactory._meta.model = Badge
    TrustTierFactory._meta.model = TrustTier
    ReputationHistoryFactory._meta.model = ReputationHistory
    ReputationExplanationFactory._meta.model = ReputationExplanation

    # Compliance Monitor
    CompliancePolicyFactory._meta.model = CompliancePolicy
    ViolationFactory._meta.model = Violation
    AuditReportFactory._meta.model = AuditReport
    ComplianceScoreFactory._meta.model = ComplianceScore
    ComplianceReportFactory._meta.model = ComplianceReport
    RemediationActionFactory._meta.model = RemediationAction

    # Member Verification
    IdentityDataFactory._meta.model = IdentityData
    DocumentDataFactory._meta.model = DocumentData
    VerificationRequestFactory._meta.model = VerificationRequest
    VerificationResultFactory._meta.model = VerificationResult
    TrustScoreFactory._meta.model = TrustScore
    FraudReportFactory._meta.model = FraudReport
    DocumentVerificationResultFactory._meta.model = DocumentVerificationResult
    VerificationExplanationFactory._meta.model = VerificationExplanation

    # Moderation Queue
    ModerationItemFactory._meta.model = ModerationItem
    QueueFactory._meta.model = Queue
    PriorityScoreFactory._meta.model = PriorityScore
    ReviewDecisionFactory._meta.model = ReviewDecision
    ModerationEscalationFactory._meta.model = ModerationEscalation
    QueueMetricsFactory._meta.model = QueueMetrics

    # Moderation Analytics
    ModerationAnalyticsFactory._meta.model = ModerationAnalytics
    TrendFactory._meta.model = Trend
    ModeratorPerformanceFactory._meta.model = ModeratorPerformance
    PolicyEffectivenessFactory._meta.model = PolicyEffectiveness
    ModerationPredictionFactory._meta.model = ModerationPrediction
    AnalyticsSummaryFactory._meta.model = AnalyticsSummary

    # Community Health Scorer
    EngagementMetricsFactory._meta.model = EngagementMetrics
    ToxicityReportFactory._meta.model = ToxicityReport
    GrowthAnalysisFactory._meta.model = GrowthAnalysis
    ChurnPredictionFactory._meta.model = ChurnPrediction
    HealthScoreFactory._meta.model = HealthScore
    HealthExplanationFactory._meta.model = HealthExplanation


# Wire models at import time
_wire_models()

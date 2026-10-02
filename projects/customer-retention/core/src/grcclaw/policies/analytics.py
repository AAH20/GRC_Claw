"""
Policy Analytics Engine for GRC_Claw.

Provides portfolio analytics, compliance dashboards, trend analysis,
and executive reporting for the policy management system.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from .models import (
    EnforcementEvent,
    EnforcementResult,
    Policy,
    PolicyAnalytics,
    PolicyCategory,
    PolicyStatus,
)

logger = logging.getLogger(__name__)


class PolicyAnalyticsEngine:
    """Analytics engine for policy portfolio insights."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._events: dict[str, list[EnforcementEvent]] = {}

    def register_policy(self, policy: Policy) -> None:
        """Register a policy for analytics tracking."""
        self._policies[policy.id] = policy

    def unregister_policy(self, policy_id: str) -> None:
        """Remove a policy from analytics tracking."""
        self._policies.pop(policy_id, None)
        self._events.pop(policy_id, None)

    def register_event(self, event: EnforcementEvent) -> None:
        """Register an enforcement event for analytics."""
        if event.policy_id not in self._events:
            self._events[event.policy_id] = []
        self._events[event.policy_id].append(event)

    def generate_portfolio_analytics(self) -> PolicyAnalytics:
        """Generate portfolio-wide analytics."""
        policies = list(self._policies.values())
        now = datetime.now(UTC)

        by_status: dict[str, int] = defaultdict(int)
        by_category: dict[str, int] = defaultdict(int)
        by_priority: dict[str, int] = defaultdict(int)
        by_enforcement_mode: dict[str, int] = defaultdict(int)

        upcoming_reviews = 0
        overdue_reviews = 0
        pending_approvals = 0
        attestations_pending = 0
        attestations_completed = 0

        total_pass = 0
        total_fail = 0
        total_warning = 0
        total_events = 0

        policies_created_last_30d = 0
        policies_updated_last_30d = 0

        rule_violation_counts: dict[str, int] = defaultdict(int)

        for policy in policies:
            by_status[policy.status.value] += 1
            by_category[policy.metadata.category.value] += 1
            by_priority[policy.metadata.priority.value] += 1
            by_enforcement_mode[policy.enforcement_mode.value] += 1

            # Review tracking
            if policy.metadata.review_date:
                try:
                    review_date = datetime.fromisoformat(policy.metadata.review_date)
                    if review_date > now and (review_date - now).days <= 30:
                        upcoming_reviews += 1
                    elif review_date <= now:
                        overdue_reviews += 1
                except ValueError:
                    pass

            # Approval tracking
            for approval in policy.approvals:
                if approval.status.value == "pending":
                    pending_approvals += 1

            # Attestation tracking
            for attestation in policy.attestations:
                if attestation.acknowledged_at:
                    attestations_completed += 1
                else:
                    attestations_pending += 1

            # Creation/update tracking (last 30 days)
            try:
                created = datetime.fromisoformat(policy.created_at)
                if (now - created).days <= 30:
                    policies_created_last_30d += 1
            except ValueError:
                pass

            try:
                updated = datetime.fromisoformat(policy.updated_at)
                if (now - updated).days <= 30:
                    policies_updated_last_30d += 1
            except ValueError:
                pass

        # Enforcement analytics
        for policy_id, events in self._events.items():
            for event in events:
                total_events += 1
                if event.result == EnforcementResult.PASS:
                    total_pass += 1
                elif event.result == EnforcementResult.FAIL:
                    total_fail += 1
                elif event.result == EnforcementResult.WARNING:
                    total_warning += 1

                for finding in event.findings:
                    rule_violation_counts[finding.title] += 1

        pass_rate = (total_pass / total_events * 100) if total_events > 0 else 0.0

        # Top violated rules
        top_violated = sorted(
            [{"rule": k, "count": v} for k, v in rule_violation_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        # Compliance trend (last 6 months)
        compliance_trend = self._generate_compliance_trend()

        return PolicyAnalytics(
            total_policies=len(policies),
            by_status=dict(by_status),
            by_category=dict(by_category),
            by_priority=dict(by_priority),
            by_enforcement_mode=dict(by_enforcement_mode),
            upcoming_reviews=upcoming_reviews,
            overdue_reviews=overdue_reviews,
            pending_approvals=pending_approvals,
            attestations_pending=attestations_pending,
            attestations_completed=attestations_completed,
            enforcement_pass_rate=round(pass_rate, 2),
            enforcement_fail_count=total_fail,
            enforcement_warning_count=total_warning,
            average_approval_time_hours=0.0,  # Calculated from approval records
            policies_created_last_30d=policies_created_last_30d,
            policies_updated_last_30d=policies_updated_last_30d,
            top_violated_rules=top_violated,
            compliance_trend=compliance_trend,
        )

    def get_policy_analytics(self, policy_id: str) -> dict:
        """Get analytics for a specific policy."""
        policy = self._policies.get(policy_id)
        if not policy:
            return {"error": "Policy not found"}

        events = self._events.get(policy_id, [])
        total = len(events)
        passes = sum(1 for e in events if e.result == EnforcementResult.PASS)
        fails = sum(1 for e in events if e.result == EnforcementResult.FAIL)
        warnings = sum(1 for e in events if e.result == EnforcementResult.WARNING)

        findings_count = sum(len(e.findings) for e in events)
        open_findings = sum(
            1 for e in events for f in e.findings if f.status == "open"
        )

        return {
            "policy_id": policy_id,
            "title": policy.metadata.title,
            "status": policy.status.value,
            "version": policy.metadata.version,
            "total_enforcement_events": total,
            "pass_count": passes,
            "fail_count": fails,
            "warning_count": warnings,
            "pass_rate": round(passes / total * 100, 2) if total > 0 else 0.0,
            "total_findings": findings_count,
            "open_findings": open_findings,
            "attestations_total": len(policy.attestations),
            "attestations_completed": sum(1 for a in policy.attestations if a.acknowledged_at),
            "attestations_pending": sum(1 for a in policy.attestations if not a.acknowledged_at),
            "enforcement_rules_count": len(policy.enforcement_rules),
            "enforcement_mode": policy.enforcement_mode.value,
            "change_log_entries": len(policy.change_log),
            "versions_count": len(policy.versions),
        }

    def generate_compliance_dashboard(self) -> dict:
        """Generate executive compliance dashboard."""
        analytics = self.generate_portfolio_analytics()

        # Calculate overall compliance score
        total_checks = (
            analytics.enforcement_pass_rate
            + analytics.enforcement_fail_count
            + analytics.enforcement_warning_count
        )
        compliance_score = analytics.enforcement_pass_rate if total_checks > 0 else 0.0

        # Risk distribution
        risk_distribution = {
            "critical": analytics.by_priority.get("critical", 0),
            "high": analytics.by_priority.get("high", 0),
            "medium": analytics.by_priority.get("medium", 0),
            "low": analytics.by_priority.get("low", 0),
        }

        # Category compliance
        category_compliance = {}
        for category in PolicyCategory:
            category_policies = [p for p in self._policies.values() if p.metadata.category == category]
            if category_policies:
                published = sum(1 for p in category_policies if p.status == PolicyStatus.PUBLISHED)
                category_compliance[category.value] = {
                    "total": len(category_policies),
                    "published": published,
                    "draft": sum(1 for p in category_policies if p.status == PolicyStatus.DRAFT),
                    "under_review": sum(1 for p in category_policies if p.status == PolicyStatus.UNDER_REVIEW),
                    "compliance_rate": round(published / len(category_policies) * 100, 2),
                }

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "compliance_score": round(compliance_score, 2),
            "total_policies": analytics.total_policies,
            "published_policies": analytics.by_status.get("published", 0),
            "draft_policies": analytics.by_status.get("draft", 0),
            "under_review_policies": analytics.by_status.get("under_review", 0),
            "overdue_reviews": analytics.overdue_reviews,
            "upcoming_reviews": analytics.upcoming_reviews,
            "pending_approvals": analytics.pending_approvals,
            "attestations_pending": analytics.attestations_pending,
            "attestations_completed": analytics.attestations_completed,
            "enforcement_pass_rate": analytics.enforcement_pass_rate,
            "enforcement_fail_count": analytics.enforcement_fail_count,
            "enforcement_warning_count": analytics.enforcement_warning_count,
            "risk_distribution": risk_distribution,
            "category_compliance": category_compliance,
            "top_violated_rules": analytics.top_violated_rules,
            "compliance_trend": analytics.compliance_trend,
            "policies_created_last_30d": analytics.policies_created_last_30d,
            "policies_updated_last_30d": analytics.policies_updated_last_30d,
        }

    def _generate_compliance_trend(self) -> list[dict]:
        """Generate 6-month compliance trend data."""
        trend = []
        now = datetime.now(UTC)

        for i in range(5, -1, -1):
            month_start = now - timedelta(days=30 * i)
            month_label = month_start.strftime("%Y-%m")

            # Filter events for this month
            month_events = []
            for events in self._events.values():
                for event in events:
                    try:
                        event_date = datetime.fromisoformat(event.enforced_at)
                        if event_date.strftime("%Y-%m") == month_label:
                            month_events.append(event)
                    except ValueError:
                        continue

            total = len(month_events)
            passes = sum(1 for e in month_events if e.result == EnforcementResult.PASS)
            fails = sum(1 for e in month_events if e.result == EnforcementResult.FAIL)

            trend.append({
                "month": month_label,
                "total_checks": total,
                "passes": passes,
                "fails": fails,
                "pass_rate": round(passes / total * 100, 2) if total > 0 else 0.0,
            })

        return trend

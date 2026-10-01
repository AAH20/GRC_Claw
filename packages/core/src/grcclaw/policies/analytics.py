"""
Policy Analytics

Aggregates policy portfolio metrics, compliance trends, enforcement
statistics, and generates executive dashboards.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from .models import (
    Policy,
    PolicyStatus,
    PolicyCategory,
    PolicyPriority,
    EnforcementMode,
    EnforcementResult,
    EnforcementEvent,
    PolicyAnalytics,
    ApprovalRecord,
    ApprovalStatus,
    Attestation,
)


class PolicyAnalyticsEngine:
    """Generates analytics and insights for the policy portfolio."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._events: dict[str, EnforcementEvent] = {}
        self._approvals: dict[str, ApprovalRecord] = {}

    # ── Data Registration ──────────────────────────────────────────────────

    def register_policy(self, policy: Policy) -> None:
        """Register a policy for analytics tracking."""
        self._policies[policy.id] = policy

    def register_event(self, event: EnforcementEvent) -> None:
        """Register an enforcement event."""
        self._events[event.id] = event

    def register_approval(self, approval: ApprovalRecord) -> None:
        """Register an approval record."""
        self._approvals[approval.id] = approval

    def clear(self) -> None:
        """Clear all registered data."""
        self._policies.clear()
        self._events.clear()
        self._approvals.clear()

    # ── Portfolio Analytics ────────────────────────────────────────────────

    def generate_portfolio_analytics(self) -> PolicyAnalytics:
        """Generate comprehensive analytics for the entire policy portfolio."""
        policies = list(self._policies.values())
        events = list(self._events.values())
        approvals = list(self._approvals.values())

        analytics = PolicyAnalytics()

        # Basic counts
        analytics.total_policies = len(policies)

        # Status distribution
        status_counts = Counter(p.status.value for p in policies)
        analytics.by_status = dict(status_counts)

        # Category distribution
        category_counts = Counter(p.metadata.category.value for p in policies)
        analytics.by_category = dict(category_counts)

        # Priority distribution
        priority_counts = Counter(p.metadata.priority.value for p in policies)
        analytics.by_priority = dict(priority_counts)

        # Enforcement mode distribution
        mode_counts = Counter(p.enforcement_mode.value for p in policies)
        analytics.by_enforcement_mode = dict(mode_counts)

        # Review tracking
        now = datetime.now(timezone.utc)
        review_threshold = now + timedelta(days=30)
        analytics.upcoming_reviews = 0
        analytics.overdue_reviews = 0
        for p in policies:
            if p.metadata.review_date:
                try:
                    review_dt = datetime.fromisoformat(p.metadata.review_date.replace("Z", "+00:00"))
                    if review_dt < now:
                        analytics.overdue_reviews += 1
                    elif review_dt <= review_threshold:
                        analytics.upcoming_reviews += 1
                except (ValueError, AttributeError):
                    pass

        # Approval tracking
        analytics.pending_approvals = sum(
            1 for a in approvals if a.status == ApprovalStatus.PENDING
        )

        # Attestation tracking
        total_attestations = sum(len(p.attestations) for p in policies)
        analytics.attestations_completed = total_attestations
        # Pending attestations would come from HR system integration
        analytics.attestations_pending = 0

        # Enforcement statistics
        if events:
            pass_count = sum(1 for e in events if e.result == EnforcementResult.PASS)
            fail_count = sum(1 for e in events if e.result == EnforcementResult.FAIL)
            warning_count = sum(1 for e in events if e.result == EnforcementResult.WARNING)
            total = len(events)

            analytics.enforcement_pass_rate = (pass_count / total) * 100 if total > 0 else 0.0
            analytics.enforcement_fail_count = fail_count
            analytics.enforcement_warning_count = warning_count

        # Approval timing
        completed_approvals = [
            a for a in approvals
            if a.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED)
            and a.decided_at
        ]
        if completed_approvals:
            total_hours = 0.0
            for a in completed_approvals:
                try:
                    requested = datetime.fromisoformat(a.requested_at.replace("Z", "+00:00"))
                    decided = datetime.fromisoformat(a.decided_at.replace("Z", "+00:00"))
                    total_hours += (decided - requested).total_seconds() / 3600
                except (ValueError, AttributeError):
                    continue
            analytics.average_approval_time_hours = total_hours / len(completed_approvals)

        # Recent activity
        thirty_days_ago = now - timedelta(days=30)
        analytics.policies_created_last_30d = sum(
            1 for p in policies
            if self._parse_date(p.created_at) and self._parse_date(p.created_at) > thirty_days_ago
        )
        analytics.policies_updated_last_30d = sum(
            1 for p in policies
            if self._parse_date(p.updated_at) and self._parse_date(p.updated_at) > thirty_days_ago
        )

        # Top violated rules
        rule_violations: Counter = Counter()
        for event in events:
            if event.result in (EnforcementResult.FAIL, EnforcementResult.WARNING):
                for finding in event.findings:
                    if finding.status == "open":
                        rule_violations[finding.title] += 1

        analytics.top_violated_rules = [
            {"rule": rule, "count": count}
            for rule, count in rule_violations.most_common(10)
        ]

        # Compliance trend (last 6 months)
        analytics.compliance_trend = self._compute_compliance_trend(events)

        return analytics

    # ── Policy-Specific Analytics ──────────────────────────────────────────

    def get_policy_analytics(self, policy_id: str) -> dict[str, Any]:
        """Generate analytics for a specific policy."""
        policy = self._policies.get(policy_id)
        if not policy:
            return {"error": "Policy not found"}

        events = [e for e in self._events.values() if e.policy_id == policy_id]
        approvals = [a for a in self._approvals.values() if a.policy_id == policy_id]

        total_events = len(events)
        pass_count = sum(1 for e in events if e.result == EnforcementResult.PASS)
        fail_count = sum(1 for e in events if e.result == EnforcementResult.FAIL)
        warning_count = sum(1 for e in events if e.result == EnforcementResult.WARNING)

        open_findings = sum(
            1 for e in events for f in e.findings if f.status == "open"
        )
        remediated_findings = sum(
            1 for e in events for f in e.findings if f.status == "remediated"
        )

        return {
            "policy_id": policy_id,
            "title": policy.metadata.title,
            "status": policy.status.value,
            "version": policy.metadata.version,
            "enforcement_mode": policy.enforcement_mode.value,
            "total_enforcement_events": total_events,
            "pass_rate": (pass_count / total_events * 100) if total_events > 0 else 0,
            "fail_count": fail_count,
            "warning_count": warning_count,
            "open_findings": open_findings,
            "remediated_findings": remediated_findings,
            "attestation_count": len(policy.attestations),
            "approval_count": len(approvals),
            "pending_approvals": sum(1 for a in approvals if a.status == ApprovalStatus.PENDING),
            "change_count": len(policy.change_log),
            "section_count": len(policy.sections),
            "rule_count": len(policy.enforcement_rules),
            "enabled_rules": sum(1 for r in policy.enforcement_rules if r.enabled),
        }

    # ── Compliance Dashboard ───────────────────────────────────────────────

    def generate_compliance_dashboard(self) -> dict[str, Any]:
        """Generate an executive compliance dashboard."""
        analytics = self.generate_portfolio_analytics()

        # Overall compliance score (0-100)
        score = self._compute_compliance_score(analytics)

        # Risk distribution
        risk_distribution = self._compute_risk_distribution()

        # Framework coverage
        framework_coverage = self._compute_framework_coverage()

        # Department breakdown
        department_breakdown = self._compute_department_breakdown()

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "compliance_score": score,
            "summary": {
                "total_policies": analytics.total_policies,
                "published": analytics.by_status.get("published", 0),
                "draft": analytics.by_status.get("draft", 0),
                "under_review": analytics.by_status.get("under_review", 0),
                "pending_approvals": analytics.pending_approvals,
                "overdue_reviews": analytics.overdue_reviews,
                "upcoming_reviews": analytics.upcoming_reviews,
            },
            "enforcement": {
                "pass_rate": round(analytics.enforcement_pass_rate, 1),
                "fail_count": analytics.enforcement_fail_count,
                "warning_count": analytics.enforcement_warning_count,
                "top_violations": analytics.top_violated_rules[:5],
            },
            "risk_distribution": risk_distribution,
            "framework_coverage": framework_coverage,
            "department_breakdown": department_breakdown,
            "trend": analytics.compliance_trend,
            "recommendations": self._generate_recommendations(analytics),
        }

    # ── Trend Analysis ─────────────────────────────────────────────────────

    def _compute_compliance_trend(
        self,
        events: list[EnforcementEvent],
    ) -> list[dict[str, Any]]:
        """Compute monthly compliance trend for the last 6 months."""
        now = datetime.now(timezone.utc)
        months: list[dict[str, Any]] = []

        for i in range(5, -1, -1):
            month_start = now - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=30)

            month_events = [
                e for e in events
                if self._parse_date(e.enforced_at)
                and month_start <= self._parse_date(e.enforced_at) < month_end  # type: ignore
            ]

            if month_events:
                pass_count = sum(1 for e in month_events if e.result == EnforcementResult.PASS)
                fail_count = sum(1 for e in month_events if e.result == EnforcementResult.FAIL)
                warning_count = sum(1 for e in month_events if e.result == EnforcementResult.WARNING)
                total = len(month_events)

                months.append({
                    "month": month_start.strftime("%Y-%m"),
                    "total_checks": total,
                    "pass_rate": round((pass_count / total) * 100, 1),
                    "fail_count": fail_count,
                    "warning_count": warning_count,
                })
            else:
                months.append({
                    "month": month_start.strftime("%Y-%m"),
                    "total_checks": 0,
                    "pass_rate": 0,
                    "fail_count": 0,
                    "warning_count": 0,
                })

        return months

    # ── Risk & Coverage ────────────────────────────────────────────────────

    def _compute_risk_distribution(self) -> dict[str, int]:
        """Compute risk distribution across policies."""
        distribution: Counter = Counter()
        for policy in self._policies.values():
            if policy.metadata.priority == PolicyPriority.CRITICAL:
                distribution["critical"] += 1
            elif policy.metadata.priority == PolicyPriority.HIGH:
                distribution["high"] += 1
            elif policy.metadata.priority == PolicyPriority.MEDIUM:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        return dict(distribution)

    def _compute_framework_coverage(self) -> dict[str, Any]:
        """Compute framework coverage statistics."""
        framework_policies: dict[str, int] = defaultdict(int)
        for policy in self._policies.values():
            if policy.metadata.framework:
                framework_policies[policy.metadata.framework] += 1

        return {
            "frameworks": dict(framework_policies),
            "total_frameworks": len(framework_policies),
            "uncovered_categories": self._find_uncovered_categories(),
        }

    def _compute_department_breakdown(self) -> dict[str, Any]:
        """Compute policy distribution by department."""
        dept_policies: dict[str, int] = defaultdict(int)
        for policy in self._policies.values():
            dept = policy.metadata.department or "Unassigned"
            dept_policies[dept] += 1
        return dict(dept_policies)

    def _find_uncovered_categories(self) -> list[str]:
        """Find categories with no policies."""
        all_categories = {c.value for c in PolicyCategory}
        covered = {p.metadata.category.value for p in self._policies.values()}
        return list(all_categories - covered)

    # ── Scoring & Recommendations ──────────────────────────────────────────

    def _compute_compliance_score(self, analytics: PolicyAnalytics) -> float:
        """Compute an overall compliance score (0-100)."""
        score = 100.0

        # Deduct for overdue reviews
        score -= analytics.overdue_reviews * 5

        # Deduct for pending approvals
        score -= analytics.pending_approvals * 2

        # Deduct for enforcement failures
        score -= analytics.enforcement_fail_count * 3

        # Deduct for low pass rate
        if analytics.enforcement_pass_rate < 80:
            score -= (80 - analytics.enforcement_pass_rate) * 0.5

        # Deduct for draft policies
        draft_count = analytics.by_status.get("draft", 0)
        if analytics.total_policies > 0:
            draft_ratio = draft_count / analytics.total_policies
            score -= draft_ratio * 10

        return max(0.0, min(100.0, round(score, 1)))

    def _generate_recommendations(self, analytics: PolicyAnalytics) -> list[str]:
        """Generate actionable recommendations based on analytics."""
        recommendations: list[str] = []

        if analytics.overdue_reviews > 0:
            recommendations.append(
                f"Address {analytics.overdue_reviews} overdue policy review(s) immediately"
            )

        if analytics.pending_approvals > 0:
            recommendations.append(
                f"Expedite {analytics.pending_approvals} pending approval(s)"
            )

        if analytics.enforcement_fail_count > 0:
            recommendations.append(
                f"Remediate {analytics.enforcement_fail_count} enforcement failure(s)"
            )

        if analytics.enforcement_pass_rate < 80:
            recommendations.append(
                f"Improve enforcement pass rate (currently {analytics.enforcement_pass_rate:.1f}%)"
            )

        draft_count = analytics.by_status.get("draft", 0)
        if draft_count > 0:
            recommendations.append(
                f"Move {draft_count} draft policy(ies) through the approval pipeline"
            )

        uncovered = self._find_uncovered_categories()
        if uncovered:
            recommendations.append(
                f"Create policies for uncovered categories: {', '.join(uncovered)}"
            )

        if not recommendations:
            recommendations.append("Policy portfolio is healthy — maintain current practices")

        return recommendations

    # ── Utility ────────────────────────────────────────────────────────────

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse an ISO date string."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

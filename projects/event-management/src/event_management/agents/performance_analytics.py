"""Performance Analytics Agent - Handles KPI tracking, ROI analysis, and engagement metrics."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from event_management.agents.base import AgentContext, BaseAgent


class KPIMetric(BaseModel):
    """A single KPI metric."""

    name: str
    value: float
    target: float
    unit: str
    status: str = "on_track"  # on_track, at_risk, off_track
    trend: str = "stable"  # improving, declining, stable


class ROIBreakdown(BaseModel):
    """ROI breakdown by category."""

    category: str
    investment: float
    revenue: float
    roi_percentage: float
    notes: str = ""


class EngagementMetric(BaseModel):
    """An engagement metric."""

    metric_name: str
    value: float
    benchmark: float
    percentile: float
    insights: str = ""


class AnalyticsInput(BaseModel):
    """Input for the Performance Analytics Agent."""

    event_name: str
    event_date: str
    total_budget: float
    actual_spend: float
    ticket_revenue: float
    sponsorship_revenue: float
    attendee_count: int
    registered_count: int
    check_in_count: int
    session_attendance: dict[str, int] = Field(default_factory=dict)
    nps_score: float | None = None
    social_media_metrics: dict[str, float] = Field(default_factory=dict)
    email_metrics: dict[str, float] = Field(default_factory=dict)
    website_metrics: dict[str, float] = Field(default_factory=dict)


class AnalyticsOutput(BaseModel):
    """Output from the Performance Analytics Agent."""

    kpis: list[KPIMetric] = Field(default_factory=list)
    roi_analysis: list[ROIBreakdown] = Field(default_factory=list)
    engagement_metrics: list[EngagementMetric] = Field(default_factory=list)
    overall_score: float = 0.0
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    benchmark_comparison: dict[str, Any] = Field(default_factory=dict)


class PerformanceAnalyticsAgent(BaseAgent[AnalyticsInput, AnalyticsOutput]):
    """Agent responsible for event performance analytics and reporting."""

    @property
    def name(self) -> str:
        return "PerformanceAnalyticsAgent"

    async def execute(self, input_data: AnalyticsInput, context: AgentContext) -> AnalyticsOutput:
        """Generate comprehensive performance analytics.

        Args:
            input_data: The event data and metrics to analyze.
            context: Execution context with event and user info.

        Returns:
            A complete analytics report with KPIs, ROI, and insights.
        """
        self.logger.info(
            "generating_analytics",
            event_name=input_data.event_name,
            attendee_count=input_data.attendee_count,
            total_budget=input_data.total_budget,
        )

        kpis = self._calculate_kpis(input_data)
        roi = self._calculate_roi(input_data)
        engagement = self._analyze_engagement(input_data)
        overall = self._calculate_overall_score(kpis)
        insights = self._generate_insights(input_data, kpis, roi)
        recommendations = self._generate_recommendations(input_data, kpis, roi)
        benchmarks = self._compare_benchmarks(input_data)

        return AnalyticsOutput(
            kpis=kpis,
            roi_analysis=roi,
            engagement_metrics=engagement,
            overall_score=overall,
            insights=insights,
            recommendations=recommendations,
            benchmark_comparison=benchmarks,
        )

    def _calculate_kpis(self, data: AnalyticsInput) -> list[KPIMetric]:
        """Calculate key performance indicators."""
        attendance_rate = (
            data.check_in_count / data.registered_count if data.registered_count > 0 else 0
        )
        registration_rate = (
            data.registered_count / data.attendee_count if data.attendee_count > 0 else 0
        )
        budget_variance = (
            (data.actual_spend - data.total_budget) / data.total_budget
            if data.total_budget > 0
            else 0
        )
        revenue = data.ticket_revenue + data.sponsorship_revenue
        cost_per_attendee = (
            data.actual_spend / data.check_in_count if data.check_in_count > 0 else 0
        )

        return [
            KPIMetric(
                name="Attendance Rate",
                value=attendance_rate,
                target=0.85,
                unit="percentage",
                status="on_track" if attendance_rate >= 0.80 else "at_risk",
                trend="stable",
            ),
            KPIMetric(
                name="Registration Conversion",
                value=registration_rate,
                target=0.70,
                unit="percentage",
                status="on_track" if registration_rate >= 0.60 else "at_risk",
                trend="stable",
            ),
            KPIMetric(
                name="Budget Variance",
                value=budget_variance,
                target=0.0,
                unit="percentage",
                status="on_track" if abs(budget_variance) <= 0.10 else "off_track",
                trend="stable",
            ),
            KPIMetric(
                name="Cost Per Attendee",
                value=cost_per_attendee,
                target=150.0,
                unit="currency",
                status="on_track" if cost_per_attendee <= 200 else "at_risk",
                trend="stable",
            ),
            KPIMetric(
                name="NPS Score",
                value=data.nps_score or 0.0,
                target=50.0,
                unit="score",
                status="on_track" if (data.nps_score or 0) >= 40 else "at_risk",
                trend="stable",
            ),
            KPIMetric(
                name="Total Revenue",
                value=revenue,
                target=data.total_budget * 1.5,
                unit="currency",
                status="on_track" if revenue >= data.total_budget else "at_risk",
                trend="stable",
            ),
        ]

    def _calculate_roi(self, data: AnalyticsInput) -> list[ROIBreakdown]:
        """Calculate ROI breakdown by category."""
        total_revenue = data.ticket_revenue + data.sponsorship_revenue
        overall_roi = (
            ((total_revenue - data.actual_spend) / data.actual_spend * 100)
            if data.actual_spend > 0
            else 0
        )

        return [
            ROIBreakdown(
                category="Ticket Sales",
                investment=data.actual_spend * 0.6,
                revenue=data.ticket_revenue,
                roi_percentage=(
                    ((data.ticket_revenue - data.actual_spend * 0.6) /
                     (data.actual_spend * 0.6) * 100)
                    if data.actual_spend > 0
                    else 0
                ),
                notes="Revenue from attendee ticket sales",
            ),
            ROIBreakdown(
                category="Sponsorship",
                investment=data.actual_spend * 0.2,
                revenue=data.sponsorship_revenue,
                roi_percentage=(
                    ((data.sponsorship_revenue - data.actual_spend * 0.2) /
                     (data.actual_spend * 0.2) * 100)
                    if data.actual_spend > 0
                    else 0
                ),
                notes="Revenue from event sponsors",
            ),
            ROIBreakdown(
                category="Overall Event",
                investment=data.actual_spend,
                revenue=total_revenue,
                roi_percentage=overall_roi,
                notes="Total event ROI including all revenue streams",
            ),
        ]

    def _analyze_engagement(self, data: AnalyticsInput) -> list[EngagementMetric]:
        """Analyze engagement metrics."""
        metrics = []

        # Social media engagement
        social_reach = data.social_media_metrics.get("reach", 0)
        social_engagement = data.social_media_metrics.get("engagement", 0)
        social_rate = social_engagement / social_reach if social_reach > 0 else 0
        metrics.append(
            EngagementMetric(
                metric_name="Social Media Engagement Rate",
                value=social_rate,
                benchmark=0.03,
                percentile=75.0 if social_rate >= 0.03 else 50.0,
                insights=(
                    "Above industry average" if social_rate >= 0.03 else "Below industry average"
                ),
            )
        )

        # Email engagement
        email_open = data.email_metrics.get("open_rate", 0)
        metrics.append(
            EngagementMetric(
                metric_name="Email Open Rate",
                value=email_open,
                benchmark=0.22,
                percentile=70.0 if email_open >= 0.22 else 45.0,
                insights=(
                    "Strong email performance"
                    if email_open >= 0.22
                    else "Consider improving subject lines"
                ),
            )
        )

        # Website conversion
        website_conversion = data.website_metrics.get("conversion_rate", 0)
        metrics.append(
            EngagementMetric(
                metric_name="Website Conversion Rate",
                value=website_conversion,
                benchmark=0.025,
                percentile=80.0 if website_conversion >= 0.025 else 55.0,
                insights=(
                    "Effective landing page"
                    if website_conversion >= 0.025
                    else "Optimize registration flow"
                ),
            )
        )

        # Session engagement
        if data.session_attendance:
            avg_session = sum(data.session_attendance.values()) / len(data.session_attendance)
            metrics.append(
                EngagementMetric(
                    metric_name="Average Session Attendance",
                    value=avg_session,
                    benchmark=data.check_in_count * 0.7 if data.check_in_count > 0 else 0,
                    percentile=65.0,
                    insights=(
                    "Good session retention"
                    if avg_session > data.check_in_count * 0.5
                    else "Consider shorter sessions"
                ),
                )
            )

        return metrics

    def _calculate_overall_score(self, kpis: list[KPIMetric]) -> float:
        """Calculate an overall event score from KPIs."""
        if not kpis:
            return 0.0
        scores = []
        for kpi in kpis:
            if kpi.target == 0:
                scores.append(1.0 if kpi.value == 0 else 0.0)
            else:
                ratio = kpi.value / kpi.target
                scores.append(min(ratio, 1.0) if ratio <= 1.0 else max(0.0, 2.0 - ratio))
        return sum(scores) / len(scores) * 100

    def _generate_insights(
        self, data: AnalyticsInput, kpis: list[KPIMetric], roi: list[ROIBreakdown]
    ) -> list[str]:
        """Generate actionable insights from the data."""
        insights = []

        attendance_rate = (
            data.check_in_count / data.registered_count if data.registered_count > 0 else 0
        )
        if attendance_rate < 0.80:
            insights.append(
                f"Attendance rate ({attendance_rate:.0%}) is below target. "
                "Consider implementing reminder emails and incentives for no-shows."
            )

        if data.nps_score and data.nps_score < 50:
            insights.append(
                f"NPS score of {data.nps_score} indicates room for improvement. "
                "Focus on content quality and venue experience."
            )

        total_revenue = data.ticket_revenue + data.sponsorship_revenue
        if total_revenue < data.actual_spend:
            insights.append(
                "Event operated at a loss. Review pricing strategy and sponsorship packages."
            )
        elif total_revenue > data.actual_spend * 1.5:
            insights.append(
                "Strong financial performance. Consider scaling up for the next event."
            )

        if data.social_media_metrics.get("reach", 0) < data.registered_count * 3:
            insights.append(
                "Social media reach is low relative to registrations. "
                "Encourage attendees to share on social media."
            )

        return insights

    def _generate_recommendations(
        self, data: AnalyticsInput, kpis: list[KPIMetric], roi: list[ROIBreakdown]
    ) -> list[str]:
        """Generate recommendations for future events."""
        return [
            "Implement automated reminder sequence to reduce no-shows",
            "Add social media sharing incentives (photo contests, hashtags)",
            "Create tiered sponsorship packages to increase sponsorship revenue",
            "Optimize registration flow to improve conversion rates",
            "Schedule sessions based on attendee preference data",
            "Invest in event mobile app for better engagement tracking",
            "Develop year-round community to maintain engagement between events",
            "A/B test email subject lines and send times",
        ]

    def _compare_benchmarks(self, data: AnalyticsInput) -> dict[str, Any]:
        """Compare event metrics against industry benchmarks."""
        return {
            "industry": "Events & Conferences",
            "metrics": {
                "attendance_rate": {
                    "event": (
                    data.check_in_count / data.registered_count if data.registered_count > 0 else 0
                ),
                    "benchmark": 0.80,
                    "status": (
                    "above"
                    if (
                        data.registered_count > 0
                        and data.check_in_count / data.registered_count >= 0.80
                    )
                    else "below"
                ),
                },
                "nps_score": {
                    "event": data.nps_score or 0,
                    "benchmark": 45,
                    "status": "above" if (data.nps_score or 0) >= 45 else "below",
                },
                "cost_per_attendee": {
                    "event": (
                        data.actual_spend / data.check_in_count if data.check_in_count > 0 else 0
                    ),
                    "benchmark": 175,
                    "status": (
                        "below"
                        if (
                            data.check_in_count > 0
                            and data.actual_spend / data.check_in_count <= 175
                        )
                        else "above"
                    ),
                },
            },
        }

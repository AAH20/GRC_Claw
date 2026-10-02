"""Performance Analytics Agent — aggregates metrics, detects anomalies, and reports."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class Anomaly(BaseModel):
    """A detected performance anomaly.

    Attributes:
        campaign_id: The campaign where the anomaly was detected.
        metric: The metric name (e.g., 'ctr', 'cpa', 'spend').
        expected_value: The expected metric value.
        actual_value: The actual metric value.
        deviation: Percentage deviation from expected.
        severity: Severity level (low, medium, high).
    """

    campaign_id: str
    metric: str
    expected_value: float = 0.0
    actual_value: float = 0.0
    deviation: float = 0.0
    severity: str = "low"


class PerformanceReport(BaseModel):
    """A performance analytics report.

    Attributes:
        period_start: Start of the reporting period.
        period_end: End of the reporting period.
        total_spend: Total spend across all campaigns.
        total_revenue: Total revenue across all campaigns.
        total_clicks: Total clicks.
        total_impressions: Total impressions.
        average_ctr: Average click-through rate.
        average_cpa: Average cost per acquisition.
        anomalies: List of detected anomalies.
        campaign_count: Number of campaigns analyzed.
    """

    period_start: str
    period_end: str
    total_spend: float = 0.0
    total_revenue: float = 0.0
    total_clicks: int = 0
    total_impressions: int = 0
    average_ctr: float = 0.0
    average_cpa: float = 0.0
    anomalies: list[Anomaly] = Field(default_factory=list)
    campaign_count: int = 0


class PerformanceAnalyticsAgent:
    """Agent responsible for performance analysis and reporting.

    Aggregates metrics across campaigns, detects anomalies using
    statistical methods, and generates comprehensive performance reports.
    """

    def __init__(self, model: str = "gpt-4o") -> None:
        """Initialize the Performance Analytics Agent.

        Args:
            model: The LLM model to use for analysis.
        """
        self.model = model
        self._llm: Any = None

    def _get_llm(self) -> Any:
        """Lazy-load the LLM client.

        Returns:
            The LangChain LLM instance.
        """
        if self._llm is None:
            from langchain_openai import ChatOpenAI

            self._llm = ChatOpenAI(model=self.model, temperature=0.1)
        return self._llm

    async def generate_report(
        self,
        period_start: str,
        period_end: str,
        campaign_data: dict[str, Any],
    ) -> PerformanceReport:
        """Generate a performance report for the given period.

        Args:
            period_start: Start date of the reporting period (ISO format).
            period_end: End date of the reporting period (ISO format).
            campaign_data: Performance data per campaign.

        Returns:
            A PerformanceReport with aggregated metrics and anomalies.

        Raises:
            ValueError: If period_start or period_end is empty.
        """
        if not period_start or not period_end:
            raise ValueError("Period start and end are required")

        logger.info(
            "Generating performance report",
            period_start=period_start,
            period_end=period_end,
        )

        total_spend = 0.0
        total_revenue = 0.0
        total_clicks = 0
        total_impressions = 0
        total_conversions = 0

        for data in campaign_data.values():
            total_spend += float(data.get("spend", 0))
            total_revenue += float(data.get("revenue", 0))
            total_clicks += int(data.get("clicks", 0))
            total_impressions += int(data.get("impressions", 0))
            total_conversions += int(data.get("conversions", 0))

        avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0.0
        avg_cpa = total_spend / total_conversions if total_conversions > 0 else 0.0

        anomalies = self._detect_anomalies(campaign_data)

        report = PerformanceReport(
            period_start=period_start,
            period_end=period_end,
            total_spend=round(total_spend, 2),
            total_revenue=round(total_revenue, 2),
            total_clicks=total_clicks,
            total_impressions=total_impressions,
            average_ctr=round(avg_ctr, 4),
            average_cpa=round(avg_cpa, 2),
            anomalies=anomalies,
            campaign_count=len(campaign_data),
        )

        logger.info(
            "Performance report generated",
            total_spend=total_spend,
            total_revenue=total_revenue,
            anomalies=len(anomalies),
        )
        return report

    def _detect_anomalies(self, campaign_data: dict[str, Any]) -> list[Anomaly]:
        """Detect performance anomalies across campaigns.

        Uses a simple threshold-based approach: flags metrics that deviate
        more than 2 standard deviations from the mean.

        Args:
            campaign_data: Performance data per campaign.

        Returns:
            A list of detected Anomaly objects.
        """
        anomalies: list[Anomaly] = []

        if not campaign_data:
            return anomalies

        # Compute means and std devs for key metrics
        metrics = ["ctr", "cpa", "spend"]
        stats: dict[str, dict[str, float]] = {}

        for metric in metrics:
            values = [
                float(d.get(metric, 0))
                for d in campaign_data.values()
                if metric in d
            ]
            if len(values) < 2:
                continue
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std_dev = variance**0.5
            stats[metric] = {"mean": mean, "std_dev": std_dev}

        for cid, data in campaign_data.items():
            for metric, values in stats.items():
                if metric not in data:
                    continue
                actual = float(data[metric])
                expected = values["mean"]
                std_dev = values["std_dev"]

                if std_dev == 0:
                    continue

                deviation = (actual - expected) / std_dev
                if abs(deviation) > 2.0:
                    severity = "high" if abs(deviation) > 3.0 else "medium"
                    anomalies.append(
                        Anomaly(
                            campaign_id=cid,
                            metric=metric,
                            expected_value=round(expected, 4),
                            actual_value=round(actual, 4),
                            deviation=round(deviation, 2),
                            severity=severity,
                        )
                    )

        return anomalies

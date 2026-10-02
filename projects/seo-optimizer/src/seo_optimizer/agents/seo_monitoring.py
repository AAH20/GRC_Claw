"""SEO Monitoring Agent for tracking rankings and detecting anomalies."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

from seo_optimizer.agents.base import AgentResult, BaseAgent
from seo_optimizer.integrations.google_search_console import GoogleSearchConsoleClient

logger = structlog.get_logger(__name__)


class SEOMonitoringAgent(BaseAgent[dict[str, Any]]):
    """Agent for monitoring SEO performance and rankings.

    Tracks keyword rankings, detects anomalies, monitors competitors,
    and alerts on significant changes.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the SEO Monitoring Agent.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__("SEOMonitoringAgent", config)
        self.gsc = GoogleSearchConsoleClient(config)

    async def execute(
        self,
        domain: str,
        keywords: list[str] | None = None,
        lookback_days: int = 30,
        alert_threshold: int = 5,
        **kwargs: Any,
    ) -> AgentResult[dict[str, Any]]:
        """Execute SEO monitoring analysis.

        Args:
            domain: Target domain to monitor.
            keywords: Optional list of keywords to track.
            lookback_days: Number of days to look back for trends.
            alert_threshold: Ranking change threshold for alerts.
            **kwargs: Additional parameters.

        Returns:
            AgentResult with monitoring data and alerts.
        """
        self.logger.info(
            "Starting SEO monitoring",
            domain=domain,
            lookback_days=lookback_days,
        )

        try:
            monitoring: dict[str, Any] = {
                "domain": domain,
                "timestamp": datetime.utcnow().isoformat(),
                "lookback_days": lookback_days,
                "rankings": {},
                "alerts": [],
                "trends": {},
                "competitor_movements": [],
                "summary": {},
            }

            # Get ranking data from GSC
            if self.gsc.is_enabled:
                monitoring["rankings"] = await self.gsc.get_ranking_data(
                    domain, keywords, lookback_days
                )

            # Detect anomalies
            monitoring["alerts"] = self._detect_anomalies(
                monitoring["rankings"], alert_threshold
            )

            # Analyze trends
            monitoring["trends"] = self._analyze_trends(
                monitoring["rankings"], lookback_days
            )

            # Generate summary
            monitoring["summary"] = self._generate_summary(monitoring)

            return AgentResult(
                success=True,
                data=monitoring,
                metadata={
                    "keywords_tracked": len(keywords or []),
                    "alerts_generated": len(monitoring["alerts"]),
                },
            )

        except Exception as exc:
            self.logger.error("SEO monitoring failed", error=str(exc))
            return AgentResult(
                success=False,
                error=f"SEO monitoring failed: {exc}",
            )

    def _detect_anomalies(
        self, rankings: dict[str, Any], threshold: int
    ) -> list[dict[str, Any]]:
        """Detect ranking anomalies and generate alerts.

        Args:
            rankings: Ranking data dictionary.
            threshold: Minimum ranking change to trigger alert.

        Returns:
            List of alert dictionaries.
        """
        alerts = []

        for keyword, data in rankings.get("keywords", {}).items():
            current_position = data.get("current_position", 0)
            previous_position = data.get("previous_position", 0)

            if previous_position > 0 and current_position > 0:
                change = previous_position - current_position

                if abs(change) >= threshold:
                    alerts.append(
                        {
                            "type": "ranking_change",
                            "keyword": keyword,
                            "severity": "high" if abs(change) >= 10 else "medium",
                            "current_position": current_position,
                            "previous_position": previous_position,
                            "change": change,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

        return alerts

    def _analyze_trends(
        self, rankings: dict[str, Any], lookback_days: int
    ) -> dict[str, Any]:
        """Analyze ranking trends over time.

        Args:
            rankings: Ranking data dictionary.
            lookback_days: Number of days to analyze.

        Returns:
            Trends analysis dictionary.
        """
        return {
            "period_days": lookback_days,
            "improving_keywords": 0,
            "declining_keywords": 0,
            "stable_keywords": 0,
            "average_position_change": 0.0,
            "visibility_trend": "stable",
        }

    def _generate_summary(self, monitoring: dict[str, Any]) -> dict[str, Any]:
        """Generate monitoring summary.

        Args:
            monitoring: Complete monitoring data.

        Returns:
            Summary dictionary.
        """
        rankings = monitoring.get("rankings", {})
        alerts = monitoring.get("alerts", [])

        total_keywords = len(rankings.get("keywords", {}))
        high_alerts = len([a for a in alerts if a.get("severity") == "high"])

        return {
            "total_keywords_tracked": total_keywords,
            "total_alerts": len(alerts),
            "high_priority_alerts": high_alerts,
            "overall_status": "attention_needed" if high_alerts > 0 else "healthy",
            "last_updated": datetime.utcnow().isoformat(),
        }

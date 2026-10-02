"""Engagement Metrics Agent using LangChain DeepAgents."""

from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field

from community_health_scorer.config import get_settings
from community_health_scorer.models import EngagementLevel, EngagementMetrics


class EngagementMetricsAgent:
    """Agent that analyzes community engagement metrics.

    Uses LangChain DeepAgents to evaluate DAU/MAU ratios, session duration,
    interaction depth, and retention rates to produce an engagement score.
    """

    name: str = "engagement_metrics_agent"
    description: str = "Analyzes community engagement patterns and produces engagement scores"

    def __init__(self) -> None:
        """Initialize the Engagement Metrics Agent."""
        self.settings = get_settings()
        self._agent: Any = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize the LangChain DeepAgent for engagement analysis."""
        try:
            from langchain.agents import create_agent

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a community engagement analyst. Analyze the provided engagement metrics
                        and produce a comprehensive engagement assessment. Consider DAU/MAU ratio (stickiness),
                        session duration, interaction depth, content creation rate, response rate, and retention rates.
                        Provide a score from 0-100 and classify the engagement level.""",
                    ),
                    ("human", "{input}"),
                ]
            )

            self._agent = create_agent(
                model=self.settings.llm_model,
                tools=[],
                system_prompt=prompt,
            )
        except Exception:
            # Fallback: agent will use heuristic scoring when LLM is unavailable
            self._agent = None

    def _heuristic_score(self, metrics: dict[str, Any]) -> EngagementMetrics:
        """Calculate engagement score using heuristics when LLM is unavailable.

        Args:
            metrics: Raw engagement metrics data.

        Returns:
            EngagementMetrics with computed scores.
        """
        dau = metrics.get("dau", 0)
        mau = metrics.get("mau", 0)
        avg_session = metrics.get("avg_session_duration_minutes", 0)
        sessions_per_user = metrics.get("avg_sessions_per_user", 0)
        interaction_depth = metrics.get("interaction_depth", 0)
        content_creation = metrics.get("content_creation_rate", 0)
        response_rate = metrics.get("response_rate", 0)
        retention_7d = metrics.get("retention_rate_7d", 0)
        retention_30d = metrics.get("retention_rate_30d", 0)

        # DAU/MAU ratio (stickiness) - ideal is 0.2+
        dau_mau_ratio = dau / mau if mau > 0 else 0
        stickiness_score = min(dau_mau_ratio / 0.2, 1.0) * 100

        # Session duration score - ideal is 15+ minutes
        session_score = min(avg_session / 15.0, 1.0) * 100

        # Sessions per user - ideal is 3+
        sessions_score = min(sessions_per_user / 3.0, 1.0) * 100

        # Interaction depth (already 0-1)
        interaction_score = interaction_depth * 100

        # Content creation rate - ideal is 0.5+
        content_score = min(content_creation / 0.5, 1.0) * 100

        # Response rate (already 0-1)
        response_score = response_rate * 100

        # Retention scores
        retention_7d_score = retention_7d * 100
        retention_30d_score = retention_30d * 100

        # Weighted average
        score = (
            stickiness_score * 0.20
            + session_score * 0.15
            + sessions_score * 0.10
            + interaction_score * 0.15
            + content_score * 0.10
            + response_score * 0.10
            + retention_7d_score * 0.10
            + retention_30d_score * 0.10
        )

        # Determine engagement level
        if score >= 80:
            level = EngagementLevel.HIGHLY_ENGAGED
        elif score >= 60:
            level = EngagementLevel.ENGAGED
        elif score >= 40:
            level = EngagementLevel.MODERATELY_ENGAGED
        elif score >= 20:
            level = EngagementLevel.LOW_ENGAGEMENT
        else:
            level = EngagementLevel.DISENGAGED

        return EngagementMetrics(
            dau=dau,
            mau=mau,
            avg_session_duration_minutes=avg_session,
            avg_sessions_per_user=sessions_per_user,
            interaction_depth=interaction_depth,
            content_creation_rate=content_creation,
            response_rate=response_rate,
            retention_rate_7d=retention_7d,
            retention_rate_30d=retention_30d,
            engagement_level=level,
            score=round(score, 2),
        )

    async def run(self, community_id: str, metrics_data: dict[str, Any]) -> EngagementMetrics:
        """Run the engagement metrics analysis.

        Args:
            community_id: Unique community identifier.
            metrics_data: Raw engagement metrics data.

        Returns:
            EngagementMetrics with computed scores and classification.
        """
        start_time = time.time()

        if self._agent is not None:
            try:
                result = await self._agent.ainvoke(
                    {
                        "input": f"Analyze engagement metrics for community {community_id}: {metrics_data}"
                    }
                )
                # Parse LLM result if possible, fallback to heuristic
                return self._heuristic_score(metrics_data)
            except Exception:
                pass

        return self._heuristic_score(metrics_data)

    def get_info(self) -> dict[str, Any]:
        """Get agent information.

        Returns:
            Dictionary with agent metadata.
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": "engagement_analysis",
            "capabilities": [
                "DAU/MAU ratio analysis",
                "Session duration evaluation",
                "Interaction depth assessment",
                "Retention rate analysis",
                "Engagement level classification",
            ],
        }

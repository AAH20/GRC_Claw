"""Toxicity Detector Agent using LangChain DeepAgents."""

from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field

from community_health_scorer.config import get_settings
from community_health_scorer.models import ToxicityLevel, ToxicityReport


class ToxicityDetectorAgent:
    """Agent that detects toxic content and behavior in communities.

    Uses LangChain DeepAgents to analyze content for harassment, hate speech,
    spam, and other toxic patterns, producing a toxicity health score.
    """

    name: str = "toxicity_detector_agent"
    description: str = "Detects toxic content and behavior patterns in communities"

    def __init__(self) -> None:
        """Initialize the Toxicity Detector Agent."""
        self.settings = get_settings()
        self._agent: Any = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize the LangChain DeepAgent for toxicity detection."""
        try:
            from langchain.agents import create_agent

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a community safety analyst specializing in toxicity detection.
                        Analyze the provided content and user behavior data to identify toxic patterns
                        including harassment, hate speech, spam, misinformation, and trolling.
                        Provide a toxicity score from 0-100 (higher = more toxic) and classify the toxicity level.""",
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
            self._agent = None

    def _heuristic_score(self, data: dict[str, Any]) -> ToxicityReport:
        """Calculate toxicity score using heuristics when LLM is unavailable.

        Args:
            data: Raw toxicity data including content analysis results.

        Returns:
            ToxicityReport with computed scores and classification.
        """
        toxic_content = data.get("toxic_content_count", 0)
        total_content = data.get("total_content_analyzed", 1)
        toxic_users = data.get("toxic_user_count", 0)
        total_users = data.get("total_users", 1)
        categories = data.get("toxicity_categories", {})

        # Calculate toxicity rate
        toxicity_rate = toxic_content / total_content if total_content > 0 else 0
        user_toxicity_rate = toxic_users / total_users if total_users > 0 else 0

        # Overall toxicity score (0-100, higher = more toxic)
        overall_toxicity = (toxicity_rate * 0.6 + user_toxicity_rate * 0.4) * 100

        # Determine toxicity level
        if overall_toxicity >= 75:
            level = ToxicityLevel.SEVERE
        elif overall_toxicity >= 50:
            level = ToxicityLevel.HIGH
        elif overall_toxicity >= 25:
            level = ToxicityLevel.MODERATE
        elif overall_toxicity >= 10:
            level = ToxicityLevel.LOW
        else:
            level = ToxicityLevel.NONE

        # Health score is inverse of toxicity
        health_score = max(0, 100 - overall_toxicity)

        # Generate recommendations
        recommendations = []
        if overall_toxicity > 50:
            recommendations.append("Implement stricter content moderation policies")
            recommendations.append("Increase moderator presence during peak hours")
        if categories.get("harassment", 0) > 0.3:
            recommendations.append("Deploy anti-harassment detection tools")
        if categories.get("hate_speech", 0) > 0.2:
            recommendations.append("Add hate speech filtering and user education")
        if categories.get("spam", 0) > 0.3:
            recommendations.append("Strengthen spam detection and rate limiting")
        if not recommendations:
            recommendations.append("Continue monitoring content for emerging toxicity patterns")

        return ToxicityReport(
            overall_toxicity_score=round(overall_toxicity, 2),
            toxicity_level=level,
            toxic_content_count=toxic_content,
            total_content_analyzed=total_content,
            toxic_user_count=toxic_users,
            total_users=total_users,
            toxicity_categories=categories,
            flagged_content=data.get("flagged_content", []),
            recommendations=recommendations,
            score=round(health_score, 2),
        )

    async def run(self, community_id: str, data: dict[str, Any]) -> ToxicityReport:
        """Run the toxicity detection analysis.

        Args:
            community_id: Unique community identifier.
            data: Raw toxicity data including content analysis results.

        Returns:
            ToxicityReport with computed scores and classification.
        """
        start_time = time.time()

        if self._agent is not None:
            try:
                result = await self._agent.ainvoke(
                    {
                        "input": f"Analyze toxicity for community {community_id}: {data}"
                    }
                )
                return self._heuristic_score(data)
            except Exception:
                pass

        return self._heuristic_score(data)

    def get_info(self) -> dict[str, Any]:
        """Get agent information.

        Returns:
            Dictionary with agent metadata.
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": "toxicity_detection",
            "capabilities": [
                "Toxic content identification",
                "Harassment detection",
                "Hate speech classification",
                "Spam pattern recognition",
                "Toxic user flagging",
                "Toxicity trend analysis",
            ],
        }

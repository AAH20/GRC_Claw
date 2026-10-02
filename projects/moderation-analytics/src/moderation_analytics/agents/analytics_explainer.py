"""Analytics Explainer Agent implementation."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate

from moderation_analytics.agents import BaseAgent


class AnalyticsExplainerAgent(BaseAgent[str]):
    """Agent that generates human-readable explanations of analytics.

    Translates complex analytics data into clear, actionable insights
    for non-technical stakeholders.
    """

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Analytics Explainer Agent.

        Args:
            llm: Optional pre-configured language model.
        """
        super().__init__(name="AnalyticsExplainer", llm=llm)
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at explaining complex analytics data in simple, "
                    "clear language. Focus on actionable insights and avoid jargon. "
                    "Your explanations should be understandable by non-technical stakeholders.",
                ),
                (
                    "human",
                    "Explain the following moderation analytics data in clear, "
                    "understandable language:\n\n{analytics_data}\n\n"
                    "Provide a summary that highlights key findings and actionable insights.",
                ),
            ]
        )

    async def run(
        self,
        analytics_data: dict[str, Any],
        audience: str = "general",
        **kwargs: Any,
    ) -> str:
        """Generate human-readable explanation of analytics.

        Args:
            analytics_data: Analytics data to explain.
            audience: Target audience (general, technical, executive).
            **kwargs: Additional parameters.

        Returns:
            str: Human-readable explanation.

        Raises:
            ValueError: If analytics_data is empty.
        """
        self._log_start(audience=audience)

        if not analytics_data:
            raise ValueError("Cannot explain empty analytics data")

        # Use LLM for natural language generation
        if self._settings.openai_api_key:
            try:
                explanation = await self._llm_explain(analytics_data, audience)
                self._log_complete(explanation)
                return explanation
            except Exception as e:
                self._log_error(e, fallback="using template-based explanation")

        # Fallback to template-based explanation
        explanation = self._template_explain(analytics_data)
        self._log_complete(explanation)
        return explanation

    async def _llm_explain(self, data: dict[str, Any], audience: str) -> str:
        """Use LLM to generate explanation.

        Args:
            data: Analytics data.
            audience: Target audience.

        Returns:
            str: LLM-generated explanation.
        """
        response = await self._prompt.ainvoke(
            {
                "analytics_data": str(data),
                "audience": audience,
            }
        )
        return str(response.content)

    def _template_explain(self, data: dict[str, Any]) -> str:
        """Generate template-based explanation.

        Args:
            data: Analytics data.

        Returns:
            str: Template-based explanation.
        """
        parts = ["Moderation Analytics Summary", "=" * 30, ""]

        if "total_events" in data:
            parts.append(f"Total moderation events: {data['total_events']}")
        if "total_actions" in data:
            parts.append(f"Total actions taken: {data['total_actions']}")
        if "average_response_time_seconds" in data:
            parts.append(
                f"Average response time: {data['average_response_time_seconds']:.2f}s"
            )

        if "trends" in data and data["trends"]:
            parts.extend(["", "Key Trends:"])
            for trend in data["trends"][:5]:
                parts.append(f"  - {trend.get('description', 'N/A')}")

        return "\n".join(parts)

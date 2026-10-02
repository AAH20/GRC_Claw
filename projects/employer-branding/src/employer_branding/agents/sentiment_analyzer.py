"""Sentiment Analyzer Agent for analyzing text sentiment."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from employer_branding.agents.base import BaseAgent
from employer_branding.models import SentimentAnalysisRequest, SentimentLabel, SentimentReport


class SentimentAnalyzerAgent(BaseAgent[SentimentReport]):
    """Agent that performs sentiment analysis on text.

    Analyzes overall sentiment, detects emotions, performs aspect-based
    analysis, and extracts sentiment-bearing keywords from text.
    """

    def __init__(self) -> None:
        """Initialize the sentiment analyzer agent."""
        super().__init__()
        self._prompt_template = self._build_prompt_template()

    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build the prompt template for sentiment analysis.

        Returns:
            Configured ChatPromptTemplate.
        """
        system_message = """You are an expert sentiment analysis engine.
Analyze the provided text and return a JSON object with the following structure:
{
    "overall_sentiment": "very_positive|positive|neutral|negative|very_negative",
    "sentiment_score": float between -1.0 and 1.0,
    "confidence": float between 0.0 and 1.0,
    "aspects": [{"aspect": "string", "sentiment": "string", "score": float}],
    "keywords": ["sentiment-bearing keywords"],
    "emotions": {"joy": float, "anger": float, "sadness": float, "fear": float, "surprise": float},
    "language": "detected language code"
}

Be precise and objective in your analysis. Consider context, sarcasm, and nuance."""

        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            HumanMessage(content="{input}"),
        ])

    async def run(self, request: SentimentAnalysisRequest) -> SentimentReport:
        """Analyze sentiment of the provided text.

        Args:
            request: Sentiment analysis request with text and options.

        Returns:
            SentimentReport with detailed analysis results.

        Raises:
            ValueError: If text is empty or invalid.
            RuntimeError: If analysis fails or response parsing fails.
        """
        self.logger.info(
            "analyzing_sentiment",
            text_length=len(request.text),
            analyze_aspects=request.analyze_aspects,
            detect_emotions=request.detect_emotions,
        )

        try:
            prompt = self._build_analysis_prompt(request)
            response = await self._model.ainvoke(prompt)
            raw_content = response.content if hasattr(response, "content") else str(response)

            parsed = self._parse_response(raw_content)

            report = SentimentReport(
                source_text=request.text,
                overall_sentiment=SentimentLabel(parsed["overall_sentiment"]),
                sentiment_score=parsed["sentiment_score"],
                confidence=parsed["confidence"],
                aspects=parsed.get("aspects", []),
                keywords=parsed.get("keywords", []),
                emotions=parsed.get("emotions", {}),
                language=parsed.get("language", request.language or "en"),
            )

            self.logger.info(
                "sentiment_analyzed",
                report_id=str(report.id),
                sentiment=report.overall_sentiment.value,
                score=report.sentiment_score,
            )
            return report

        except Exception as exc:
            self.logger.error("sentiment_analysis_failed", error=str(exc))
            raise RuntimeError(f"Failed to analyze sentiment: {exc}") from exc

    def _build_analysis_prompt(self, request: SentimentAnalysisRequest) -> str:
        """Build the analysis prompt from request.

        Args:
            request: Sentiment analysis request.

        Returns:
            Formatted prompt string.
        """
        parts = [f"Analyze the sentiment of this text:\n\n{request.text}"]

        if request.analyze_aspects:
            parts.append("\nInclude aspect-based sentiment analysis.")
        if request.detect_emotions:
            parts.append("Include emotion detection scores.")
        if request.language:
            parts.append(f"\nText language: {request.language}")

        return "\n".join(parts)

    def _parse_response(self, raw_content: str) -> dict[str, Any]:
        """Parse the LLM response into a structured dictionary.

        Args:
            raw_content: Raw response content from the model.

        Returns:
            Parsed dictionary with sentiment data.

        Raises:
            ValueError: If response cannot be parsed as valid JSON.
        """
        # Handle potential markdown code blocks
        content = raw_content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse sentiment analysis response: {exc}") from exc

        # Validate required fields
        required = ["overall_sentiment", "sentiment_score", "confidence"]
        for field in required:
            if field not in parsed:
                raise ValueError(f"Missing required field in response: {field}")

        return parsed

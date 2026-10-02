"""Response Agent - Generates response suggestions for negative mentions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog

from brand_monitoring.agents.analysis import AnalysisResult, Sentiment

logger = structlog.get_logger(__name__)


class ResponseType(StrEnum):
    """Type of response to generate."""

    APOLOGY = "apology"
    THANK_YOU = "thank_you"
    INFORMATION = "information"
    ESCALATION = "escalation"
    NO_RESPONSE = "no_response"


class ResponseChannel(StrEnum):
    """Channel for the response."""

    TWITTER = "twitter"
    REDDIT = "reddit"
    EMAIL = "email"
    INTERNAL = "internal"


@dataclass
class ResponseSuggestion:
    """A suggested response to a brand mention."""

    mention_id: str
    response_type: ResponseType
    channel: ResponseChannel
    content: str
    confidence: float
    requires_approval: bool
    created_at: datetime
    metadata: dict[str, Any]


class ResponseAgent:
    """Agent responsible for generating response suggestions."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = logger.bind(agent="response")
        self._auto_respond = config.get("auto_respond", False)
        self._approval_required = config.get("approval_required", True)
        self._max_length = config.get("max_response_length", 280)
        self._templates = self._load_templates()

    def _load_templates(self) -> dict[ResponseType, list[str]]:
        """Load response templates."""
        return {
            ResponseType.APOLOGY: [
                "We're sorry to hear about your experience. We'd like to make it right. "
                "Please DM us so we can help.",
                "We apologize for the inconvenience. Our team is looking into this right away.",
            ],
            ResponseType.THANK_YOU: [
                "Thank you for your kind words! We're glad you're enjoying our product.",
                "We appreciate your feedback! It means a lot to our team.",
            ],
            ResponseType.INFORMATION: [
                "Thanks for reaching out! Here's some information that might help: [link]",
                "We'd be happy to help! Check out our FAQ at [link] or DM us for assistance.",
            ],
            ResponseType.ESCALATION: [
                "We understand your concern and want to escalate this to our support team. "
                "Please expect a response within 24 hours.",
                "This sounds important. We're connecting you with a specialist who can help "
                "right away.",
            ],
            ResponseType.NO_RESPONSE: [],
        }

    async def generate_response(
        self,
        mention: Any,
        analysis: AnalysisResult,
    ) -> ResponseSuggestion | None:
        """Generate a response suggestion for a mention."""
        self.logger.info(
            "Generating response",
            mention_id=mention.id,
            sentiment=analysis.sentiment.value,
        )

        response_type = self._determine_response_type(analysis)
        if response_type == ResponseType.NO_RESPONSE:
            self.logger.info("No response needed", mention_id=mention.id)
            return None

        channel = self._determine_channel(mention)
        content = self._generate_content(response_type, mention, analysis)
        confidence = self._calculate_confidence(analysis)
        requires_approval = self._requires_approval(response_type, confidence)

        suggestion = ResponseSuggestion(
            mention_id=mention.id,
            response_type=response_type,
            channel=channel,
            content=content,
            confidence=confidence,
            requires_approval=requires_approval,
            created_at=datetime.utcnow(),
            metadata={"auto_respond": self._auto_respond and not requires_approval},
        )

        self.logger.info(
            "Response generated",
            mention_id=mention.id,
            response_type=response_type.value,
            confidence=confidence,
        )
        return suggestion

    async def generate_batch(
        self,
        mentions_with_analysis: list[tuple[Any, AnalysisResult]],
    ) -> list[ResponseSuggestion]:
        """Generate responses for a batch of mentions."""
        self.logger.info("Starting batch response generation", count=len(mentions_with_analysis))
        suggestions: list[ResponseSuggestion] = []
        for mention, analysis in mentions_with_analysis:
            try:
                suggestion = await self.generate_response(mention, analysis)
                if suggestion:
                    suggestions.append(suggestion)
            except Exception as exc:
                self.logger.error(
                    "Failed to generate response",
                    mention_id=getattr(mention, "id", "unknown"),
                    error=str(exc),
                )
        self.logger.info("Batch response generation complete", generated=len(suggestions))
        return suggestions

    def _determine_response_type(self, analysis: AnalysisResult) -> ResponseType:
        """Determine the appropriate response type."""
        if analysis.sentiment == Sentiment.NEGATIVE:
            if analysis.urgency >= 4:
                return ResponseType.ESCALATION
            return ResponseType.APOLOGY
        if analysis.sentiment == Sentiment.POSITIVE:
            return ResponseType.THANK_YOU
        if analysis.sentiment == Sentiment.MIXED:
            return ResponseType.INFORMATION
        return ResponseType.NO_RESPONSE

    def _determine_channel(self, mention: Any) -> ResponseChannel:
        """Determine the response channel based on the mention platform."""
        platform = getattr(mention, "platform", "")
        if platform == "twitter":
            return ResponseChannel.TWITTER
        if platform == "reddit":
            return ResponseChannel.REDDIT
        return ResponseChannel.EMAIL

    def _generate_content(
        self,
        response_type: ResponseType,
        mention: Any,
        analysis: AnalysisResult,
    ) -> str:
        """Generate response content."""
        templates = self._templates.get(response_type, [])
        if not templates:
            return ""

        content = templates[0]

        if len(content) > self._max_length:
            content = content[: self._max_length - 3] + "..."

        return content

    def _calculate_confidence(self, analysis: AnalysisResult) -> float:
        """Calculate confidence score for the response."""
        base_confidence = 0.7

        if analysis.sentiment in (Sentiment.POSITIVE, Sentiment.NEGATIVE):
            base_confidence += 0.15

        if analysis.sentiment == Sentiment.MIXED:
            base_confidence -= 0.1

        base_confidence += abs(analysis.sentiment_score) * 0.1

        return min(max(base_confidence, 0.0), 1.0)

    def _requires_approval(self, response_type: ResponseType, confidence: float) -> bool:
        """Determine if the response requires human approval."""
        if self._approval_required:
            return True
        if response_type == ResponseType.ESCALATION:
            return True
        return confidence < 0.8

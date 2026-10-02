"""Response Agent - generates personalized responses to feedback."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

from feedback_management.agents.analysis import AnalysisResult
from feedback_management.agents.collection import FeedbackItem

logger = structlog.get_logger(__name__)


class ResponseDraft(BaseModel):
    """A generated response draft for a feedback item."""

    feedback_id: str
    subject: str = ""
    body: str
    tone: str = "professional"
    language: str = "en"
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    requires_approval: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResponseResult(BaseModel):
    """Result of response generation for a batch of items."""

    drafts: list[ResponseDraft] = Field(default_factory=list)
    total_generated: int = 0
    total_requiring_approval: int = 0


class ResponseAgent:
    """Agent responsible for generating personalized responses to feedback.

    Uses LLM-powered response generation based on analysis results,
    maintaining brand voice and appropriate tone for each situation.
    """

    def __init__(
        self,
        llm: Any = None,
        tone: str = "professional",
        language: str = "en",
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the Response Agent.

        Args:
            llm: Language model for response generation.
            tone: Default tone for responses (professional, friendly, empathetic).
            language: Default language for responses.
            max_tokens: Maximum tokens for generated responses.
            temperature: Sampling temperature for generation.
        """
        self.llm = llm
        self.tone = tone
        self.language = language
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def generate_response(
        self,
        item: FeedbackItem,
        analysis: AnalysisResult,
    ) -> ResponseDraft:
        """Generate a response for a single feedback item.

        Args:
            item: The original feedback item.
            analysis: Analysis result for the feedback.

        Returns:
            ResponseDraft with the generated response.
        """
        logger.info(
            "Generating response",
            feedback_id=item.id,
            sentiment=analysis.sentiment.label,
            priority=analysis.suggested_priority,
        )

        if self.llm:
            body = await self._generate_with_llm(item, analysis)
        else:
            body = self._generate_template_response(item, analysis)

        requires_approval = self._requires_approval(analysis)

        return ResponseDraft(
            feedback_id=item.id,
            subject=self._generate_subject(item, analysis),
            body=body,
            tone=self._select_tone(analysis),
            language=analysis.language_detected or self.language,
            requires_approval=requires_approval,
            metadata={
                "sentiment": analysis.sentiment.label,
                "priority": analysis.suggested_priority,
                "topics": [t.name for t in analysis.topics],
            },
        )

    async def generate_batch(
        self,
        items: list[FeedbackItem],
        analyses: list[AnalysisResult],
    ) -> ResponseResult:
        """Generate responses for a batch of feedback items.

        Args:
            items: List of feedback items.
            analyses: List of analysis results corresponding to items.

        Returns:
            ResponseResult with all generated drafts.
        """
        import asyncio

        if len(items) != len(analyses):
            raise ValueError("Items and analyses must have the same length")

        drafts = await asyncio.gather(
            *[self.generate_response(item, analysis) for item, analysis in zip(items, analyses)]
        )

        result = ResponseResult(
            drafts=list(drafts),
            total_generated=len(drafts),
            total_requiring_approval=sum(1 for d in drafts if d.requires_approval),
        )

        logger.info(
            "Batch response generation complete",
            total=result.total_generated,
            requiring_approval=result.total_requiring_approval,
        )

        return result

    async def _generate_with_llm(self, item: FeedbackItem, analysis: AnalysisResult) -> str:
        """Generate response using the configured LLM.

        Args:
            item: The feedback item.
            analysis: Analysis result.

        Returns:
            Generated response text.
        """
        prompt = self._build_prompt(item, analysis)

        try:
            response = await self.llm.ainvoke(prompt)
            if hasattr(response, "content"):
                return response.content.strip()
            return str(response).strip()
        except Exception as exc:
            logger.error("LLM response generation failed, using template", error=str(exc))
            return self._generate_template_response(item, analysis)

    def _build_prompt(self, item: FeedbackItem, analysis: AnalysisResult) -> str:
        """Build the prompt for LLM response generation.

        Args:
            item: The feedback item.
            analysis: Analysis result.

        Returns:
            Formatted prompt string.
        """
        topics_str = (
            ", ".join(t.name.replace("_", " ") for t in analysis.topics) or "general feed"
            "back")

        return f"""You are a customer feedback response specialist. Write a {self.tone} response to the following customer feedback.  # noqa: E501

Customer Feedback:
- Rating: {item.rating or "N/A"}/5
- Text: {item.text}
- Topics: {topics_str}
- Sentiment: {analysis.sentiment.label} (score: {analysis.sentiment.score:.2f})
- Priority: {analysis.suggested_priority}
- Summary: {analysis.summary}

Requirements:
- Acknowledge the customer's feedback specifically
- Address the main topics: {topics_str}
- Match the tone to the sentiment (empathetic for negative, appreciative for positive)
- Keep it concise (under 200 words)
- Include a clear next step or call to action
- Do not make promises that cannot be kept
- Sign off appropriately

Response:"""

    def _generate_template_response(self, item: FeedbackItem, analysis: AnalysisResult) -> str:
        """Generate a template-based response when LLM is unavailable.

        Args:
            item: The feedback item.
            analysis: Analysis result.

        Returns:
            Template-based response text.
        """
        sentiment = analysis.sentiment.label
        topics_str = (
            ", ".join(t.name.replace("_", " ") for t in analysis.topics[:2]) or "your fee"
            "dback")

        if sentiment == "negative":
            return self._negative_template(item, topics_str, analysis)
        elif sentiment == "positive":
            return self._positive_template(item, topics_str, analysis)
        else:
            return self._neutral_template(item, topics_str, analysis)

    def _negative_template(self,
        item: FeedbackItem, topics_str: str, analysis: AnalysisResult) -> str:
        """Generate a template response for negative feedback."""
        return f"""Dear Valued Customer,

Thank you for taking the time to share your feedback with us. We sincerely apologize that your experience with {topics_str} did not meet your expectations.  # noqa: E501

We take your concerns seriously
    and want to make this right. Your feedback has been escalated to our team, and a representative will reach out to you within 24 hours to discuss how we can improve your experience.  # noqa: E501

If you have any additional details you'd like to share, please don't hesitate to reply to this message.  # noqa: E501

We appreciate your patience and the opportunity to serve you better.

Best regards,
Customer Experience Team"""

    def _positive_template(self,
        item: FeedbackItem, topics_str: str, analysis: AnalysisResult) -> str:
        """Generate a template response for positive feedback."""
        return f"""Dear Valued Customer,

Thank you so much for your wonderful feedback! We're thrilled to hear that you had a great experience with {topics_str}.  # noqa: E501

Your satisfaction is our top priority,
    and it's customers like you that make our work rewarding. We look forward to serving you again soon.  # noqa: E501

If there's anything else we can do for you, please don't hesitate to reach out.

Best regards,
Customer Experience Team"""

    def _neutral_template(self,
        item: FeedbackItem, topics_str: str, analysis: AnalysisResult) -> str:
        """Generate a template response for neutral feedback."""
        return f"""Dear Valued Customer,

Thank you for your feedback regarding {topics_str}. We appreciate you taking the time to share your thoughts with us.  # noqa: E501

Your input helps us improve our products and services. If you have any additional suggestions
    or questions, please feel free to reach out.

We look forward to serving you again.

Best regards,
Customer Experience Team"""

    def _generate_subject(self, item: FeedbackItem, analysis: AnalysisResult) -> str:
        """Generate an email subject line for the response."""
        if analysis.sentiment.label == "negative":
            return "We're sorry - we're here to help"
        elif analysis.sentiment.label == "positive":
            return "Thank you for your feedback!"
        else:
            return "Thank you for reaching out"

    def _select_tone(self, analysis: AnalysisResult) -> str:
        """Select the appropriate tone based on analysis."""
        if analysis.sentiment.label == "negative":
            return "empathetic"
        elif analysis.sentiment.label == "positive":
            return "appreciative"
        return self.tone

    def _requires_approval(self, analysis: AnalysisResult) -> bool:
        """Determine if the response requires human approval."""
        if analysis.sentiment.score < -0.5:
            return True
        if analysis.urgency_score > 0.7:
            return True
        if analysis.suggested_priority == "high":
            return True
        return False

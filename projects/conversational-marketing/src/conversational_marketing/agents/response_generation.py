"""Response Generation Agent for creating marketing responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from conversational_marketing.config.settings import get_settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

    from conversational_marketing.agents.intent_detection import Intent, IntentResult

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class ResponseResult:
    """Result of response generation."""

    response: str
    intent: Intent
    metadata: dict[str, Any] = field(default_factory=dict)


class ResponseGenerationAgent:
    """Agent responsible for generating contextually appropriate marketing responses.

    Uses LLM-based generation with intent awareness and conversation context
    to produce personalized, on-brand responses.
    """

    SYSTEM_PROMPT = """You are a conversational marketing assistant for a B2B SaaS company.
Your goal is to engage prospects, answer questions, and guide them toward purchase.

Guidelines:
- Be professional yet friendly and conversational
- Keep responses concise (2-3 sentences unless detail is needed)
- Always include a relevant call-to-action when appropriate
- Personalize based on the user's intent and context
- Never make promises about pricing or features without certainty
- If unsure, offer to connect them with a human specialist

Tone: {tone}
Max response length: {max_length} characters
"""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the Response Generation Agent.

        Args:
            llm: Optional LangChain chat model. If not provided, creates default.
        """
        self._llm = llm or self._create_default_llm()
        self._max_length = settings.agents.response_generation.max_response_length
        self._tone = settings.agents.response_generation.tone

    @staticmethod
    def _create_default_llm() -> BaseChatModel:
        """Create default LLM instance.

        Returns:
            Configured chat model instance.

        Raises:
            ValueError: If OPENAI_API_KEY is not configured.
        """
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for response generation")

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm.model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            api_key=api_key,
        )

    async def generate(
        self,
        message: str,
        intent_result: IntentResult,
        context: list[dict[str, str]] | None = None,
        user_profile: dict[str, Any] | None = None,
    ) -> ResponseResult:
        """Generate a response to a user message.

        Args:
            message: The user's original message.
            intent_result: Detected intent from IntentDetectionAgent.
            context: Optional conversation history.
            user_profile: Optional user information for personalization.

        Returns:
            ResponseResult with generated response text and metadata.

        Raises:
            ValueError: If message is empty.
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        system_content = self.SYSTEM_PROMPT.format(
            tone=self._tone,
            max_length=self._max_length,
        )

        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(content=system_content)
        ]

        if user_profile:
            profile_text = "\n".join(f"{k}: {v}" for k, v in user_profile.items())
            messages.append(HumanMessage(content=f"User profile:\n{profile_text}"))

        if context:
            for msg in context[-10:]:
                role = "Assistant" if msg["role"] == "assistant" else "User"
                messages.append(HumanMessage(content=f"{role}: {msg['content']}"))

        messages.append(
            HumanMessage(
                content=f"[Intent: {intent_result.intent.value}, "
                f"Confidence: {intent_result.confidence:.2f}]\n"
                f"User message: {message}"
            )
        )

        try:
            response = await self._llm.ainvoke(messages)
            response_text = (
                response.content if isinstance(response.content, str) else str(response.content)
            )

            # Truncate if exceeds max length
            if len(response_text) > self._max_length:
                response_text = response_text[: self._max_length - 3] + "..."

            logger.info(
                "Response generated",
                intent=intent_result.intent.value,
                response_length=len(response_text),
            )

            return ResponseResult(
                response=response_text,
                intent=intent_result.intent,
                metadata={
                    "confidence": intent_result.confidence,
                    "response_length": len(response_text),
                },
            )

        except Exception as exc:
            logger.error("Response generation failed", error=str(exc))
            return ResponseResult(
                response="I apologize, but I'm having trouble processing your request. "
                "Let me connect you with a team member who can help.",
                intent=intent_result.intent,
                metadata={"error": str(exc)},
            )

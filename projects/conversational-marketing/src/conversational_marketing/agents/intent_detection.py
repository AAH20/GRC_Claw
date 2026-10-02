"""Intent Detection Agent for classifying user messages into marketing intents."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from conversational_marketing.config.settings import get_settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = structlog.get_logger(__name__)
settings = get_settings()


class Intent(str, Enum):
    """Enumeration of supported marketing intents."""

    PURCHASE_INTENT = "purchase_intent"
    PRODUCT_INQUIRY = "product_inquiry"
    SUPPORT_REQUEST = "support_request"
    COMPLAINT = "complaint"
    PRICING_QUESTION = "pricing_question"
    DEMO_REQUEST = "demo_request"
    GENERAL_INQUIRY = "general_inquiry"
    GREETING = "greeting"
    FAREWELL = "farewell"


@dataclass(frozen=True)
class IntentResult:
    """Result of intent detection."""

    intent: Intent
    confidence: float
    metadata: dict[str, Any]


class IntentDetectionAgent:
    """Agent responsible for detecting user intent from conversation messages.

    Uses LLM-based classification to determine the marketing intent behind
    user messages, enabling appropriate response routing and handling.
    """

    SYSTEM_PROMPT = """You are an intent detection system for a conversational marketing platform.
Analyze the user's message and classify it into exactly one of the following intents:
- purchase_intent: User wants to buy or is close to purchasing
- product_inquiry: User asks about product features, capabilities, or details
- support_request: User needs help with an existing product or service
- complaint: User expresses dissatisfaction or reports a problem
- pricing_question: User asks about costs, plans, or pricing
- demo_request: User wants a product demonstration or trial
- general_inquiry: General question that doesn't fit other categories
- greeting: User is saying hello or starting a conversation
- farewell: User is saying goodbye or ending a conversation

Respond with JSON only: {"intent": "<intent_name>", "confidence": <float 0-1>}
"""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the Intent Detection Agent.

        Args:
            llm: Optional LangChain chat model. If not provided, creates default.
        """
        self._llm = llm or self._create_default_llm()
        self._confidence_threshold = settings.agents.intent_detection.confidence_threshold
        self._fallback_intent = Intent(settings.agents.intent_detection.fallback_intent)

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
            raise ValueError("OPENAI_API_KEY is required for intent detection")

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm.model,
            temperature=0.1,
            max_tokens=100,
            api_key=api_key,
        )

    async def detect(
        self, message: str, context: list[dict[str, str]] | None = None
    ) -> IntentResult:
        """Detect the intent of a user message.

        Args:
            message: The user's message text.
            context: Optional conversation history for context-aware detection.

        Returns:
            IntentResult with detected intent and confidence score.

        Raises:
            ValueError: If message is empty.
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        messages: list[SystemMessage | HumanMessage] = [
            SystemMessage(content=self.SYSTEM_PROMPT)
        ]

        if context:
            context_text = "\n".join(
                f"{msg['role']}: {msg['content']}" for msg in context[-5:]
            )
            messages.append(HumanMessage(content=f"Conversation context:\n{context_text}"))

        messages.append(HumanMessage(content=f"Current message: {message}"))

        try:
            response = await self._llm.ainvoke(messages)
            result = self._parse_response(response.content)

            if result.confidence < self._confidence_threshold:
                logger.info(
                    "Low confidence intent detection, using fallback",
                    detected_intent=result.intent.value,
                    confidence=result.confidence,
                    fallback_intent=self._fallback_intent.value,
                )
                return IntentResult(
                    intent=self._fallback_intent,
                    confidence=result.confidence,
                    metadata={"original_intent": result.intent.value, "low_confidence": True},
                )

            logger.info(
                "Intent detected",
                intent=result.intent.value,
                confidence=result.confidence,
            )
            return result

        except Exception as exc:
            logger.error("Intent detection failed", error=str(exc))
            return IntentResult(
                intent=self._fallback_intent,
                confidence=0.0,
                metadata={"error": str(exc)},
            )

    def _parse_response(self, content: str | list[str | dict]) -> IntentResult:
        """Parse LLM response into IntentResult.

        Args:
            content: Raw LLM response content.

        Returns:
            Parsed IntentResult.

        Raises:
            ValueError: If response cannot be parsed.
        """
        import json

        text = content if isinstance(content, str) else str(content)

        # Extract JSON from response
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"Failed to parse intent response: {text}") from exc

        intent_str = data.get("intent", self._fallback_intent.value)
        confidence = float(data.get("confidence", 0.0))

        try:
            intent = Intent(intent_str)
        except ValueError:
            intent = self._fallback_intent

        return IntentResult(intent=intent, confidence=confidence, metadata={})

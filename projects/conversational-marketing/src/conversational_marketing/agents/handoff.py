"""Handoff Agent for determining when to escalate to human agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from conversational_marketing.agents.intent_detection import Intent, IntentResult
from conversational_marketing.config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class HandoffReason(str, Enum):
    """Reasons for handing off to a human agent."""

    LOW_CONFIDENCE = "low_confidence"
    EXPLICIT_REQUEST = "explicit_request"
    COMPLAINT_ESCALATION = "complaint_escalation"
    MAX_TURNS_REACHED = "max_turns_reached"
    HIGH_VALUE_LEAD = "high_value_lead"
    COMPLEX_QUERY = "complex_query"


class HandoffPriority(str, Enum):
    """Priority levels for handoff."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class HandoffDecision:
    """Decision result from the Handoff Agent."""

    should_handoff: bool
    reason: HandoffReason | None = None
    priority: HandoffPriority = HandoffPriority.LOW
    metadata: dict[str, Any] = field(default_factory=dict)


class HandoffAgent:
    """Agent responsible for determining when conversations should be escalated.

    Evaluates conversation state, intent confidence, user requests, and
    business rules to decide when human intervention is needed.
    """

    def __init__(self) -> None:
        """Initialize the Handoff Agent with configuration."""
        self._enabled = settings.agents.handoff.enabled
        self._confidence_threshold = settings.agents.handoff.confidence_threshold
        self._max_turns = settings.agents.handoff.max_agent_turns
        self._escalation_rules = settings.agents.handoff.escalation_rules

    async def evaluate(
        self,
        intent_result: IntentResult,
        conversation_turns: int,
        user_message: str,
        context: list[dict[str, str]] | None = None,
    ) -> HandoffDecision:
        """Evaluate whether a conversation should be handed off to a human.

        Args:
            intent_result: The detected intent and confidence.
            conversation_turns: Number of agent turns in this conversation.
            user_message: The latest user message.
            context: Optional conversation history.

        Returns:
            HandoffDecision with handoff recommendation and metadata.
        """
        if not self._enabled:
            return HandoffDecision(should_handoff=False)

        # Check for explicit human request
        if self._is_explicit_handoff_request(user_message):
            logger.info("Explicit handoff request detected")
            return HandoffDecision(
                should_handoff=True,
                reason=HandoffReason.EXPLICIT_REQUEST,
                priority=HandoffPriority.HIGH,
            )

        # Check max turns
        if conversation_turns >= self._max_turns:
            logger.info("Max agent turns reached", turns=conversation_turns)
            return HandoffDecision(
                should_handoff=True,
                reason=HandoffReason.MAX_TURNS_REACHED,
                priority=HandoffPriority.MEDIUM,
                metadata={"turns": conversation_turns},
            )

        # Check low confidence
        if intent_result.confidence < self._confidence_threshold:
            logger.info(
                "Low confidence triggering handoff",
                confidence=intent_result.confidence,
                threshold=self._confidence_threshold,
            )
            return HandoffDecision(
                should_handoff=True,
                reason=HandoffReason.LOW_CONFIDENCE,
                priority=HandoffPriority.MEDIUM,
                metadata={"confidence": intent_result.confidence},
            )

        # Check escalation rules
        for rule in self._escalation_rules:
            if rule["intent"] == intent_result.intent.value and rule.get("auto_handoff"):
                logger.info(
                    "Escalation rule triggered",
                    intent=intent_result.intent.value,
                    priority=rule.get("priority", "medium"),
                )
                return HandoffDecision(
                    should_handoff=True,
                    reason=HandoffReason.COMPLAINT_ESCALATION,
                    priority=HandoffPriority(rule.get("priority", "medium")),
                    metadata={"rule": rule},
                )

        # Check for high-value lead indicators
        if self._is_high_value_lead(intent_result, context or []):
            logger.info("High-value lead detected")
            return HandoffDecision(
                should_handoff=True,
                reason=HandoffReason.HIGH_VALUE_LEAD,
                priority=HandoffPriority.HIGH,
            )

        return HandoffDecision(should_handoff=False)

    def _is_explicit_handoff_request(self, message: str) -> bool:
        """Check if user explicitly requested a human agent.

        Args:
            message: The user's message.

        Returns:
            True if explicit handoff is requested.
        """
        handoff_phrases = [
            "talk to a human",
            "speak to a human",
            "talk to a person",
            "speak to a person",
            "real person",
            "real human",
            "human agent",
            "human representative",
            "speak to someone",
            "talk to someone",
            "manager",
            "supervisor",
            "escalate",
        ]
        message_lower = message.lower()
        return any(phrase in message_lower for phrase in handoff_phrases)

    def _is_high_value_lead(
        self,
        intent_result: IntentResult,
        context: list[dict[str, str]],
    ) -> bool:
        """Detect high-value lead signals.

        Args:
            intent_result: The detected intent.
            context: Conversation history.

        Returns:
            True if high-value lead signals are detected.
        """
        high_value_intents = {Intent.PURCHASE_INTENT, Intent.DEMO_REQUEST, Intent.PRICING_QUESTION}

        if intent_result.intent not in high_value_intents:
            return False

        # Check for enterprise signals in context
        enterprise_keywords = ["enterprise", "team", "company", "organization", "department"]
        context_text = " ".join(msg["content"].lower() for msg in context)

        return any(keyword in context_text for keyword in enterprise_keywords)

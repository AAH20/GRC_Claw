"""Base moderation agent with common functionality."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from ugc_marketplace.config import get_settings
from ugc_marketplace.models.schemas import ContentType, ModerationAction, ModerationResult

logger = structlog.get_logger(__name__)


class BaseModerationAgent(ABC):
    """Abstract base class for all moderation agents.

    Provides common functionality for LLM initialization, execution timing,
    and result construction. Subclasses must implement the _analyze method.
    """

    def __init__(self, model: BaseChatModel | None = None) -> None:
        """Initialize the moderation agent.

        Args:
            model: Optional pre-configured chat model. If not provided,
                   creates a default OpenAI model from settings.
        """
        self.settings = get_settings()
        self.model = model or self._create_default_model()
        self._trace: dict[str, Any] = {}

    def _create_default_model(self) -> BaseChatModel:
        """Create default LLM model from application settings.

        Returns:
            Configured chat model instance.
        """
        return ChatOpenAI(
            model=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            api_key=self.settings.openai_api_key or None,
        )

    @property
    @abstractmethod
    def content_type(self) -> ContentType:
        """Content type this agent handles."""
        ...

    @abstractmethod
    async def _analyze(self, content: str, context: dict[str, Any]) -> dict[str, Any]:
        """Perform content analysis.

        Args:
            content: The content to analyze.
            context: Additional context for analysis.

        Returns:
            Analysis result dictionary with action, confidence, categories, reasons.
        """
        ...

    async def moderate(
        self,
        content: str,
        request_id: str,
        context: dict[str, Any] | None = None,
    ) -> ModerationResult:
        """Moderate content and return structured result.

        Args:
            content: Content to moderate.
            request_id: Unique request identifier.
            context: Optional additional context.

        Returns:
            Structured moderation result.
        """
        start_time = time.monotonic()
        ctx = context or {}

        logger.info(
            "Starting moderation",
            agent=self.__class__.__name__,
            content_type=self.content_type.value,
            request_id=request_id,
        )

        try:
            analysis = await self._analyze(content, ctx)
            processing_time = (time.monotonic() - start_time) * 1000

            result = ModerationResult(
                request_id=request_id,  # type: ignore[arg-type]
                content_type=self.content_type,
                action=ModerationAction(analysis.get("action", "flag")),
                confidence=float(analysis.get("confidence", 0.5)),
                categories=analysis.get("categories", []),
                reasons=analysis.get("reasons", []),
                policy_violations=analysis.get("policy_violations", []),
                processing_time_ms=processing_time,
                agent_trace=self._trace or None,
            )

            logger.info(
                "Moderation complete",
                agent=self.__class__.__name__,
                action=result.action.value,
                confidence=result.confidence,
                processing_time_ms=processing_time,
            )

            return result

        except Exception as exc:
            processing_time = (time.monotonic() - start_time) * 1000
            logger.error(
                "Moderation failed",
                agent=self.__class__.__name__,
                error=str(exc),
                processing_time_ms=processing_time,
            )
            return ModerationResult(
                request_id=request_id,  # type: ignore[arg-type]
                content_type=self.content_type,
                action=ModerationAction.ESCALATE,
                confidence=0.0,
                categories=["error"],
                reasons=[f"Agent error: {exc}"],
                processing_time_ms=processing_time,
                agent_trace=self._trace or None,
            )

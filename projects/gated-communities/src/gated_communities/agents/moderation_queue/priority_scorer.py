"""Priority Scorer Agent for AI-driven priority assessment."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage
from moderation_queue.agents.base import AgentConfig, BaseAgent
from moderation_queue.models import ModerationItem, PriorityLevel, PriorityScore
from pydantic import BaseModel, Field


class PriorityScorerInput(BaseModel):
    """Input for the Priority Scorer Agent."""

    item: ModerationItem = Field(..., description="Moderation item to score")
    queue_context: dict[str, Any] = Field(
        default_factory=dict, description="Queue context information"
    )
    historical_data: dict[str, Any] = Field(
        default_factory=dict, description="Historical scoring data"
    )


class PriorityScorerOutput(BaseModel):
    """Output from the Priority Scorer Agent."""

    score: float = Field(..., ge=0.0, le=1.0, description="Priority score")
    level: PriorityLevel = Field(..., description="Priority level")
    factors: dict[str, float] = Field(
        default_factory=dict, description="Scoring factors"
    )
    reasoning: str = Field(default="", description="Scoring reasoning")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence")


SYSTEM_PROMPT = """You are an AI priority scorer for content moderation.
Your task is to analyze moderation items and assign priority scores based on:
- Content severity and potential harm
- User history and reputation
- Content type and context
- Urgency indicators
- Queue load and SLA requirements

Provide a score between 0.0 (lowest) and 1.0 (highest priority).
Always respond with valid JSON matching the expected schema."""


class PriorityScorerAgent(BaseAgent[PriorityScorerInput, PriorityScorerOutput]):
    """Agent that scores moderation items by priority using AI.

    This agent analyzes content, user history, and queue context to determine
    the priority level of moderation items, enabling efficient triage.
    """

    def __init__(self, settings: Any = None) -> None:
        """Initialize the Priority Scorer Agent.

        Args:
            settings: Application settings.
        """
        config = AgentConfig(
            name="PriorityScorerAgent",
            description="AI agent for scoring moderation item priority",
            temperature=0.1,
            max_tokens=500,
        )
        super().__init__(config, settings)

    async def process(self, input_data: PriorityScorerInput) -> PriorityScorerOutput:
        """Process a moderation item and assign a priority score.

        Args:
            input_data: Input containing the item and context.

        Returns:
            PriorityScorerOutput: Priority scoring result.
        """
        item = input_data.item
        context = {
            "queue_context": input_data.queue_context,
            "historical_data": input_data.historical_data,
        }

        user_content = f"""Analyze this moderation item and assign a priority score.

Content Type: {item.content_type.value}
Content: {item.content[:500]}
Author ID: {item.author_id}
Tags: {item.tags}
Metadata: {json.dumps(item.metadata)}
Context: {json.dumps(context)}

Provide:
1. score: float (0.0-1.0)
2. level: one of "low", "medium", "high", "critical"
3. factors: dict of scoring factors and their weights
4. reasoning: brief explanation
5. confidence: float (0.0-1.0)

Respond with JSON only."""

        messages = self._build_messages(SYSTEM_PROMPT, user_content)
        response = await self._model.ainvoke(messages)

        if isinstance(response, AIMessage) and isinstance(response.content, str):
            try:
                data = json.loads(response.content)
                return PriorityScorerOutput.model_validate(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback scoring based on heuristics
        return self._heuristic_score(item)

    def _heuristic_score(self, item: ModerationItem) -> PriorityScorerOutput:
        """Generate a heuristic-based priority score as fallback.

        Args:
            item: Moderation item to score.

        Returns:
            PriorityScorerOutput: Heuristic scoring result.
        """
        score = 0.3  # Base score
        factors: dict[str, float] = {"base": 0.3}

        # Content type weighting
        type_weights = {
            "video": 0.15,
            "image": 0.1,
            "text": 0.05,
            "comment": 0.08,
            "post": 0.1,
            "message": 0.05,
        }
        type_score = type_weights.get(item.content_type.value, 0.05)
        score += type_score
        factors["content_type"] = type_score

        # Tag-based adjustments
        high_priority_tags = {"violence", "hate", "nsfw", "spam", "harassment"}
        tag_matches = set(item.tags) & high_priority_tags
        if tag_matches:
            tag_score = min(0.3, len(tag_matches) * 0.1)
            score += tag_score
            factors["tags"] = tag_score

        # Content length factor (longer content may need more attention)
        if len(item.content) > 1000:
            score += 0.05
            factors["length"] = 0.05

        # Cap score
        score = min(1.0, score)

        # Determine level
        if score >= 0.8:
            level = PriorityLevel.CRITICAL
        elif score >= 0.6:
            level = PriorityLevel.HIGH
        elif score >= 0.4:
            level = PriorityLevel.MEDIUM
        else:
            level = PriorityLevel.LOW

        return PriorityScorerOutput(
            score=score,
            level=level,
            factors=factors,
            reasoning="Heuristic-based scoring (AI model unavailable)",
            confidence=0.5,
        )

    def create_priority_score(
        self, item: ModerationItem, output: PriorityScorerOutput
    ) -> PriorityScore:
        """Create a PriorityScore model from agent output.

        Args:
            item: The moderation item.
            output: Agent output.

        Returns:
            PriorityScore: Complete priority score record.
        """
        return PriorityScore(
            item_id=item.id,
            score=output.score,
            level=output.level,
            factors=output.factors,
            reasoning=output.reasoning,
            confidence=output.confidence,
        )

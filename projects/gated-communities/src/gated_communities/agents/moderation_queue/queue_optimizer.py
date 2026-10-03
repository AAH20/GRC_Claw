"""Queue Optimizer Agent for dynamic queue balancing."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage
from moderation_queue.agents.base import AgentConfig, BaseAgent
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from moderation_queue.models import Queue, QueueMetrics


class QueueOptimizerInput(BaseModel):
    """Input for the Queue Optimizer Agent."""

    queues: list[Queue] = Field(..., description="List of queues to optimize")
    metrics: list[QueueMetrics] = Field(
        default_factory=list, description="Current queue metrics"
    )
    pending_items: list[dict[str, Any]] = Field(
        default_factory=list, description="Pending items awaiting assignment"
    )
    optimization_goals: dict[str, Any] = Field(
        default_factory=dict, description="Optimization goals and constraints"
    )


class QueueOptimizerOutput(BaseModel):
    """Output from the Queue Optimizer Agent."""

    reassignments: list[dict[str, Any]] = Field(
        default_factory=list, description="Recommended item reassignments"
    )
    queue_adjustments: list[dict[str, Any]] = Field(
        default_factory=list, description="Recommended queue configuration changes"
    )
    priority_updates: list[dict[str, Any]] = Field(
        default_factory=list, description="Recommended priority updates"
    )
    reasoning: str = Field(default="", description="Optimization reasoning")
    expected_improvement: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Expected efficiency improvement"
    )


SYSTEM_PROMPT = """You are an AI queue optimization specialist.
Your task is to analyze moderation queues and optimize their performance.

Consider:
- Queue load balancing
- SLA compliance
- Reviewer utilization
- Priority distribution
- Bottleneck identification
- Resource allocation

Provide actionable recommendations for queue optimization.
Always respond with valid JSON matching the expected schema."""


class QueueOptimizerAgent(BaseAgent[QueueOptimizerInput, QueueOptimizerOutput]):
    """Agent that optimizes moderation queue performance using AI.

    This agent analyzes queue metrics and provides recommendations for
    load balancing, priority adjustments, and resource allocation.
    """

    def __init__(self, settings: Any = None) -> None:
        """Initialize the Queue Optimizer Agent.

        Args:
            settings: Application settings.
        """
        config = AgentConfig(
            name="QueueOptimizerAgent",
            description="AI agent for optimizing moderation queue performance",
            temperature=0.1,
            max_tokens=1000,
        )
        super().__init__(config, settings)

    async def process(self, input_data: QueueOptimizerInput) -> QueueOptimizerOutput:
        """Analyze queues and generate optimization recommendations.

        Args:
            input_data: Input containing queues, metrics, and goals.

        Returns:
            QueueOptimizerOutput: Optimization recommendations.
        """
        user_content = f"""Analyze and optimize these moderation queues:

Queues: {json.dumps([q.model_dump() for q in input_data.queues])}
Metrics: {json.dumps([m.model_dump() for m in input_data.metrics])}
Pending Items: {json.dumps(input_data.pending_items)}
Goals: {json.dumps(input_data.optimization_goals)}

Provide:
1. reassignments: list of {{"item_id": string, "from_queue": string, "to_queue": string,
"reason": string}}
2. queue_adjustments: list of {{"queue_id": string, "action": string, "value": any}}
3. priority_updates: list of {{"item_id": string, "new_priority": string, "reason": string}}
4. reasoning: brief explanation
5. expected_improvement: float (0.0-1.0)

Respond with JSON only."""

        messages = self._build_messages(SYSTEM_PROMPT, user_content)
        response = await self._model.ainvoke(messages)

        if isinstance(response, AIMessage) and isinstance(response.content, str):
            try:
                data = json.loads(response.content)
                return QueueOptimizerOutput.model_validate(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: basic load balancing
        return self._fallback_optimize(input_data)

    def _fallback_optimize(
        self, input_data: QueueOptimizerInput
    ) -> QueueOptimizerOutput:
        """Fallback optimization when AI is unavailable.

        Args:
            input_data: Input data.

        Returns:
            QueueOptimizerOutput: Basic optimization recommendations.
        """
        reassignments: list[dict[str, Any]] = []
        queue_adjustments: list[dict[str, Any]] = []

        # Simple load balancing: move items from overloaded to underloaded queues
        metrics_map = {str(m.queue_id): m for m in input_data.metrics}
        for queue in input_data.queues:
            qm = metrics_map.get(str(queue.id))
            if qm and qm.pending_items > queue.max_size * 0.8:
                # Queue is near capacity, flag for adjustment
                queue_adjustments.append(
                    {
                        "queue_id": str(queue.id),
                        "action": "increase_capacity",
                        "value": int(queue.max_size * 1.2),
                    }
                )

        return QueueOptimizerOutput(
            reassignments=reassignments,
            queue_adjustments=queue_adjustments,
            priority_updates=[],
            reasoning="Fallback optimization (AI model unavailable)",
            expected_improvement=0.1,
        )

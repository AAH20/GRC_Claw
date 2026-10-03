"""Human Review Router Agent for intelligent reviewer assignment."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage
from moderation_queue.agents.base import AgentConfig, BaseAgent
from moderation_queue.models import ModerationItem, PriorityLevel
from pydantic import BaseModel, Field


class HumanReviewRouterInput(BaseModel):
    """Input for the Human Review Router Agent."""

    item: ModerationItem = Field(..., description="Moderation item to route")
    available_reviewers: list[dict[str, Any]] = Field(
        default_factory=list, description="Available reviewers with metadata"
    )
    queue_info: dict[str, Any] = Field(
        default_factory=dict, description="Queue information"
    )
    reviewer_workloads: dict[str, int] = Field(
        default_factory=dict, description="Current workload per reviewer"
    )


class HumanReviewRouterOutput(BaseModel):
    """Output from the Human Review Router Agent."""

    assigned_reviewer_id: str = Field(..., description="ID of assigned reviewer")
    assigned_queue_id: str = Field(..., description="ID of assigned queue")
    priority: PriorityLevel = Field(..., description="Priority for routing")
    reasoning: str = Field(default="", description="Routing reasoning")
    estimated_review_time_minutes: int = Field(
        default=30, description="Estimated review time in minutes"
    )


SYSTEM_PROMPT = """You are an AI router for human content review.
Your task is to assign moderation items to the most appropriate human reviewer.

Consider:
- Reviewer expertise and specializations
- Current workload and availability
- Content type and complexity
- Priority and SLA requirements
- Language and cultural context

Always respond with valid JSON matching the expected schema."""


class HumanReviewRouterAgent(
    BaseAgent[HumanReviewRouterInput, HumanReviewRouterOutput]
):
    """Agent that routes moderation items to human reviewers intelligently.

    This agent matches items with reviewers based on expertise, workload,
    and content requirements to optimize review efficiency.
    """

    def __init__(self, settings: Any = None) -> None:
        """Initialize the Human Review Router Agent.

        Args:
            settings: Application settings.
        """
        config = AgentConfig(
            name="HumanReviewRouterAgent",
            description="AI agent for routing items to human reviewers",
            temperature=0.1,
            max_tokens=500,
        )
        super().__init__(config, settings)

    async def process(
        self, input_data: HumanReviewRouterInput
    ) -> HumanReviewRouterOutput:
        """Route a moderation item to a human reviewer.

        Args:
            input_data: Input containing item and reviewer information.

        Returns:
            HumanReviewRouterOutput: Routing decision.
        """
        item = input_data.item

        user_content = f"""Route this moderation item to a human reviewer:

Content Type: {item.content_type.value}
Content Preview: {item.content[:300]}
Priority Score: {item.priority_score}
Priority Level: {item.priority_level}
Tags: {item.tags}

Available Reviewers: {json.dumps(input_data.available_reviewers)}
Queue Info: {json.dumps(input_data.queue_info)}
Reviewer Workloads: {json.dumps(input_data.reviewer_workloads)}

Provide:
1. assigned_reviewer_id: string
2. assigned_queue_id: string
3. priority: one of "low", "medium", "high", "critical"
4. reasoning: brief explanation
5. estimated_review_time_minutes: integer

Respond with JSON only."""

        messages = self._build_messages(SYSTEM_PROMPT, user_content)
        response = await self._model.ainvoke(messages)

        if isinstance(response, AIMessage) and isinstance(response.content, str):
            try:
                data = json.loads(response.content)
                return HumanReviewRouterOutput.model_validate(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: assign to least loaded reviewer
        return self._fallback_route(input_data)

    def _fallback_route(
        self, input_data: HumanReviewRouterInput
    ) -> HumanReviewRouterOutput:
        """Fallback routing when AI is unavailable.

        Args:
            input_data: Input data.

        Returns:
            HumanReviewRouterOutput: Fallback routing decision.
        """
        reviewers = input_data.available_reviewers
        workloads = input_data.reviewer_workloads

        if reviewers:
            # Find least loaded reviewer
            least_loaded = min(
                reviewers,
                key=lambda r: workloads.get(r.get("id", ""), 0),
            )
            reviewer_id = least_loaded.get("id", "default_reviewer")
        else:
            reviewer_id = "default_reviewer"

        return HumanReviewRouterOutput(
            assigned_reviewer_id=reviewer_id,
            assigned_queue_id=input_data.queue_info.get("id", "default_queue"),
            priority=input_data.item.priority_level or PriorityLevel.MEDIUM,
            reasoning="Fallback routing (AI model unavailable)",
            estimated_review_time_minutes=30,
        )

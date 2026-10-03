"""Agent API routes for AI-powered moderation operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends
from moderation_queue.agents.auto_moderation import AutoModerationAgent, AutoModerationInput
from moderation_queue.agents.escalation import EscalationAgent, EscalationInput
from moderation_queue.agents.human_review_router import (
    HumanReviewRouterAgent,
    HumanReviewRouterInput,
)
from moderation_queue.agents.priority_scorer import PriorityScorerAgent, PriorityScorerInput
from moderation_queue.agents.queue_optimizer import QueueOptimizerAgent, QueueOptimizerInput
from moderation_queue.api.dependencies import get_logger
from moderation_queue.models import AgentResponse, ModerationItem
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from uuid import UUID

router = APIRouter(prefix="/agents", tags=["agents"])


class ScoreRequest(BaseModel):
    """Request model for priority scoring."""

    item_id: UUID = Field(..., description="Item to score")
    queue_context: dict = Field(default_factory=dict, description="Queue context")
    historical_data: dict = Field(default_factory=dict, description="Historical data")


class AutoModerateRequest(BaseModel):
    """Request model for auto-moderation."""

    item_id: UUID = Field(..., description="Item to moderate")
    rules: dict = Field(default_factory=dict, description="Moderation rules")
    threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Confidence threshold"
    )


class RouteRequest(BaseModel):
    """Request model for human review routing."""

    item_id: UUID = Field(..., description="Item to route")
    available_reviewers: list[dict] = Field(
        default_factory=list, description="Available reviewers"
    )
    queue_info: dict = Field(default_factory=dict, description="Queue information")
    reviewer_workloads: dict[str, int] = Field(
        default_factory=dict, description="Reviewer workloads"
    )


class OptimizeRequest(BaseModel):
    """Request model for queue optimization."""

    queue_ids: list[UUID] = Field(
        default_factory=list, description="Queue IDs to optimize"
    )
    optimization_goals: dict = Field(
        default_factory=dict, description="Optimization goals"
    )


class EscalateRequest(BaseModel):
    """Request model for escalation."""

    item_id: UUID = Field(..., description="Item to escalate")
    reason: str = Field(..., description="Escalation reason")
    available_teams: list[dict] = Field(
        default_factory=list, description="Available teams"
    )
    urgency_indicators: dict = Field(
        default_factory=dict, description="Urgency indicators"
    )


# Agent instances (singletons)
_priority_scorer: PriorityScorerAgent | None = None
_auto_moderation: AutoModerationAgent | None = None
_human_router: HumanReviewRouterAgent | None = None
_queue_optimizer: QueueOptimizerAgent | None = None
_escalation: EscalationAgent | None = None


def _get_priority_scorer() -> PriorityScorerAgent:
    """Get or create PriorityScorerAgent instance.

    Returns:
        PriorityScorerAgent: Agent instance.
    """
    global _priority_scorer
    if _priority_scorer is None:
        _priority_scorer = PriorityScorerAgent()
    return _priority_scorer


def _get_auto_moderation() -> AutoModerationAgent:
    """Get or create AutoModerationAgent instance.

    Returns:
        AutoModerationAgent: Agent instance.
    """
    global _auto_moderation
    if _auto_moderation is None:
        _auto_moderation = AutoModerationAgent()
    return _auto_moderation


def _get_human_router() -> HumanReviewRouterAgent:
    """Get or create HumanReviewRouterAgent instance.

    Returns:
        HumanReviewRouterAgent: Agent instance.
    """
    global _human_router
    if _human_router is None:
        _human_router = HumanReviewRouterAgent()
    return _human_router


def _get_queue_optimizer() -> QueueOptimizerAgent:
    """Get or create QueueOptimizerAgent instance.

    Returns:
        QueueOptimizerAgent: Agent instance.
    """
    global _queue_optimizer
    if _queue_optimizer is None:
        _queue_optimizer = QueueOptimizerAgent()
    return _queue_optimizer


def _get_escalation() -> EscalationAgent:
    """Get or create EscalationAgent instance.

    Returns:
        EscalationAgent: Agent instance.
    """
    global _escalation
    if _escalation is None:
        _escalation = EscalationAgent()
    return _escalation


@router.post(
    "/score",
    response_model=AgentResponse,
    summary="Score item priority",
    description="Use AI to score the priority of a moderation item",
)
async def score_priority(
    request: ScoreRequest,
    logger=Depends(get_logger),  # noqa: B008
) -> AgentResponse:
    """Score a moderation item's priority using AI.

    Args:
        request: Scoring request.
        logger: Request logger.

    Returns:
        AgentResponse: Scoring result.
    """
    # Create a placeholder item for demo
    item = ModerationItem(
        id=request.item_id,
        content="Sample content for scoring",
        author_id="system",
    )
    agent = _get_priority_scorer()
    input_data = PriorityScorerInput(
        item=item,
        queue_context=request.queue_context,
        historical_data=request.historical_data,
    )
    result = await agent.run(input_data)
    logger.info("Priority scoring completed", item_id=str(request.item_id))
    return result


@router.post(
    "/auto-moderate",
    response_model=AgentResponse,
    summary="Auto-moderate an item",
    description="Use AI to automatically moderate content",
)
async def auto_moderate(
    request: AutoModerateRequest,
    logger=Depends(get_logger),  # noqa: B008
) -> AgentResponse:
    """Auto-moderate a content item using AI.

    Args:
        request: Auto-moderation request.
        logger: Request logger.

    Returns:
        AgentResponse: Moderation result.
    """
    item = ModerationItem(
        id=request.item_id,
        content="Sample content for moderation",
        author_id="system",
    )
    agent = _get_auto_moderation()
    input_data = AutoModerationInput(
        item=item,
        rules=request.rules,
        threshold=request.threshold,
    )
    result = await agent.run(input_data)
    logger.info("Auto-moderation completed", item_id=str(request.item_id))
    return result


@router.post(
    "/route",
    response_model=AgentResponse,
    summary="Route to human review",
    description="Use AI to route an item to a human reviewer",
)
async def route_to_human(
    request: RouteRequest,
    logger=Depends(get_logger),  # noqa: B008
) -> AgentResponse:
    """Route an item to a human reviewer using AI.

    Args:
        request: Routing request.
        logger: Request logger.

    Returns:
        AgentResponse: Routing result.
    """
    item = ModerationItem(
        id=request.item_id,
        content="Sample content for routing",
        author_id="system",
    )
    agent = _get_human_router()
    input_data = HumanReviewRouterInput(
        item=item,
        available_reviewers=request.available_reviewers,
        queue_info=request.queue_info,
        reviewer_workloads=request.reviewer_workloads,
    )
    result = await agent.run(input_data)
    logger.info("Human review routing completed", item_id=str(request.item_id))
    return result


@router.post(
    "/optimize",
    response_model=AgentResponse,
    summary="Optimize queues",
    description="Use AI to optimize moderation queue performance",
)
async def optimize_queues(
    request: OptimizeRequest,
    logger=Depends(get_logger),  # noqa: B008
) -> AgentResponse:
    """Optimize moderation queues using AI.

    Args:
        request: Optimization request.
        logger: Request logger.

    Returns:
        AgentResponse: Optimization result.
    """
    agent = _get_queue_optimizer()
    input_data = QueueOptimizerInput(
        queues=[],
        metrics=[],
        pending_items=[],
        optimization_goals=request.optimization_goals,
    )
    result = await agent.run(input_data)
    logger.info("Queue optimization completed")
    return result


@router.post(
    "/escalate",
    response_model=AgentResponse,
    summary="Escalate an item",
    description="Use AI to manage escalation of high-priority items",
)
async def escalate_item(
    request: EscalateRequest,
    logger=Depends(get_logger),  # noqa: B008
) -> AgentResponse:
    """Escalate a moderation item using AI.

    Args:
        request: Escalation request.
        logger: Request logger.

    Returns:
        AgentResponse: Escalation result.
    """
    item = ModerationItem(
        id=request.item_id,
        content="Sample content for escalation",
        author_id="system",
    )
    agent = _get_escalation()
    input_data = EscalationInput(
        item=item,
        reason=request.reason,
        available_teams=request.available_teams,
        escalation_history=[],
        urgency_indicators=request.urgency_indicators,
    )
    result = await agent.run(input_data)
    logger.info("Escalation completed", item_id=str(request.item_id))
    return result

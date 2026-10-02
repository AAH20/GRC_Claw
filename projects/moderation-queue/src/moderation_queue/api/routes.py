"""API routes for the moderation queue."""

import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from structlog import get_logger

from moderation_queue.api.models import (
    ContentSubmission,
    ModerationDecision,
    ModerationPipelineResponse,
    ModerationResultResponse,
    PriorityScoreResponse,
    QueueItemResponse,
    QueueName,
    QueueStatsResponse,
    RoutingResultResponse,
    UrgencyLevel,
)
from moderation_queue.agents.auto_moderator import AutoModeratorAgent
from moderation_queue.agents.human_review_router import HumanReviewRouterAgent
from moderation_queue.agents.priority_scorer import PriorityScorerAgent
from moderation_queue.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter()

# In-memory store (replace with Redis/DB in production)
_queue: dict[str, dict[str, Any]] = {}


@router.post("/moderate", response_model=ModerationPipelineResponse)
async def moderate_content(submission: ContentSubmission) -> ModerationPipelineResponse:
    """Run the full moderation pipeline on submitted content."""
    start = time.monotonic()
    submission_id = str(uuid.uuid4())

    priority_agent = PriorityScorerAgent()
    moderator_agent = AutoModeratorAgent()
    router_agent = HumanReviewRouterAgent()

    # Step 1: Priority scoring
    priority_result = await priority_agent.execute(
        {
            "content": submission.content,
            "content_type": submission.content_type.value,
            "user_history": submission.metadata.get("user_history", {}),
        }
    )
    if not priority_result.success:
        raise HTTPException(status_code=500, detail=priority_result.error)

    # Step 2: Auto-moderation
    mod_result = await moderator_agent.execute(
        {
            "content": submission.content,
            "content_type": submission.content_type.value,
            "metadata": submission.metadata,
        }
    )
    if not mod_result.success:
        raise HTTPException(status_code=500, detail=mod_result.error)

    # Step 3: Route to human review if needed
    routing_result = None
    final_decision = ModerationDecision(mod_result.data["decision"])

    if final_decision == ModerationDecision.ESCALATE:
        route_result = await router_agent.execute(
            {
                "content": submission.content,
                "content_type": submission.content_type.value,
                "auto_moderation_result": mod_result.data,
                "priority_score": priority_result.data["priority"],
            }
        )
        if route_result.success:
            routing_result = RoutingResultResponse(**route_result.data)

    elapsed_ms = (time.monotonic() - start) * 1000

    response = ModerationPipelineResponse(
        submission_id=submission_id,
        priority=PriorityScoreResponse(**priority_result.data),
        moderation=ModerationResultResponse(**mod_result.data),
        routing=routing_result,
        final_decision=final_decision,
        processing_time_ms=round(elapsed_ms, 2),
    )

    # Store in queue
    _queue[submission_id] = {
        "id": submission_id,
        "content_type": submission.content_type,
        "priority": priority_result.data["priority"],
        "status": "resolved" if final_decision != ModerationDecision.ESCALATE else "in_review",
        "assigned_queue": routing_result.queue if routing_result else None,
        "created_at": response.processed_at,
        "updated_at": response.processed_at,
    }

    logger.info(
        "moderation.completed",
        submission_id=submission_id,
        decision=final_decision.value,
        priority=priority_result.data["priority"],
        processing_time_ms=round(elapsed_ms, 2),
    )

    return response


@router.get("/queue", response_model=list[QueueItemResponse])
async def list_queue() -> list[QueueItemResponse]:
    """List all items in the moderation queue."""
    return [QueueItemResponse(**item) for item in _queue.values()]


@router.get("/queue/stats", response_model=QueueStatsResponse)
async def queue_stats() -> QueueStatsResponse:
    """Get queue statistics."""
    items = list(_queue.values())
    pending = sum(1 for i in items if i["status"] == "pending")
    in_review = sum(1 for i in items if i["status"] == "in_review")
    resolved = sum(1 for i in items if i["status"] == "resolved")

    queue_breakdown: dict[str, int] = {}
    for item in items:
        q = item.get("assigned_queue")
        if q:
            queue_breakdown[q.value] = queue_breakdown.get(q.value, 0) + 1

    return QueueStatsResponse(
        total_pending=pending,
        total_in_review=in_review,
        total_resolved=resolved,
        avg_processing_time_ms=0.0,
        queue_breakdown=queue_breakdown,
    )


@router.get("/queue/{item_id}", response_model=QueueItemResponse)
async def get_queue_item(item_id: str) -> QueueItemResponse:
    """Get a specific queue item."""
    if item_id not in _queue:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return QueueItemResponse(**_queue[item_id])


@router.post("/queue/{item_id}/resolve")
async def resolve_queue_item(item_id: str, decision: ModerationDecision) -> dict[str, str]:
    """Resolve a queue item with a final decision."""
    if item_id not in _queue:
        raise HTTPException(status_code=404, detail="Queue item not found")

    _queue[item_id]["status"] = "resolved"
    from datetime import datetime

    _queue[item_id]["updated_at"] = datetime.utcnow()

    logger.info("queue.item_resolved", item_id=item_id, decision=decision.value)
    return {"status": "resolved", "decision": decision.value}

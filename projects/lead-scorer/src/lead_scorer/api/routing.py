"""API routes for lead routing endpoints."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from lead_scorer.agents.lead_routing import LeadRoutingAgent, RoutingContext
from lead_scorer.agents.qualification import QualificationAgent
from lead_scorer.agents.scoring import ScoringAgent
from lead_scorer.models.routing import (
    BatchRoutingRequest,
    BatchRoutingResponse,
    RoutingDecision,
    RoutingRule,
    RoutingRuleCreate,
    RoutingRuleUpdate,
)

router = APIRouter(prefix="/api/v1/routing", tags=["routing"])


class RouteRequest(BaseModel):
    """Request model for routing a lead."""

    lead_id: str = Field(..., min_length=1, description="Unique lead identifier")
    score: float = Field(default=0.0, ge=0, le=100, description="Lead score")
    grade: str = Field(default="", description="Lead grade (hot/warm/cold)")
    qualification_status: str = Field(default="", description="Qualification status")
    qualification_score: float = Field(default=0.0, ge=0, le=1)
    industry: str = Field(default="", description="Industry")
    company_size: int = Field(default=0, ge=0, description="Company size")
    annual_revenue: float | None = Field(default=None, ge=0)
    source: str = Field(default="", description="Lead source")
    job_title: str = Field(default="", description="Job title")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteResponse(BaseModel):
    """Response model for routing decision."""

    success: bool
    data: RoutingDecision


class RoutingRulesResponse(BaseModel):
    """Response model for routing rules list."""

    success: bool
    rules: list[RoutingRule]
    total: int


class RoutingStatsResponse(BaseModel):
    """Response model for routing statistics."""

    success: bool
    stats: dict[str, int]


def get_routing_agent() -> LeadRoutingAgent:
    """Dependency to get routing agent instance."""
    return LeadRoutingAgent()


def get_scoring_agent() -> ScoringAgent:
    """Dependency to get scoring agent instance."""
    return ScoringAgent()


def get_qualification_agent() -> QualificationAgent:
    """Dependency to get qualification agent instance."""
    return QualificationAgent()


@router.post("/route", response_model=RouteResponse)
async def route_lead(
    request: RouteRequest,
    routing_agent: Annotated[LeadRoutingAgent, Depends(get_routing_agent)],
) -> RouteResponse:
    """Route a lead to the appropriate destination.

    Args:
        request: Routing request with lead context.
        routing_agent: Routing agent instance.

    Returns:
        RouteResponse with routing decision.

    Raises:
        HTTPException: If routing fails.
    """
    try:
        context = RoutingContext(
            lead_id=request.lead_id,
            score=request.score,
            grade=request.grade,
            qualification_status=request.qualification_status,
            qualification_score=request.qualification_score,
            industry=request.industry,
            company_size=request.company_size,
            annual_revenue=request.annual_revenue,
            source=request.source,
            job_title=request.job_title,
            metadata=request.metadata,
        )
        decision = await routing_agent.route(context)
        return RouteResponse(success=True, data=decision)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing failed: {str(exc)}",
        ) from exc


@router.post("/batch", response_model=BatchRoutingResponse)
async def batch_route(
    request: BatchRoutingRequest,
    routing_agent: Annotated[LeadRoutingAgent, Depends(get_routing_agent)],
) -> BatchRoutingResponse:
    """Route multiple leads in batch.

    Args:
        request: Batch routing request with lead IDs.
        routing_agent: Routing agent instance.

    Returns:
        BatchRoutingResponse with decisions for all leads.

    Raises:
        HTTPException: If batch routing fails.
    """
    try:
        return await routing_agent.route_batch(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch routing failed: {str(exc)}",
        ) from exc


@router.get("/rules", response_model=RoutingRulesResponse)
async def list_routing_rules(
    routing_agent: Annotated[LeadRoutingAgent, Depends(get_routing_agent)],
) -> RoutingRulesResponse:
    """List all routing rules.

    Args:
        routing_agent: Routing agent instance.

    Returns:
        RoutingRulesResponse with all rules.
    """
    rules = routing_agent.rules
    return RoutingRulesResponse(success=True, rules=rules, total=len(rules))


@router.post("/rules", response_model=RoutingRule, status_code=status.HTTP_201_CREATED)
async def create_routing_rule(
    request: RoutingRuleCreate,
    routing_agent: Annotated[LeadRoutingAgent, Depends(get_routing_agent)],
) -> RoutingRule:
    """Create a new routing rule.

    Args:
        request: Rule creation request.
        routing_agent: Routing agent instance.

    Returns:
        The created RoutingRule.

    Raises:
        HTTPException: If rule creation fails.
    """
    import uuid

    rule = RoutingRule(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        destination=request.destination,
        priority=request.priority,
        conditions=request.conditions,
        score_threshold=request.score_threshold,
        grade_filter=request.grade_filter,
        industry_filter=request.industry_filter,
        company_size_min=request.company_size_min,
        company_size_max=request.company_size_max,
        is_active=request.is_active,
        order=request.order,
    )
    routing_agent.add_rule(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=RoutingRule)
async def update_routing_rule(
    rule_id: str,
    request: RoutingRuleUpdate,
    routing_agent: Annotated[LeadRoutingAgent, Depends(get_routing_agent)],
) -> RoutingRule:
    """Update an existing routing rule.

    Args:
        rule_id: The rule identifier.
        request: Rule update request.
        routing_agent: Routing agent instance.

    Returns:
        The updated RoutingRule.

    Raises:
        HTTPException: If rule not found or update fails.
    """
    updated = routing_agent.update_rule(rule_id, request)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )
    return updated


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routing_rule(
    rule_id: str,
    routing_agent: Annotated[LeadRoutingAgent, Depends(get_routing_agent)],
) -> None:
    """Delete a routing rule.

    Args:
        rule_id: The rule identifier.
        routing_agent: Routing agent instance.

    Raises:
        HTTPException: If rule not found.
    """
    removed = routing_agent.remove_rule(rule_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )


@router.get("/stats", response_model=RoutingStatsResponse)
async def get_routing_stats(
    routing_agent: Annotated[LeadRoutingAgent, Depends(get_routing_agent)],
) -> RoutingStatsResponse:
    """Get routing assignment statistics.

    Args:
        routing_agent: Routing agent instance.

    Returns:
        RoutingStatsResponse with assignment counters.
    """
    stats = routing_agent.get_assignment_stats()
    return RoutingStatsResponse(success=True, stats=stats)


@router.post("/reset-stats", status_code=status.HTTP_204_NO_CONTENT)
async def reset_routing_stats(
    routing_agent: Annotated[LeadRoutingAgent, Depends(get_routing_agent)],
) -> None:
    """Reset routing assignment counters.

    Args:
        routing_agent: Routing agent instance.
    """
    routing_agent.reset_assignment_counters()

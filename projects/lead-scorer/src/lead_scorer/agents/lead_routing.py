"""Intelligent lead routing agent.

Routes leads to the appropriate destination (sales, marketing, nurture, etc.)
based on scoring results, qualification status, firmographic data, and
configurable routing rules.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

from lead_scorer.agents.qualification import QualificationResult, QualificationStatus
from lead_scorer.models.routing import (
    BatchRoutingRequest,
    BatchRoutingResponse,
    RouteDestination,
    RoutingConfig,
    RoutingDecision,
    RoutingPriority,
    RoutingRule,
    RoutingRuleUpdate,
    RoutingStrategy,
)

if TYPE_CHECKING:
    from lead_scorer.agents.scoring import ScoringResult

logger = structlog.get_logger(__name__)


class RoutingContext(BaseModel):
    """Context information used during routing decisions."""

    lead_id: str
    score: float = Field(default=0.0, ge=0, le=100)
    grade: str = ""
    qualification_status: str = ""
    qualification_score: float = Field(default=0.0, ge=0, le=1)
    industry: str = ""
    company_size: int = Field(default=0, ge=0)
    annual_revenue: float | None = None
    source: str = ""
    job_title: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class LeadRoutingAgent:
    """Agent responsible for intelligent lead routing.

    Evaluates leads against configurable routing rules and determines
    the optimal destination based on score, qualification, firmographics,
    and engagement signals.
    """

    def __init__(
        self,
        config: RoutingConfig | None = None,
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ) -> None:
        """Initialize the routing agent.

        Args:
            config: Routing configuration with rules and strategy.
            timeout_seconds: Maximum time allowed for routing.
            max_retries: Number of retry attempts on failure.
        """
        self.config = config or RoutingConfig()
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._rules: list[RoutingRule] = list(self.config.rules)
        self._assignment_counters: dict[str, int] = {}

    @property
    def rules(self) -> list[RoutingRule]:
        """Get the current routing rules."""
        return list(self._rules)

    def add_rule(self, rule: RoutingRule) -> None:
        """Add a routing rule.

        Args:
            rule: The routing rule to add.
        """
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.order)
        logger.info("routing_rule_added", rule_id=rule.id, name=rule.name)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a routing rule by ID.

        Args:
            rule_id: The rule identifier to remove.

        Returns:
            True if the rule was found and removed, False otherwise.
        """
        original_len = len(self._rules)
        self._rules = [r for r in self._rules if r.id != rule_id]
        removed = len(self._rules) < original_len
        if removed:
            logger.info("routing_rule_removed", rule_id=rule_id)
        return removed

    def update_rule(self, rule_id: str, update: RoutingRuleUpdate) -> RoutingRule | None:
        """Update an existing routing rule.

        Args:
            rule_id: The rule identifier to update.
            update: The update data.

        Returns:
            The updated rule, or None if not found.
        """
        for i, rule in enumerate(self._rules):
            if rule.id == rule_id:
                update_data = update.model_dump(exclude_unset=True)
                updated = rule.model_copy(update=update_data)
                self._rules[i] = updated
                self._rules.sort(key=lambda r: r.order)
                logger.info("routing_rule_updated", rule_id=rule_id)
                return updated
        logger.warning("routing_rule_update_not_found", rule_id=rule_id)
        return None

    async def route(
        self,
        context: RoutingContext,
        scoring_result: ScoringResult | None = None,
        qualification_result: QualificationResult | None = None,
    ) -> RoutingDecision:
        """Route a lead to the appropriate destination.

        Args:
            context: Routing context with lead information.
            scoring_result: Optional scoring result for additional signals.
            qualification_result: Optional qualification result.

        Returns:
            RoutingDecision with destination and assignment details.

        Raises:
            ValueError: If lead_id is empty.
            TimeoutError: If routing exceeds timeout.
        """
        if not context.lead_id:
            raise ValueError("lead_id is required")

        logger.info(
            "routing_lead",
            lead_id=context.lead_id,
            score=context.score,
            grade=context.grade,
        )
        start_time = time.monotonic()

        try:
            # Enrich context from scoring and qualification results
            enriched = self._enrich_context(context, scoring_result, qualification_result)

            # Evaluate rules in order
            decision = self._evaluate_rules(enriched)

            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(f"Routing timed out after {elapsed:.1f}s")

            logger.info(
                "lead_routed",
                lead_id=context.lead_id,
                destination=decision.destination.value,
                priority=decision.priority.value,
                confidence=decision.confidence,
            )
            return decision

        except Exception as exc:
            logger.error("routing_failed", lead_id=context.lead_id, error=str(exc))
            raise

    async def route_batch(
        self,
        request: BatchRoutingRequest,
        contexts: dict[str, RoutingContext] | None = None,
    ) -> BatchRoutingResponse:
        """Route multiple leads in batch.

        Args:
            request: Batch routing request with lead IDs.
            contexts: Optional mapping of lead_id to routing context.

        Returns:
            BatchRoutingResponse with decisions for all leads.

        Raises:
            ValueError: If lead_ids is empty.
        """
        if not request.lead_ids:
            raise ValueError("lead_ids cannot be empty")

        logger.info("batch_routing_started", count=len(request.lead_ids))
        start_time = time.monotonic()

        results: list[RoutingDecision] = []
        for lead_id in request.lead_ids:
            try:
                ctx = contexts.get(lead_id) if contexts else None
                if ctx is None:
                    ctx = RoutingContext(
                        lead_id=lead_id,
                        metadata=request.context,
                    )
                decision = await self.route(ctx)
                results.append(decision)
            except Exception as exc:
                logger.error(
                    "batch_routing_item_failed",
                    lead_id=lead_id,
                    error=str(exc),
                )
                results.append(
                    RoutingDecision(
                        lead_id=lead_id,
                        destination=RouteDestination.NURTURE,
                        priority=RoutingPriority.LOW,
                        reason=f"Routing failed: {exc}",
                        confidence=0.0,
                    )
                )

        elapsed = time.monotonic() - start_time
        logger.info(
            "batch_routing_completed",
            total=len(results),
            elapsed_seconds=elapsed,
        )

        return BatchRoutingResponse(success=True, results=results, total=len(results))

    def _enrich_context(
        self,
        context: RoutingContext,
        scoring_result: ScoringResult | None,
        qualification_result: QualificationResult | None,
    ) -> RoutingContext:
        """Enrich routing context with scoring and qualification data."""
        if scoring_result:
            context.score = scoring_result.total_score
            context.grade = scoring_result.grade.value
        if qualification_result:
            context.qualification_status = qualification_result.status.value
            context.qualification_score = qualification_result.total_score
        return context

    def _evaluate_rules(self, context: RoutingContext) -> RoutingDecision:
        """Evaluate routing rules against the context.

        Rules are evaluated in order. The first matching rule determines
        the destination. If no rules match, the default destination is used.
        """
        active_rules = [r for r in self._rules if r.is_active]
        active_rules = active_rules[: self.config.max_rules_evaluated]

        for rule in active_rules:
            if self._rule_matches(rule, context):
                assigned_to = self._assign_destination(rule.destination, context)
                confidence = self._compute_confidence(rule, context)
                return RoutingDecision(
                    lead_id=context.lead_id,
                    destination=rule.destination,
                    priority=rule.priority,
                    assigned_to=assigned_to,
                    assigned_team=rule.destination.value,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    reason=f"Matched rule: {rule.name}",
                    confidence=confidence,
                    routing_strategy=self.config.strategy,
                    metadata={
                        "score": context.score,
                        "grade": context.grade,
                        "qualification_status": context.qualification_status,
                    },
                )

        # No rules matched — use default destination
        assigned_to = self._assign_destination(
            self.config.default_destination, context
        )
        return RoutingDecision(
            lead_id=context.lead_id,
            destination=self.config.default_destination,
            priority=RoutingPriority.LOW,
            assigned_to=assigned_to,
            assigned_team=self.config.default_destination.value,
            rule_id="",
            rule_name="default",
            reason="No matching rule — using default destination",
            confidence=0.5,
            routing_strategy=self.config.strategy,
            metadata={
                "score": context.score,
                "grade": context.grade,
                "qualification_status": context.qualification_status,
            },
        )

    def _rule_matches(self, rule: RoutingRule, context: RoutingContext) -> bool:
        """Check if a routing rule matches the given context."""
        # Score threshold check
        if rule.score_threshold is not None and context.score < rule.score_threshold:
            return False

        # Grade filter check
        if rule.grade_filter and context.grade not in rule.grade_filter:
            return False

        # Industry filter check
        if rule.industry_filter and context.industry not in rule.industry_filter:
            return False

        # Company size range check
        if rule.company_size_min is not None and context.company_size < rule.company_size_min:
            return False
        if rule.company_size_max is not None and context.company_size > rule.company_size_max:
            return False

        # Custom conditions check
        for key, expected_value in rule.conditions.items():
            actual_value = context.metadata.get(key)
            if actual_value is None:
                # Also check top-level context attributes
                actual_value = getattr(context, key, None)
            if actual_value != expected_value:
                return False

        return True

    def _assign_destination(
        self, destination: RouteDestination, context: RoutingContext
    ) -> str:
        """Assign a specific team member or queue for the destination.

        In production, this would query a CRM or workforce management system
        to find the best available rep based on skill, territory, and workload.
        """
        counter_key = destination.value
        current = self._assignment_counters.get(counter_key, 0)
        self._assignment_counters[counter_key] = current + 1

        if self.config.strategy == RoutingStrategy.ROUND_ROBIN:
            return f"{destination.value}-rep-{(current % 5) + 1}"
        if self.config.strategy == RoutingStrategy.SKILL_BASED:
            return self._skill_based_assignment(destination, context)
        if self.config.strategy == RoutingStrategy.TERRITORY:
            return self._territory_assignment(destination, context)
        if self.config.strategy == RoutingStrategy.LOAD_BALANCED:
            return f"{destination.value}-queue"
        # PRIORITY strategy — assign based on lead priority
        return f"{destination.value}-priority-queue"

    def _skill_based_assignment(
        self, destination: RouteDestination, context: RoutingContext
    ) -> str:
        """Assign based on lead industry/needs matching rep skills."""
        industry = context.industry.lower() if context.industry else "general"
        return f"{destination.value}-{industry}-specialist"

    def _territory_assignment(
        self, destination: RouteDestination, context: RoutingContext
    ) -> str:
        """Assign based on geographic territory."""
        location = context.metadata.get("location", "unknown")
        return f"{destination.value}-{location}-territory"

    def _compute_confidence(self, rule: RoutingRule, context: RoutingContext) -> float:
        """Compute confidence score for a routing decision."""
        confidence = 0.5  # Base confidence

        # Higher score = higher confidence
        if context.score >= 80:
            confidence += 0.3
        elif context.score >= 50:
            confidence += 0.15

        # Qualification status increases confidence
        if context.qualification_status == QualificationStatus.QUALIFIED.value:
            confidence += 0.2
        elif context.qualification_status == QualificationStatus.PENDING.value:
            confidence += 0.1

        # More metadata = higher confidence
        if context.metadata:
            confidence += min(len(context.metadata) * 0.02, 0.1)

        return min(round(confidence, 2), 1.0)

    def get_assignment_stats(self) -> dict[str, int]:
        """Get assignment counters for monitoring.

        Returns:
            Dictionary mapping destination to assignment count.
        """
        return dict(self._assignment_counters)

    def reset_assignment_counters(self) -> None:
        """Reset all assignment counters."""
        self._assignment_counters.clear()
        logger.debug("assignment_counters_reset")

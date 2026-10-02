"""Rule management routes."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from community_governance.api.dependencies import get_rule_enforcer
from community_governance.agents import RuleEnforcerAgent
from community_governance.config.logging_config import get_logger
from community_governance.exceptions import RuleNotFoundException
from community_governance.models.governance_action import GovernanceAction, GovernanceActionCreate
from community_governance.models.rule import Rule, RuleCreate, RuleEnforcementResult, RuleUpdate

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/rules", tags=["rules"])

# In-memory storage for demo purposes
_rules_store: dict[UUID, Rule] = {}


@router.post("", response_model=Rule, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: RuleCreate,
    agent: RuleEnforcerAgent = Depends(get_rule_enforcer),
) -> Rule:
    """Create a new governance rule.

    Args:
        rule_data: The rule creation data.
        agent: The rule enforcer agent.

    Returns:
        The newly created rule.
    """
    rule = Rule(
        name=rule_data.name,
        description=rule_data.description,
        category=rule_data.category,
        severity=rule_data.severity,
        conditions=rule_data.conditions,
        actions=rule_data.actions,
        priority=rule_data.priority,
        created_by=rule_data.created_by,
    )
    _rules_store[rule.id] = rule
    agent.add_rule(rule)
    logger.info(f"Rule created: {rule.name}", rule_id=str(rule.id))
    return rule


@router.get("", response_model=list[Rule])
async def list_rules(
    category: str | None = Query(default=None, description="Filter by category"),
    active_only: bool = Query(default=True, description="Show only active rules"),
    agent: RuleEnforcerAgent = Depends(get_rule_enforcer),
) -> list[Rule]:
    """List all governance rules.

    Args:
        category: Optional category filter.
        active_only: Whether to show only active rules.
        agent: The rule enforcer agent.

    Returns:
        List of rules.
    """
    rules = list(_rules_store.values())
    if category:
        rules = [r for r in rules if r.category.value == category]
    if active_only:
        rules = [r for r in rules if r.is_active]
    return rules


@router.get("/{rule_id}", response_model=Rule)
async def get_rule(
    rule_id: UUID,
    agent: RuleEnforcerAgent = Depends(get_rule_enforcer),
) -> Rule:
    """Get a specific rule by ID.

    Args:
        rule_id: The rule ID.
        agent: The rule enforcer agent.

    Returns:
        The requested rule.

    Raises:
        HTTPException: If the rule is not found.
    """
    rule = _rules_store.get(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with ID '{rule_id}' not found",
        )
    return rule


@router.put("/{rule_id}", response_model=Rule)
async def update_rule(
    rule_id: UUID,
    rule_data: RuleUpdate,
    agent: RuleEnforcerAgent = Depends(get_rule_enforcer),
) -> Rule:
    """Update an existing rule.

    Args:
        rule_id: The rule ID.
        rule_data: The rule update data.
        agent: The rule enforcer agent.

    Returns:
        The updated rule.

    Raises:
        HTTPException: If the rule is not found.
    """
    rule = _rules_store.get(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with ID '{rule_id}' not found",
        )

    update_dict = rule_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(rule, field, value)

    rule.version += 1
    from datetime import datetime

    rule.updated_at = datetime.utcnow()
    logger.info(f"Rule updated: {rule.name}", rule_id=str(rule.id), version=rule.version)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    agent: RuleEnforcerAgent = Depends(get_rule_enforcer),
) -> None:
    """Delete a rule.

    Args:
        rule_id: The rule ID.
        agent: The rule enforcer agent.

    Raises:
        HTTPException: If the rule is not found.
    """
    if rule_id not in _rules_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with ID '{rule_id}' not found",
        )
    rule = _rules_store.pop(rule_id)
    agent.remove_rule(rule_id)
    logger.info(f"Rule deleted: {rule.name}", rule_id=str(rule_id))


@router.post("/enforce", response_model=list[RuleEnforcementResult])
async def enforce_rules(
    action_data: GovernanceActionCreate,
    context: dict[str, Any] | None = None,
    agent: RuleEnforcerAgent = Depends(get_rule_enforcer),
) -> list[RuleEnforcementResult]:
    """Enforce rules against a governance action.

    Args:
        action_data: The action to evaluate.
        context: Optional additional context.
        agent: The rule enforcer agent.

    Returns:
        List of enforcement results.
    """
    action = GovernanceAction(
        action_type=action_data.action_type,
        target_id=action_data.target_id,
        target_type=action_data.target_type,
        actor_id=action_data.actor_id,
        reason=action_data.reason,
        metadata=action_data.metadata,
    )

    results = await agent.execute({"action": action, "context": context or {}})
    logger.info(
        f"Rules enforced for action {action.id}",
        action_id=str(action.id),
        violation_count=len([r for r in results if r.is_violation]),
    )
    return results

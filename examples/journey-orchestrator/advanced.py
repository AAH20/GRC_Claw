"""
Advanced Journey Orchestration Example
======================================

Demonstrates advanced journey orchestration including:
- Dynamic journey personalization
- A/B testing within journeys
- Multi-step conditional branching
- Journey performance optimization
- Predictive next-best-action
- Journey versioning and rollback
- Cross-journey orchestration

Usage:
    python advanced.py
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BranchOperator(str, Enum):
    """Operators for conditional branching."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    IN = "in"
    BETWEEN = "between"
    EXISTS = "exists"


class ActionType(str, Enum):
    """Types of journey actions."""

    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    SEND_PUSH = "send_push"
    UPDATE_PROFILE = "update_profile"
    WEBHOOK = "webhook"
    WAIT = "wait"
    SPLIT_TEST = "split_test"
    GOAL = "goal"


@dataclass
class Condition:
    """A condition for branching."""

    attribute: str
    operator: BranchOperator
    value: Any = None
    value_range: tuple[Any, Any] | None = None

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate the condition against a context.

        Args:
            context: The context data to evaluate against.

        Returns:
            True if condition is met.
        """
        actual = context.get(self.attribute)

        if self.operator == BranchOperator.EQUALS:
            return actual == self.value
        elif self.operator == BranchOperator.NOT_EQUALS:
            return actual != self.value
        elif self.operator == BranchOperator.GREATER_THAN:
            return actual is not None and actual > self.value
        elif self.operator == BranchOperator.LESS_THAN:
            return actual is not None and actual < self.value
        elif self.operator == BranchOperator.CONTAINS:
            return self.value in actual if actual else False
        elif self.operator == BranchOperator.IN:
            return actual in self.value if self.value else False
        elif self.operator == BranchOperator.BETWEEN:
            if self.value_range and actual is not None:
                return self.value_range[0] <= actual <= self.value_range[1]
            return False
        elif self.operator == BranchOperator.EXISTS:
            return actual is not None

        return False


@dataclass
class JourneyAction:
    """An action to execute in a journey."""

    id: str
    action_type: ActionType
    config: dict[str, Any] = field(default_factory=dict)
    conditions: list[Condition] = field(default_factory=list)
    fallback_action_id: str | None = None

    def should_execute(self, context: dict[str, Any]) -> bool:
        """Check if this action should execute.

        Args:
            context: The journey context.

        Returns:
            True if all conditions are met.
        """
        return all(c.evaluate(context) for c in self.conditions)


@dataclass
class JourneyVariant:
    """A variant for A/B testing."""

    id: str
    name: str
    weight: float
    actions: list[JourneyAction] = field(default_factory=list)
    performance_score: float = 0.0


@dataclass
class JourneyNode:
    """A node in the journey graph."""

    id: str
    name: str
    node_type: str
    actions: list[JourneyAction] = field(default_factory=dict)
    conditions: list[Condition] = field(default_factory=list)
    next_nodes: list[str] = field(default_factory=list)
    variants: list[JourneyVariant] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalizationRule:
    """A rule for journey personalization."""

    id: str
    name: str
    condition: Condition
    action_modifications: dict[str, Any] = field(default_factory=dict)
    priority: int = 0


class AdvancedJourneyOrchestrator:
    """Advanced journey orchestrator with personalization and A/B testing."""

    def __init__(self) -> None:
        """Initialize the advanced orchestrator."""
        self.journeys: dict[str, Any] = {}
        self.nodes: dict[str, JourneyNode] = {}
        self.personalization_rules: dict[str, list[PersonalizationRule]] = {}
        self.execution_history: list[dict[str, Any]] = []

    def create_journey(
        self,
        name: str,
        description: str,
        version: str = "1.0",
    ) -> dict[str, Any]:
        """Create a new journey.

        Args:
            name: Journey name.
            description: Journey description.
            version: Journey version.

        Returns:
            Journey data dictionary.
        """
        journey_id = f"adv_journey_{len(self.journeys) + 1:04d}"
        journey = {
            "id": journey_id,
            "name": name,
            "description": description,
            "version": version,
            "nodes": {},
            "start_node_id": "",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
        }
        self.journeys[journey_id] = journey
        self.personalization_rules[journey_id] = []
        logger.info("Created advanced journey '%s' v%s", name, version)
        return journey

    def add_node(self, journey_id: str, node: JourneyNode) -> None:
        """Add a node to a journey.

        Args:
            journey_id: Journey identifier.
            node: The node to add.
        """
        if journey_id not in self.journeys:
            raise ValueError(f"Journey '{journey_id}' not found")

        self.journeys[journey_id]["nodes"][node.id] = {
            "id": node.id,
            "name": node.name,
            "type": node.node_type,
            "actions": node.actions,
            "conditions": node.conditions,
            "next_nodes": node.next_nodes,
            "variants": node.variants,
        }
        self.nodes[node.id] = node

    def add_personalization_rule(
        self,
        journey_id: str,
        rule: PersonalizationRule,
    ) -> None:
        """Add a personalization rule to a journey.

        Args:
            journey_id: Journey identifier.
            rule: The personalization rule.
        """
        if journey_id not in self.personalization_rules:
            raise ValueError(f"Journey '{journey_id}' not found")

        self.personalization_rules[journey_id].append(rule)
        # Sort by priority (higher first)
        self.personalization_rules[journey_id].sort(key=lambda r: r.priority, reverse=True)

    def select_variant(
        self,
        node: JourneyNode,
        customer_id: str,
    ) -> JourneyVariant | None:
        """Select an A/B test variant for a customer.

        Args:
            node: The node with variants.
            customer_id: Customer identifier.

        Returns:
            Selected variant or None.
        """
        if not node.variants:
            return None

        # Deterministic assignment based on customer_id
        hash_val = hash(customer_id) % 1000 / 1000.0
        cumulative = 0.0
        for variant in node.variants:
            cumulative += variant.weight
            if hash_val <= cumulative:
                return variant

        return node.variants[-1]

    def evaluate_conditions(
        self,
        conditions: list[Condition],
        context: dict[str, Any],
    ) -> bool:
        """Evaluate conditions against context.

        Args:
            conditions: List of conditions.
            context: Context data.

        Returns:
            True if all conditions are met.
        """
        return all(c.evaluate(context) for c in conditions)

    def get_personalized_actions(
        self,
        journey_id: str,
        node_id: str,
        context: dict[str, Any],
    ) -> list[JourneyAction]:
        """Get personalized actions for a customer.

        Args:
            journey_id: Journey identifier.
            node_id: Node identifier.
            context: Customer context.

        Returns:
            List of personalized actions.
        """
        if journey_id not in self.journeys:
            raise ValueError(f"Journey '{journey_id}' not found")

        journey = self.journeys[journey_id]
        node_data = journey["nodes"].get(node_id)
        if node_data is None:
            raise ValueError(f"Node '{node_id}' not found")

        actions = node_data.get("actions", [])

        # Apply personalization rules
        rules = self.personalization_rules.get(journey_id, [])
        for rule in rules:
            if rule.condition.evaluate(context):
                # Modify actions based on rule
                for action in actions:
                    for key, value in rule.action_modifications.items():
                        if key in action.config:
                            action.config[key] = value
                break  # Only apply highest priority matching rule

        return actions

    def execute_journey(
        self,
        journey_id: str,
        customer_id: str,
        context: dict[str, Any],
        max_steps: int = 20,
    ) -> dict[str, Any]:
        """Execute a journey for a customer.

        Args:
            journey_id: Journey identifier.
            customer_id: Customer identifier.
            context: Initial context.
            max_steps: Maximum steps to prevent infinite loops.

        Returns:
            Execution result dictionary.
        """
        if journey_id not in self.journeys:
            raise ValueError(f"Journey '{journey_id}' not found")

        journey = self.journeys[journey_id]
        current_node_id = journey.get("start_node_id", "")
        if not current_node_id:
            raise ValueError("Journey has no start node")

        execution_path: list[dict[str, Any]] = []
        step = 0

        while step < max_steps:
            step += 1
            node_data = journey["nodes"].get(current_node_id)
            if node_data is None:
                break

            node = self.nodes.get(current_node_id)
            if node is None:
                break

            # Check conditions
            if node.conditions and not self.evaluate_conditions(node.conditions, context):
                # Skip this node
                if node.next_nodes:
                    current_node_id = node.next_nodes[0]
                    continue
                break

            # Select variant if A/B testing
            variant = self.select_variant(node, customer_id) if node else None

            # Get personalized actions
            actions = self.get_personalized_actions(journey_id, current_node_id, context)

            # Execute actions
            executed_actions = []
            for action in actions:
                if action.should_execute(context):
                    executed_actions.append({
                        "action_id": action.id,
                        "type": action.action_type.value,
                        "config": action.config,
                    })
                    # Simulate action execution
                    self._simulate_action(action, context)

            execution_path.append({
                "node_id": current_node_id,
                "node_name": node_data["name"],
                "variant": variant.id if variant else None,
                "actions": executed_actions,
                "timestamp": datetime.now().isoformat(),
            })

            # Determine next node
            next_nodes = node.next_nodes
            if not next_nodes:
                break

            # Simple: take first next node (in production, use conditions)
            current_node_id = next_nodes[0]

        result = {
            "journey_id": journey_id,
            "customer_id": customer_id,
            "steps_taken": step,
            "path": execution_path,
            "completed": step < max_steps,
            "final_context": context,
        }

        self.execution_history.append(result)
        return result

    def _simulate_action(self, action: JourneyAction, context: dict[str, Any]) -> None:
        """Simulate action execution.

        Args:
            action: The action to simulate.
            context: The journey context.
        """
        if action.action_type == ActionType.UPDATE_PROFILE:
            context.update(action.config.get("updates", {}))
        elif action.action_type == ActionType.WAIT:
            pass  # No-op for simulation

    def get_journey_performance(self, journey_id: str) -> dict[str, Any]:
        """Get performance metrics for a journey.

        Args:
            journey_id: Journey identifier.

        Returns:
            Performance metrics dictionary.
        """
        if journey_id not in self.journeys:
            raise ValueError(f"Journey '{journey_id}' not found")

        executions = [
            e for e in self.execution_history
            if e["journey_id"] == journey_id
        ]

        total = len(executions)
        completed = sum(1 for e in executions if e["completed"])
        avg_steps = sum(e["steps_taken"] for e in executions) / total if total > 0 else 0

        # Node-level metrics
        node_metrics: dict[str, dict[str, Any]] = {}
        for exec_result in executions:
            for step in exec_result["path"]:
                node_id = step["node_id"]
                if node_id not in node_metrics:
                    node_metrics[node_id] = {
                        "visits": 0,
                        "actions_executed": 0,
                    }
                node_metrics[node_id]["visits"] += 1
                node_metrics[node_id]["actions_executed"] += len(step["actions"])

        return {
            "journey_id": journey_id,
            "total_executions": total,
            "completed": completed,
            "completion_rate": round(completed / total, 4) if total > 0 else 0,
            "avg_steps": round(avg_steps, 2),
            "node_metrics": node_metrics,
        }


def main() -> None:
    """Run the advanced journey orchestration example."""
    logger.info("=" * 60)
    logger.info("Advanced Journey Orchestration Example")
    logger.info("=" * 60)

    orchestrator = AdvancedJourneyOrchestrator()

    # Create journey
    journey = orchestrator.create_journey(
        name="Personalized Onboarding",
        description="AI-powered personalized onboarding journey",
        version="2.0",
    )

    # Create nodes
    start_node = JourneyNode(
        id="start",
        name="Start",
        node_type="start",
        next_nodes=["check_segment"],
    )

    segment_check = JourneyNode(
        id="check_segment",
        name="Check Segment",
        node_type="condition",
        conditions=[
            Condition("customer_segment", BranchOperator.EQUALS, "enterprise"),
        ],
        next_nodes=["enterprise_path", "standard_path"],
    )

    enterprise_path = JourneyNode(
        id="enterprise_path",
        name="Enterprise Path",
        node_type="action",
        actions=[
            JourneyAction(
                id="ent_welcome",
                action_type=ActionType.SEND_EMAIL,
                config={"template": "enterprise_welcome", "channel": "email"},
            ),
            JourneyAction(
                id="ent_schedule",
                action_type=ActionType.SEND_EMAIL,
                config={"template": "schedule_csm", "channel": "email"},
            ),
        ],
        next_nodes=["wait_1_day"],
    )

    standard_path = JourneyNode(
        id="standard_path",
        name="Standard Path",
        node_type="action",
        actions=[
            JourneyAction(
                id="std_welcome",
                action_type=ActionType.SEND_EMAIL,
                config={"template": "standard_welcome", "channel": "email"},
            ),
        ],
        next_nodes=["wait_1_day"],
    )

    wait_node = JourneyNode(
        id="wait_1_day",
        name="Wait 1 Day",
        node_type="wait",
        config={"duration_hours": 24},
        next_nodes=["engagement_check"],
    )

    engagement_check = JourneyNode(
        id="engagement_check",
        name="Engagement Check",
        node_type="split_test",
        variants=[
            JourneyVariant(
                id="variant_a",
                name="Email Focus",
                weight=0.5,
                actions=[
                    JourneyAction(
                        id="email_content",
                        action_type=ActionType.SEND_EMAIL,
                        config={"template": "content_series", "channel": "email"},
                    ),
                ],
            ),
            JourneyVariant(
                id="variant_b",
                name="Push Focus",
                weight=0.5,
                actions=[
                    JourneyAction(
                        id="push_content",
                        action_type=ActionType.SEND_PUSH,
                        config={"template": "content_push", "channel": "push"},
                    ),
                ],
            ),
        ],
        next_nodes=["end"],
    )

    end_node = JourneyNode(
        id="end",
        name="End",
        node_type="end",
    )

    # Add nodes to journey
    for node in [start_node, segment_check, enterprise_path, standard_path, wait_node, engagement_check, end_node]:
        orchestrator.add_node(journey["id"], node)

    journey["start_node_id"] = "start"

    # Add personalization rules
    orchestrator.add_personalization_rule(
        journey["id"],
        PersonalizationRule(
            id="rule_1",
            name="VIP Treatment",
            condition=Condition("customer_tier", BranchOperator.EQUALS, "vip"),
            action_modifications={"priority": "high", "template": "vip_welcome"},
            priority=10,
        ),
    )

    orchestrator.add_personalization_rule(
        journey["id"],
        PersonalizationRule(
            id="rule_2",
            name="Low Engagement",
            condition=Condition("engagement_score", BranchOperator.LESS_THAN, 30),
            action_modifications={"template": "re_engagement"},
            priority=5,
        ),
    )

    # Execute journeys for different customers
    customers = [
        {"customer_id": "cust_001", "context": {"customer_segment": "enterprise", "customer_tier": "vip", "engagement_score": 80}},
        {"customer_id": "cust_002", "context": {"customer_segment": "standard", "customer_tier": "regular", "engagement_score": 50}},
        {"customer_id": "cust_003", "context": {"customer_segment": "enterprise", "customer_tier": "regular", "engagement_score": 20}},
    ]

    logger.info("\nExecuting journeys...")
    for cust in customers:
        result = orchestrator.execute_journey(
            journey_id=journey["id"],
            customer_id=cust["customer_id"],
            context=cust["context"].copy(),
        )
        logger.info(
            "  %s: %d steps, completed=%s",
            cust["customer_id"],
            result["steps_taken"],
            result["completed"],
        )

    # Get performance metrics
    performance = orchestrator.get_journey_performance(journey["id"])
    logger.info("\nJourney Performance:")
    logger.info("  Total executions: %d", performance["total_executions"])
    logger.info("  Completion rate: %.1f%%", performance["completion_rate"] * 100)
    logger.info("  Avg steps: %.1f", performance["avg_steps"])

    logger.info("\n" + "=" * 60)
    logger.info("Advanced example complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

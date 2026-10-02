"""Event routing for directing events to appropriate handlers.

Provides pattern-based event routing with support for wildcards, content-based
routing rules, and dynamic route management.
"""

from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from .schema import Event

logger = logging.getLogger(__name__)


@dataclass
class RouteRule:
    """A single routing rule that matches events and directs them to a target.

    Attributes:
        name: Human-readable name for the rule.
        pattern: Glob pattern matched against event_type (e.g., 'campaign.*').
        target: Destination identifier (e.g., handler name, queue name).
        priority: Rule evaluation priority; higher values are evaluated first.
        condition: Optional predicate for content-based routing.
        metadata: Arbitrary metadata associated with the rule.
    """

    name: str
    pattern: str
    target: str
    priority: int = 0
    condition: Optional[Callable[[Event], bool]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventRouter:
    """Pattern-based event router.

    Routes events to targets based on glob-pattern matching on event types
    and optional content-based conditions. Rules are evaluated in priority
    order; the first matching rule wins.

    Example:
        >>> router = EventRouter()
        >>> router.add_rule(RouteRule("campaign_route", "campaign.*", "campaign_handler"))
        >>> router.add_rule(RouteRule("all_events", "*", "default_handler"))
        >>> target = router.route(event)
    """

    def __init__(self) -> None:
        """Initialize the event router."""
        self._rules: List[RouteRule] = []
        self._targets: Dict[str, Callable[[Event], None]] = {}
        self._default_target: Optional[str] = None

    def add_rule(self, rule: RouteRule) -> None:
        """Add a routing rule.

        Args:
            rule: The routing rule to add.

        Raises:
            ValueError: If a rule with the same name already exists.
        """
        if any(r.name == rule.name for r in self._rules):
            raise ValueError(f"Rule '{rule.name}' already exists")
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
        logger.debug("Added routing rule '%s' (pattern=%s, target=%s)", rule.name, rule.pattern, rule.target)

    def remove_rule(self, name: str) -> bool:
        """Remove a routing rule by name.

        Args:
            name: The name of the rule to remove.

        Returns:
            True if the rule was found and removed, False otherwise.
        """
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                return True
        return False

    def register_target(self, name: str, handler: Callable[[Event], None]) -> None:
        """Register a named target handler.

        Args:
            name: Target identifier used in routing rules.
            handler: Callback function invoked when an event is routed to this target.

        Raises:
            ValueError: If name is empty or handler is not callable.
        """
        if not name:
            raise ValueError("Target name must not be empty")
        if not callable(handler):
            raise ValueError("Handler must be callable")
        self._targets[name] = handler

    def set_default_target(self, target: str) -> None:
        """Set the default target for events that match no rules.

        Args:
            target: The default target identifier.
        """
        self._default_target = target

    def route(self, event: Event) -> Optional[str]:
        """Route an event to its target.

        Evaluates rules in priority order. The first rule whose pattern
        matches the event type and whose condition (if any) passes determines
        the target.

        Args:
            event: The event to route.

        Returns:
            The target identifier, or None if no rule matched and no default
            target is set.
        """
        for rule in self._rules:
            if not fnmatch.fnmatch(event.event_type, rule.pattern):
                continue
            if rule.condition and not rule.condition(event):
                continue
            logger.debug(
                "Routed event %s (type=%s) to target '%s' via rule '%s'",
                event.metadata.event_id,
                event.event_type,
                rule.target,
                rule.name,
            )
            return rule.target

        if self._default_target:
            logger.debug(
                "Routed event %s (type=%s) to default target '%s'",
                event.metadata.event_id,
                event.event_type,
                self._default_target,
            )
            return self._default_target

        logger.warning(
            "No route found for event %s (type=%s)",
            event.metadata.event_id,
            event.event_type,
        )
        return None

    def dispatch(self, event: Event) -> bool:
        """Route an event and invoke the target handler.

        Args:
            event: The event to dispatch.

        Returns:
            True if the event was routed and the handler was invoked,
            False if no route was found or the target handler is not registered.
        """
        target = self.route(event)
        if target is None:
            return False

        handler = self._targets.get(target)
        if handler is None:
            logger.error("Target '%s' has no registered handler", target)
            return False

        try:
            handler(event)
            return True
        except Exception:
            logger.exception("Handler for target '%s' failed", target)
            return False

    def get_rules(self) -> List[RouteRule]:
        """Get all registered routing rules.

        Returns:
            List of routing rules sorted by priority (highest first).
        """
        return list(self._rules)

    def get_targets(self) -> Set[str]:
        """Get all registered target names.

        Returns:
            Set of target identifiers.
        """
        return set(self._targets.keys())

    def clear(self) -> None:
        """Remove all rules and targets."""
        self._rules.clear()
        self._targets.clear()
        self._default_target = None

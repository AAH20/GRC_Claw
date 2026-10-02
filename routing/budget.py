"""Token budget enforcement system.

Provides configurable token budgets with enforcement, tracking,
and alerting for AI model usage across projects and time windows.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class BudgetPeriod(Enum):
    """Budget enforcement period."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    TOTAL = "total"


@dataclass
class BudgetConfig:
    """Configuration for a token budget.

    Attributes:
        period: The budget enforcement period.
        max_tokens: Maximum tokens allowed in the period.
        max_cost_usd: Maximum cost in USD allowed in the period.
        alert_thresholds: List of percentage thresholds for alerts (0.0-1.0).
        hard_limit: Whether to hard-block when budget is exceeded.
        project_id: Optional project identifier for scoped budgets.
    """

    period: BudgetPeriod
    max_tokens: int
    max_cost_usd: float = 0.0
    alert_thresholds: List[float] = field(default_factory=lambda: [0.5, 0.8, 0.95])
    hard_limit: bool = True
    project_id: Optional[str] = None


@dataclass
class UsageRecord:
    """Record of token usage.

    Attributes:
        timestamp: Unix timestamp of the usage.
        tokens: Number of tokens consumed.
        cost_usd: Cost in USD.
        model: Model that was used.
        project_id: Optional project identifier.
    """

    timestamp: float
    tokens: int
    cost_usd: float
    model: str
    project_id: Optional[str] = None


class BudgetExceededError(Exception):
    """Raised when a token budget is exceeded."""

    def __init__(
        self,
        message: str,
        budget_config: BudgetConfig,
        current_usage: int,
        attempted_tokens: int,
    ) -> None:
        """Initialize BudgetExceededError.

        Args:
            message: Error message.
            budget_config: The budget configuration that was exceeded.
            current_usage: Current token usage.
            attempted_tokens: Tokens that were attempted to be consumed.
        """
        super().__init__(message)
        self.budget_config = budget_config
        self.current_usage = current_usage
        self.attempted_tokens = attempted_tokens


class TokenBudget:
    """Token budget with enforcement and tracking.

    Thread-safe budget tracker that enforces token and cost limits
    across configurable time periods.

    Example:
        >>> config = BudgetConfig(period=BudgetPeriod.DAILY, max_tokens=100_000)
        >>> budget = TokenBudget(config)
        >>> budget.consume(tokens=1000, cost_usd=0.01, model="gpt-4o")
        >>> usage = budget.get_usage()
        >>> print(usage["tokens"])
        1000
    """

    _PERIOD_SECONDS: Dict[BudgetPeriod, float] = {
        BudgetPeriod.HOURLY: 3600.0,
        BudgetPeriod.DAILY: 86400.0,
        BudgetPeriod.WEEKLY: 604800.0,
        BudgetPeriod.MONTHLY: 2592000.0,
        BudgetPeriod.TOTAL: float("inf"),
    }

    def __init__(self, config: BudgetConfig) -> None:
        """Initialize the token budget.

        Args:
            config: Budget configuration.
        """
        self._config = config
        self._usage_history: List[UsageRecord] = []
        self._lock = threading.Lock()
        self._alert_callbacks: List[Callable[[float, BudgetConfig], None]] = []
        self._alerted_thresholds: Set[float] = set()

    @property
    def config(self) -> BudgetConfig:
        """Get the budget configuration.

        Returns:
            The budget configuration.
        """
        return self._config

    def add_alert_callback(
        self,
        callback: Callable[[float, BudgetConfig], None],
    ) -> None:
        """Add a callback for budget threshold alerts.

        Args:
            callback: Function called with (usage_ratio, config) when
                a threshold is crossed.
        """
        self._alert_callbacks.append(callback)

    def consume(
        self,
        tokens: int,
        cost_usd: float = 0.0,
        model: str = "unknown",
        project_id: Optional[str] = None,
    ) -> None:
        """Consume tokens from the budget.

        Args:
            tokens: Number of tokens to consume.
            cost_usd: Cost in USD for this consumption.
            model: Model that was used.
            project_id: Optional project identifier.

        Raises:
            BudgetExceededError: If the budget would be exceeded and
                hard_limit is True.
            ValueError: If tokens is negative.
        """
        if tokens < 0:
            raise ValueError("Token consumption cannot be negative")

        with self._lock:
            self._cleanup_old_records()

            current_tokens = self._sum_tokens()
            current_cost = self._sum_cost()

            # Check token limit
            if self._config.hard_limit and current_tokens + tokens > self._config.max_tokens:
                raise BudgetExceededError(
                    f"Token budget exceeded: {current_tokens + tokens} > "
                    f"{self._config.max_tokens} ({self._config.period.value})",
                    self._config,
                    current_tokens,
                    tokens,
                )

            # Check cost limit
            if (
                self._config.max_cost_usd > 0
                and self._config.hard_limit
                and current_cost + cost_usd > self._config.max_cost_usd
            ):
                raise BudgetExceededError(
                    f"Cost budget exceeded: ${current_cost + cost_usd:.4f} > "
                    f"${self._config.max_cost_usd:.4f} ({self._config.period.value})",
                    self._config,
                    current_tokens,
                    tokens,
                )

            # Record usage
            record = UsageRecord(
                timestamp=time.time(),
                tokens=tokens,
                cost_usd=cost_usd,
                model=model,
                project_id=project_id or self._config.project_id,
            )
            self._usage_history.append(record)

            # Check alert thresholds
            self._check_alerts()

    def get_usage(self) -> Dict[str, float]:
        """Get current budget usage.

        Returns:
            Dictionary with tokens, cost_usd, and usage_ratio.
        """
        with self._lock:
            self._cleanup_old_records()
            tokens = self._sum_tokens()
            cost = self._sum_cost()
            ratio = tokens / self._config.max_tokens if self._config.max_tokens > 0 else 0.0
            return {
                "tokens": float(tokens),
                "cost_usd": cost,
                "usage_ratio": ratio,
                "remaining_tokens": float(self._config.max_tokens - tokens),
            }

    def get_usage_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Get usage breakdown by model.

        Returns:
            Dictionary mapping model names to usage stats.
        """
        with self._lock:
            self._cleanup_old_records()
            breakdown: Dict[str, Dict[str, float]] = {}
            for record in self._usage_history:
                if record.model not in breakdown:
                    breakdown[record.model] = {"tokens": 0, "cost_usd": 0.0}
                breakdown[record.model]["tokens"] += record.tokens
                breakdown[record.model]["cost_usd"] += record.cost_usd
            return breakdown

    def reset(self) -> None:
        """Reset the budget usage history."""
        with self._lock:
            self._usage_history.clear()
            self._alerted_thresholds.clear()
            logger.info("Budget reset for period: %s", self._config.period.value)

    def _cleanup_old_records(self) -> None:
        """Remove records outside the current budget period."""
        if self._config.period == BudgetPeriod.TOTAL:
            return

        cutoff = time.time() - self._PERIOD_SECONDS[self._config.period]
        self._usage_history = [
            r for r in self._usage_history if r.timestamp >= cutoff
        ]

    def _sum_tokens(self) -> int:
        """Sum tokens in current period.

        Returns:
            Total tokens consumed in the current period.
        """
        return sum(r.tokens for r in self._usage_history)

    def _sum_cost(self) -> float:
        """Sum cost in current period.

        Returns:
            Total cost in USD for the current period.
        """
        return sum(r.cost_usd for r in self._usage_history)

    def _check_alerts(self) -> None:
        """Check and fire alert callbacks for crossed thresholds."""
        if not self._config.alert_thresholds:
            return

        ratio = self._sum_tokens() / self._config.max_tokens if self._config.max_tokens > 0 else 0.0

        for threshold in self._config.alert_thresholds:
            if ratio >= threshold and threshold not in self._alerted_thresholds:
                self._alerted_thresholds.add(threshold)
                logger.warning(
                    "Budget alert: %.1f%% of %s budget used",
                    threshold * 100,
                    self._config.period.value,
                )
                for callback in self._alert_callbacks:
                    try:
                        callback(ratio, self._config)
                    except Exception as exc:
                        logger.error("Alert callback failed: %s", exc)


class BudgetManager:
    """Manages multiple token budgets across projects and periods.

    Example:
        >>> manager = BudgetManager()
        >>> manager.add_budget("project-a", BudgetConfig(
        ...     period=BudgetPeriod.DAILY, max_tokens=50_000
        ... ))
        >>> manager.consume("project-a", tokens=1000, cost_usd=0.01)
    """

    def __init__(self) -> None:
        """Initialize the budget manager."""
        self._budgets: Dict[str, TokenBudget] = {}
        self._lock = threading.Lock()

    def add_budget(self, name: str, config: BudgetConfig) -> TokenBudget:
        """Add a named budget.

        Args:
            name: Unique budget name.
            config: Budget configuration.

        Returns:
            The created TokenBudget instance.

        Raises:
            ValueError: If a budget with the same name exists.
        """
        with self._lock:
            if name in self._budgets:
                raise ValueError(f"Budget '{name}' already exists")
            budget = TokenBudget(config)
            self._budgets[name] = budget
            return budget

    def get_budget(self, name: str) -> Optional[TokenBudget]:
        """Get a budget by name.

        Args:
            name: Budget name.

        Returns:
            The TokenBudget or None if not found.
        """
        return self._budgets.get(name)

    def consume(
        self,
        budget_name: str,
        tokens: int,
        cost_usd: float = 0.0,
        model: str = "unknown",
    ) -> None:
        """Consume tokens from a named budget.

        Args:
            budget_name: Name of the budget.
            tokens: Tokens to consume.
            cost_usd: Cost in USD.
            model: Model used.

        Raises:
            KeyError: If the budget doesn't exist.
        """
        budget = self._budgets.get(budget_name)
        if budget is None:
            raise KeyError(f"Budget '{budget_name}' not found")
        budget.consume(tokens=tokens, cost_usd=cost_usd, model=model)

    def get_all_usage(self) -> Dict[str, Dict[str, float]]:
        """Get usage for all budgets.

        Returns:
            Dictionary mapping budget names to usage stats.
        """
        return {name: budget.get_usage() for name, budget in self._budgets.items()}

"""Model routing and cost optimization system for agentic AI marketing projects.

Provides tiered model routing, Laya integration, token budget enforcement,
cost monitoring, semantic caching, fallback strategies, quality scoring,
and latency optimization.
"""

from .router import ModelRouter, ModelSpec, RoutingDecision, RouteTier
from .laya import LayaClient, LayaConfig
from .budget import TokenBudget, BudgetExceededError
from .cost import CostMonitor, CostEntry
from .cache import SemanticCache, CacheEntry
from .fallback import FallbackStrategy, FallbackChain
from .quality import QualityScorer, QualityScore
from .latency import LatencyOptimizer, LatencyProfile

__all__ = [
    "ModelRouter",
    "ModelSpec",
    "RoutingDecision",
    "RouteTier",
    "LayaClient",
    "LayaConfig",
    "TokenBudget",
    "BudgetExceededError",
    "CostMonitor",
    "CostEntry",
    "SemanticCache",
    "CacheEntry",
    "FallbackStrategy",
    "FallbackChain",
    "QualityScorer",
    "QualityScore",
    "LatencyOptimizer",
    "LatencyProfile",
]

__version__ = "1.0.0"

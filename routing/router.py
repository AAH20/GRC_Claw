"""Tiered model routing system.

Routes incoming requests to the optimal model based on task complexity,
cost constraints, latency requirements, and quality thresholds.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


class RouteTier(Enum):
    """Model tier classification."""

    ULTRA_FAST = "ultra_fast"  # <50ms, minimal cost
    FAST = "fast"  # <200ms, low cost
    BALANCED = "balanced"  # <1s, moderate cost
    QUALITY = "quality"  # <5s, higher cost
    ULTRA_QUALITY = "ultra_quality"  # <30s, premium cost


@dataclass(frozen=True)
class ModelSpec:
    """Specification for a routable model."""

    name: str
    tier: RouteTier
    max_tokens: int
    cost_per_1k_tokens: float
    avg_latency_ms: float
    quality_score: float  # 0.0 - 1.0
    capabilities: frozenset[str] = field(default_factory=frozenset)
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_function_calling: bool = False


@dataclass
class RoutingDecision:
    """Result of a routing decision."""

    model: ModelSpec
    tier: RouteTier
    estimated_cost: float
    estimated_latency_ms: float
    confidence: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ComplexityAnalyzer(Protocol):
    """Protocol for complexity analysis backends."""

    def analyze(self, prompt: str, context: Optional[str] = None) -> float:
        """Return complexity score 0.0-1.0."""
        ...


class HeuristicComplexityAnalyzer:
    """Rule-based complexity analyzer (no external dependencies)."""

    COMPLEX_INDICATORS = [
        "analyze", "compare", "synthesize", "evaluate", "design",
        "architect", "strategize", "optimize", "reason", "prove",
        "multi-step", "trade-off", "implications", "forecast",
    ]

    SIMPLE_INDICATORS = [
        "what is", "define", "list", "name", "when", "where",
        "who", "how many", "translate", "summarize briefly",
    ]

    def analyze(self, prompt: str, context: Optional[str] = None) -> float:
        """Analyze prompt complexity using keyword heuristics.

        Args:
            prompt: The user prompt to analyze.
            context: Optional conversation context.

        Returns:
            Complexity score between 0.0 and 1.0.
        """
        text = prompt.lower()
        words = len(text.split())

        complex_hits = sum(1 for ind in self.COMPLEX_INDICATORS if ind in text)
        simple_hits = sum(1 for ind in self.SIMPLE_INDICATORS if ind in text)

        # Base score from keyword density
        score = 0.3
        score += min(complex_hits * 0.15, 0.4)
        score -= min(simple_hits * 0.1, 0.2)

        # Length factor: longer prompts tend to be more complex
        if words > 200:
            score += 0.15
        elif words > 100:
            score += 0.08

        # Context factor
        if context and len(context) > 1000:
            score += 0.05

        return max(0.0, min(1.0, score))


class ModelRouter:
    """Tiered model router with cost and latency optimization.

    Routes requests to the most appropriate model based on complexity,
    budget constraints, and quality requirements.

    Example:
        >>> router = ModelRouter()
        >>> router.register_model(ModelSpec(
        ...     name="gpt-4o-mini",
        ...     tier=RouteTier.FAST,
        ...     max_tokens=128000,
        ...     cost_per_1k_tokens=0.00015,
        ...     avg_latency_ms=150,
        ...     quality_score=0.75,
        ... ))
        >>> decision = router.route("What is 2+2?")
        >>> print(decision.model.name)
        gpt-4o-mini
    """

    def __init__(
        self,
        complexity_analyzer: Optional[ComplexityAnalyzer] = None,
        default_tier: RouteTier = RouteTier.BALANCED,
    ) -> None:
        """Initialize the model router.

        Args:
            complexity_analyzer: Custom complexity analyzer. Uses heuristic
                analyzer if None.
            default_tier: Default tier for routing when no specific tier
                is requested.
        """
        self._models: Dict[str, ModelSpec] = {}
        self._complexity_analyzer = complexity_analyzer or HeuristicComplexityAnalyzer()
        self._default_tier = default_tier
        self._pre_routing_hooks: List[Callable[[str], None]] = []
        self._post_routing_hooks: List[Callable[[RoutingDecision], None]] = []

    def register_model(self, model: ModelSpec) -> None:
        """Register a model for routing.

        Args:
            model: The model specification to register.

        Raises:
            ValueError: If a model with the same name is already registered.
        """
        if model.name in self._models:
            raise ValueError(f"Model '{model.name}' is already registered")
        self._models[model.name] = model
        logger.info("Registered model: %s (tier=%s)", model.name, model.tier.value)

    def unregister_model(self, name: str) -> None:
        """Unregister a model.

        Args:
            name: The model name to unregister.

        Raises:
            KeyError: If the model is not registered.
        """
        if name not in self._models:
            raise KeyError(f"Model '{name}' is not registered")
        del self._models[name]
        logger.info("Unregistered model: %s", name)

    def add_pre_routing_hook(self, hook: Callable[[str], None]) -> None:
        """Add a hook called before routing.

        Args:
            hook: Callable that receives the prompt string.
        """
        self._pre_routing_hooks.append(hook)

    def add_post_routing_hook(self, hook: Callable[[RoutingDecision], None]) -> None:
        """Add a hook called after routing.

        Args:
            hook: Callable that receives the routing decision.
        """
        self._post_routing_hooks.append(hook)

    def route(
        self,
        prompt: str,
        context: Optional[str] = None,
        tier: Optional[RouteTier] = None,
        max_cost: Optional[float] = None,
        max_latency_ms: Optional[float] = None,
        min_quality: Optional[float] = None,
        required_capabilities: Optional[List[str]] = None,
    ) -> RoutingDecision:
        """Route a prompt to the optimal model.

        Args:
            prompt: The user prompt to route.
            context: Optional conversation context.
            tier: Target tier. Uses default_tier if None.
            max_cost: Maximum acceptable cost per request in USD.
            max_latency_ms: Maximum acceptable latency in milliseconds.
            min_quality: Minimum acceptable quality score (0.0-1.0).
            required_capabilities: List of required capability strings.

        Returns:
            RoutingDecision with the selected model and metadata.

        Raises:
            NoSuitableModelError: If no model matches the constraints.
        """
        target_tier = tier or self._default_tier

        # Run pre-routing hooks
        for hook in self._pre_routing_hooks:
            try:
                hook(prompt)
            except Exception as exc:
                logger.warning("Pre-routing hook failed: %s", exc)

        complexity = self._complexity_analyzer.analyze(prompt, context)
        candidates = self._filter_models(
            tier=target_tier,
            max_cost=max_cost,
            max_latency_ms=max_latency_ms,
            min_quality=min_quality,
            required_capabilities=required_capabilities,
        )

        if not candidates:
            # Fallback: try all tiers
            candidates = self._filter_models(
                tier=None,
                max_cost=max_cost,
                max_latency_ms=max_latency_ms,
                min_quality=min_quality,
                required_capabilities=required_capabilities,
            )

        if not candidates:
            raise NoSuitableModelError(
                f"No model matches constraints: tier={target_tier.value}, "
                f"max_cost={max_cost}, max_latency={max_latency_ms}ms, "
                f"min_quality={min_quality}"
            )

        # Score candidates
        best_model = self._select_best(candidates, complexity, prompt)
        estimated_tokens = self._estimate_tokens(prompt, context)
        estimated_cost = (estimated_tokens / 1000) * best_model.cost_per_1k_tokens

        decision = RoutingDecision(
            model=best_model,
            tier=best_model.tier,
            estimated_cost=estimated_cost,
            estimated_latency_ms=best_model.avg_latency_ms,
            confidence=self._calculate_confidence(best_model, complexity),
            reason=self._generate_reason(best_model, complexity, target_tier),
            metadata={
                "complexity": complexity,
                "estimated_tokens": estimated_tokens,
                "candidates_considered": len(candidates),
            },
        )

        # Run post-routing hooks
        for hook in self._post_routing_hooks:
            try:
                hook(decision)
            except Exception as exc:
                logger.warning("Post-routing hook failed: %s", exc)

        logger.info(
            "Routed to %s (tier=%s, cost=$%.6f, confidence=%.2f)",
            best_model.name,
            best_model.tier.value,
            estimated_cost,
            decision.confidence,
        )

        return decision

    def get_models_by_tier(self, tier: RouteTier) -> List[ModelSpec]:
        """Get all models in a specific tier.

        Args:
            tier: The tier to filter by.

        Returns:
            List of model specifications in the tier.
        """
        return [m for m in self._models.values() if m.tier == tier]

    def list_models(self) -> List[ModelSpec]:
        """List all registered models.

        Returns:
            List of all registered model specifications.
        """
        return list(self._models.values())

    def _filter_models(
        self,
        tier: Optional[RouteTier],
        max_cost: Optional[float],
        max_latency_ms: Optional[float],
        min_quality: Optional[float],
        required_capabilities: Optional[List[str]],
    ) -> List[ModelSpec]:
        """Filter models based on constraints.

        Args:
            tier: Filter by tier. None means all tiers.
            max_cost: Maximum cost per 1k tokens.
            max_latency_ms: Maximum average latency.
            min_quality: Minimum quality score.
            required_capabilities: Required capabilities.

        Returns:
            Filtered list of model specifications.
        """
        candidates = self._models.values()

        if tier is not None:
            candidates = [m for m in candidates if m.tier == tier]
        if max_cost is not None:
            candidates = [m for m in candidates if m.cost_per_1k_tokens <= max_cost]
        if max_latency_ms is not None:
            candidates = [m for m in candidates if m.avg_latency_ms <= max_latency_ms]
        if min_quality is not None:
            candidates = [m for m in candidates if m.quality_score >= min_quality]
        if required_capabilities:
            req_set = set(required_capabilities)
            candidates = [m for m in candidates if req_set.issubset(m.capabilities)]

        return list(candidates)

    def _select_best(
        self,
        candidates: List[ModelSpec],
        complexity: float,
        prompt: str,
    ) -> ModelSpec:
        """Select the best model from candidates.

        Uses a weighted scoring function balancing quality, cost, and latency.

        Args:
            candidates: Filtered model candidates.
            complexity: Prompt complexity score.
            prompt: The original prompt.

        Returns:
            The best model specification.
        """
        if len(candidates) == 1:
            return candidates[0]

        def score(model: ModelSpec) -> float:
            # Quality weight increases with complexity
            quality_weight = 0.3 + (complexity * 0.4)
            cost_weight = 0.2
            latency_weight = 0.2
            capability_weight = 0.1

            # Normalize cost (lower is better)
            max_cost = max(m.cost_per_1k_tokens for m in candidates) or 1.0
            cost_score = 1.0 - (model.cost_per_1k_tokens / max_cost)

            # Normalize latency (lower is better)
            max_latency = max(m.avg_latency_ms for m in candidates) or 1.0
            latency_score = 1.0 - (model.avg_latency_ms / max_latency)

            # Quality (higher is better)
            quality_score = model.quality_score

            # Capability richness
            cap_score = min(len(model.capabilities) / 5.0, 1.0)

            return (
                quality_weight * quality_score
                + cost_weight * cost_score
                + latency_weight * latency_score
                + capability_weight * cap_score
            )

        return max(candidates, key=score)

    def _estimate_tokens(self, prompt: str, context: Optional[str]) -> int:
        """Estimate token count for a prompt.

        Uses a simple heuristic: ~4 characters per token for English text.

        Args:
            prompt: The user prompt.
            context: Optional conversation context.

        Returns:
            Estimated token count.
        """
        total_chars = len(prompt) + (len(context) if context else 0)
        return max(1, total_chars // 4)

    def _calculate_confidence(self, model: ModelSpec, complexity: float) -> float:
        """Calculate routing confidence.

        Args:
            model: The selected model.
            complexity: Prompt complexity score.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        # Higher confidence when model quality matches complexity needs
        quality_match = 1.0 - abs(model.quality_score - (0.5 + complexity * 0.5))
        return max(0.0, min(1.0, quality_match))

    def _generate_reason(
        self,
        model: ModelSpec,
        complexity: float,
        target_tier: RouteTier,
    ) -> str:
        """Generate human-readable routing reason.

        Args:
            model: The selected model.
            complexity: Prompt complexity score.
            target_tier: The requested tier.

        Returns:
            Human-readable explanation string.
        """
        if model.tier != target_tier:
            return (
                f"Selected {model.name} from {model.tier.value} tier "
                f"(requested {target_tier.value}) as best available match "
                f"for complexity={complexity:.2f}"
            )
        return (
            f"Selected {model.name} from {model.tier.value} tier "
            f"for complexity={complexity:.2f}"
        )


class NoSuitableModelError(Exception):
    """Raised when no model matches the routing constraints."""

    pass

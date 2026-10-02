"""Multi-Armed Bandit Optimizer Agent — Adaptive campaign optimization using bandit algorithms."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

import structlog

from campaign_agents.models.optimization import (
    BanditAlgorithm,
    BanditConfig,
    BanditResult,
    BanditState,
    OptimizationRecommendation,
    OptimizationResult,
    OptimizationStrategy,
)

logger = structlog.get_logger(__name__)


@dataclass
class _ArmState:
    """Internal state tracking for a single bandit arm."""

    arm_id: str
    pulls: int = 0
    total_reward: float = 0.0
    rewards: list[float] = field(default_factory=list)

    @property
    def mean_reward(self) -> float:
        """Calculate mean reward for this arm."""
        if self.pulls == 0:
            return 0.0
        return self.total_reward / self.pulls

    def update(self, reward: float) -> None:
        """Update arm state with a new reward observation."""
        self.pulls += 1
        self.total_reward += reward
        self.rewards.append(reward)

    def ucb_score(self, total_pulls: int, exploration_factor: float) -> float:
        """Calculate UCB1 score for this arm."""
        if self.pulls == 0:
            return float("inf")
        exploitation = self.mean_reward
        exploration = exploration_factor * math.sqrt(math.log(total_pulls) / self.pulls)
        return exploitation + exploration

    def thompson_sample(self) -> float:
        """Draw a sample from Beta distribution (Thompson Sampling)."""
        successes = sum(1 for r in self.rewards if r > 0)
        failures = self.pulls - successes
        return random.betavariate(successes + 1, failures + 1)

    def softmax_score(self, temperature: float) -> float:
        """Calculate softmax probability for this arm."""
        if self.pulls == 0:
            return 1.0
        return math.exp(self.mean_reward / temperature)


class MultiArmedBanditOptimizer:
    """Multi-armed bandit optimizer for adaptive campaign optimization.

    Supports multiple bandit algorithms (epsilon-greedy, UCB1, Thompson Sampling,
    Softmax) for balancing exploration and exploitation in campaign optimization.
    """

    def __init__(self, config: BanditConfig) -> None:
        """Initialize the bandit optimizer.

        Args:
            config: Bandit configuration including algorithm choice and arm definitions.

        Raises:
            ValueError: If config is invalid.
        """
        self._validate_config(config)
        self.config = config
        self._arms: dict[str, _ArmState] = {}
        self._total_pulls = 0
        self._total_reward = 0.0
        self._history: list[BanditResult] = []

        for arm in config.arms:
            self._arms[arm.arm_id] = _ArmState(
                arm_id=arm.arm_id,
                pulls=arm.initial_pulls,
                total_reward=arm.initial_reward,
            )
            self._total_pulls += arm.initial_pulls
            self._total_reward += arm.initial_reward

        logger.info(
            "Bandit optimizer initialized",
            algorithm=config.algorithm.value,
            num_arms=len(config.arms),
        )

    def _validate_config(self, config: BanditConfig) -> None:
        """Validate bandit configuration.

        Args:
            config: Configuration to validate.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not config.arms:
            raise ValueError("At least one arm must be configured")
        arm_ids = [a.arm_id for a in config.arms]
        if len(arm_ids) != len(set(arm_ids)):
            raise ValueError("Arm IDs must be unique")
        if config.algorithm == BanditAlgorithm.EPSILON_GREEDY and not (0 <= config.epsilon <= 1):
            raise ValueError("Epsilon must be between 0 and 1")

    def select_arm(self) -> tuple[str, bool]:
        """Select an arm using the configured algorithm.

        Returns:
            Tuple of (selected_arm_id, is_exploration).
        """
        if self.config.algorithm == BanditAlgorithm.EPSILON_GREEDY:
            return self._epsilon_greedy_select()
        elif self.config.algorithm == BanditAlgorithm.UCB1:
            return self._ucb1_select()
        elif self.config.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
            return self._thompson_select()
        elif self.config.algorithm == BanditAlgorithm.SOFTMAX:
            return self._softmax_select()
        else:
            raise ValueError(f"Unknown algorithm: {self.config.algorithm}")

    def _epsilon_greedy_select(self) -> tuple[str, bool]:
        """Epsilon-greedy arm selection."""
        if random.random() < self.config.epsilon:
            arm_id = random.choice(list(self._arms.keys()))
            return arm_id, True
        best_arm = None
        best_reward = -float("inf")
        for arm in self._arms.values():
            if arm.mean_reward > best_reward:
                best_reward = arm.mean_reward
                best_arm = arm
        if best_arm is None:
            raise RuntimeError("No arms available for selection")
        return best_arm.arm_id, False

    def _ucb1_select(self) -> tuple[str, bool]:
        """UCB1 arm selection."""
        best_arm_id = ""
        best_score = -float("inf")
        is_exploration = False

        for arm_id, state in self._arms.items():
            score = state.ucb_score(self._total_pulls, self.config.exploration_factor)
            if score == float("inf"):
                is_exploration = True
            if score > best_score:
                best_score = score
                best_arm_id = arm_id

        return best_arm_id, is_exploration

    def _thompson_select(self) -> tuple[str, bool]:
        """Thompson Sampling arm selection."""
        samples = {aid: state.thompson_sample() for aid, state in self._arms.items()}
        best_arm_id = max(samples, key=samples.get)
        is_exploration = self._arms[best_arm_id].pulls < self.config.min_pulls_before_exploit
        return best_arm_id, is_exploration

    def _softmax_select(self) -> tuple[str, bool]:
        """Softmax arm selection."""
        scores = {
            aid: state.softmax_score(self.config.temperature)
            for aid, state in self._arms.items()
        }
        total = sum(scores.values())
        probabilities = {aid: s / total for aid, s in scores.items()}
        arm_id = random.choices(list(probabilities.keys()), weights=list(probabilities.values()))[0]
        is_exploration = self._arms[arm_id].pulls < self.config.min_pulls_before_exploit
        return arm_id, is_exploration

    def update_reward(self, arm_id: str, reward: float) -> None:
        """Update the reward for a specific arm.

        Args:
            arm_id: The arm that was pulled.
            reward: The observed reward value.

        Raises:
            ValueError: If arm_id is not found.
        """
        if arm_id not in self._arms:
            raise ValueError(f"Unknown arm: {arm_id}")
        self._arms[arm_id].update(reward)
        self._total_pulls += 1
        self._total_reward += reward

    def get_state(self) -> list[BanditState]:
        """Get current state of all arms.

        Returns:
            List of BanditState objects for all arms.
        """
        states = []
        for arm_id, state in self._arms.items():
            ucb = state.ucb_score(self._total_pulls, self.config.exploration_factor)
            confidence = min(1.0, state.pulls / max(1, self.config.min_pulls_before_exploit))
            states.append(
                BanditState(
                    arm_id=arm_id,
                    pulls=state.pulls,
                    total_reward=state.total_reward,
                    mean_reward=state.mean_reward,
                    ucb_score=ucb,
                    confidence=confidence,
                )
            )
        return states

    def run_optimization_round(self) -> BanditResult:
        """Run a single optimization round.

        Returns:
            BanditResult with selected arm and current state.
        """
        selected_arm, is_exploration = self.select_arm()
        result = BanditResult(
            selected_arm=selected_arm,
            exploration=is_exploration,
            arm_states=self.get_state(),
            total_pulls=self._total_pulls,
            total_reward=self._total_reward,
        )
        self._history.append(result)
        return result

    def optimize(
        self,
        campaign_id: str,
        reward_callback: Any = None,
    ) -> OptimizationResult:
        """Run a complete optimization cycle.

        Args:
            campaign_id: Campaign identifier.
            reward_callback: Optional callback to compute rewards after arm selection.

        Returns:
            OptimizationResult with recommendations.
        """
        bandit_result = self.run_optimization_round()
        recommendations = self._generate_recommendations(bandit_result)

        result = OptimizationResult(
            campaign_id=campaign_id,
            strategy=OptimizationStrategy.MULTI_ARMED_BANDIT,
            recommendations=recommendations,
            bandit_result=bandit_result,
        )

        logger.info(
            "Optimization round completed",
            campaign_id=campaign_id,
            selected_arm=bandit_result.selected_arm,
            exploration=bandit_result.exploration,
        )
        return result

    def _generate_recommendations(
        self, bandit_result: BanditResult
    ) -> list[OptimizationRecommendation]:
        """Generate optimization recommendations from bandit state.

        Args:
            bandit_result: Current bandit result.

        Returns:
            List of optimization recommendations.
        """
        recommendations = []
        for state in bandit_result.arm_states:
            if state.confidence < 0.5:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"explore_{state.arm_id}",
                        category="exploration",
                        action="increase_traffic",
                        target=state.arm_id,
                        expected_improvement=0.0,
                        confidence=state.confidence,
                        reasoning=(
                            f"Arm {state.arm_id} needs more exploration "
                            f"(confidence: {state.confidence:.2f})"
                        ),
                        priority=7,
                    )
                )
            elif state.mean_reward > 0:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=f"exploit_{state.arm_id}",
                        category="exploitation",
                        action="allocate_budget",
                        target=state.arm_id,
                        current_value=state.mean_reward,
                        recommended_value=state.mean_reward * 1.1,
                        expected_improvement=state.mean_reward * 0.1,
                        confidence=state.confidence,
                        reasoning=(
                            f"Arm {state.arm_id} performing well "
                            f"(mean reward: {state.mean_reward:.4f})"
                        ),
                        priority=3,
                    )
                )
        return recommendations

    def get_history(self) -> list[BanditResult]:
        """Get optimization history.

        Returns:
            List of all BanditResult objects from previous rounds.
        """
        return list(self._history)

    def reset(self) -> None:
        """Reset optimizer state."""
        self._arms.clear()
        self._total_pulls = 0
        self._total_reward = 0.0
        self._history.clear()
        for arm in self.config.arms:
            self._arms[arm.arm_id] = _ArmState(
                arm_id=arm.arm_id,
                pulls=arm.initial_pulls,
                total_reward=arm.initial_reward,
            )
            self._total_pulls += arm.initial_pulls
            self._total_reward += arm.initial_reward
        logger.info("Bandit optimizer reset")

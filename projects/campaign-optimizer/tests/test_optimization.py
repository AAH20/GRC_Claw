"""Tests for multi-armed bandit optimization agent."""
from __future__ import annotations

import pytest

from campaign_agents.agents.optimizer import MultiArmedBanditOptimizer
from campaign_agents.models.optimization import (
    ArmConfig,
    BanditAlgorithm,
    BanditConfig,
    BanditResult,
    BanditState,
    OptimizationRecommendation,
    OptimizationResult,
    OptimizationStrategy,
)


# ─── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def basic_bandit_config() -> BanditConfig:
    """Create a basic bandit configuration for testing."""
    return BanditConfig(
        algorithm=BanditAlgorithm.UCB1,
        arms=[
            ArmConfig(arm_id="arm_a", name="Arm A"),
            ArmConfig(arm_id="arm_b", name="Arm B"),
        ],
        reward_metric="conversion_rate",
    )


@pytest.fixture
def epsilon_greedy_config() -> BanditConfig:
    """Create an epsilon-greedy bandit configuration."""
    return BanditConfig(
        algorithm=BanditAlgorithm.EPSILON_GREEDY,
        epsilon=0.2,
        arms=[
            ArmConfig(arm_id="arm_a", name="Arm A"),
            ArmConfig(arm_id="arm_b", name="Arm B"),
        ],
    )


@pytest.fixture
def thompson_sampling_config() -> BanditConfig:
    """Create a Thompson Sampling bandit configuration."""
    return BanditConfig(
        algorithm=BanditAlgorithm.THOMPSON_SAMPLING,
        arms=[
            ArmConfig(arm_id="arm_a", name="Arm A"),
            ArmConfig(arm_id="arm_b", name="Arm B"),
        ],
    )


@pytest.fixture
def softmax_config() -> BanditConfig:
    """Create a softmax bandit configuration."""
    return BanditConfig(
        algorithm=BanditAlgorithm.SOFTMAX,
        temperature=1.0,
        arms=[
            ArmConfig(arm_id="arm_a", name="Arm A"),
            ArmConfig(arm_id="arm_b", name="Arm B"),
        ],
    )


# ─── Initialization Tests ───────────────────────────────────────────


class TestBanditOptimizerInit:
    """Tests for bandit optimizer initialization."""

    def test_init_with_ucb1(self, basic_bandit_config: BanditConfig) -> None:
        """Test initialization with UCB1 algorithm."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        assert optimizer.config.algorithm == BanditAlgorithm.UCB1
        assert len(optimizer._arms) == 2
        assert optimizer._total_pulls == 0

    def test_init_with_epsilon_greedy(self, epsilon_greedy_config: BanditConfig) -> None:
        """Test initialization with epsilon-greedy algorithm."""
        optimizer = MultiArmedBanditOptimizer(epsilon_greedy_config)
        assert optimizer.config.algorithm == BanditAlgorithm.EPSILON_GREEDY
        assert optimizer.config.epsilon == 0.2

    def test_init_with_thompson_sampling(self, thompson_sampling_config: BanditConfig) -> None:
        """Test initialization with Thompson Sampling."""
        optimizer = MultiArmedBanditOptimizer(thompson_sampling_config)
        assert optimizer.config.algorithm == BanditAlgorithm.THOMPSON_SAMPLING

    def test_init_with_softmax(self, softmax_config: BanditConfig) -> None:
        """Test initialization with softmax algorithm."""
        optimizer = MultiArmedBanditOptimizer(softmax_config)
        assert optimizer.config.algorithm == BanditAlgorithm.SOFTMAX

    def test_init_empty_arms_raises(self) -> None:
        """Test that empty arms list raises ValueError."""
        with pytest.raises(ValueError, match="At least one arm"):
            MultiArmedBanditOptimizer(
                BanditConfig(
                    algorithm=BanditAlgorithm.UCB1,
                    arms=[],
                )
            )

    def test_init_with_initial_pulls(self) -> None:
        """Test initialization with initial pull counts."""
        config = BanditConfig(
            algorithm=BanditAlgorithm.UCB1,
            arms=[
                ArmConfig(arm_id="arm_a", name="Arm A", initial_pulls=10, initial_reward=5.0),
                ArmConfig(arm_id="arm_b", name="Arm B", initial_pulls=5, initial_reward=2.0),
            ],
        )
        optimizer = MultiArmedBanditOptimizer(config)
        assert optimizer._total_pulls == 15
        assert optimizer._total_reward == 7.0

    def test_init_duplicate_arm_ids_raises(self) -> None:
        """Test that duplicate arm IDs raise ValueError."""
        with pytest.raises(ValueError, match="Arm IDs must be unique"):
            MultiArmedBanditOptimizer(
                BanditConfig(
                    algorithm=BanditAlgorithm.UCB1,
                    arms=[
                        ArmConfig(arm_id="arm_a", name="Arm A"),
                        ArmConfig(arm_id="arm_a", name="Arm A Duplicate"),
                    ],
                )
            )

    def test_init_invalid_epsilon_raises(self) -> None:
        """Test that invalid epsilon value raises ValueError."""
        with pytest.raises(ValueError, match="Epsilon must be between 0 and 1"):
            MultiArmedBanditOptimizer(
                BanditConfig(
                    algorithm=BanditAlgorithm.EPSILON_GREEDY,
                    epsilon=1.5,
                    arms=[
                        ArmConfig(arm_id="arm_a", name="Arm A"),
                        ArmConfig(arm_id="arm_b", name="Arm B"),
                    ],
                )
            )


# ─── Arm Selection Tests ────────────────────────────────────────────


class TestArmSelection:
    """Tests for arm selection algorithms."""

    def test_ucb1_selects_unpulled_arm(self, basic_bandit_config: BanditConfig) -> None:
        """Test that UCB1 selects unpulled arms first."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        arm_id, is_exploration = optimizer.select_arm()
        assert arm_id in ("arm_a", "arm_b")
        assert is_exploration is True

    def test_epsilon_greedy_exploration(self, epsilon_greedy_config: BanditConfig) -> None:
        """Test epsilon-greedy exploration."""
        optimizer = MultiArmedBanditOptimizer(epsilon_greedy_config)
        # With epsilon=0.2, should explore ~20% of the time
        explorations = 0
        for _ in range(100):
            _, is_exploration = optimizer.select_arm()
            if is_exploration:
                explorations += 1
        # Should be roughly 20% (with some variance)
        assert 5 < explorations < 40

    def test_epsilon_greedy_exploitation(self, epsilon_greedy_config: BanditConfig) -> None:
        """Test epsilon-greedy exploitation selects best arm."""
        optimizer = MultiArmedBanditOptimizer(epsilon_greedy_config)
        # Give arm_a better rewards
        for _ in range(20):
            optimizer.update_reward("arm_a", 1.0)
            optimizer.update_reward("arm_b", 0.1)

        # With epsilon=0.2, should exploit ~80% of the time
        arm_a_count = 0
        for _ in range(100):
            arm_id, _ = optimizer.select_arm()
            if arm_id == "arm_a":
                arm_a_count += 1
        # Should select arm_a most of the time
        assert arm_a_count > 50

    def test_thompson_sampling_selects_valid_arm(self, thompson_sampling_config: BanditConfig) -> None:
        """Test Thompson Sampling selects a valid arm."""
        optimizer = MultiArmedBanditOptimizer(thompson_sampling_config)
        arm_id, _ = optimizer.select_arm()
        assert arm_id in ("arm_a", "arm_b")

    def test_softmax_selects_valid_arm(self, softmax_config: BanditConfig) -> None:
        """Test softmax selects a valid arm."""
        optimizer = MultiArmedBanditOptimizer(softmax_config)
        arm_id, _ = optimizer.select_arm()
        assert arm_id in ("arm_a", "arm_b")


# ─── Reward Update Tests ────────────────────────────────────────────


class TestRewardUpdate:
    """Tests for reward updates."""

    def test_update_reward_increments_pulls(self, basic_bandit_config: BanditConfig) -> None:
        """Test that updating reward increments pull count."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        optimizer.update_reward("arm_a", 0.5)
        assert optimizer._arms["arm_a"].pulls == 1
        assert optimizer._arms["arm_a"].total_reward == 0.5

    def test_update_reward_accumulates(self, basic_bandit_config: BanditConfig) -> None:
        """Test that multiple rewards accumulate correctly."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        optimizer.update_reward("arm_a", 0.5)
        optimizer.update_reward("arm_a", 0.7)
        assert optimizer._arms["arm_a"].pulls == 2
        assert optimizer._arms["arm_a"].total_reward == 1.2

    def test_update_reward_invalid_arm_raises(self, basic_bandit_config: BanditConfig) -> None:
        """Test that updating unknown arm raises ValueError."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        with pytest.raises(ValueError, match="Unknown arm"):
            optimizer.update_reward("nonexistent_arm", 0.5)

    def test_mean_reward_calculation(self, basic_bandit_config: BanditConfig) -> None:
        """Test mean reward calculation."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        optimizer.update_reward("arm_a", 0.5)
        optimizer.update_reward("arm_a", 0.7)
        assert optimizer._arms["arm_a"].mean_reward == pytest.approx(0.6)


# ─── State and History Tests ────────────────────────────────────────


class TestStateAndHistory:
    """Tests for state retrieval and history."""

    def test_get_state_returns_all_arms(self, basic_bandit_config: BanditConfig) -> None:
        """Test that get_state returns all arms."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        states = optimizer.get_state()
        assert len(states) == 2
        assert all(isinstance(s, BanditState) for s in states)

    def test_get_state_after_updates(self, basic_bandit_config: BanditConfig) -> None:
        """Test state reflects updates."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        optimizer.update_reward("arm_a", 0.8)
        states = optimizer.get_state()
        arm_a_state = next(s for s in states if s.arm_id == "arm_a")
        assert arm_a_state.pulls == 1
        assert arm_a_state.mean_reward == pytest.approx(0.8)

    def test_optimization_round_returns_result(self, basic_bandit_config: BanditConfig) -> None:
        """Test that optimization round returns a BanditResult."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        result = optimizer.run_optimization_round()
        assert isinstance(result, BanditResult)
        assert result.selected_arm in ("arm_a", "arm_b")
        assert result.total_pulls == 0

    def test_history_tracks_rounds(self, basic_bandit_config: BanditConfig) -> None:
        """Test that history tracks optimization rounds."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        assert len(optimizer.get_history()) == 0
        optimizer.run_optimization_round()
        assert len(optimizer.get_history()) == 1
        optimizer.run_optimization_round()
        assert len(optimizer.get_history()) == 2


# ─── Full Optimization Tests ────────────────────────────────────────


class TestOptimization:
    """Tests for full optimization cycles."""

    def test_optimize_returns_result(self, basic_bandit_config: BanditConfig) -> None:
        """Test that optimize returns an OptimizationResult."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        result = optimizer.optimize("campaign_123")
        assert isinstance(result, OptimizationResult)
        assert result.campaign_id == "campaign_123"
        assert result.strategy == OptimizationStrategy.MULTI_ARMED_BANDIT

    def test_optimize_generates_recommendations(self, basic_bandit_config: BanditConfig) -> None:
        """Test that optimize generates recommendations."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        result = optimizer.optimize("campaign_123")
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0
        assert all(isinstance(r, OptimizationRecommendation) for r in result.recommendations)

    def test_optimize_includes_bandit_result(self, basic_bandit_config: BanditConfig) -> None:
        """Test that optimize includes bandit result."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        result = optimizer.optimize("campaign_123")
        assert result.bandit_result is not None
        assert isinstance(result.bandit_result, BanditResult)


# ─── Reset Tests ────────────────────────────────────────────────────


class TestReset:
    """Tests for optimizer reset."""

    def test_reset_clears_state(self, basic_bandit_config: BanditConfig) -> None:
        """Test that reset clears all state."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        optimizer.update_reward("arm_a", 0.5)
        optimizer.run_optimization_round()
        optimizer.reset()
        assert optimizer._total_pulls == 0
        assert optimizer._total_reward == 0.0
        assert len(optimizer.get_history()) == 0
        assert optimizer._arms["arm_a"].pulls == 0


# ─── Edge Cases ─────────────────────────────────────────────────────


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_pull_mean_reward(self, basic_bandit_config: BanditConfig) -> None:
        """Test mean reward with single pull."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        optimizer.update_reward("arm_a", 0.75)
        assert optimizer._arms["arm_a"].mean_reward == pytest.approx(0.75)

    def test_zero_reward_updates(self, basic_bandit_config: BanditConfig) -> None:
        """Test that zero rewards are handled correctly."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        optimizer.update_reward("arm_a", 0.0)
        assert optimizer._arms["arm_a"].pulls == 1
        assert optimizer._arms["arm_a"].mean_reward == 0.0

    def test_large_number_of_pulls(self, basic_bandit_config: BanditConfig) -> None:
        """Test optimizer with many pulls."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        for _ in range(1000):
            optimizer.update_reward("arm_a", 0.5)
        assert optimizer._arms["arm_a"].pulls == 1000
        assert optimizer._arms["arm_a"].mean_reward == pytest.approx(0.5)

    def test_ucb_score_unpulled_arm(self, basic_bandit_config: BanditConfig) -> None:
        """Test UCB score for unpulled arm is infinity."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        state = optimizer._arms["arm_a"]
        assert state.ucb_score(0, 1.414) == float("inf")

    def test_confidence_calculation(self, basic_bandit_config: BanditConfig) -> None:
        """Test confidence calculation."""
        optimizer = MultiArmedBanditOptimizer(basic_bandit_config)
        optimizer.update_reward("arm_a", 0.5)
        states = optimizer.get_state()
        arm_a_state = next(s for s in states if s.arm_id == "arm_a")
        assert 0.0 <= arm_a_state.confidence <= 1.0

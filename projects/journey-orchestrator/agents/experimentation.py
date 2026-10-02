"""Experimentation Agent — designs and manages A/B tests and experiments."""

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentResult, BaseAgent
from core.logging import get_logger

logger = get_logger(__name__)


class ExperimentVariant(BaseModel):
    """A single experiment variant."""

    name: str = Field(..., description="Variant name (e.g., 'control', 'treatment_a')")
    description: str = Field(..., description="What this variant tests")
    config: dict[str, Any] = Field(default_factory=dict, description="Variant configuration")
    traffic_allocation: float = Field(default=0.5, description="Traffic allocation (0-1)")


class ExperimentDesign(BaseModel):
    """A complete experiment design."""

    name: str = Field(..., description="Experiment name")
    hypothesis: str = Field(..., description="Experiment hypothesis")
    experiment_type: str = Field(default="ab_test", description="Type: ab_test, multi_armed_bandit, etc.")
    variants: list[ExperimentVariant] = Field(..., description="Experiment variants")
    primary_metric: str = Field(..., description="Primary success metric")
    secondary_metrics: list[str] = Field(default_factory=list, description="Secondary metrics")
    minimum_sample_size: int = Field(default=1000, description="Minimum sample size per variant")
    confidence_level: float = Field(default=0.95, description="Statistical confidence level")
    max_duration_days: int = Field(default=14, description="Maximum experiment duration")
    success_criteria: str = Field(default="", description="Criteria for declaring a winner")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExperimentResult(BaseModel):
    """Results of a completed experiment."""

    experiment_id: str = Field(..., description="Experiment identifier")
    status: str = Field(..., description="Status: running, completed, stopped")
    winner: str = Field(default="", description="Winning variant name")
    confidence: float = Field(default=0.0, description="Statistical confidence")
    sample_size: int = Field(default=0, description="Total sample size")
    metrics: dict[str, float] = Field(default_factory=dict, description="Metric values per variant")
    recommendation: str = Field(default="", description="Recommended action")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExperimentationAgent(BaseAgent[ExperimentDesign]):
    """Agent that designs A/B tests, manages experiment lifecycle, and analyzes results.

    Creates statistically sound experiment designs, monitors running experiments,
    and provides actionable recommendations based on results.
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        """Initialize the Experimentation agent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
        """
        if config is None:
            config = AgentConfig(
                name="experimentation",
                temperature=0.5,
                system_prompt=(
                    "You are an expert experimentation designer. You create rigorous "
                    "A/B tests and multi-armed bandit experiments with proper sample "
                    "sizes, confidence levels, and success criteria. You analyze "
                    "results and provide clear, actionable recommendations."
                ),
            )
        super().__init__(config)
        self._parser = PydanticOutputParser(pydantic_object=ExperimentDesign)

    async def run(self, input_data: dict[str, Any]) -> AgentResult[ExperimentDesign]:
        """Design an experiment from the given input.

        Args:
            input_data: Must contain:
                - hypothesis: The hypothesis to test
                - Optional: variants, primary_metric, constraints, experiment_type

        Returns:
            AgentResult containing the ExperimentDesign or an error.
        """
        try:
            messages = self._build_messages(input_data)
            messages.append(
                HumanMessage(
                    content=f"\n\n{self._parser.get_format_instructions()}"
                )
            )

            response = await self.llm.ainvoke(messages)
            result = self._parser.parse(response.content)

            logger.info(
                "experiment_designed",
                experiment_name=result.name,
                num_variants=len(result.variants),
                min_sample_size=result.minimum_sample_size,
            )

            return AgentResult(
                success=True,
                data=result,
                agent_name=self.config.name,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
            )

        except Exception as e:
            logger.error("experiment_design_failed", error=str(e))
            return AgentResult(
                success=False,
                error=f"Failed to design experiment: {e}",
                agent_name=self.config.name,
            )

    async def analyze_results(
        self, experiment_id: str, results_data: dict[str, Any]
    ) -> AgentResult[ExperimentResult]:
        """Analyze experiment results and provide recommendations.

        Args:
            experiment_id: The experiment identifier.
            results_data: Raw experiment results data.

        Returns:
            AgentResult containing the ExperimentResult or an error.
        """
        try:
            input_data = {
                "experiment_id": experiment_id,
                "task": "analyze_results",
                **results_data,
            }
            messages = self._build_messages(input_data)

            response = await self.llm.ainvoke(messages)
            # Parse the response as ExperimentResult
            result = ExperimentResult.model_validate_json(response.content)

            logger.info(
                "experiment_analyzed",
                experiment_id=experiment_id,
                winner=result.winner,
                confidence=result.confidence,
            )

            return AgentResult(
                success=True,
                data=result,
                agent_name=self.config.name,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
            )

        except Exception as e:
            logger.error("experiment_analysis_failed", experiment_id=experiment_id, error=str(e))
            return AgentResult(
                success=False,
                error=f"Failed to analyze experiment results: {e}",
                agent_name=self.config.name,
            )

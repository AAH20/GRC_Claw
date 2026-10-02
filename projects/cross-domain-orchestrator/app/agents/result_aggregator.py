"""Result Aggregator Agent.

Aggregates results from multiple workflow steps, providing unified
views, summaries, and cross-step data correlation.
"""

from __future__ import annotations

import logging
from typing import Any

from app.models.workflow import WorkflowResult, WorkflowStepResult

logger = logging.getLogger(__name__)


class ResultAggregatorAgent:
    """Agent responsible for aggregating workflow execution results.

    Provides methods to combine, summarize, and correlate results
    from multiple workflow steps and executions.

    Attributes:
        aggregation_strategies: Available aggregation strategies.
    """

    def __init__(self) -> None:
        """Initialize the Result Aggregator Agent."""
        self.aggregation_strategies: dict[str, Any] = {
            "merge": self._merge_outputs,
            "concat": self._concat_outputs,
            "summary": self._summarize_outputs,
        }

    def aggregate(
        self,
        step_results: list[WorkflowStepResult],
        strategy: str = "merge",
    ) -> dict[str, Any]:
        """Aggregate step results using the specified strategy.

        Args:
            step_results: List of step results to aggregate.
            strategy: Aggregation strategy to use.

        Returns:
            Aggregated result data.

        Raises:
            ValueError: If the strategy is not supported.
        """
        if strategy not in self.aggregation_strategies:
            raise ValueError(
                f"Unsupported aggregation strategy: {strategy}. "
                f"Available: {list(self.aggregation_strategies.keys())}",
            )

        logger.info(
            "Aggregating %d step results using strategy: %s",
            len(step_results),
            strategy,
        )

        return self.aggregation_strategies[strategy](step_results)

    def _merge_outputs(self, step_results: list[WorkflowStepResult]) -> dict[str, Any]:
        """Merge all step outputs into a single dictionary.

        Args:
            step_results: Step results to merge.

        Returns:
            Merged output dictionary.
        """
        merged: dict[str, Any] = {}
        for result in step_results:
            if result.success:
                merged.update(result.output)
        return merged

    def _concat_outputs(self, step_results: list[WorkflowStepResult]) -> dict[str, Any]:
        """Concatenate step outputs into lists.

        Args:
            step_results: Step results to concatenate.

        Returns:
            Dictionary with concatenated values.
        """
        concatenated: dict[str, list[Any]] = {}
        for result in step_results:
            if result.success:
                for key, value in result.output.items():
                    if key not in concatenated:
                        concatenated[key] = []
                    concatenated[key].append(value)
        return concatenated

    def _summarize_outputs(self, step_results: list[WorkflowStepResult]) -> dict[str, Any]:
        """Create a summary of step outputs.

        Args:
            step_results: Step results to summarize.

        Returns:
            Summary dictionary.
        """
        successful = [r for r in step_results if r.success]
        failed = [r for r in step_results if not r.success]

        return {
            "total_steps": len(step_results),
            "successful_steps": len(successful),
            "failed_steps": len(failed),
            "success_rate": len(successful) / len(step_results) if step_results else 0.0,
            "failed_step_ids": [r.step_id for r in failed],
            "total_duration_ms": sum(
                (r.completed_at - r.started_at).total_seconds() * 1000
                for r in step_results
            ),
        }

    def create_workflow_summary(self, result: WorkflowResult) -> dict[str, Any]:
        """Create a comprehensive summary of a workflow execution.

        Args:
            result: Workflow execution result.

        Returns:
            Summary dictionary with key metrics.
        """
        successful_steps = [r for r in result.step_results if r.success]
        failed_steps = [r for r in result.step_results if not r.success]

        return {
            "workflow_id": result.workflow_id,
            "success": result.success,
            "total_steps": len(result.step_results),
            "successful_steps": len(successful_steps),
            "failed_steps": len(failed_steps),
            "success_rate": (
                len(successful_steps) / len(result.step_results)
                if result.step_results
                else 0.0
            ),
            "total_duration_ms": result.total_duration_ms,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
        }

    def correlate_results(
        self,
        results: list[WorkflowResult],
    ) -> dict[str, Any]:
        """Correlate results across multiple workflow executions.

        Args:
            results: List of workflow results to correlate.

        Returns:
            Correlation analysis dictionary.
        """
        if not results:
            return {"message": "No results to correlate"}

        total_executions = len(results)
        successful_executions = sum(1 for r in results if r.success)
        total_steps = sum(len(r.step_results) for r in results)
        total_duration = sum(r.total_duration_ms for r in results)

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": total_executions - successful_executions,
            "success_rate": successful_executions / total_executions,
            "total_steps_executed": total_steps,
            "average_duration_ms": total_duration / total_executions,
            "total_duration_ms": total_duration,
        }

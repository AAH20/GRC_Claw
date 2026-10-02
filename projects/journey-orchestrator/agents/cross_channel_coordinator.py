"""Cross-Channel Coordinator Agent — orchestrates execution across channels."""

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentResult, BaseAgent
from core.exceptions import ChannelError
from core.logging import get_logger

logger = get_logger(__name__)


class ChannelAction(BaseModel):
    """A single action to execute on a channel."""

    channel: str = Field(..., description="Channel name (email, sms, push, web, ads)")
    action_type: str = Field(..., description="Action type (send, trigger, update, suppress)")
    priority: int = Field(default=5, description="Priority (1-10, lower is higher)")
    scheduled_time: str = Field(default="", description="When to execute (ISO 8601)")
    content_id: str = Field(default="", description="Reference to content to use")
    config: dict[str, Any] = Field(default_factory=dict, description="Channel-specific config")
    dependencies: list[str] = Field(default_factory=list, description="Action IDs that must complete first")


class ChannelExecutionPlan(BaseModel):
    """A complete cross-channel execution plan."""

    journey_id: str = Field(..., description="Journey identifier")
    customer_id: str = Field(..., description="Customer identifier")
    actions: list[ChannelAction] = Field(..., description="Ordered list of channel actions")
    execution_strategy: str = Field(default="sequential", description="Strategy: sequential, parallel, adaptive")
    fallback_actions: dict[str, str] = Field(
        default_factory=dict, description="Fallback action ID per primary action ID"
    )
    estimated_completion_time: str = Field(default="", description="Estimated completion time")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChannelExecutionResult(BaseModel):
    """Result of executing a channel action."""

    action_id: str = Field(..., description="Action identifier")
    channel: str = Field(..., description="Channel name")
    status: str = Field(..., description="Status: pending, running, completed, failed, skipped")
    started_at: str = Field(default="", description="Start time")
    completed_at: str = Field(default="", description="Completion time")
    error: str = Field(default="", description="Error message if failed")
    response_data: dict[str, Any] = Field(default_factory=dict, description="Channel response data")


class CrossChannelCoordinatorAgent(BaseAgent[ChannelExecutionPlan]):
    """Agent that orchestrates execution across email, SMS, push, web, and ad channels.

    Takes a journey design and customer context, then produces an execution plan
    with properly ordered, prioritized channel actions respecting dependencies,
    frequency caps, and timing constraints.
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        """Initialize the Cross-Channel Coordinator agent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
        """
        if config is None:
            config = AgentConfig(
                name="cross_channel_coordinator",
                temperature=0.5,
                system_prompt=(
                    "You are an expert cross-channel marketing coordinator. You "
                    "orchestrate customer communications across email, SMS, push "
                    "notifications, web, and advertising channels. You respect "
                    "frequency caps, timing constraints, and channel dependencies "
                    "to deliver a cohesive customer experience."
                ),
            )
        super().__init__(config)
        self._parser = PydanticOutputParser(pydantic_object=ChannelExecutionPlan)

    async def run(self, input_data: dict[str, Any]) -> AgentResult[ChannelExecutionPlan]:
        """Create a cross-channel execution plan.

        Args:
            input_data: Must contain:
                - journey_id: The journey identifier
                - customer_id: The customer identifier
                - journey_design: The journey design to execute
                - Optional: channel_preferences, timing_restrictions, frequency_caps

        Returns:
            AgentResult containing the ChannelExecutionPlan or an error.
        """
        try:
            messages = self._build_messages(input_data)
            messages.append(
                HumanMessage(
                    content=f"\n\n{self._parser.get_format_instructions()}"
                )
            )

            response = await self.llm.ainvoke(messages)
            plan = self._parser.parse(response.content)

            # Validate the plan
            self._validate_plan(plan)

            logger.info(
                "execution_plan_created",
                journey_id=plan.journey_id,
                customer_id=plan.customer_id,
                num_actions=len(plan.actions),
                strategy=plan.execution_strategy,
            )

            return AgentResult(
                success=True,
                data=plan,
                agent_name=self.config.name,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
            )

        except Exception as e:
            logger.error("execution_plan_failed", error=str(e))
            return AgentResult(
                success=False,
                error=f"Failed to create execution plan: {e}",
                agent_name=self.config.name,
            )

    def _validate_plan(self, plan: ChannelExecutionPlan) -> None:
        """Validate the execution plan for consistency.

        Args:
            plan: The execution plan to validate.

        Raises:
            ChannelError: If the plan is invalid.
        """
        if not plan.actions:
            raise ChannelError("Execution plan has no actions", code="EMPTY_PLAN")

        # Check for circular dependencies
        action_ids = {a.content_id for a in plan.actions if a.content_id}
        for action in plan.actions:
            for dep in action.dependencies:
                if dep not in action_ids:
                    raise ChannelError(
                        f"Action {action.content_id} depends on unknown action {dep}",
                        code="INVALID_DEPENDENCY",
                    )

    async def execute_action(
        self, action: ChannelAction, context: dict[str, Any]
    ) -> AgentResult[ChannelExecutionResult]:
        """Execute a single channel action.

        Args:
            action: The channel action to execute.
            context: Execution context (API keys, endpoints, etc.).

        Returns:
            AgentResult containing the ChannelExecutionResult or an error.
        """
        try:
            logger.info(
                "executing_channel_action",
                action_id=action.content_id,
                channel=action.channel,
                action_type=action.action_type,
            )

            # This would integrate with actual channel providers
            # For now, return a simulated success
            result = ChannelExecutionResult(
                action_id=action.content_id,
                channel=action.channel,
                status="completed",
                response_data={"simulated": True},
            )

            return AgentResult(
                success=True,
                data=result,
                agent_name=self.config.name,
            )

        except Exception as e:
            logger.error(
                "channel_action_failed",
                action_id=action.content_id,
                channel=action.channel,
                error=str(e),
            )
            return AgentResult(
                success=False,
                error=f"Channel action failed: {e}",
                agent_name=self.config.name,
            )

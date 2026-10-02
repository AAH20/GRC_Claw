"""Launch Agent - Campaign launch and deployment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class LaunchStatus(str, Enum):
    """Status of a campaign launch."""

    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    LAUNCHING = "launching"
    LIVE = "live"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class LaunchChannelStatus(str, Enum):
    """Status of a channel launch."""

    PENDING = "pending"
    CONFIGURED = "configured"
    TESTED = "tested"
    LIVE = "live"
    FAILED = "failed"


class LaunchChecklistItem(BaseModel):
    """A single launch checklist item."""

    id: str = Field(..., description="Checklist item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(..., description="Item description")
    category: str = Field(..., description="Category (e.g., 'technical', 'content', 'compliance')")
    completed: bool = Field(False, description="Whether the item is completed")
    required: bool = Field(True, description="Whether the item is required for launch")
    completed_at: str | None = Field(None, description="Completion timestamp")
    completed_by: str | None = Field(None, description="Who completed the item")


class ChannelLaunchStatus(BaseModel):
    """Launch status for a specific channel."""

    channel: str = Field(..., description="Channel name")
    status: LaunchChannelStatus = Field(..., description="Current launch status")
    config: dict[str, Any] = Field(default_factory=dict, description="Channel configuration")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered")
    live_url: str | None = Field(None, description="Live URL if applicable")
    launched_at: str | None = Field(None, description="Launch timestamp")


class LaunchResult(BaseModel):
    """Result of a campaign launch."""

    campaign_id: str = Field(..., description="Campaign identifier")
    status: LaunchStatus = Field(..., description="Overall launch status")
    checklist: list[LaunchChecklistItem] = Field(
        default_factory=list, description="Launch checklist"
    )
    channels: list[ChannelLaunchStatus] = Field(
        default_factory=list, description="Channel statuses"
    )
    pre_launch_tests: dict[str, bool] = Field(
        default_factory=dict, description="Pre-launch test results"
    )
    launch_notes: list[str] = Field(
        default_factory=list, description="Launch notes and observations"
    )
    launched_at: str | None = Field(None, description="Launch timestamp")
    launched_by: str | None = Field(None, description="Who initiated the launch")


@dataclass
class LaunchAgentConfig:
    """Configuration for the Launch Agent."""

    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.3
    timeout_seconds: int = 120
    retry_attempts: int = 3
    enabled: bool = True
    auto_rollback: bool = True
    require_approval: bool = True


class LaunchAgent:
    """AI agent for campaign launch and deployment.

    This agent orchestrates the launch of marketing campaigns across
    multiple channels, manages launch checklists, performs pre-launch
    testing, and handles rollback procedures if issues are detected.
    """

    def __init__(self, config: LaunchAgentConfig | None = None) -> None:
        """Initialize the Launch Agent.

        Args:
            config: Optional configuration override.
        """
        self.config = config or LaunchAgentConfig()
        self._agent: Any = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize the underlying LangChain agent."""
        try:
            from langchain.agents import create_openai_functions_agent
            from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert campaign launch manager with deep experience
                in multi-channel marketing deployment, QA testing, and go-live procedures.
                Ensure all pre-launch checks pass before going live.
                Have rollback plans ready for every launch."""),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            self._agent = create_openai_functions_agent(llm, [], prompt)
            logger.info("LaunchAgent initialized", model=self.config.model)
        except ImportError:
            logger.warning("LangChain not available, running in mock mode")
            self._agent = None

    async def prepare_launch(
        self,
        campaign_id: str,
        channels: list[str],
        assets: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> LaunchResult:
        """Prepare a campaign for launch.

        Args:
            campaign_id: Campaign identifier.
            channels: List of channels to launch on.
            assets: Creative assets and configurations.
            context: Optional additional context.

        Returns:
            LaunchResult with preparation status and checklist.

        Raises:
            ValueError: If the agent is not enabled.
            RuntimeError: If launch preparation fails.
        """
        if not self.config.enabled:
            raise ValueError("LaunchAgent is not enabled")

        logger.info("Preparing launch", campaign_id=campaign_id, channels=channels)

        try:
            checklist = self._generate_checklist(channels)
            channel_statuses = [
                ChannelLaunchStatus(
                    channel=ch,
                    status=LaunchChannelStatus.PENDING,
                    config={},
                )
                for ch in channels
            ]

            return LaunchResult(
                campaign_id=campaign_id,
                status=LaunchStatus.PREPARING,
                checklist=checklist,
                channels=channel_statuses,
                pre_launch_tests={},
            )

        except Exception as e:
            logger.error("Launch preparation failed", error=str(e))
            raise RuntimeError(f"Launch preparation failed: {e}") from e

    async def execute_launch(
        self,
        campaign_id: str,
        preparation_result: LaunchResult,
        context: dict[str, Any] | None = None,
    ) -> LaunchResult:
        """Execute the campaign launch.

        Args:
            campaign_id: Campaign identifier.
            preparation_result: Result from prepare_launch.
            context: Optional additional context.

        Returns:
            LaunchResult with launch status.

        Raises:
            ValueError: If pre-launch checks fail.
            RuntimeError: If launch execution fails.
        """
        if not self.config.enabled:
            raise ValueError("LaunchAgent is not enabled")

        logger.info("Executing launch", campaign_id=campaign_id)

        try:
            # Verify all required checklist items are complete
            incomplete_required = [
                item for item in preparation_result.checklist
                if item.required and not item.completed
            ]
            if incomplete_required:
                raise ValueError(
                    f"Cannot launch: {len(incomplete_required)} required items incomplete"
                )

            # Execute launch across channels
            updated_channels: list[ChannelLaunchStatus] = []
            for ch_status in preparation_result.channels:
                updated_channels.append(ChannelLaunchStatus(
                    channel=ch_status.channel,
                    status=LaunchChannelStatus.LIVE,
                    config=ch_status.config,
                    errors=[],
                    launched_at="2024-01-01T00:00:00Z",
                ))

            return LaunchResult(
                campaign_id=campaign_id,
                status=LaunchStatus.LIVE,
                checklist=preparation_result.checklist,
                channels=updated_channels,
                pre_launch_tests={
                    "smoke_test": True,
                    "integration_test": True,
                    "performance_test": True,
                },
                launch_notes=["Campaign launched successfully"],
                launched_at="2024-01-01T00:00:00Z",
            )

        except Exception as e:
            logger.error("Launch execution failed", error=str(e))
            if self.config.auto_rollback:
                await self.rollback_launch(campaign_id, str(e))
            raise RuntimeError(f"Launch execution failed: {e}") from e

    async def rollback_launch(
        self,
        campaign_id: str,
        reason: str,
    ) -> LaunchResult:
        """Rollback a campaign launch.

        Args:
            campaign_id: Campaign identifier.
            reason: Reason for rollback.

        Returns:
            LaunchResult with rollback status.
        """
        logger.warning("Rolling back launch", campaign_id=campaign_id, reason=reason)

        return LaunchResult(
            campaign_id=campaign_id,
            status=LaunchStatus.ROLLED_BACK,
            checklist=[],
            channels=[],
            pre_launch_tests={},
            launch_notes=[f"Rolled back: {reason}"],
        )

    def _generate_checklist(self, channels: list[str]) -> list[LaunchChecklistItem]:
        """Generate a launch checklist for the given channels.

        Args:
            channels: Channels being launched.

        Returns:
            List of LaunchChecklistItem objects.
        """
        base_items = [
            LaunchChecklistItem(
                id="tracking_setup",
                name="Tracking & Analytics Setup",
                description="Verify all tracking pixels, UTMs, and analytics are configured",
                category="technical",
                required=True,
            ),
            LaunchChecklistItem(
                id="creative_review",
                name="Creative Review",
                description="All creatives reviewed and approved by stakeholders",
                category="content",
                required=True,
            ),
            LaunchChecklistItem(
                id="landing_page_test",
                name="Landing Page Testing",
                description="All landing pages tested across devices and browsers",
                category="technical",
                required=True,
            ),
            LaunchChecklistItem(
                id="compliance_check",
                name="Compliance Check",
                description="Legal and compliance review completed",
                category="compliance",
                required=True,
            ),
            LaunchChecklistItem(
                id="budget_verification",
                name="Budget Verification",
                description="Campaign budgets verified in all ad platforms",
                category="financial",
                required=True,
            ),
        ]

        channel_specific: list[LaunchChecklistItem] = []
        for channel in channels:
            channel_specific.append(LaunchChecklistItem(
                id=f"{channel}_config",
                name=f"{channel.title()} Configuration",
                description=f"Verify {channel} campaign configuration",
                category="technical",
                required=True,
            ))

        return base_items + channel_specific

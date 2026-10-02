"""Orchestrator agent: coordinates the compliance agent workflow."""

from __future__ import annotations

import asyncio
from typing import Any

from compliance.agents.analytics import AnalyticsAgent
from compliance.agents.base import AgentResult, AgentStatus, BaseAgent
from compliance.agents.detect import DetectAgent
from compliance.agents.monitor import MonitorAgent
from compliance.agents.report import ReportAgent
from compliance.agents.respond import RespondAgent


class OrchestratorAgent(BaseAgent):
    """Coordinates monitor, detect, respond, report and analytics agents.

    The orchestrator runs the pipeline stages sequentially (each stage depends
    on the previous stage's output) while allowing independent agents to be
    executed with bounded concurrency.
    """

    name = "orchestrator"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialise the orchestrator and its child agents.

        Args:
            config: Configuration mapping; per-agent sub-configs are read from
                the ``agents`` key when present.
        """
        super().__init__(config)
        agents_cfg: dict[str, Any] = self.config.get("agents", {})
        self.monitor = MonitorAgent(agents_cfg.get("monitor"))
        self.detect = DetectAgent(agents_cfg.get("detect"))
        self.respond = RespondAgent(agents_cfg.get("respond"))
        self.report = ReportAgent(agents_cfg.get("report"))
        self.analytics = AnalyticsAgent(agents_cfg.get("analytics"))

    async def run(self, payload: dict[str, Any]) -> AgentResult:
        """Execute the full compliance pipeline.

        Args:
            payload: Pipeline input, forwarded to the monitor agent. May also
                carry ``campaigns``, ``sources`` and ``format``.

        Returns:
            An :class:`AgentResult` summarising the whole run.
        """
        monitor_result = await self.monitor.execute(payload)
        if monitor_result.status is AgentStatus.FAILED:
            return self._failed("monitor stage failed", monitor_result.errors)

        detect_result = await self.detect.execute({"items": monitor_result.items})
        if detect_result.status is AgentStatus.FAILED:
            return self._failed("detect stage failed", detect_result.errors)

        violations = detect_result.items

        respond_result, analytics_result = await asyncio.gather(
            self.respond.execute({"violations": violations}),
            self.analytics.execute({"violations": violations}),
        )

        report_result = await self.report.execute(
            {
                "violations": violations,
                "responses": respond_result.items,
                "format": payload.get("format", "json"),
            }
        )

        return AgentResult(
            agent=self.name,
            items=report_result.items,
            metrics={
                "items_collected": float(len(monitor_result.items)),
                "violations_detected": float(len(violations)),
                "responses_generated": float(len(respond_result.items)),
                "compliance_rate": analytics_result.metrics.get("compliance_rate", 0.0),
            },
            errors=monitor_result.errors + detect_result.errors,
        )

    @staticmethod
    def _failed(message: str, errors: list[str]) -> AgentResult:
        """Build a failed orchestrator result.

        Args:
            message: High-level failure description.
            errors: Underlying error strings.

        Returns:
            A failed :class:`AgentResult`.
        """
        return AgentResult(
            agent="orchestrator",
            status=AgentStatus.FAILED,
            errors=[message, *errors],
        )

"""Reporting agent for business intelligence."""
from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class ReportingAgent:
    """Agent for generating reports."""

    def __init__(self) -> None:
        logger.info("ReportingAgent initialized")

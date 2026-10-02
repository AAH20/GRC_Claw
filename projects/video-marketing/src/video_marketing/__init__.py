"""Video Marketing - Agentic AI video marketing platform.

A production-grade platform with 5 specialized agents for video marketing:
Script Generation, Production, Editing, Distribution, and Analytics.
"""

__version__ = "0.1.0"
__author__ = "Ahmed Hassan"
__email__ = "ahmed@example.com"

from video_marketing.agents import (
    AnalyticsAgent,
    DistributionAgent,
    EditingAgent,
    ProductionAgent,
    ScriptGenerationAgent,
)

__all__ = [
    "AnalyticsAgent",
    "DistributionAgent",
    "EditingAgent",
    "ProductionAgent",
    "ScriptGenerationAgent",
    "__version__",
]

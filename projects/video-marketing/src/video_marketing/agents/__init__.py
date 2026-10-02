"""Video Marketing Agents.

Specialized agents for the video marketing pipeline:
- ScriptGenerationAgent: Creates video scripts from topics/briefs
- ProductionAgent: Manages video production workflows
- EditingAgent: Handles video editing and post-processing
- DistributionAgent: Distributes videos across platforms
- AnalyticsAgent: Tracks and analyzes video performance
"""

from video_marketing.agents.analytics import AnalyticsAgent
from video_marketing.agents.distribution import DistributionAgent
from video_marketing.agents.editing import EditingAgent
from video_marketing.agents.production import ProductionAgent
from video_marketing.agents.script_generation import ScriptGenerationAgent

__all__ = [
    "AnalyticsAgent",
    "DistributionAgent",
    "EditingAgent",
    "ProductionAgent",
    "ScriptGenerationAgent",
]

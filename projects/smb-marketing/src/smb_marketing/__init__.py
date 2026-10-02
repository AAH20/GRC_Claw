"""SMB Marketing — Agentic AI marketing platform for small businesses."""

__version__ = "0.1.0"
__author__ = "Ahmed Hassan"
__email__ = "ahmed@example.com"

from smb_marketing.agents.analytics import AnalyticsAgent
from smb_marketing.agents.campaigns import CampaignsAgent
from smb_marketing.agents.content import ContentAgent
from smb_marketing.agents.email import EmailAgent
from smb_marketing.agents.social import SocialAgent

__all__ = [
    "AnalyticsAgent",
    "CampaignsAgent",
    "ContentAgent",
    "EmailAgent",
    "SocialAgent",
    "__version__",
]

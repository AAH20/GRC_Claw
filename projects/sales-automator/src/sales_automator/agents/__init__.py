"""Agent implementations for Sales Automator."""

from sales_automator.agents.demo_scheduling import DemoSchedulingAgent
from sales_automator.agents.followup import FollowUpAgent
from sales_automator.agents.outreach import OutreachAgent
from sales_automator.agents.prospecting import ProspectingAgent
from sales_automator.agents.qualification import QualificationAgent
from sales_automator.agents.sales_forecasting import SalesForecastingAgent

__all__ = [
    "ProspectingAgent",
    "OutreachAgent",
    "QualificationAgent",
    "DemoSchedulingAgent",
    "FollowUpAgent",
    "SalesForecastingAgent",
]

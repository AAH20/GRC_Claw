"""Integration modules for n8n, Zapier, and Make."""

from workflow_automation.integrations.make import MakeClient, MakeExecution, MakeScenario
from workflow_automation.integrations.n8n import N8nClient, N8nExecution, N8nWorkflow
from workflow_automation.integrations.zapier import ZapierClient, ZapierZap

__all__ = [
    "MakeClient",
    "MakeExecution",
    "MakeScenario",
    "N8nClient",
    "N8nExecution",
    "N8nWorkflow",
    "ZapierClient",
    "ZapierZap",
]

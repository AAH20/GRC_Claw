"""Agent implementations for the Workflow Automation platform."""

from workflow_automation.agents.integration_automation import IntegrationAutomationAgent
from workflow_automation.agents.performance_analytics import PerformanceAnalyticsAgent
from workflow_automation.agents.process_automation import ProcessAutomationAgent
from workflow_automation.agents.workflow_discovery import WorkflowDiscoveryAgent
from workflow_automation.agents.workflow_optimization import WorkflowOptimizationAgent

__all__ = [
    "IntegrationAutomationAgent",
    "PerformanceAnalyticsAgent",
    "ProcessAutomationAgent",
    "WorkflowDiscoveryAgent",
    "WorkflowOptimizationAgent",
]

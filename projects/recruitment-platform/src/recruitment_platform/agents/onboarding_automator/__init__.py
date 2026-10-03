"""Onboarding automator agents."""

from recruitment_platform.agents.onboarding_automator.compliance_checker import ComplianceChecker
from recruitment_platform.agents.onboarding_automator.document_generator import DocumentGenerator
from recruitment_platform.agents.onboarding_automator.progress_tracker import ProgressTracker
from recruitment_platform.agents.onboarding_automator.task_scheduler import TaskScheduler
from recruitment_platform.agents.onboarding_automator.welcome_message import WelcomeMessage

__all__ = [
    "ComplianceChecker",
    "DocumentGenerator",
    "ProgressTracker",
    "TaskScheduler",
    "WelcomeMessage",
]

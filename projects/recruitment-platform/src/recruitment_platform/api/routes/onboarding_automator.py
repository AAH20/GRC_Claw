"""Onboarding automator API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/check-compliance")
async def check_compliance(data: dict[str, Any]) -> dict[str, Any]:
    """Check onboarding compliance.

    Args:
        data: Dictionary with 'employee_data' and 'jurisdiction'.

    Returns:
        Compliance status.
    """
    try:
        from recruitment_platform.agents.onboarding_automator.compliance_checker import \
            ComplianceChecker

        agent = ComplianceChecker()
        result = await agent.process(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/generate-documents")
async def generate_documents(data: dict[str, Any]) -> dict[str, Any]:
    """Generate onboarding documents.

    Args:
        data: Dictionary with 'employee' and 'template_config'.

    Returns:
        Generated documents.
    """
    from recruitment_platform.agents.onboarding_automator.document_generator import \
        DocumentGenerator

    agent = DocumentGenerator()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/track-progress")
async def track_progress(data: dict[str, Any]) -> dict[str, Any]:
    """Track onboarding progress.

    Args:
        data: Dictionary with 'employee_id' and 'onboarding_plan'.

    Returns:
        Progress status.
    """
    from recruitment_platform.agents.onboarding_automator.progress_tracker import \
        ProgressTracker

    agent = ProgressTracker()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/schedule-tasks")
async def schedule_tasks(data: dict[str, Any]) -> dict[str, Any]:
    """Schedule onboarding tasks.

    Args:
        data: Dictionary with 'employee' and 'start_date'.

    Returns:
        Scheduled tasks.
    """
    from recruitment_platform.agents.onboarding_automator.task_scheduler import \
        TaskScheduler

    agent = TaskScheduler()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/welcome-message")
async def generate_welcome(data: dict[str, Any]) -> dict[str, Any]:
    """Generate welcome message.

    Args:
        data: Dictionary with 'employee' and 'team_info'.

    Returns:
        Welcome message content.
    """
    from recruitment_platform.agents.onboarding_automator.welcome_message import \
        WelcomeMessage

    agent = WelcomeMessage()
    result = await agent.process(data)
    return {"success": True, "data": result}

"""Process API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from workflow_automation.agents.process_automation import (
    ProcessAutomationAgent,
    ProcessCreateRequest,
    ProcessExecutionRequest,
)

router = APIRouter()

# Module-level agent
_process_agent: ProcessAutomationAgent | None = None


def _get_process_agent() -> ProcessAutomationAgent:
    global _process_agent
    if _process_agent is None:
        _process_agent = ProcessAutomationAgent()
    return _process_agent


@router.post("", status_code=201)
async def create_process(request: ProcessCreateRequest) -> dict:
    """Create a new automated process."""
    agent = _get_process_agent()
    if not agent._is_initialized:
        await agent.initialize()

    process = await agent.create_process(request)
    return process.model_dump()


@router.get("")
async def list_processes() -> list[dict]:
    """List all processes."""
    agent = _get_process_agent()
    if not agent._is_initialized:
        await agent.initialize()

    processes = await agent.list_processes()
    return [p.model_dump() for p in processes]


@router.get("/{process_id}")
async def get_process(process_id: str) -> dict:
    """Get a specific process by ID."""
    agent = _get_process_agent()
    if not agent._is_initialized:
        await agent.initialize()

    process = await agent.get_process(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return process.model_dump()


@router.post("/{process_id}/execute")
async def execute_process(process_id: str, request: ProcessExecutionRequest) -> dict:
    """Execute a process."""
    agent = _get_process_agent()
    if not agent._is_initialized:
        await agent.initialize()

    request.process_id = process_id
    try:
        execution = await agent.execute_process(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return execution.model_dump()


@router.get("/{process_id}/executions")
async def list_executions(process_id: str) -> list[dict]:
    """List executions for a process."""
    agent = _get_process_agent()
    if not agent._is_initialized:
        await agent.initialize()

    executions = await agent.list_executions(process_id=process_id)
    return [e.model_dump() for e in executions]


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str) -> dict:
    """Cancel a running execution."""
    agent = _get_process_agent()
    if not agent._is_initialized:
        await agent.initialize()

    result = await agent.cancel_execution(execution_id)
    if not result:
        raise HTTPException(status_code=400, detail="Execution not found or not running")
    return {"cancelled": True}

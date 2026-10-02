"""Welcome message endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from onboarding_automator.agents import WelcomeAgent
from onboarding_automator.config.settings import Settings, get_settings
from onboarding_automator.integrations.store import InMemoryStore
from onboarding_automator.models import AgentResponse, WelcomeMessage, WelcomeMessageCreate

__all__ = ["router"]

router = APIRouter()


def get_store(request: Request) -> InMemoryStore:
    """Dependency to get the in-memory store from app state."""
    return request.app.state.store


@router.post("/generate", response_model=AgentResponse)
async def generate_welcome_message(
    message_data: WelcomeMessageCreate,
    request: Request,
    store: InMemoryStore = Depends(get_store),
) -> AgentResponse:
    """Generate a welcome message for a new employee.

    Args:
        message_data: The welcome message configuration.
        request: The incoming request.

    Returns:
        AgentResponse with the generated message.

    Raises:
        HTTPException: If the plan is not found.
    """
    plan = await store.get_plan(message_data.plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding plan {message_data.plan_id} not found",
        )

    tasks = await store.list_tasks(plan_id=message_data.plan_id)
    agent = WelcomeAgent(request.app.state.settings)
    return await agent.execute(message_data, plan, tasks)


@router.post("/send", response_model=AgentResponse)
async def send_welcome_message(
    message_id: UUID,
    recipient_email: str,
    request: Request,
    store: InMemoryStore = Depends(get_store),
) -> AgentResponse:
    """Send a previously generated welcome message.

    Args:
        message_id: The message's unique identifier.
        recipient_email: The recipient's email address.
        request: The incoming request.

    Returns:
        AgentResponse with the send result.

    Raises:
        HTTPException: If the message is not found.
    """
    message = await store.get_welcome_message(message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Welcome message {message_id} not found",
        )

    agent = WelcomeAgent(request.app.state.settings)
    return await agent.send_message(message, recipient_email)


@router.get("/{plan_id}", response_model=list[WelcomeMessage])
async def list_welcome_messages(
    plan_id: UUID,
    store: InMemoryStore = Depends(get_store),
) -> list[WelcomeMessage]:
    """List all welcome messages for a plan.

    Args:
        plan_id: The plan's unique identifier.

    Returns:
        List of welcome messages.
    """
    return await store.list_welcome_messages(plan_id=plan_id)

"""Rights validation API routes."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Request

from rights_management.agents.rights_validator import RightsValidatorAgent
from rights_management.integrations.storage import InMemoryStorage
from rights_management.models import RightsValidation, RightsValidationRequest

router = APIRouter()


def get_storage(request: Request) -> InMemoryStorage:
    """Dependency to retrieve the storage backend from app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The InMemoryStorage instance.
    """
    return request.app.state.storage


def get_agent(request: Request) -> RightsValidatorAgent:
    """Dependency to retrieve the rights validator agent.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The RightsValidatorAgent instance.
    """
    if not hasattr(request.app.state, "rights_validator_agent"):
        request.app.state.rights_validator_agent = RightsValidatorAgent()
    return request.app.state.rights_validator_agent


@router.post("", response_model=RightsValidation, status_code=201)
async def validate_rights(
    payload: RightsValidationRequest,
    storage: InMemoryStorage = Depends(get_storage),
    agent: RightsValidatorAgent = Depends(get_agent),
) -> RightsValidation:
    """Validate content usage against its license.

    Args:
        payload: The validation request.
        storage: The storage backend.
        agent: The rights validator agent.

    Returns:
        The validation result.
    """
    result = await agent.run(payload)
    await storage.save_validation(result)
    return result


@router.get("/{validation_id}", response_model=RightsValidation)
async def get_validation(
    validation_id: str,
    storage: InMemoryStorage = Depends(get_storage),
) -> RightsValidation:
    """Retrieve a specific validation result.

    Args:
        validation_id: The validation identifier.
        storage: The storage backend.

    Returns:
        The requested RightsValidation.

    Raises:
        HTTPException: If the validation is not found.
    """
    result = await storage.get_validation(validation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Validation not found")
    return result


@router.get("/content/{content_id}", response_model=list[RightsValidation])
async def list_validations(
    content_id: str,
    storage: InMemoryStorage = Depends(get_storage),
) -> list[RightsValidation]:
    """List all validation results for a piece of content.

    Args:
        content_id: The content identifier.
        storage: The storage backend.

    Returns:
        List of validation results.
    """
    return await storage.list_validations(content_id=content_id)

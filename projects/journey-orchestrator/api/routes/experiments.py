"""Experiment management API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from api.models import ExperimentCreateRequest, ExperimentResponse, ExperimentResultsResponse
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# In-memory store for demo purposes — replace with database in production
_experiments: dict[str, dict[str, Any]] = {}


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(request: ExperimentCreateRequest) -> ExperimentResponse:
    """Create a new A/B test or experiment.

    Args:
        request: The experiment creation request.

    Returns:
        The created experiment.
    """
    experiment_id = str(uuid.uuid4())

    experiment = {
        "id": experiment_id,
        "name": request.name,
        "hypothesis": request.hypothesis,
        "status": "draft",
        "variants": request.variants,
        "primary_metric": request.primary_metric,
        "created_at": datetime.utcnow(),
    }

    _experiments[experiment_id] = experiment
    logger.info("experiment_created", experiment_id=experiment_id, name=request.name)

    return ExperimentResponse(**experiment)


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str) -> ExperimentResponse:
    """Get an experiment by ID.

    Args:
        experiment_id: The experiment identifier.

    Returns:
        The experiment.

    Raises:
        HTTPException: If the experiment is not found.
    """
    experiment = _experiments.get(experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )
    return ExperimentResponse(**experiment)


@router.get("/{experiment_id}/results", response_model=ExperimentResultsResponse)
async def get_experiment_results(experiment_id: str) -> ExperimentResultsResponse:
    """Get the results of an experiment.

    Args:
        experiment_id: The experiment identifier.

    Returns:
        The experiment results.

    Raises:
        HTTPException: If the experiment is not found.
    """
    experiment = _experiments.get(experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    # In production, this would call the ExperimentationAgent to analyze results
    return ExperimentResultsResponse(
        experiment_id=experiment_id,
        status="running",
        sample_size=0,
        metrics={},
        recommendation="Experiment still in progress",
    )


@router.post("/{experiment_id}/start", response_model=ExperimentResponse)
async def start_experiment(experiment_id: str) -> ExperimentResponse:
    """Start an experiment.

    Args:
        experiment_id: The experiment identifier.

    Returns:
        The updated experiment.

    Raises:
        HTTPException: If the experiment is not found.
    """
    experiment = _experiments.get(experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    experiment["status"] = "running"
    logger.info("experiment_started", experiment_id=experiment_id)

    return ExperimentResponse(**experiment)


@router.post("/{experiment_id}/stop", response_model=ExperimentResponse)
async def stop_experiment(experiment_id: str) -> ExperimentResponse:
    """Stop an experiment.

    Args:
        experiment_id: The experiment identifier.

    Returns:
        The updated experiment.

    Raises:
        HTTPException: If the experiment is not found.
    """
    experiment = _experiments.get(experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    experiment["status"] = "stopped"
    logger.info("experiment_stopped", experiment_id=experiment_id)

    return ExperimentResponse(**experiment)

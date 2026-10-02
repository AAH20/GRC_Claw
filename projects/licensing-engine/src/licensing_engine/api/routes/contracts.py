"""Contract analysis endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from licensing_engine.agents import AgentContext, ContractAnalyzerAgent
from licensing_engine.config.settings import Settings, get_settings
from licensing_engine.models import (
    ContractAnalysis,
    ContractAnalysisCreate,
    ContractAnalysisResponse,
)

router = APIRouter()

# In-memory store for demo purposes
_analyses: dict[UUID, ContractAnalysis] = {}


@router.post(
    "/analyze",
    response_model=ContractAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze a contract",
)
async def analyze_contract(
    data: ContractAnalysisCreate,
    settings: Settings = Depends(get_settings),
) -> ContractAnalysisResponse:
    """Analyze a contract using the ContractAnalyzerAgent.

    Args:
        data: The contract analysis request data.
        settings: Application settings.

    Returns:
        The contract analysis result.
    """
    context = AgentContext(settings=settings)
    agent = ContractAnalyzerAgent(context)
    result = await agent.execute(data.model_dump(mode="json"))

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Failed to analyze contract",
        )

    analysis = ContractAnalysis(
        contract_type=data.contract_type,
        clauses=result.data.get("clauses", []),
        risks=result.data.get("risks", []),
        overall_risk=result.data.get("overall_risk", "low"),
        summary=result.data.get("summary", ""),
        recommendations=result.data.get("recommendations", []),
    )
    _analyses[analysis.id] = analysis
    return ContractAnalysisResponse(
        analysis=analysis, message="Contract analysis completed"
    )


@router.get(
    "/{analysis_id}",
    response_model=ContractAnalysisResponse,
    summary="Get a contract analysis by ID",
)
async def get_analysis(analysis_id: UUID) -> ContractAnalysisResponse:
    """Get a specific contract analysis by its ID.

    Args:
        analysis_id: The analysis ID.

    Returns:
        The requested contract analysis.

    Raises:
        HTTPException: If the analysis is not found.
    """
    analysis = _analyses.get(analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract analysis {analysis_id} not found",
        )
    return ContractAnalysisResponse(analysis=analysis)

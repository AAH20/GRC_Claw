"""Assessment API routes with 10+ endpoints."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from skills_assessor.agents.gap_analyzer import GapAnalyzerAgent
from skills_assessor.agents.learning_path_recommender import LearningPathRecommenderAgent
from skills_assessor.agents.proficiency_scorer import ProficiencyScorerAgent
from skills_assessor.agents.skill_extractor import SkillExtractorAgent
from skills_assessor.agents.skill_validator import SkillValidatorAgent
from skills_assessor.config.settings import Settings, get_settings
from skills_assessor.models.schemas import (
    ExtractionRequest,
    ExtractionResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
    LearningPathRequest,
    LearningPathResponse,
    ScoringRequest,
    ScoringResponse,
    Skill,
    SkillAssessment,
    SkillValidationResult,
)

from uuid import UUID

router = APIRouter(prefix="/assessments", tags=["assessments"])

# In-memory store for demo purposes (replace with database in production)
_assessments: dict[UUID, SkillAssessment] = {}


class CreateAssessmentRequest(BaseModel):
    """Request model for creating an assessment."""

    candidate_id: str = Field(..., min_length=1, max_length=200)
    candidate_name: str | None = Field(default=None, max_length=200)
    target_role: str | None = Field(default=None, max_length=200)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssessmentListResponse(BaseModel):
    """Response model for listing assessments."""

    assessments: list[SkillAssessment]
    total: int


class ValidationRequest(BaseModel):
    """Request model for skill validation."""

    skills: list[Skill] = Field(..., min_length=1)


class ValidationResponse(BaseModel):
    """Response model for skill validation."""

    results: list[SkillValidationResult]
    total_valid: int
    total_invalid: int


def _get_agents(settings: Settings) -> dict[str, Any]:
    """Get or create agent instances.

    Args:
        settings: Application settings.

    Returns:
        dict[str, Any]: Dictionary of agent instances.
    """
    return {
        "extractor": SkillExtractorAgent(),
        "scorer": ProficiencyScorerAgent(),
        "gap_analyzer": GapAnalyzerAgent(),
        "validator": SkillValidatorAgent(),
        "learning_path": LearningPathRecommenderAgent(),
    }


@router.post("", response_model=SkillAssessment, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    request: CreateAssessmentRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SkillAssessment:
    """Create a new skill assessment.

    Args:
        request: Assessment creation request.
        settings: Application settings.

    Returns:
        SkillAssessment: The newly created assessment.
    """
    assessment = SkillAssessment(
        candidate_id=request.candidate_id,
        candidate_name=request.candidate_name,
        target_role=request.target_role,
        status="pending",
        metadata=request.metadata,
    )
    _assessments[assessment.id] = assessment
    return assessment


@router.get("", response_model=AssessmentListResponse)
async def list_assessments(
    skip: int = 0,
    limit: int = 100,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> AssessmentListResponse:
    """List all assessments with pagination.

    Args:
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        settings: Application settings.

    Returns:
        AssessmentListResponse: Paginated list of assessments.
    """
    all_assessments = list(_assessments.values())
    paginated = all_assessments[skip : skip + limit]
    return AssessmentListResponse(assessments=paginated, total=len(all_assessments))


@router.get("/{assessment_id}", response_model=SkillAssessment)
async def get_assessment(
    assessment_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SkillAssessment:
    """Get an assessment by ID.

    Args:
        assessment_id: The assessment UUID.
        settings: Application settings.

    Returns:
        SkillAssessment: The requested assessment.

    Raises:
        HTTPException: If assessment is not found.
    """
    assessment = _assessments.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )
    return assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> None:
    """Delete an assessment by ID.

    Args:
        assessment_id: The assessment UUID.
        settings: Application settings.

    Raises:
        HTTPException: If assessment is not found.
    """
    if assessment_id not in _assessments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )
    del _assessments[assessment_id]


@router.post("/{assessment_id}/extract-skills", response_model=ExtractionResponse)
async def extract_skills(
    assessment_id: UUID,
    request: ExtractionRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ExtractionResponse:
    """Extract skills from text and add to assessment.

    Args:
        assessment_id: The assessment UUID.
        request: Extraction request with text to analyze.
        settings: Application settings.

    Returns:
        ExtractionResponse: Extracted skills with confidence scores.

    Raises:
        HTTPException: If assessment is not found.
    """
    assessment = _assessments.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )

    agents = _get_agents(settings)
    extractor: SkillExtractorAgent = agents["extractor"]

    start = time.perf_counter()
    result = await extractor.run(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Update assessment with extracted skills
    assessment.skills = []
    for skill in result.skills:
        from skills_assessor.models.schemas import ProficiencyLevel, SkillProficiency

        assessment.skills.append(
            SkillProficiency(
                skill=skill,
                level=ProficiencyLevel.BEGINNER,
                confidence=result.confidence,
            )
        )
    assessment.status = "in_progress"
    assessment.updated_at = __import__("datetime").datetime.utcnow()

    return ExtractionResponse(
        skills=result.skills,
        total_found=result.total_found,
        confidence=result.confidence,
        processing_time_ms=elapsed_ms,
    )


@router.post("/{assessment_id}/score", response_model=ScoringResponse)
async def score_proficiency(
    assessment_id: UUID,
    request: ScoringRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ScoringResponse:
    """Score proficiency levels for assessment skills.

    Args:
        assessment_id: The assessment UUID.
        request: Scoring request with skills and context.
        settings: Application settings.

    Returns:
        ScoringResponse: Proficiency scores for each skill.

    Raises:
        HTTPException: If assessment is not found.
    """
    assessment = _assessments.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )

    agents = _get_agents(settings)
    scorer: ProficiencyScorerAgent = agents["scorer"]

    start = time.perf_counter()
    result = await scorer.run(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Update assessment with scored skills
    assessment.skills = result.proficiencies
    assessment.overall_score = result.overall_score
    assessment.status = "in_progress"
    assessment.updated_at = __import__("datetime").datetime.utcnow()

    return ScoringResponse(
        proficiencies=result.proficiencies,
        overall_score=result.overall_score,
        processing_time_ms=elapsed_ms,
    )


@router.post("/{assessment_id}/analyze-gaps", response_model=GapAnalysisResponse)
async def analyze_gaps(
    assessment_id: UUID,
    request: GapAnalysisRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> GapAnalysisResponse:
    """Analyze skill gaps for the assessment.

    Args:
        assessment_id: The assessment UUID.
        request: Gap analysis request.
        settings: Application settings.

    Returns:
        GapAnalysisResponse: Gap analysis report.

    Raises:
        HTTPException: If assessment is not found.
    """
    assessment = _assessments.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )

    agents = _get_agents(settings)
    gap_analyzer: GapAnalyzerAgent = agents["gap_analyzer"]

    start = time.perf_counter()
    result = await gap_analyzer.run(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return GapAnalysisResponse(
        report=result.report,
        processing_time_ms=elapsed_ms,
    )


@router.post("/{assessment_id}/validate", response_model=ValidationResponse)
async def validate_skills(
    assessment_id: UUID,
    request: ValidationRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ValidationResponse:
    """Validate skills in the assessment.

    Args:
        assessment_id: The assessment UUID.
        request: Validation request with skills to validate.
        settings: Application settings.

    Returns:
        ValidationResponse: Validation results for each skill.

    Raises:
        HTTPException: If assessment is not found.
    """
    assessment = _assessments.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )

    agents = _get_agents(settings)
    validator: SkillValidatorAgent = agents["validator"]

    results = await validator.run(request.skills)

    total_valid = sum(1 for r in results if r.is_valid)
    total_invalid = len(results) - total_valid

    return ValidationResponse(
        results=results,
        total_valid=total_valid,
        total_invalid=total_invalid,
    )


@router.post("/{assessment_id}/learning-path", response_model=LearningPathResponse)
async def generate_learning_path(
    assessment_id: UUID,
    request: LearningPathRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> LearningPathResponse:
    """Generate a learning path for the assessment.

    Args:
        assessment_id: The assessment UUID.
        request: Learning path request.
        settings: Application settings.

    Returns:
        LearningPathResponse: Generated learning path.

    Raises:
        HTTPException: If assessment is not found.
    """
    assessment = _assessments.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )

    agents = _get_agents(settings)
    recommender: LearningPathRecommenderAgent = agents["learning_path"]

    start = time.perf_counter()
    result = await recommender.run(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return LearningPathResponse(
        learning_path=result.learning_path,
        processing_time_ms=elapsed_ms,
    )


@router.post("/{assessment_id}/complete", response_model=SkillAssessment)
async def complete_assessment(
    assessment_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SkillAssessment:
    """Mark an assessment as completed.

    Args:
        assessment_id: The assessment UUID.
        settings: Application settings.

    Returns:
        SkillAssessment: The completed assessment.

    Raises:
        HTTPException: If assessment is not found.
    """
    assessment = _assessments.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )

    assessment.status = "completed"
    assessment.completed_at = __import__("datetime").datetime.utcnow()
    assessment.updated_at = __import__("datetime").datetime.utcnow()
    return assessment


@router.get("/{assessment_id}/summary")
async def get_assessment_summary(
    assessment_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict[str, Any]:
    """Get a summary of the assessment.

    Args:
        assessment_id: The assessment UUID.
        settings: Application settings.

    Returns:
        dict[str, Any]: Assessment summary with key metrics.

    Raises:
        HTTPException: If assessment is not found.
    """
    assessment = _assessments.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found",
        )


    level_counts: dict[str, int] = {}
    for prof in assessment.skills:
        level = prof.level.value
        level_counts[level] = level_counts.get(level, 0) + 1

    return {
        "assessment_id": str(assessment.id),
        "candidate_id": assessment.candidate_id,
        "candidate_name": assessment.candidate_name,
        "target_role": assessment.target_role,
        "status": assessment.status,
        "total_skills": len(assessment.skills),
        "overall_score": assessment.overall_score,
        "proficiency_distribution": level_counts,
        "created_at": assessment.created_at.isoformat(),
        "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
    }

"""Assessment service for orchestrating skill assessment workflows."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from skills_assessor.agents.gap_analyzer import GapAnalyzerAgent
from skills_assessor.agents.learning_path_recommender import LearningPathRecommenderAgent
from skills_assessor.agents.proficiency_scorer import ProficiencyScorerAgent
from skills_assessor.agents.skill_extractor import SkillExtractorAgent
from skills_assessor.agents.skill_validator import SkillValidatorAgent
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
    SkillValidationResult,
)

if TYPE_CHECKING:
    from uuid import UUID

    from skills_assessor.config.settings import Settings


class AssessmentService:
    """Service for managing skill assessment workflows.

    Orchestrates the full assessment pipeline: extraction, scoring,
    gap analysis, validation, and learning path generation.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the assessment service.

        Args:
            settings: Application settings.
        """
        self._settings = settings
        self._extractor = SkillExtractorAgent()
        self._scorer = ProficiencyScorerAgent()
        self._gap_analyzer = GapAnalyzerAgent()
        self._validator = SkillValidatorAgent()
        self._learning_path = LearningPathRecommenderAgent()

    async def extract_skills(
        self, text: str, context: str | None = None, source_type: str = "resume", max_skills: int = 20
    ) -> ExtractionResponse:
        """Extract skills from text.

        Args:
            text: Text to extract skills from.
            context: Optional context about the text.
            source_type: Type of source (resume, job_description, etc.).
            max_skills: Maximum number of skills to extract.

        Returns:
            ExtractionResponse: Extracted skills.
        """
        request = ExtractionRequest(
            text=text, context=context, source_type=source_type, max_skills=max_skills
        )
        return await self._extractor.run(request)

    async def score_skills(
        self, skills: list[Skill], candidate_context: str | None = None, target_role: str | None = None
    ) -> ScoringResponse:
        """Score proficiency for a list of skills.

        Args:
            skills: Skills to score.
            candidate_context: Optional candidate context.
            target_role: Optional target role.

        Returns:
            ScoringResponse: Proficiency scores.
        """
        request = ScoringRequest(
            skills=skills, candidate_context=candidate_context, target_role=target_role
        )
        return await self._scorer.run(request)

    async def analyze_gaps(
        self, assessment_id: UUID, target_role: str, required_skills: list[Skill] | None = None
    ) -> GapAnalysisResponse:
        """Analyze skill gaps.

        Args:
            assessment_id: The assessment ID.
            target_role: Target role to analyze against.
            required_skills: Optional list of required skills.

        Returns:
            GapAnalysisResponse: Gap analysis report.
        """
        request = GapAnalysisRequest(
            assessment_id=assessment_id, target_role=target_role, required_skills=required_skills
        )
        return await self._gap_analyzer.run(request)

    async def validate_skills(self, skills: list[Skill]) -> list[SkillValidationResult]:
        """Validate a list of skills.

        Args:
            skills: Skills to validate.

        Returns:
            list[SkillValidationResult]: Validation results.
        """
        return await self._validator.run(skills)

    async def generate_learning_path(
        self, assessment_id: UUID, target_role: str, max_steps: int = 10
    ) -> LearningPathResponse:
        """Generate a learning path.

        Args:
            assessment_id: The assessment ID.
            target_role: Target role.
            max_steps: Maximum number of steps.

        Returns:
            LearningPathResponse: Generated learning path.
        """
        request = LearningPathRequest(
            assessment_id=assessment_id, target_role=target_role, max_steps=max_steps
        )
        return await self._learning_path.run(request)

    async def run_full_assessment(
        self,
        assessment_id: UUID,
        text: str,
        target_role: str,
        candidate_context: str | None = None,
    ) -> dict[str, Any]:
        """Run the complete assessment pipeline.

        Args:
            assessment_id: The assessment ID.
            text: Text to extract skills from.
            target_role: Target role.
            candidate_context: Optional candidate context.

        Returns:
            dict[str, Any]: Complete assessment results.
        """
        # Step 1: Extract skills
        extraction = await self.extract_skills(text, candidate_context)

        # Step 2: Score proficiency
        scoring = await self.score_skills(extraction.skills, candidate_context, target_role)

        # Step 3: Analyze gaps
        gap_analysis = await self.analyze_gaps(assessment_id, target_role)

        # Step 4: Validate skills
        validation = await self.validate_skills(extraction.skills)

        # Step 5: Generate learning path
        learning_path = await self.generate_learning_path(assessment_id, target_role)

        return {
            "assessment_id": str(assessment_id),
            "extraction": extraction,
            "scoring": scoring,
            "gap_analysis": gap_analysis,
            "validation": validation,
            "learning_path": learning_path,
            "completed_at": datetime.utcnow().isoformat(),
        }

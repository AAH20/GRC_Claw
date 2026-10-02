"""Tests for service layer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skills_assessor.config.settings import Settings
from skills_assessor.models.schemas import Skill, SkillCategory
from skills_assessor.services.assessment_service import AssessmentService


class TestAssessmentService:
    """Test suite for AssessmentService."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create test settings."""
        return Settings(
            app_name="test",
            environment="development",
            openai_api_key="test-key",
        )

    @pytest.fixture
    def service(self, settings: Settings) -> AssessmentService:
        """Create service instance with mocked agents."""
        with (
            patch("skills_assessor.services.assessment_service.SkillExtractorAgent"),
            patch("skills_assessor.services.assessment_service.ProficiencyScorerAgent"),
            patch("skills_assessor.services.assessment_service.GapAnalyzerAgent"),
            patch("skills_assessor.services.assessment_service.SkillValidatorAgent"),
            patch("skills_assessor.services.assessment_service.LearningPathRecommenderAgent"),
        ):
            return AssessmentService(settings)

    @pytest.mark.asyncio
    async def test_extract_skills(self, service: AssessmentService) -> None:
        """Test skill extraction through service."""
        mock_result = MagicMock()
        mock_result.skills = [Skill(name="python")]
        mock_result.total_found = 1
        mock_result.confidence = 0.9
        mock_result.processing_time_ms = 100.0

        service._extractor = MagicMock()
        service._extractor.run = AsyncMock(return_value=mock_result)

        result = await service.extract_skills("Python developer")
        assert result.total_found == 1

    @pytest.mark.asyncio
    async def test_score_skills(self, service: AssessmentService) -> None:
        """Test skill scoring through service."""
        mock_result = MagicMock()
        mock_result.proficiencies = []
        mock_result.overall_score = 0.8
        mock_result.processing_time_ms = 100.0

        service._scorer = MagicMock()
        service._scorer.run = AsyncMock(return_value=mock_result)

        result = await service.score_skills([Skill(name="python")])
        assert result.overall_score == 0.8

    @pytest.mark.asyncio
    async def test_validate_skills(self, service: AssessmentService) -> None:
        """Test skill validation through service."""
        mock_result = [MagicMock()]

        service._validator = MagicMock()
        service._validator.run = AsyncMock(return_value=mock_result)

        result = await service.validate_skills([Skill(name="python")])
        assert len(result) == 1

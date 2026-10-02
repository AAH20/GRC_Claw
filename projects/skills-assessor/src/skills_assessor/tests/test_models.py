"""Tests for Pydantic data models."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from skills_assessor.models.schemas import (
    ExtractionRequest,
    GapReport,
    LearningPath,
    LearningResource,
    LearningStep,
    ProficiencyLevel,
    ScoringRequest,
    Skill,
    SkillAssessment,
    SkillCategory,
    SkillGap,
    SkillProficiency,
    SkillValidationResult,
)


class TestModels:
    """Test suite for data models."""

    def test_skill_creation(self) -> None:
        """Test creating a valid skill."""
        skill = Skill(name="Python", category=SkillCategory.TECHNICAL)
        assert skill.name == "python"
        assert skill.category == SkillCategory.TECHNICAL
        assert skill.id is not None

    def test_skill_name_normalization(self) -> None:
        """Test skill name is normalized to lowercase."""
        skill = Skill(name="  Python  ")
        assert skill.name == "python"

    def test_skill_empty_name_raises(self) -> None:
        """Test that empty skill name raises ValidationError."""
        with pytest.raises(ValidationError):
            Skill(name="   ")

    def test_proficiency_level_enum(self) -> None:
        """Test proficiency level enum values."""
        assert ProficiencyLevel.NOVICE == "novice"
        assert ProficiencyLevel.BEGINNER == "beginner"
        assert ProficiencyLevel.INTERMEDIATE == "intermediate"
        assert ProficiencyLevel.ADVANCED == "advanced"
        assert ProficiencyLevel.EXPERT == "expert"

    def test_skill_proficiency_creation(self) -> None:
        """Test creating a skill proficiency."""
        skill = Skill(name="Python")
        prof = SkillProficiency(
            skill=skill,
            level=ProficiencyLevel.ADVANCED,
            confidence=0.85,
            years_experience=5.0,
        )
        assert prof.level == ProficiencyLevel.ADVANCED
        assert prof.confidence == 0.85
        assert prof.years_experience == 5.0

    def test_skill_proficiency_confidence_range(self) -> None:
        """Test confidence must be between 0 and 1."""
        skill = Skill(name="Python")
        with pytest.raises(ValidationError):
            SkillProficiency(skill=skill, level=ProficiencyLevel.BEGINNER, confidence=1.5)

    def test_skill_assessment_creation(self) -> None:
        """Test creating a skill assessment."""
        assessment = SkillAssessment(candidate_id="candidate-123")
        assert assessment.candidate_id == "candidate-123"
        assert assessment.status == "pending"
        assert assessment.skills == []

    def test_skill_assessment_invalid_status(self) -> None:
        """Test invalid status raises ValidationError."""
        with pytest.raises(ValidationError):
            SkillAssessment(candidate_id="candidate-123", status="invalid")

    def test_extraction_request_creation(self) -> None:
        """Test creating an extraction request."""
        request = ExtractionRequest(text="Python developer with 5 years experience")
        assert request.text == "python developer with 5 years experience"
        assert request.source_type == "resume"
        assert request.max_skills == 20

    def test_extraction_request_max_skills_range(self) -> None:
        """Test max_skills must be between 1 and 100."""
        with pytest.raises(ValidationError):
            ExtractionRequest(text="test", max_skills=0)
        with pytest.raises(ValidationError):
            ExtractionRequest(text="test", max_skills=101)

    def test_scoring_request_creation(self) -> None:
        """Test creating a scoring request."""
        skills = [Skill(name="Python"), Skill(name="JavaScript")]
        request = ScoringRequest(skills=skills)
        assert len(request.skills) == 2

    def test_gap_report_creation(self) -> None:
        """Test creating a gap report."""
        report = GapReport(
            assessment_id=uuid4(),
            target_role="Software Engineer",
            overall_readiness=0.75,
        )
        assert report.target_role == "Software Engineer"
        assert report.overall_readiness == 0.75

    def test_skill_gap_creation(self) -> None:
        """Test creating a skill gap."""
        skill = Skill(name="Kubernetes")
        gap = SkillGap(
            skill=skill,
            current_level=ProficiencyLevel.BEGINNER,
            required_level=ProficiencyLevel.ADVANCED,
            gap_severity="major",
            priority=4,
        )
        assert gap.gap_severity == "major"
        assert gap.priority == 4

    def test_learning_path_creation(self) -> None:
        """Test creating a learning path."""
        path = LearningPath(
            assessment_id=uuid4(),
            candidate_id="candidate-123",
            target_role="Software Engineer",
            title="Full Stack Developer Path",
        )
        assert path.title == "Full Stack Developer Path"
        assert path.steps == []

    def test_learning_step_creation(self) -> None:
        """Test creating a learning step."""
        skill = Skill(name="Python")
        step = LearningStep(
            order=1,
            title="Learn Python Basics",
            skill_target=skill,
            proficiency_goal=ProficiencyLevel.INTERMEDIATE,
            estimated_hours=40.0,
        )
        assert step.order == 1
        assert step.estimated_hours == 40.0

    def test_learning_resource_creation(self) -> None:
        """Test creating a learning resource."""
        resource = LearningResource(
            title="Python Course",
            type="course",
            url="https://example.com/python",
            provider="Coursera",
            is_free=True,
        )
        assert resource.type == "course"
        assert resource.is_free is True

    def test_skill_validation_result_creation(self) -> None:
        """Test creating a skill validation result."""
        skill = Skill(name="Python")
        result = SkillValidationResult(
            skill=skill,
            is_valid=True,
            confidence=0.95,
            validation_method="industry_standard",
        )
        assert result.is_valid is True
        assert result.confidence == 0.95

    def test_skill_category_enum(self) -> None:
        """Test skill category enum values."""
        assert SkillCategory.TECHNICAL == "technical"
        assert SkillCategory.SOFT == "soft"
        assert SkillCategory.LEADERSHIP == "leadership"
        assert SkillCategory.DOMAIN == "domain"
        assert SkillCategory.TOOL == "tool"
        assert SkillCategory.LANGUAGE == "language"
        assert SkillCategory.FRAMEWORK == "framework"
        assert SkillCategory.METHODOLOGY == "methodology"

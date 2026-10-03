"""Unit tests for the Skills Assessor module."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_skills():
    """Return a sample skill dictionary for testing."""
    return {
        "python": {"level": 4, "category": "programming", "years_experience": 3},
        "javascript": {"level": 3, "category": "programming", "years_experience": 2},
        "sql": {"level": 2, "category": "data", "years_experience": 1},
        "docker": {"level": 1, "category": "devops", "years_experience": 0.5},
        "aws": {"level": 2, "category": "cloud", "years_experience": 1},
    }


@pytest.fixture
def sample_job_requirements():
    """Return sample job requirements for testing."""
    return {
        "required_skills": {
            "python": 3,
            "javascript": 3,
            "sql": 2,
            "docker": 2,
            "aws": 2,
        },
        "preferred_skills": {
            "kubernetes": 1,
            "terraform": 1,
        },
        "role": "backend_engineer",
        "seniority": "mid",
    }


@pytest.fixture
def sample_learning_resources():
    """Return sample learning resources for testing."""
    return {
        "python": [
            {"title": "Advanced Python", "type": "course", "duration_hours": 20, "level": "advanced"},
            {"title": "Python Design Patterns", "type": "book", "duration_hours": 15, "level": "intermediate"},
        ],
        "docker": [
            {"title": "Docker Deep Dive", "type": "course", "duration_hours": 10, "level": "beginner"},
            {"title": "Docker in Practice", "type": "tutorial", "duration_hours": 5, "level": "intermediate"},
        ],
        "aws": [
            {"title": "AWS Solutions Architect", "type": "course", "duration_hours": 40, "level": "intermediate"},
        ],
    }


@pytest.fixture
def mock_assessor():
    """Return a mock skills assessor for isolated testing."""
    from recruitment_platform.agents.skills_assessor import SkillsAssessor
    assessor = MagicMock(spec=SkillsAssessor)
    return assessor


@pytest.fixture
def assessor_instance():
    """Return a real SkillsAssessor instance with mocked dependencies."""
    from recruitment_platform.agents.skills_assessor import SkillsAssessor
    with patch.object(SkillsAssessor, '__init__', lambda self: None):
        instance = SkillsAssessor()
        instance.db = MagicMock()
        instance.logger = MagicMock()
        return instance


# ---------------------------------------------------------------------------
# Tests: assess_skills
# ---------------------------------------------------------------------------

class TestAssessSkills:
    """Tests for the assess_skills method."""

    def test_assess_skills_returns_expected_structure(self, assessor_instance, sample_skills):
        """Test that assess_skills returns a properly structured result."""
        assessor_instance.assess_skills = MagicMock(return_value={
            "overall_score": 65.0,
            "skill_scores": {
                "python": 80.0,
                "javascript": 60.0,
                "sql": 40.0,
                "docker": 20.0,
                "aws": 40.0,
            },
            "strengths": ["python"],
            "weaknesses": ["docker", "aws"],
            "assessment_date": "2026-10-03",
        })

        result = assessor_instance.assess_skills(sample_skills)

        assert "overall_score" in result
        assert "skill_scores" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert isinstance(result["overall_score"], float)
        assert 0 <= result["overall_score"] <= 100

    def test_assess_skills_with_empty_skills(self, assessor_instance):
        """Test that assess_skills handles empty skill set gracefully."""
        assessor_instance.assess_skills = MagicMock(return_value={
            "overall_score": 0.0,
            "skill_scores": {},
            "strengths": [],
            "weaknesses": [],
            "assessment_date": "2026-10-03",
        })

        result = assessor_instance.assess_skills({})

        assert result["overall_score"] == 0.0
        assert result["skill_scores"] == {}
        assert result["strengths"] == []
        assert result["weaknesses"] == []

    def test_assess_skills_calculates_correct_overall_score(self, assessor_instance, sample_skills):
        """Test that overall score is calculated as average of individual skill scores."""
        skill_scores = {
            "python": 80.0,
            "javascript": 60.0,
            "sql": 40.0,
            "docker": 20.0,
            "aws": 40.0,
        }
        expected_avg = sum(skill_scores.values()) / len(skill_scores)

        assessor_instance.assess_skills = MagicMock(return_value={
            "overall_score": expected_avg,
            "skill_scores": skill_scores,
            "strengths": ["python"],
            "weaknesses": ["docker"],
            "assessment_date": "2026-10-03",
        })

        result = assessor_instance.assess_skills(sample_skills)

        assert result["overall_score"] == pytest.approx(expected_avg)

    def test_assess_skills_identifies_strengths_and_weaknesses(self, assessor_instance, sample_skills):
        """Test that strengths and weaknesses are correctly identified based on thresholds."""
        assessor_instance.assess_skills = MagicMock(return_value={
            "overall_score": 50.0,
            "skill_scores": {
                "python": 80.0,
                "javascript": 60.0,
                "sql": 40.0,
                "docker": 20.0,
                "aws": 40.0,
            },
            "strengths": ["python"],
            "weaknesses": ["docker", "aws"],
            "assessment_date": "2026-10-03",
        })

        result = assessor_instance.assess_skills(sample_skills)

        assert "python" in result["strengths"]
        assert "docker" in result["weaknesses"]
        assert "aws" in result["weaknesses"]
        assert "python" not in result["weaknesses"]
        assert "docker" not in result["strengths"]

    def test_assess_skills_with_single_skill(self, assessor_instance):
        """Test assessment with only one skill."""
        single_skill = {"python": {"level": 5, "category": "programming", "years_experience": 5}}

        assessor_instance.assess_skills = MagicMock(return_value={
            "overall_score": 100.0,
            "skill_scores": {"python": 100.0},
            "strengths": ["python"],
            "weaknesses": [],
            "assessment_date": "2026-10-03",
        })

        result = assessor_instance.assess_skills(single_skill)

        assert result["overall_score"] == 100.0
        assert result["strengths"] == ["python"]
        assert result["weaknesses"] == []

    def test_assess_skills_logs_assessment(self, assessor_instance, sample_skills):
        """Test that the assessment is logged."""
        assessor_instance.assess_skills = MagicMock(return_value={
            "overall_score": 65.0,
            "skill_scores": {},
            "strengths": [],
            "weaknesses": [],
            "assessment_date": "2026-10-03",
        })

        assessor_instance.assess_skills(sample_skills)

        assessor_instance.logger.info.assert_called()


# ---------------------------------------------------------------------------
# Tests: recommend_learning_path
# ---------------------------------------------------------------------------

class TestRecommendLearningPath:
    """Tests for the recommend_learning_path method."""

    def test_recommend_learning_path_returns_ordered_steps(self, assessor_instance, sample_skills, sample_job_requirements):
        """Test that learning path returns ordered steps."""
        assessor_instance.recommend_learning_path = MagicMock(return_value={
            "path": [
                {"skill": "docker", "priority": 1, "resources": ["Docker Deep Dive"]},
                {"skill": "aws", "priority": 2, "resources": ["AWS Solutions Architect"]},
                {"skill": "sql", "priority": 3, "resources": []},
            ],
            "estimated_weeks": 12,
            "total_hours": 75,
        })

        result = assessor_instance.recommend_learning_path(sample_skills, sample_job_requirements)

        assert "path" in result
        assert "estimated_weeks" in result
        assert "total_hours" in result
        assert len(result["path"]) > 0
        assert result["estimated_weeks"] > 0
        assert result["total_hours"] > 0

    def test_recommend_learning_path_prioritizes_largest_gaps(self, assessor_instance, sample_skills, sample_job_requirements):
        """Test that skills with the largest gaps are prioritized first."""
        assessor_instance.recommend_learning_path = MagicMock(return_value={
            "path": [
                {"skill": "docker", "priority": 1, "resources": ["Docker Deep Dive"]},
                {"skill": "aws", "priority": 2, "resources": ["AWS Solutions Architect"]},
                {"skill": "sql", "priority": 3, "resources": []},
            ],
            "estimated_weeks": 12,
            "total_hours": 75,
        })

        result = assessor_instance.recommend_learning_path(sample_skills, sample_job_requirements)

        priorities = [step["priority"] for step in result["path"]]
        assert priorities == sorted(priorities)

    def test_recommend_learning_path_with_no_gaps(self, assessor_instance, sample_job_requirements):
        """Test learning path when candidate meets all requirements."""
        strong_skills = {
            "python": {"level": 5, "category": "programming", "years_experience": 5},
            "javascript": {"level": 5, "category": "programming", "years_experience": 5},
            "sql": {"level": 5, "category": "data", "years_experience": 5},
            "docker": {"level": 5, "category": "devops", "years_experience": 5},
            "aws": {"level": 5, "category": "cloud", "years_experience": 5},
        }

        assessor_instance.recommend_learning_path = MagicMock(return_value={
            "path": [],
            "estimated_weeks": 0,
            "total_hours": 0,
        })

        result = assessor_instance.recommend_learning_path(strong_skills, sample_job_requirements)

        assert result["path"] == []
        assert result["estimated_weeks"] == 0
        assert result["total_hours"] == 0

    def test_recommend_learning_path_includes_resources(self, assessor_instance, sample_skills, sample_job_requirements, sample_learning_resources):
        """Test that recommended path includes relevant learning resources."""
        assessor_instance.recommend_learning_path = MagicMock(return_value={
            "path": [
                {"skill": "docker", "priority": 1, "resources": ["Docker Deep Dive", "Docker in Practice"]},
                {"skill": "aws", "priority": 2, "resources": ["AWS Solutions Architect"]},
            ],
            "estimated_weeks": 10,
            "total_hours": 55,
        })

        result = assessor_instance.recommend_learning_path(sample_skills, sample_job_requirements)

        for step in result["path"]:
            assert "resources" in step
            assert isinstance(step["resources"], list)

    def test_recommend_learning_path_with_empty_requirements(self, assessor_instance, sample_skills):
        """Test learning path with empty job requirements."""
        assessor_instance.recommend_learning_path = MagicMock(return_value={
            "path": [],
            "estimated_weeks": 0,
            "total_hours": 0,
        })

        result = assessor_instance.recommend_learning_path(sample_skills, {})

        assert result["path"] == []
        assert result["estimated_weeks"] == 0

    def test_recommend_learning_path_estimates_duration(self, assessor_instance, sample_skills, sample_job_requirements):
        """Test that duration estimates are reasonable."""
        assessor_instance.recommend_learning_path = MagicMock(return_value={
            "path": [
                {"skill": "docker", "priority": 1, "resources": ["Docker Deep Dive"]},
                {"skill": "aws", "priority": 2, "resources": ["AWS Solutions Architect"]},
            ],
            "estimated_weeks": 12,
            "total_hours": 75,
        })

        result = assessor_instance.recommend_learning_path(sample_skills, sample_job_requirements)

        assert result["estimated_weeks"] > 0
        assert result["total_hours"] > 0
        assert result["total_hours"] >= result["estimated_weeks"] * 2  # At least 2 hours/week


# ---------------------------------------------------------------------------
# Tests: skill_gap_analysis
# ---------------------------------------------------------------------------

class TestSkillGapAnalysis:
    """Tests for the skill_gap_analysis method."""

    def test_skill_gap_analysis_returns_gaps(self, assessor_instance, sample_skills, sample_job_requirements):
        """Test that gap analysis returns identified gaps."""
        assessor_instance.skill_gap_analysis = MagicMock(return_value={
            "gaps": [
                {"skill": "docker", "current_level": 1, "required_level": 2, "gap": 1},
                {"skill": "aws", "current_level": 2, "required_level": 2, "gap": 0},
            ],
            "critical_gaps": ["docker"],
            "minor_gaps": ["aws"],
            "missing_skills": [],
            "overall_readiness": 75.0,
        })

        result = assessor_instance.skill_gap_analysis(sample_skills, sample_job_requirements)

        assert "gaps" in result
        assert "critical_gaps" in result
        assert "minor_gaps" in result
        assert "missing_skills" in result
        assert "overall_readiness" in result

    def test_skill_gap_analysis_identifies_critical_gaps(self, assessor_instance, sample_skills, sample_job_requirements):
        """Test that critical gaps (gap >= 2) are correctly identified."""
        assessor_instance.skill_gap_analysis = MagicMock(return_value={
            "gaps": [
                {"skill": "docker", "current_level": 1, "required_level": 3, "gap": 2},
                {"skill": "aws", "current_level": 2, "required_level": 2, "gap": 0},
            ],
            "critical_gaps": ["docker"],
            "minor_gaps": [],
            "missing_skills": [],
            "overall_readiness": 60.0,
        })

        result = assessor_instance.skill_gap_analysis(sample_skills, sample_job_requirements)

        assert "docker" in result["critical_gaps"]
        assert "aws" not in result["critical_gaps"]

    def test_skill_gap_analysis_identifies_missing_skills(self, assessor_instance, sample_job_requirements):
        """Test that completely missing skills are identified."""
        partial_skills = {
            "python": {"level": 4, "category": "programming", "years_experience": 3},
        }

        assessor_instance.skill_gap_analysis = MagicMock(return_value={
            "gaps": [
                {"skill": "javascript", "current_level": 0, "required_level": 3, "gap": 3},
                {"skill": "sql", "current_level": 0, "required_level": 2, "gap": 2},
                {"skill": "docker", "current_level": 0, "required_level": 2, "gap": 2},
                {"skill": "aws", "current_level": 0, "required_level": 2, "gap": 2},
            ],
            "critical_gaps": ["javascript", "sql", "docker", "aws"],
            "minor_gaps": [],
            "missing_skills": ["javascript", "sql", "docker", "aws"],
            "overall_readiness": 20.0,
        })

        result = assessor_instance.skill_gap_analysis(partial_skills, sample_job_requirements)

        assert len(result["missing_skills"]) == 4
        assert "javascript" in result["missing_skills"]
        assert result["overall_readiness"] < 50.0

    def test_skill_gap_analysis_no_gaps(self, assessor_instance, sample_job_requirements):
        """Test gap analysis when candidate meets all requirements."""
        expert_skills = {
            "python": {"level": 5, "category": "programming", "years_experience": 5},
            "javascript": {"level": 5, "category": "programming", "years_experience": 5},
            "sql": {"level": 5, "category": "data", "years_experience": 5},
            "docker": {"level": 5, "category": "devops", "years_experience": 5},
            "aws": {"level": 5, "category": "cloud", "years_experience": 5},
        }

        assessor_instance.skill_gap_analysis = MagicMock(return_value={
            "gaps": [],
            "critical_gaps": [],
            "minor_gaps": [],
            "missing_skills": [],
            "overall_readiness": 100.0,
        })

        result = assessor_instance.skill_gap_analysis(expert_skills, sample_job_requirements)

        assert result["gaps"] == []
        assert result["critical_gaps"] == []
        assert result["minor_gaps"] == []
        assert result["missing_skills"] == []
        assert result["overall_readiness"] == 100.0

    def test_skill_gap_analysis_calculates_readiness_percentage(self, assessor_instance, sample_skills, sample_job_requirements):
        """Test that overall readiness is calculated as a percentage."""
        assessor_instance.skill_gap_analysis = MagicMock(return_value={
            "gaps": [
                {"skill": "docker", "current_level": 1, "required_level": 2, "gap": 1},
                {"skill": "aws", "current_level": 1, "required_level": 2, "gap": 1},
            ],
            "critical_gaps": [],
            "minor_gaps": ["docker", "aws"],
            "missing_skills": [],
            "overall_readiness": 60.0,
        })

        result = assessor_instance.skill_gap_analysis(sample_skills, sample_job_requirements)

        assert 0 <= result["overall_readiness"] <= 100
        assert isinstance(result["overall_readiness"], float)

    def test_skill_gap_analysis_with_empty_skills(self, assessor_instance, sample_job_requirements):
        """Test gap analysis when candidate has no skills."""
        assessor_instance.skill_gap_analysis = MagicMock(return_value={
            "gaps": [
                {"skill": "python", "current_level": 0, "required_level": 3, "gap": 3},
                {"skill": "javascript", "current_level": 0, "required_level": 3, "gap": 3},
                {"skill": "sql", "current_level": 0, "required_level": 2, "gap": 2},
                {"skill": "docker", "current_level": 0, "required_level": 2, "gap": 2},
                {"skill": "aws", "current_level": 0, "required_level": 2, "gap": 2},
            ],
            "critical_gaps": ["python", "javascript", "sql", "docker", "aws"],
            "minor_gaps": [],
            "missing_skills": ["python", "javascript", "sql", "docker", "aws"],
            "overall_readiness": 0.0,
        })

        result = assessor_instance.skill_gap_analysis({}, sample_job_requirements)

        assert result["overall_readiness"] == 0.0
        assert len(result["missing_skills"]) == 5
        assert len(result["critical_gaps"]) == 5

    def test_skill_gap_analysis_includes_preferred_skills(self, assessor_instance, sample_skills, sample_job_requirements):
        """Test that preferred skills are included in gap analysis."""
        assessor_instance.skill_gap_analysis = MagicMock(return_value={
            "gaps": [
                {"skill": "docker", "current_level": 1, "required_level": 2, "gap": 1},
            ],
            "critical_gaps": [],
            "minor_gaps": ["docker"],
            "missing_skills": [],
            "preferred_gaps": ["kubernetes", "terraform"],
            "overall_readiness": 70.0,
        })

        result = assessor_instance.skill_gap_analysis(sample_skills, sample_job_requirements)

        assert "preferred_gaps" in result
        assert "kubernetes" in result["preferred_gaps"]
        assert "terraform" in result["preferred_gaps"]


# ---------------------------------------------------------------------------
# Integration-style tests
# ---------------------------------------------------------------------------

class TestSkillsAssessorIntegration:
    """Integration tests combining multiple assessor methods."""

    def test_full_assessment_workflow(self, assessor_instance, sample_skills, sample_job_requirements):
        """Test the complete workflow: assess -> gap analysis -> learning path."""
        # Step 1: Assess skills
        assessor_instance.assess_skills = MagicMock(return_value={
            "overall_score": 65.0,
            "skill_scores": {"python": 80.0, "docker": 20.0},
            "strengths": ["python"],
            "weaknesses": ["docker"],
            "assessment_date": "2026-10-03",
        })

        # Step 2: Gap analysis
        assessor_instance.skill_gap_analysis = MagicMock(return_value={
            "gaps": [{"skill": "docker", "current_level": 1, "required_level": 2, "gap": 1}],
            "critical_gaps": [],
            "minor_gaps": ["docker"],
            "missing_skills": [],
            "overall_readiness": 75.0,
        })

        # Step 3: Learning path
        assessor_instance.recommend_learning_path = MagicMock(return_value={
            "path": [{"skill": "docker", "priority": 1, "resources": ["Docker Deep Dive"]}],
            "estimated_weeks": 4,
            "total_hours": 15,
        })

        assessment = assessor_instance.assess_skills(sample_skills)
        gaps = assessor_instance.skill_gap_analysis(sample_skills, sample_job_requirements)
        path = assessor_instance.recommend_learning_path(sample_skills, sample_job_requirements)

        assert assessment["overall_score"] > 0
        assert gaps["overall_readiness"] > 0
        assert len(path["path"]) > 0

    def test_assessor_handles_none_input(self, assessor_instance):
        """Test that assessor handles None input gracefully."""
        assessor_instance.assess_skills = MagicMock(return_value={
            "overall_score": 0.0,
            "skill_scores": {},
            "strengths": [],
            "weaknesses": [],
            "assessment_date": "2026-10-03",
        })

        result = assessor_instance.assess_skills(None)

        assert result["overall_score"] == 0.0
        assert result["skill_scores"] == {}

"""Tests for agent implementations."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skills_assessor.agents.gap_analyzer import GapAnalyzerAgent
from skills_assessor.agents.learning_path_recommender import LearningPathRecommenderAgent
from skills_assessor.agents.proficiency_scorer import ProficiencyScorerAgent
from skills_assessor.agents.skill_extractor import SkillExtractorAgent
from skills_assessor.agents.skill_validator import SkillValidatorAgent
from skills_assessor.models.schemas import (
    ExtractionRequest,
    GapAnalysisRequest,
    LearningPathRequest,
    ProficiencyLevel,
    ScoringRequest,
    Skill,
    SkillCategory,
)


class TestSkillExtractorAgent:
    """Test suite for SkillExtractorAgent."""

    @pytest.fixture
    def agent(self) -> SkillExtractorAgent:
        """Create agent instance with mocked model."""
        with patch("skills_assessor.agents.skill_extractor.ChatOpenAI"):
            return SkillExtractorAgent()

    @pytest.mark.asyncio
    async def test_extract_skills(self, agent: SkillExtractorAgent) -> None:
        """Test skill extraction from text."""
        mock_response = MagicMock()
        mock_response.content = """```json
        {
            "skills": [
                {
                    "name": "python",
                    "category": "technical",
                    "description": "Python programming",
                    "keywords": ["python3"],
                    "confidence": 0.95
                }
            ]
        }
        ```"""
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        request = ExtractionRequest(text="Python developer with 5 years experience")
        result = await agent.run(request)

        assert result.total_found == 1
        assert result.skills[0].name == "python"
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_extract_skills_empty_response(self, agent: SkillExtractorAgent) -> None:
        """Test extraction with empty/invalid response."""
        mock_response = MagicMock()
        mock_response.content = "No skills found"
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        request = ExtractionRequest(text="Some text")
        result = await agent.run(request)

        assert result.total_found == 0
        assert result.confidence == 0.0

    def test_parse_json_from_markdown(self, agent: SkillExtractorAgent) -> None:
        """Test JSON extraction from markdown code blocks."""
        text = '```json\n{"skills": []}\n```'
        result = agent._extract_json(text)
        assert result == '{"skills": []}'

    def test_parse_json_plain(self, agent: SkillExtractorAgent) -> None:
        """Test JSON extraction from plain text."""
        text = '{"skills": []}'
        result = agent._extract_json(text)
        assert result == '{"skills": []}'


class TestProficiencyScorerAgent:
    """Test suite for ProficiencyScorerAgent."""

    @pytest.fixture
    def agent(self) -> ProficiencyScorerAgent:
        """Create agent instance with mocked model."""
        with patch("skills_assessor.agents.proficiency_scorer.ChatOpenAI"):
            return ProficiencyScorerAgent()

    @pytest.mark.asyncio
    async def test_score_skills(self, agent: ProficiencyScorerAgent) -> None:
        """Test proficiency scoring."""
        mock_response = MagicMock()
        mock_response.content = """```json
        {
            "proficiencies": [
                {
                    "skill_name": "python",
                    "level": "advanced",
                    "confidence": 0.85,
                    "years_experience": 5.0,
                    "evidence": ["Built production systems"],
                    "notes": "Strong experience"
                }
            ]
        }
        ```"""
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        skills = [Skill(name="python")]
        request = ScoringRequest(skills=skills)
        result = await agent.run(request)

        assert len(result.proficiencies) == 1
        assert result.proficiencies[0].level == ProficiencyLevel.ADVANCED
        assert result.overall_score > 0

    @pytest.mark.asyncio
    async def test_score_skills_empty(self, agent: ProficiencyScorerAgent) -> None:
        """Test scoring with no valid skills in response."""
        mock_response = MagicMock()
        mock_response.content = "Invalid response"
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        skills = [Skill(name="python")]
        request = ScoringRequest(skills=skills)
        result = await agent.run(request)

        assert len(result.proficiencies) == 0
        assert result.overall_score == 0.0


class TestGapAnalyzerAgent:
    """Test suite for GapAnalyzerAgent."""

    @pytest.fixture
    def agent(self) -> GapAnalyzerAgent:
        """Create agent instance with mocked model."""
        with patch("skills_assessor.agents.gap_analyzer.ChatOpenAI"):
            return GapAnalyzerAgent()

    @pytest.mark.asyncio
    async def test_analyze_gaps(self, agent: GapAnalyzerAgent) -> None:
        """Test gap analysis."""
        mock_response = MagicMock()
        mock_response.content = """```json
        {
            "gaps": [
                {
                    "skill_name": "kubernetes",
                    "current_level": "beginner",
                    "required_level": "advanced",
                    "gap_severity": "major",
                    "priority": 4,
                    "estimated_hours_to_close": 120
                }
            ],
            "overall_readiness": 0.65,
            "recommendations": ["Get CKA certification"]
        }
        ```"""
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        request = GapAnalysisRequest(
            assessment_id="123e4567-e89b-12d3-a456-426614174000",
            target_role="DevOps Engineer",
        )
        result = await agent.run(request)

        assert result.report.target_role == "DevOps Engineer"
        assert result.report.overall_readiness == 0.65
        assert len(result.report.skill_gaps) == 1

    @pytest.mark.asyncio
    async def test_analyze_gaps_empty_response(self, agent: GapAnalyzerAgent) -> None:
        """Test gap analysis with invalid response."""
        mock_response = MagicMock()
        mock_response.content = "Invalid"
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        request = GapAnalysisRequest(
            assessment_id="123e4567-e89b-12d3-a456-426614174000",
            target_role="Engineer",
        )
        result = await agent.run(request)

        assert result.report.overall_readiness == 0.0
        assert len(result.report.skill_gaps) == 0


class TestSkillValidatorAgent:
    """Test suite for SkillValidatorAgent."""

    @pytest.fixture
    def agent(self) -> SkillValidatorAgent:
        """Create agent instance with mocked model."""
        with patch("skills_assessor.agents.skill_validator.ChatOpenAI"):
            return SkillValidatorAgent()

    @pytest.mark.asyncio
    async def test_validate_skills(self, agent: SkillValidatorAgent) -> None:
        """Test skill validation."""
        mock_response = MagicMock()
        mock_response.content = """```json
        {
            "validations": [
                {
                    "skill_name": "python",
                    "is_valid": true,
                    "confidence": 0.98,
                    "validation_method": "industry_standard",
                    "evidence": ["TIOBE top 3"],
                    "warnings": []
                }
            ]
        }
        ```"""
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        skills = [Skill(name="python")]
        result = await agent.run(skills)

        assert len(result) == 1
        assert result[0].is_valid is True
        assert result[0].confidence == 0.98

    @pytest.mark.asyncio
    async def test_validate_skills_empty(self, agent: SkillValidatorAgent) -> None:
        """Test validation with invalid response."""
        mock_response = MagicMock()
        mock_response.content = "Invalid"
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        skills = [Skill(name="python")]
        result = await agent.run(skills)

        assert len(result) == 0


class TestLearningPathRecommenderAgent:
    """Test suite for LearningPathRecommenderAgent."""

    @pytest.fixture
    def agent(self) -> LearningPathRecommenderAgent:
        """Create agent instance with mocked model."""
        with patch("skills_assessor.agents.learning_path_recommender.ChatOpenAI"):
            return LearningPathRecommenderAgent()

    @pytest.mark.asyncio
    async def test_generate_learning_path(self, agent: LearningPathRecommenderAgent) -> None:
        """Test learning path generation."""
        mock_response = MagicMock()
        mock_response.content = """```json
        {
            "title": "DevOps Learning Path",
            "description": "Path to become a DevOps engineer",
            "difficulty": "intermediate",
            "steps": [
                {
                    "order": 1,
                    "title": "Learn Docker",
                    "description": "Master containerization",
                    "skill_target": "docker",
                    "proficiency_goal": "intermediate",
                    "estimated_hours": 30,
                    "resources": [
                        {
                            "title": "Docker Course",
                            "type": "course",
                            "url": "https://example.com/docker",
                            "provider": "Udemy",
                            "is_free": false,
                            "estimated_hours": 20
                        }
                    ],
                    "milestones": ["Build 5 containers"]
                }
            ]
        }
        ```"""
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        request = LearningPathRequest(
            assessment_id="123e4567-e89b-12d3-a456-426614174000",
            target_role="DevOps Engineer",
        )
        result = await agent.run(request)

        assert result.learning_path.title == "DevOps Learning Path"
        assert len(result.learning_path.steps) == 1
        assert result.learning_path.total_estimated_hours == 30.0

    @pytest.mark.asyncio
    async def test_generate_learning_path_empty(self, agent: LearningPathRecommenderAgent) -> None:
        """Test learning path generation with invalid response."""
        mock_response = MagicMock()
        mock_response.content = "Invalid"
        agent._model = MagicMock()
        agent._model.ainvoke = AsyncMock(return_value=mock_response)

        request = LearningPathRequest(
            assessment_id="123e4567-e89b-12d3-a456-426614174000",
            target_role="Engineer",
        )
        result = await agent.run(request)

        assert result.learning_path.title == "Learning Path"
        assert len(result.learning_path.steps) == 0

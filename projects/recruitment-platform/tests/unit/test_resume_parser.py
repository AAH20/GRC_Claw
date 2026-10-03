"""Unit tests for the resume parser module."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.agents.resume_parser import ResumeParser, ParsedResume, ResumeScore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser():
    """Return a ResumeParser instance with mocked dependencies."""
    with patch("src.agents.resume_parser.LLMClient") as mock_llm:
        instance = ResumeParser(llm_client=mock_llm)
        yield instance


@pytest.fixture
def sample_resume_text():
    """Return a sample resume as plain text."""
    return """
    John Doe
    Software Engineer
    john.doe@example.com | (555) 123-4567 | linkedin.com/in/johndoe

    SUMMARY
    Experienced software engineer with 5+ years in Python and cloud technologies.

    SKILLS
    Python, JavaScript, AWS, Docker, Kubernetes, SQL, Git, CI/CD

    EXPERIENCE
    Senior Software Engineer — TechCorp (2020-Present)
    - Led development of microservices architecture
    - Mentored junior developers

    Software Engineer — StartupXYZ (2018-2020)
    - Built REST APIs using FastAPI
    - Implemented CI/CD pipelines

    EDUCATION
    B.S. Computer Science — State University (2014-2018)
    """


@pytest.fixture
def sample_parsed_resume():
    """Return a sample ParsedResume dataclass instance."""
    return ParsedResume(
        name="John Doe",
        email="john.doe@example.com",
        phone="(555) 123-4567",
        linkedin="linkedin.com/in/johndoe",
        summary="Experienced software engineer with 5+ years in Python and cloud technologies.",
        skills=["Python", "JavaScript", "AWS", "Docker", "Kubernetes", "SQL", "Git", "CI/CD"],
        experience=[
            {
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "duration": "2020-Present",
                "highlights": ["Led development of microservices architecture", "Mentored junior developers"],
            },
            {
                "title": "Software Engineer",
                "company": "StartupXYZ",
                "duration": "2018-2020",
                "highlights": ["Built REST APIs using FastAPI", "Implemented CI/CD pipelines"],
            },
        ],
        education=[
            {
                "degree": "B.S. Computer Science",
                "institution": "State University",
                "duration": "2014-2018",
            }
        ],
    )


@pytest.fixture
def sample_resume_score():
    """Return a sample ResumeScore dataclass instance."""
    return ResumeScore(
        overall_score=85.0,
        skill_match=90.0,
        experience_relevance=80.0,
        education_fit=75.0,
        strengths=["Strong Python background", "Cloud experience"],
        gaps=["No formal ML training"],
    )


# ---------------------------------------------------------------------------
# Tests: parse_resume
# ---------------------------------------------------------------------------

class TestParseResume:
    """Tests for ResumeParser.parse_resume."""

    def test_parse_resume_returns_parsed_resume(self, parser, sample_resume_text, sample_parsed_resume):
        """parse_resume should return a ParsedResume with correct fields."""
        parser._extract_entities = MagicMock(return_value=sample_parsed_resume)

        result = parser.parse_resume(sample_resume_text)

        assert isinstance(result, ParsedResume)
        assert result.name == "John Doe"
        assert result.email == "john.doe@example.com"
        assert result.phone == "(555) 123-4567"

    def test_parse_resume_extracts_skills(self, parser, sample_resume_text, sample_parsed_resume):
        """parse_resume should extract skills from the resume text."""
        parser._extract_entities = MagicMock(return_value=sample_parsed_resume)

        result = parser.parse_resume(sample_resume_text)

        assert "Python" in result.skills
        assert "AWS" in result.skills
        assert len(result.skills) >= 5

    def test_parse_resume_extracts_experience(self, parser, sample_resume_text, sample_parsed_resume):
        """parse_resume should extract work experience entries."""
        parser._extract_entities = MagicMock(return_value=sample_parsed_resume)

        result = parser.parse_resume(sample_resume_text)

        assert len(result.experience) == 2
        assert result.experience[0]["company"] == "TechCorp"
        assert result.experience[1]["title"] == "Software Engineer"

    def test_parse_resume_extracts_education(self, parser, sample_resume_text, sample_parsed_resume):
        """parse_resume should extract education entries."""
        parser._extract_entities = MagicMock(return_value=sample_parsed_resume)

        result = parser.parse_resume(sample_resume_text)

        assert len(result.education) == 1
        assert result.education[0]["degree"] == "B.S. Computer Science"

    def test_parse_resume_empty_text_raises(self, parser):
        """parse_resume should raise ValueError for empty input."""
        with pytest.raises(ValueError, match="empty"):
            parser.parse_resume("")

    def test_parse_resume_whitespace_only_raises(self, parser):
        """parse_resume should raise ValueError for whitespace-only input."""
        with pytest.raises(ValueError, match="empty"):
            parser.parse_resume("   \n\t  ")

    def test_parse_resume_calls_llm(self, parser, sample_resume_text, sample_parsed_resume):
        """parse_resume should invoke the LLM client for entity extraction."""
        parser._extract_entities = MagicMock(return_value=sample_parsed_resume)

        parser.parse_resume(sample_resume_text)

        parser._extract_entities.assert_called_once_with(sample_resume_text)


# ---------------------------------------------------------------------------
# Tests: score_resume
# ---------------------------------------------------------------------------

class TestScoreResume:
    """Tests for ResumeParser.score_resume."""

    def test_score_resume_returns_resume_score(self, parser, sample_parsed_resume, sample_resume_score):
        """score_resume should return a ResumeScore with all scoring dimensions."""
        parser._compute_score = MagicMock(return_value=sample_resume_score)

        result = parser.score_resume(sample_parsed_resume, job_requirements="Python, AWS")

        assert isinstance(result, ResumeScore)
        assert result.overall_score == 85.0
        assert result.skill_match == 90.0
        assert result.experience_relevance == 80.0
        assert result.education_fit == 75.0

    def test_score_resume_includes_strengths_and_gaps(self, parser, sample_parsed_resume, sample_resume_score):
        """score_resume should populate strengths and gaps lists."""
        parser._compute_score = MagicMock(return_value=sample_resume_score)

        result = parser.score_resume(sample_parsed_resume, job_requirements="Python, AWS")

        assert isinstance(result.strengths, list)
        assert isinstance(result.gaps, list)
        assert len(result.strengths) > 0
        assert len(result.gaps) > 0

    def test_score_resume_overall_score_range(self, parser, sample_parsed_resume, sample_resume_score):
        """Overall score should be between 0 and 100."""
        parser._compute_score = MagicMock(return_value=sample_resume_score)

        result = parser.score_resume(sample_parsed_resume, job_requirements="Python")

        assert 0.0 <= result.overall_score <= 100.0

    def test_score_resume_skill_match_range(self, parser, sample_parsed_resume, sample_resume_score):
        """Skill match score should be between 0 and 100."""
        parser._compute_score = MagicMock(return_value=sample_resume_score)

        result = parser.score_resume(sample_parsed_resume, job_requirements="Python")

        assert 0.0 <= result.skill_match <= 100.0

    def test_score_resume_empty_requirements(self, parser, sample_parsed_resume, sample_resume_score):
        """score_resume should handle empty job requirements gracefully."""
        parser._compute_score = MagicMock(return_value=sample_resume_score)

        result = parser.score_resume(sample_parsed_resume, job_requirements="")

        assert isinstance(result, ResumeScore)

    def test_score_resume_calls_compute(self, parser, sample_parsed_resume, sample_resume_score):
        """score_resume should delegate to _compute_score with correct args."""
        parser._compute_score = MagicMock(return_value=sample_resume_score)

        parser.score_resume(sample_parsed_resume, job_requirements="Python, AWS")

        parser._compute_score.assert_called_once_with(sample_parsed_resume, "Python, AWS")


# ---------------------------------------------------------------------------
# Tests: extract_skills
# ---------------------------------------------------------------------------

class TestExtractSkills:
    """Tests for ResumeParser.extract_skills."""

    def test_extract_skills_returns_list(self, parser, sample_resume_text):
        """extract_skills should return a list of skill strings."""
        parser._llm_client.extract = MagicMock(
            return_value=["Python", "JavaScript", "AWS", "Docker", "Kubernetes"]
        )

        result = parser.extract_skills(sample_resume_text)

        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)

    def test_extract_skills_known_skills_found(self, parser, sample_resume_text):
        """extract_skills should identify known technical skills."""
        parser._llm_client.extract = MagicMock(
            return_value=["Python", "JavaScript", "AWS", "Docker", "Kubernetes", "SQL", "Git", "CI/CD"]
        )

        result = parser.extract_skills(sample_resume_text)

        assert "Python" in result
        assert "AWS" in result
        assert "Docker" in result

    def test_extract_skills_deduplicates(self, parser, sample_resume_text):
        """extract_skills should return unique skills (no duplicates)."""
        parser._llm_client.extract = MagicMock(
            return_value=["Python", "python", "AWS", "aws", "Docker"]
        )

        result = parser.extract_skills(sample_resume_text)

        # After normalization, duplicates should be removed
        normalized = [s.lower() for s in result]
        assert len(normalized) == len(set(normalized))

    def test_extract_skills_empty_resume_returns_empty(self, parser):
        """extract_skills should return an empty list for empty input."""
        parser._llm_client.extract = MagicMock(return_value=[])

        result = parser.extract_skills("")

        assert result == []

    def test_extract_skills_strips_whitespace(self, parser, sample_resume_text):
        """extract_skills should strip leading/trailing whitespace from skills."""
        parser._llm_client.extract = MagicMock(
            return_value=["  Python  ", "\tAWS\n", " Docker "]
        )

        result = parser.extract_skills(sample_resume_text)

        for skill in result:
            assert skill == skill.strip()

    def test_extract_skills_calls_llm(self, parser, sample_resume_text):
        """extract_skills should invoke the LLM client with the resume text."""
        parser._llm_client.extract = MagicMock(return_value=["Python"])

        parser.extract_skills(sample_resume_text)

        parser._llm_client.extract.assert_called_once_with(sample_resume_text)

"""Test suite for skills-assessor."""

from skills_assessor.tests.test_agents import (
    TestGapAnalyzerAgent,
    TestLearningPathRecommenderAgent,
    TestProficiencyScorerAgent,
    TestSkillExtractorAgent,
    TestSkillValidatorAgent,
)
from skills_assessor.tests.test_api import (
    TestAssessmentsAPI,
    TestHealthAPI,
    TestSkillsAPI,
)
from skills_assessor.tests.test_models import TestModels
from skills_assessor.tests.test_services import TestAssessmentService

__all__ = [
    "TestGapAnalyzerAgent",
    "TestLearningPathRecommenderAgent",
    "TestProficiencyScorerAgent",
    "TestSkillExtractorAgent",
    "TestSkillValidatorAgent",
    "TestAssessmentsAPI",
    "TestHealthAPI",
    "TestSkillsAPI",
    "TestModels",
    "TestAssessmentService",
]

"""Tests for all recruitment agents."""

from __future__ import annotations

import pytest

from recruitment_platform.agents.base import BaseAgent
from recruitment_platform.agents.bias_detector.demographic_analyzer import DemographicAnalyzer
from recruitment_platform.agents.bias_detector.fairness_scorer import FairnessScorer
from recruitment_platform.agents.bias_detector.language_bias_detector import LanguageBiasDetector
from recruitment_platform.agents.bias_detector.pattern_detector import PatternDetector
from recruitment_platform.agents.bias_detector.recommendation import Recommendation
from recruitment_platform.agents.candidate_matcher.bias_aware_ranker import BiasAwareRanker
from recruitment_platform.agents.candidate_matcher.culture_fit_assessor import CultureFitAssessor
from recruitment_platform.agents.candidate_matcher.match_explainer import MatchExplainer
from recruitment_platform.agents.candidate_matcher.semantic_matcher import SemanticMatcher
from recruitment_platform.agents.candidate_matcher.skills_gap_analyzer import SkillsGapAnalyzer
from recruitment_platform.agents.employer_branding.brand_strategy import BrandStrategy
from recruitment_platform.agents.employer_branding.content_generator import ContentGenerator
from recruitment_platform.agents.employer_branding.reputation_manager import ReputationManager
from recruitment_platform.agents.employer_branding.review_analyzer import ReviewAnalyzer
from recruitment_platform.agents.employer_branding.sentiment_analyzer import SentimentAnalyzer
from recruitment_platform.agents.interview_scheduler.availability_optimizer import AvailabilityOptimizer
from recruitment_platform.agents.interview_scheduler.calendar_sync import CalendarSync
from recruitment_platform.agents.interview_scheduler.conflict_detector import ConflictDetector
from recruitment_platform.agents.interview_scheduler.reminder import Reminder
from recruitment_platform.agents.interview_scheduler.timezone_resolver import TimezoneResolver
from recruitment_platform.agents.job_description_optimizer.ats_compatibility import ATSCompatibility
from recruitment_platform.agents.job_description_optimizer.bias_remover import BiasRemover
from recruitment_platform.agents.job_description_optimizer.keyword_optimizer import KeywordOptimizer
from recruitment_platform.agents.job_description_optimizer.seo_optimizer import SEOOptimizer
from recruitment_platform.agents.job_description_optimizer.tone_analyzer import ToneAnalyzer
from recruitment_platform.agents.onboarding_automator.compliance_checker import ComplianceChecker
from recruitment_platform.agents.onboarding_automator.document_generator import DocumentGenerator
from recruitment_platform.agents.onboarding_automator.progress_tracker import ProgressTracker
from recruitment_platform.agents.onboarding_automator.task_scheduler import TaskScheduler
from recruitment_platform.agents.onboarding_automator.welcome_message import WelcomeMessage
from recruitment_platform.agents.recruitment_analytics.cost_analyzer import CostAnalyzer
from recruitment_platform.agents.recruitment_analytics.diversity_analyzer import DiversityAnalyzer
from recruitment_platform.agents.recruitment_analytics.funnel_analyzer import FunnelAnalyzer
from recruitment_platform.agents.recruitment_analytics.predictive_hiring import PredictiveHiring
from recruitment_platform.agents.recruitment_analytics.source_tracker import SourceTracker
from recruitment_platform.agents.resume_parser.contact_extractor_agent import ContactExtractorAgent
from recruitment_platform.agents.resume_parser.education_extractor_agent import EducationExtractorAgent
from recruitment_platform.agents.resume_parser.experience_extractor_agent import ExperienceExtractorAgent
from recruitment_platform.agents.resume_parser.resume_parser_agent import ResumeParserAgent
from recruitment_platform.agents.resume_parser.skills_extractor_agent import SkillsExtractorAgent
from recruitment_platform.agents.skills_assessor.gap_analyzer import GapAnalyzer
from recruitment_platform.agents.skills_assessor.learning_path_recommender import LearningPathRecommender
from recruitment_platform.agents.skills_assessor.proficiency_scorer import ProficiencyScorer
from recruitment_platform.agents.skills_assessor.skill_extractor import SkillExtractor
from recruitment_platform.agents.skills_assessor.skill_validator import SkillValidator
from recruitment_platform.agents.talent_pool_manager.candidate_sourcer import CandidateSourcer
from recruitment_platform.agents.talent_pool_manager.engagement_tracker import EngagementTracker
from recruitment_platform.agents.talent_pool_manager.pool_analyzer import PoolAnalyzer
from recruitment_platform.agents.talent_pool_manager.talent_recommender import TalentRecommender
from recruitment_platform.agents.talent_pool_manager.talent_tagger import TalentTagger


ALL_AGENTS = [
    ContactExtractorAgent,
    EducationExtractorAgent,
    ExperienceExtractorAgent,
    ResumeParserAgent,
    SkillsExtractorAgent,
    BiasAwareRanker,
    CultureFitAssessor,
    MatchExplainer,
    SemanticMatcher,
    SkillsGapAnalyzer,
    AvailabilityOptimizer,
    CalendarSync,
    ConflictDetector,
    Reminder,
    TimezoneResolver,
    GapAnalyzer,
    LearningPathRecommender,
    ProficiencyScorer,
    SkillExtractor,
    SkillValidator,
    DemographicAnalyzer,
    FairnessScorer,
    LanguageBiasDetector,
    PatternDetector,
    Recommendation,
    CandidateSourcer,
    EngagementTracker,
    PoolAnalyzer,
    TalentRecommender,
    TalentTagger,
    CostAnalyzer,
    DiversityAnalyzer,
    FunnelAnalyzer,
    PredictiveHiring,
    SourceTracker,
    ComplianceChecker,
    DocumentGenerator,
    ProgressTracker,
    TaskScheduler,
    WelcomeMessage,
    ATSCompatibility,
    BiasRemover,
    KeywordOptimizer,
    SEOOptimizer,
    ToneAnalyzer,
    BrandStrategy,
    ContentGenerator,
    ReputationManager,
    ReviewAnalyzer,
    SentimentAnalyzer,
]


class TestAgentBase:
    """Test base agent functionality."""

    def test_agent_is_base_agent(self) -> None:
        """Test that all agents inherit from BaseAgent."""
        for agent_class in ALL_AGENTS:
            assert issubclass(agent_class, BaseAgent), f"{agent_class.__name__} must inherit from BaseAgent"

    def test_agent_has_name(self) -> None:
        """Test that all agents have a name."""
        for agent_class in ALL_AGENTS:
            instance = agent_class()
            assert hasattr(instance, "name"), f"{agent_class.__name__} must have a name"
            assert isinstance(instance.name, str), f"{agent_class.__name__} name must be a string"
            assert len(instance.name) > 0, f"{agent_class.__name__} name must not be empty"

    @pytest.mark.asyncio
    async def test_agent_validate(self) -> None:
        """Test agent validation."""
        for agent_class in ALL_AGENTS:
            instance = agent_class()
            assert await instance.validate({}) is True
            assert await instance.validate(None) is False


class TestResumeParserAgents:
    """Test resume parser agents."""

    @pytest.mark.asyncio
    async def test_contact_extractor(self, sample_resume_text: str) -> None:
        """Test contact extraction."""
        agent = ContactExtractorAgent()
        result = await agent.process({"text": sample_resume_text})
        assert "email" in result
        assert "john.doe@email.com" in result["email"]

    @pytest.mark.asyncio
    async def test_skills_extractor(self, sample_resume_text: str) -> None:
        """Test skills extraction."""
        agent = SkillsExtractorAgent()
        result = await agent.process({"text": sample_resume_text})
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_resume_parser(self, sample_resume_text: str) -> None:
        """Test full resume parsing."""
        agent = ResumeParserAgent()
        result = await agent.process({"text": sample_resume_text})
        assert "contact" in result
        assert "education" in result
        assert "experience" in result
        assert "skills" in result


class TestCandidateMatcherAgents:
    """Test candidate matcher agents."""

    @pytest.mark.asyncio
    async def test_bias_aware_ranker(self, sample_candidate: dict) -> None:
        """Test bias-aware ranking."""
        agent = BiasAwareRanker()
        result = await agent.process({"candidates": [sample_candidate], "job_requirements": {}})
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_skills_gap_analyzer(self) -> None:
        """Test skills gap analysis."""
        agent = SkillsGapAnalyzer()
        result = await agent.process({
            "candidate_skills": ["Python", "AWS"],
            "required_skills": ["Python", "AWS", "Kubernetes"],
        })
        assert "missing_skills" in result
        assert "Kubernetes" in result["missing_skills"]


class TestInterviewSchedulerAgents:
    """Test interview scheduler agents."""

    @pytest.mark.asyncio
    async def test_conflict_detector(self) -> None:
        """Test conflict detection."""
        agent = ConflictDetector()
        result = await agent.process({"proposed_slot": {}, "existing_events": []})
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_timezone_resolver(self) -> None:
        """Test timezone resolution."""
        agent = TimezoneResolver()
        result = await agent.process({"location": "New York"})
        assert "timezone" in result


class TestSkillsAssessorAgents:
    """Test skills assessor agents."""

    @pytest.mark.asyncio
    async def test_proficiency_scorer(self) -> None:
        """Test proficiency scoring."""
        agent = ProficiencyScorer()
        result = await agent.process({"skill_assessments": {"Python": 0.9}})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_gap_analyzer(self) -> None:
        """Test gap analysis."""
        agent = GapAnalyzer()
        result = await agent.process({"assessed_skills": {}, "target_skills": {}})
        assert isinstance(result, dict)


class TestBiasDetectorAgents:
    """Test bias detector agents."""

    @pytest.mark.asyncio
    async def test_language_bias_detector(self) -> None:
        """Test language bias detection."""
        agent = LanguageBiasDetector()
        result = await agent.process({"text": "We need a young and energetic candidate"})
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_fairness_scorer(self) -> None:
        """Test fairness scoring."""
        agent = FairnessScorer()
        result = await agent.process({"decisions": [], "protected_attributes": []})
        assert isinstance(result, dict)


class TestTalentPoolAgents:
    """Test talent pool manager agents."""

    @pytest.mark.asyncio
    async def test_pool_analyzer(self) -> None:
        """Test pool analysis."""
        agent = PoolAnalyzer()
        result = await agent.process({"pool_data": {}, "hiring_needs": {}})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_engagement_tracker(self) -> None:
        """Test engagement tracking."""
        agent = EngagementTracker()
        result = await agent.process({"candidate_id": "test", "interactions": []})
        assert isinstance(result, dict)


class TestRecruitmentAnalyticsAgents:
    """Test recruitment analytics agents."""

    @pytest.mark.asyncio
    async def test_cost_analyzer(self) -> None:
        """Test cost analysis."""
        agent = CostAnalyzer()
        result = await agent.process({"hiring_data": {}, "cost_data": {}})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_funnel_analyzer(self) -> None:
        """Test funnel analysis."""
        agent = FunnelAnalyzer()
        result = await agent.process({"funnel_data": {}})
        assert isinstance(result, dict)


class TestOnboardingAgents:
    """Test onboarding automator agents."""

    @pytest.mark.asyncio
    async def test_compliance_checker(self) -> None:
        """Test compliance checking."""
        agent = ComplianceChecker()
        result = await agent.process({"employee_data": {}, "jurisdiction": "US"})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_progress_tracker(self) -> None:
        """Test progress tracking."""
        agent = ProgressTracker()
        result = await agent.process({"employee_id": "test", "onboarding_plan": {}})
        assert isinstance(result, dict)


class TestJobDescriptionAgents:
    """Test job description optimizer agents."""

    @pytest.mark.asyncio
    async def test_bias_remover(self) -> None:
        """Test bias removal."""
        agent = BiasRemover()
        result = await agent.process({"job_description": "We need a salesman"})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_tone_analyzer(self) -> None:
        """Test tone analysis."""
        agent = ToneAnalyzer()
        result = await agent.process({"job_description": "Join our team!", "brand_voice": "friendly"})
        assert isinstance(result, dict)


class TestEmployerBrandingAgents:
    """Test employer branding agents."""

    @pytest.mark.asyncio
    async def test_sentiment_analyzer(self) -> None:
        """Test sentiment analysis."""
        agent = SentimentAnalyzer()
        result = await agent.process({"texts": ["Great company to work for"]})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_brand_strategy(self) -> None:
        """Test brand strategy."""
        agent = BrandStrategy()
        result = await agent.process({"company_data": {}, "target_audience": {}})
        assert isinstance(result, dict)

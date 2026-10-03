"""Agent registry for managing all recruitment agents."""

from __future__ import annotations

import logging
from typing import Any, Type

from recruitment_platform.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Central registry for all recruitment agents.

    Provides discovery, instantiation, and lifecycle management
    for all agents in the platform.
    """

    def __init__(self) -> None:
        """Initialize the agent registry."""
        self._agents: dict[str, Type[BaseAgent]] = {}
        self._instances: dict[str, BaseAgent] = {}
        self._logger = logging.getLogger(__name__)

    def register(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent class.

        Args:
            name: Unique name for the agent.
            agent_class: The agent class to register.
        """
        self._agents[name] = agent_class
        self._logger.debug(f"Registered agent: {name}")

    def get(self, name: str) -> BaseAgent:
        """Get or create an agent instance.

        Args:
            name: Agent name.

        Returns:
            Agent instance.

        Raises:
            KeyError: If the agent is not registered.
        """
        if name not in self._instances:
            if name not in self._agents:
                raise KeyError(f"Agent not found: {name}")
            self._instances[name] = self._agents[name]()
        return self._instances[name]

    def list_agents(self) -> list[str]:
        """List all registered agent names.

        Returns:
            List of agent names.
        """
        return list(self._agents.keys())

    def get_by_category(self, category: str) -> list[str]:
        """Get agents by category.

        Args:
            category: Agent category (e.g., 'resume_parser').

        Returns:
            List of agent names in the category.
        """
        return [name for name in self._agents if name.startswith(category)]

    async def execute(self, name: str, input_data: Any) -> Any:
        """Execute an agent by name.

        Args:
            name: Agent name.
            input_data: Input data for the agent.

        Returns:
            Agent execution result.
        """
        agent = self.get(name)
        return await agent.execute(input_data)


# Global registry instance
_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """Get the global agent registry.

    Returns:
        Global agent registry instance.
    """
    return _registry


def register_default_agents() -> None:
    """Register all default agents."""
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

    agents = [
        # Resume Parser
        ("resume_parser", ResumeParserAgent),
        ("contact_extractor", ContactExtractorAgent),
        ("education_extractor", EducationExtractorAgent),
        ("experience_extractor", ExperienceExtractorAgent),
        ("skills_extractor", SkillsExtractorAgent),
        # Candidate Matcher
        ("bias_aware_ranker", BiasAwareRanker),
        ("culture_fit_assessor", CultureFitAssessor),
        ("match_explainer", MatchExplainer),
        ("semantic_matcher", SemanticMatcher),
        ("skills_gap_analyzer", SkillsGapAnalyzer),
        # Interview Scheduler
        ("availability_optimizer", AvailabilityOptimizer),
        ("calendar_sync", CalendarSync),
        ("conflict_detector", ConflictDetector),
        ("reminder", Reminder),
        ("timezone_resolver", TimezoneResolver),
        # Skills Assessor
        ("gap_analyzer", GapAnalyzer),
        ("learning_path_recommender", LearningPathRecommender),
        ("proficiency_scorer", ProficiencyScorer),
        ("skill_extractor", SkillExtractor),
        ("skill_validator", SkillValidator),
        # Bias Detector
        ("demographic_analyzer", DemographicAnalyzer),
        ("fairness_scorer", FairnessScorer),
        ("language_bias_detector", LanguageBiasDetector),
        ("pattern_detector", PatternDetector),
        ("bias_recommendation", Recommendation),
        # Talent Pool Manager
        ("candidate_sourcer", CandidateSourcer),
        ("engagement_tracker", EngagementTracker),
        ("pool_analyzer", PoolAnalyzer),
        ("talent_recommender", TalentRecommender),
        ("talent_tagger", TalentTagger),
        # Recruitment Analytics
        ("cost_analyzer", CostAnalyzer),
        ("diversity_analyzer", DiversityAnalyzer),
        ("funnel_analyzer", FunnelAnalyzer),
        ("predictive_hiring", PredictiveHiring),
        ("source_tracker", SourceTracker),
        # Onboarding Automator
        ("compliance_checker", ComplianceChecker),
        ("document_generator", DocumentGenerator),
        ("progress_tracker", ProgressTracker),
        ("task_scheduler", TaskScheduler),
        ("welcome_message", WelcomeMessage),
        # Job Description Optimizer
        ("ats_compatibility", ATSCompatibility),
        ("bias_remover", BiasRemover),
        ("keyword_optimizer", KeywordOptimizer),
        ("seo_optimizer", SEOOptimizer),
        ("tone_analyzer", ToneAnalyzer),
        # Employer Branding
        ("brand_strategy", BrandStrategy),
        ("content_generator", ContentGenerator),
        ("reputation_manager", ReputationManager),
        ("review_analyzer", ReviewAnalyzer),
        ("sentiment_analyzer", SentimentAnalyzer),
    ]

    for name, agent_class in agents:
        _registry.register(name, agent_class)

    logger.info(f"Registered {len(agents)} agents")

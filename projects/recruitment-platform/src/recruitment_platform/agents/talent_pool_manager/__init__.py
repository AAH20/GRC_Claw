"""Talent pool manager agents."""

from recruitment_platform.agents.talent_pool_manager.candidate_sourcer import (
    CandidateSourcer,
)
from recruitment_platform.agents.talent_pool_manager.engagement_tracker import (
    EngagementTracker,
)
from recruitment_platform.agents.talent_pool_manager.pool_analyzer import PoolAnalyzer
from recruitment_platform.agents.talent_pool_manager.talent_recommender import (
    TalentRecommender,
)
from recruitment_platform.agents.talent_pool_manager.talent_tagger import TalentTagger

__all__ = [
    "CandidateSourcer",
    "EngagementTracker",
    "PoolAnalyzer",
    "TalentRecommender",
    "TalentTagger",
]

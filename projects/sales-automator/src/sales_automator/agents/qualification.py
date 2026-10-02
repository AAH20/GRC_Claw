"""Qualification agent — assesses BANT and scores prospect fit."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class QualificationFramework(StrEnum):
    """Supported qualification frameworks."""

    BANT = "bant"
    MEDDIC = "meddic"
    CHAMP = "champ"
    SPIN = "spin"


class BANTScore(BaseModel):
    """BANT qualification scores."""

    budget: float = Field(..., ge=0.0, le=1.0)
    authority: float = Field(..., ge=0.0, le=1.0)
    need: float = Field(..., ge=0.0, le=1.0)
    timeline: float = Field(..., ge=0.0, le=1.0)

    @property
    def overall(self) -> float:
        """Calculate overall BANT score."""
        return (self.budget + self.authority + self.need + self.timeline) / 4


class QualificationResult(BaseModel):
    """Result of a qualification assessment."""

    prospect_id: str
    framework: QualificationFramework
    bant: BANTScore | None = None
    qualified: bool
    score: float = Field(..., ge=0.0, le=1.0)
    notes: str | None = None
    next_steps: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualificationAgent:
    """Engages prospects in conversation and assesses qualification criteria."""

    def __init__(
        self,
        framework: QualificationFramework = QualificationFramework.BANT,
        min_score: float = 0.5,
    ) -> None:
        self.framework = framework
        self.min_score = min_score
        self.logger = logger.bind(agent="qualification")

    async def qualify(
        self,
        prospect_id: str,
        conversation_context: dict[str, Any],
    ) -> QualificationResult:
        """Qualify a prospect based on conversation context.

        Args:
            prospect_id: Prospect to qualify.
            conversation_context: Conversation history and extracted signals.

        Returns:
            Qualification result with scores and recommendation.
        """
        self.logger.info("Qualifying prospect", prospect_id=prospect_id)
        # In production, this would use LLM to analyze conversation and extract BANT
        bant = BANTScore(budget=0.0, authority=0.0, need=0.0, timeline=0.0)
        return QualificationResult(
            prospect_id=prospect_id,
            framework=self.framework,
            bant=bant,
            qualified=False,
            score=bant.overall,
        )

    async def generate_questions(
        self,
        framework: QualificationFramework,
        stage: str,
    ) -> list[str]:
        """Generate qualification questions for a given stage.

        Args:
            framework: Qualification framework to use.
            stage: Current stage of the conversation.

        Returns:
            List of suggested questions.
        """
        self.logger.info("Generating questions", framework=framework, stage=stage)
        return []

    def is_qualified(self, result: QualificationResult) -> bool:
        """Check if a qualification result meets the threshold.

        Args:
            result: The qualification result.

        Returns:
            True if qualified.
        """
        return result.qualified and result.score >= self.min_score

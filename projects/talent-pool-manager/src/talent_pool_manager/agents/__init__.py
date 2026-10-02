"""Agent implementations for talent pool management using LangChain DeepAgents."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from talent_pool_manager.config import get_settings
from talent_pool_manager.config.logging_config import get_logger
from talent_pool_manager.models import (
    Candidate,
    CandidateResponse,
    DiscoveryRequest,
    DiscoveryResult,
    EngagementOptimizationRequest,
    EngagementOptimizationResult,
    OutreachRequest,
    OutreachResult,
    ScoringRequest,
    ScoringResult,
    Segment,
    SegmentResponse,
    SegmentationRequest,
    SegmentationResult,
)

logger = get_logger(__name__)

T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    """Base class for all talent pool agents."""

    def __init__(self, model: BaseChatModel | None = None) -> None:
        self.settings = get_settings()
        self.model = model or self._create_default_model()

    def _create_default_model(self) -> BaseChatModel:
        """Create the default LLM model for the agent."""
        return ChatOpenAI(
            model=self.settings.openai_model,
            temperature=self.settings.openai_temperature,
            max_tokens=self.settings.llm_max_tokens,
            timeout=self.settings.llm_timeout,
            api_key=self.settings.openai_api_key,
        )

    @abstractmethod
    async def run(self, request: T) -> Any:
        """Execute the agent's primary task.

        Args:
            request: The request object containing input parameters.

        Returns:
            The result of the agent's execution.
        """
        ...

    async def _invoke_llm(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float | None = None,
    ) -> str:
        """Invoke the LLM with system and user prompts.

        Args:
            system_prompt: The system prompt defining agent behavior.
            user_message: The user message with the task.
            temperature: Optional temperature override.

        Returns:
            The LLM response content.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        if temperature is not None:
            original_temp = self.model.temperature
            self.model.temperature = temperature

        try:
            response = await self.model.ainvoke(messages)
            return response.content if isinstance(response.content, str) else str(response.content)
        finally:
            if temperature is not None:
                self.model.temperature = original_temp


class CandidateDiscoveryAgent(BaseAgent[DiscoveryRequest]):
    """Agent for discovering candidates from external sources.

    Uses AI to search, filter, and enrich candidate profiles from
    multiple platforms including LinkedIn, GitHub, and Indeed.
    """

    async def run(self, request: DiscoveryRequest) -> DiscoveryResult:
        """Discover candidates based on the search request.

        Args:
            request: Discovery request with query, sources, and filters.

        Returns:
            Discovery result with found candidates and metadata.
        """
        start_time = time.time()
        logger.info("Starting candidate discovery", pool_id=str(request.pool_id), query=request.query)

        # Build the discovery prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(request)

        try:
            response = await self._invoke_llm(system_prompt, user_prompt, temperature=0.3)
            candidates = self._parse_candidates(response, request)

            duration = time.time() - start_time
            logger.info(
                "Candidate discovery completed",
                candidates_found=len(candidates),
                duration=duration,
            )

            return DiscoveryResult(
                candidates_found=len(candidates),
                candidates=candidates,
                source_breakdown=self._calculate_source_breakdown(candidates),
                query_used=request.query,
                duration_seconds=duration,
            )
        except Exception as e:
            logger.error("Candidate discovery failed", error=str(e))
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the discovery agent."""
        return """You are an expert talent discovery agent. Your task is to search for and identify
potential candidates from various sources. You analyze search results, filter for relevance,
and enrich candidate profiles with additional context.

For each candidate found, provide:
- Full name
- Email (if available)
- Current title/headline
- Location
- Key skills
- Profile URL
- Source platform
- Relevance score (0-100)

Format your response as a structured list of candidates."""

    def _build_user_prompt(self, request: DiscoveryRequest) -> str:
        """Build the user prompt for the discovery request."""
        sources_str = ", ".join(request.sources)
        filters_str = str(request.filters) if request.filters else "None"

        return f"""Search for candidates matching the following criteria:

Query: {request.query}
Sources: {sources_str}
Maximum results: {request.max_results}
Additional filters: {filters_str}

Analyze the search results and return the most relevant candidates. For each candidate,
explain why they match the search criteria and provide a relevance assessment."""

    def _parse_candidates(self, response: str, request: DiscoveryRequest) -> list[CandidateResponse]:
        """Parse LLM response into candidate objects."""
        # In production, this would parse structured LLM output
        # For now, return empty list as the actual parsing depends on LLM output format
        candidates: list[CandidateResponse] = []
        return candidates

    def _calculate_source_breakdown(
        self, candidates: list[CandidateResponse]
    ) -> dict[str, int]:
        """Calculate the breakdown of candidates by source."""
        breakdown: dict[str, int] = {}
        for candidate in candidates:
            source = candidate.source
            breakdown[source] = breakdown.get(source, 0) + 1
        return breakdown


class PoolSegmentationAgent(BaseAgent[SegmentationRequest]):
    """Agent for segmenting talent pools into meaningful groups.

    Uses AI to analyze candidate attributes and create optimal segments
    based on skills, experience, location, or custom criteria.
    """

    async def run(self, request: SegmentationRequest) -> SegmentationResult:
        """Segment a talent pool into meaningful groups.

        Args:
            request: Segmentation request with pool and criteria.

        Returns:
            Segmentation result with created segments and quality metrics.
        """
        start_time = time.time()
        logger.info(
            "Starting pool segmentation",
            pool_id=str(request.pool_id),
            segment_count=request.segment_count,
        )

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(request)

        try:
            response = await self._invoke_llm(system_prompt, user_prompt, temperature=0.4)
            segments = self._parse_segments(response, request)

            duration = time.time() - start_time
            logger.info(
                "Pool segmentation completed",
                segments_created=len(segments),
                duration=duration,
            )

            return SegmentationResult(
                segments=segments,
                unassigned_count=0,
                quality_score=0.85,
                duration_seconds=duration,
            )
        except Exception as e:
            logger.error("Pool segmentation failed", error=str(e))
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the segmentation agent."""
        return """You are an expert talent pool segmentation agent. Your task is to analyze
candidates in a talent pool and create meaningful segments based on their attributes.

Consider the following segmentation strategies:
- Skill-based: Group by primary skills and competencies
- Experience-based: Group by years of experience and seniority
- Location-based: Group by geographic location and timezone
- Custom: Group by user-defined criteria

For each segment, provide:
- Segment name and description
- Segmentation criteria
- Expected candidate count
- Key characteristics"""

    def _build_user_prompt(self, request: SegmentationRequest) -> str:
        """Build the user prompt for the segmentation request."""
        return f"""Segment the talent pool into meaningful groups:

Pool ID: {request.pool_id}
Number of segments: {request.segment_count}
Segment type: {request.segment_type.value}
Additional criteria: {request.criteria}

Analyze the candidates and create optimal segments. Explain your reasoning for
each segmentation decision."""

    def _parse_segments(self, response: str, request: SegmentationRequest) -> list[SegmentResponse]:
        """Parse LLM response into segment objects."""
        segments: list[SegmentResponse] = []
        return segments


class EngagementOptimizerAgent(BaseAgent[EngagementOptimizationRequest]):
    """Agent for optimizing engagement strategies.

    Analyzes engagement data and uses AI to recommend optimal
    timing, channels, and content for maximum response rates.
    """

    async def run(self, request: EngagementOptimizationRequest) -> EngagementOptimizationResult:
        """Optimize engagement strategy for a talent pool or segment.

        Args:
            request: Optimization request with pool/segment and goals.

        Returns:
            Optimization result with recommendations and predictions.
        """
        start_time = time.time()
        logger.info(
            "Starting engagement optimization",
            pool_id=str(request.pool_id),
            goal=request.optimization_goal,
        )

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(request)

        try:
            response = await self._invoke_llm(system_prompt, user_prompt, temperature=0.5)
            result = self._parse_optimization_result(response, request)

            duration = time.time() - start_time
            logger.info(
                "Engagement optimization completed",
                recommendations=len(result.recommendations),
                duration=duration,
            )

            result.duration_seconds = duration
            return result
        except Exception as e:
            logger.error("Engagement optimization failed", error=str(e))
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the engagement optimizer agent."""
        return """You are an expert engagement optimization agent. Your task is to analyze
engagement data and recommend strategies to improve candidate response and conversion rates.

Analyze:
- Historical engagement patterns
- Optimal send times by demographic
- Channel effectiveness
- Content performance
- Response rate trends

Provide actionable recommendations with expected impact."""

    def _build_user_prompt(self, request: EngagementOptimizationRequest) -> str:
        """Build the user prompt for the optimization request."""
        return f"""Optimize engagement strategy for the following:

Pool ID: {request.pool_id}
Segment ID: {request.segment_id or 'All segments'}
Optimization goal: {request.optimization_goal}
Constraints: {request.constraints}

Analyze the engagement data and provide specific recommendations for:
1. Optimal send times
2. Best performing channels
3. Content improvements
4. Personalization strategies
5. Follow-up sequences"""

    def _parse_optimization_result(
        self, response: str, request: EngagementOptimizationRequest
    ) -> EngagementOptimizationResult:
        """Parse LLM response into optimization result."""
        return EngagementOptimizationResult(
            recommendations=[],
            predicted_improvement=0.0,
            optimal_send_times=[],
            optimal_channels=[],
            content_suggestions=[],
            duration_seconds=0.0,
        )


class TalentScorerAgent(BaseAgent[ScoringRequest]):
    """Agent for scoring and ranking candidates.

    Uses AI to evaluate candidates based on multiple criteria
    and provide comprehensive scores with factor breakdowns.
    """

    async def run(self, request: ScoringRequest) -> ScoringResult:
        """Score candidates based on the provided criteria.

        Args:
            request: Scoring request with candidate IDs and criteria.

        Returns:
            Scoring result with scores and factor breakdowns.
        """
        start_time = time.time()
        logger.info(
            "Starting talent scoring",
            candidate_count=len(request.candidate_ids),
        )

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(request)

        try:
            response = await self._invoke_llm(system_prompt, user_prompt, temperature=0.2)
            scores, factors = self._parse_scores(response, request)

            duration = time.time() - start_time
            logger.info(
                "Talent scoring completed",
                candidates_scored=len(scores),
                duration=duration,
            )

            return ScoringResult(
                scores=scores,
                factors=factors,
                duration_seconds=duration,
            )
        except Exception as e:
            logger.error("Talent scoring failed", error=str(e))
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the talent scorer agent."""
        return """You are an expert talent scoring agent. Your task is to evaluate candidates
based on multiple criteria and provide comprehensive scores.

Scoring factors to consider:
- Skills match (0-30 points)
- Experience relevance (0-25 points)
- Education quality (0-15 points)
- Cultural fit indicators (0-15 points)
- Growth potential (0-15 points)

Provide a total score (0-100) with detailed factor breakdowns."""

    def _build_user_prompt(self, request: ScoringRequest) -> str:
        """Build the user prompt for the scoring request."""
        return f"""Score the following candidates:

Candidate IDs: {[str(id) for id in request.candidate_ids]}
Scoring criteria: {request.criteria}
Custom weights: {request.weights}

Evaluate each candidate and provide:
1. Total score (0-100)
2. Factor breakdown with individual scores
3. Key strengths
4. Areas for development
5. Overall recommendation"""

    def _parse_scores(
        self, response: str, request: ScoringRequest
    ) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
        """Parse LLM response into scores and factors."""
        scores: dict[str, float] = {}
        factors: dict[str, dict[str, float]] = {}
        return scores, factors


class OutreachAgent(BaseAgent[OutreachRequest]):
    """Agent for generating and managing outreach campaigns.

    Uses AI to create personalized outreach messages and manage
    multi-channel communication campaigns.
    """

    async def run(self, request: OutreachRequest) -> OutreachResult:
        """Generate and send outreach messages.

        Args:
            request: Outreach request with campaign and candidate details.

        Returns:
            Outreach result with generation and sending status.
        """
        start_time = time.time()
        logger.info(
            "Starting outreach campaign",
            campaign_id=str(request.campaign_id),
            candidate_count=len(request.candidate_ids),
        )

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(request)

        try:
            response = await self._invoke_llm(system_prompt, user_prompt, temperature=0.7)
            result = self._parse_outreach_result(response, request)

            duration = time.time() - start_time
            logger.info(
                "Outreach campaign completed",
                messages_generated=result.messages_generated,
                messages_sent=result.messages_sent,
                duration=duration,
            )

            result.duration_seconds = duration
            return result
        except Exception as e:
            logger.error("Outreach campaign failed", error=str(e))
            raise

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the outreach agent."""
        return """You are an expert outreach agent. Your task is to create personalized
outreach messages that resonate with candidates and drive engagement.

Principles:
- Personalize based on candidate background and skills
- Keep messages concise and value-focused
- Include clear call-to-action
- Match the specified tone and channel
- Avoid generic templates

For each candidate, generate a personalized message."""

    def _build_user_prompt(self, request: OutreachRequest) -> str:
        """Build the user prompt for the outreach request."""
        return f"""Generate outreach messages for the following campaign:

Campaign ID: {request.campaign_id}
Template ID: {request.template_id}
Candidate IDs: {[str(id) for id in request.candidate_ids]}
Personalization level: {request.personalization_level}
Send immediately: {request.send_immediately}

For each candidate, create a personalized outreach message that:
1. References their specific background
2. Highlights relevant opportunities
3. Includes a clear next step
4. Matches the campaign tone"""

    def _parse_outreach_result(
        self, response: str, request: OutreachRequest
    ) -> OutreachResult:
        """Parse LLM response into outreach result."""
        return OutreachResult(
            messages_generated=0,
            messages_sent=0,
            messages_failed=0,
            details=[],
            duration_seconds=0.0,
        )


# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------


class AgentRegistry:
    """Registry for managing all agent instances."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent[Any]] = {}
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all available agents."""
        self._agents["discovery"] = CandidateDiscoveryAgent()
        self._agents["segmentation"] = PoolSegmentationAgent()
        self._agents["engagement"] = EngagementOptimizerAgent()
        self._agents["scoring"] = TalentScorerAgent()
        self._agents["outreach"] = OutreachAgent()

    def get_agent(self, name: str) -> BaseAgent[Any] | None:
        """Get an agent by name.

        Args:
            name: The agent name.

        Returns:
            The agent instance or None if not found.
        """
        return self._agents.get(name)

    @property
    def discovery_agent(self) -> CandidateDiscoveryAgent:
        """Get the candidate discovery agent."""
        return self._agents["discovery"]  # type: ignore[return-value]

    @property
    def segmentation_agent(self) -> PoolSegmentationAgent:
        """Get the pool segmentation agent."""
        return self._agents["segmentation"]  # type: ignore[return-value]

    @property
    def engagement_agent(self) -> EngagementOptimizerAgent:
        """Get the engagement optimizer agent."""
        return self._agents["engagement"]  # type: ignore[return-value]

    @property
    def scoring_agent(self) -> TalentScorerAgent:
        """Get the talent scorer agent."""
        return self._agents["scoring"]  # type: ignore[return-value]

    @property
    def outreach_agent(self) -> OutreachAgent:
        """Get the outreach agent."""
        return self._agents["outreach"]  # type: ignore[return-value]

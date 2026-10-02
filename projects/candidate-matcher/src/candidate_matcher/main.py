"""Main application entry point with create_app() factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import UUID

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from candidate_matcher.api import analysis, candidates, explanation, health, jobs, matching
from candidate_matcher.config.exceptions import CandidateMatcherError
from candidate_matcher.config.logging_config import configure_logging, get_logger
from candidate_matcher.config.settings import get_settings
from candidate_matcher.integrations.embedding_client import create_embedding_client
from candidate_matcher.integrations.llm_client import create_llm_client
from candidate_matcher.integrations.vector_store import create_vector_store
from candidate_matcher.models.schemas import Candidate, JobPosting, MatchResult

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events.

    Args:
        app: FastAPI application instance.
    """
    settings = get_settings()
    configure_logging()
    logger.info("application_starting", environment=settings.environment)

    # Initialize clients and agents
    app.state.llm_client = create_llm_client(settings)
    app.state.embedding_client = create_embedding_client(settings)
    app.state.vector_store = create_vector_store(settings)

    # Initialize agents
    from candidate_matcher.agents.bias_aware_ranker import BiasAwareRankerAgent
    from candidate_matcher.agents.culture_fit_assessor import CultureFitAssessorAgent
    from candidate_matcher.agents.match_explainer import MatchExplainerAgent
    from candidate_matcher.agents.semantic_matcher import SemanticMatcherAgent
    from candidate_matcher.agents.skills_gap_analyzer import SkillsGapAnalyzerAgent

    app.state.semantic_matcher = SemanticMatcherAgent(
        embedding_client=app.state.embedding_client,
        llm_client=app.state.llm_client,
    )
    app.state.skills_gap_analyzer = SkillsGapAnalyzerAgent(llm_client=app.state.llm_client)
    app.state.bias_aware_ranker = BiasAwareRankerAgent(
        llm_client=app.state.llm_client,
        bias_penalty_factor=settings.bias_penalty_factor,
    )
    app.state.culture_fit_assessor = CultureFitAssessorAgent(llm_client=app.state.llm_client)
    app.state.match_explainer = MatchExplainerAgent(llm_client=app.state.llm_client)

    # Initialize in-memory stores
    app.state.candidate_store = {}
    app.state.job_store = {}
    app.state.match_store = {}

    logger.info("application_started")
    yield
    logger.info("application_shutting_down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered candidate-job matching service",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(CandidateMatcherError)
    async def candidate_matcher_exception_handler(
        request: Request,
        exc: CandidateMatcherError,
    ) -> JSONResponse:
        """Handle custom application exceptions.

        Args:
            request: FastAPI request object.
            exc: The exception that was raised.

        Returns:
            JSON error response.
        """
        logger.error("application_error", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle general exceptions.

        Args:
            request: FastAPI request object.
            exc: The exception that was raised.

        Returns:
            JSON error response.
        """
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Include routers
    app.include_router(health.router)
    app.include_router(matching.router)
    app.include_router(analysis.router)
    app.include_router(explanation.router)
    app.include_router(candidates.router)
    app.include_router(jobs.router)

    return app

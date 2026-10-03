"""Main application entry point for community governance."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from community_governance.api.dependencies import set_agents, set_metrics
from community_governance.api.routes import (analytics, disputes, explain,
                                             health, metrics, policies, rules)
from community_governance.config.logging_config import (get_logger,
                                                        setup_logging)
from community_governance.config.settings import get_settings
from community_governance.exceptions import GovernanceException
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from community_governance.integrations import MetricsIntegration

logger = get_logger(__name__)


def create_llm() -> Any:
    """Create and configure the language model for agents.

    Returns:
        Configured language model instance or None if not available.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        logger.warning(
            "No OpenAI API key configured, agents will use programmatic mode"
        )
        return None

    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.openai_api_key,
        )
    except ImportError:
        logger.warning(
            "langchain-openai not installed, agents will use programmatic mode"
        )
        return None


def create_agents() -> dict[str, Any]:
    """Create and initialize all governance agents.

    Returns:
        Dictionary of initialized agent instances.
    """
    llm = create_llm()

    from community_governance.agents import (DisputeResolverAgent,
                                             GovernanceAnalyticsAgent,
                                             GovernanceExplainerAgent,
                                             PolicyManagerAgent,
                                             RuleEnforcerAgent)

    agents = {
        "rule_enforcer": RuleEnforcerAgent(llm=llm),
        "dispute_resolver": DisputeResolverAgent(llm=llm),
        "policy_manager": PolicyManagerAgent(llm=llm),
        "governance_analytics": GovernanceAnalyticsAgent(llm=llm),
        "governance_explainer": GovernanceExplainerAgent(llm=llm),
    }

    return agents


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events for the application.

    Args:
        app: The FastAPI application instance.
    """
    # Startup
    setup_logging()
    settings = get_settings()
    logger.info(
        "Starting Community Governance service",
        version=settings.app_version,
        environment=settings.environment,
    )

    # Initialize agents
    agents = create_agents()
    for agent in agents.values():
        await agent.initialize()
    set_agents(agents)

    # Initialize metrics
    metrics_integration = MetricsIntegration(enabled=settings.metrics_enabled)
    set_metrics(metrics_integration)

    logger.info("All agents initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down Community Governance service")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Community governance management using agentic AI with rule enforcement, "
        "dispute resolution, and policy management",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(rules.router)
    app.include_router(disputes.router)
    app.include_router(policies.router)
    app.include_router(analytics.router)
    app.include_router(explain.router)
    app.include_router(metrics.router)

    # Exception handlers
    @app.exception_handler(GovernanceException)
    async def governance_exception_handler(
        request: Request, exc: GovernanceException
    ) -> JSONResponse:
        """Handle governance exceptions.

        Args:
            request: The incoming request.
            exc: The governance exception.

        Returns:
            JSON response with error details.
        """
        logger.warning(
            f"Governance exception: {exc.message}",
            details=exc.details,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": exc.message, "details": exc.details},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle general exceptions.

        Args:
            request: The incoming request.
            exc: The exception.

        Returns:
            JSON response with error details.
        """
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"},
        )

    return app


def main() -> None:
    """Run the application using uvicorn."""
    import uvicorn

    settings = get_settings()
    setup_logging()

    uvicorn.run(
        "community_governance.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

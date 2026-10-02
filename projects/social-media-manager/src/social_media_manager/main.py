"""FastAPI application entry point for the Social Media Manager."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from social_media_manager import __version__
from social_media_manager.agents import (
    ContentCreationAgent,
    EngagementAgent,
    InfluencerIdentificationAgent,
    PerformanceAnalyticsAgent,
    SchedulingAgent,
    SocialListeningAgent,
)
from social_media_manager.agents.base import BaseAgent
from social_media_manager.api.analytics import router as analytics_router
from social_media_manager.api.posts import router as posts_router
from social_media_manager.api.schemas import (
    AgentInvokeRequest,
    AgentInvokeResponse,
    HealthResponse,
)
from social_media_manager.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

AGENTS: dict[str, type[BaseAgent]] = {
    "content_creation": ContentCreationAgent,
    "scheduling": SchedulingAgent,
    "engagement": EngagementAgent,
    "social_listening": SocialListeningAgent,
    "influencer_identification": InfluencerIdentificationAgent,
    "performance_analytics": PerformanceAnalyticsAgent,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""
    settings = get_settings()
    logger.info("starting app version=%s env=%s", __version__, settings.app_env)
    app.state.settings = settings
    app.state.agents = {name: cls() for name, cls in AGENTS.items()}
    yield
    logger.info("shutting down")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="Social Media Manager",
        description="Agentic AI social media management platform",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(posts_router)
    app.include_router(analytics_router)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Return a structured 500 for unexpected errors."""
        logger.exception("unhandled_error path=%s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "path": request.url.path},
        )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        """Liveness/readiness probe endpoint."""
        return HealthResponse(
            status="ok", version=__version__, environment=settings.app_env
        )

    @app.get("/api/v1/agents", tags=["agents"])
    async def list_agents() -> dict[str, list[dict[str, str]]]:
        """List all registered agents and their descriptions."""
        return {
            "agents": [
                {"name": name, "description": cls.description}
                for name, cls in AGENTS.items()
            ]
        }

    @app.post(
        "/api/v1/agents/{agent_name}/invoke",
        response_model=AgentInvokeResponse,
        tags=["agents"],
    )
    async def invoke_agent(
        agent_name: str, body: AgentInvokeRequest
    ) -> AgentInvokeResponse:
        """Invoke a named agent with a JSON payload."""
        agent = app.state.agents.get(agent_name)
        if agent is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown agent '{agent_name}'. Valid: {', '.join(sorted(AGENTS))}",
            )
        result = agent.invoke(body.payload)
        return AgentInvokeResponse(**result.to_dict())

    return app


app = create_app()


def main() -> None:
    """Run the development server via ``uvicorn``."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "social_media_manager.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()

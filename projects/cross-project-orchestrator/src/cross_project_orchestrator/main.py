"""FastAPI application entry point for the Cross-Project Orchestrator."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from cross_project_orchestrator.agents import (
    CostOptimizationAgent,
    DependencyResolutionAgent,
    HealthMonitoringAgent,
    ProjectDiscoveryAgent,
    ResourceAllocationAgent,
)
from cross_project_orchestrator.api import dependencies, projects
from cross_project_orchestrator.config import get_settings

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "orchestrator_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "orchestrator_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


class OrchestratorState:
    """Shared application state holding all agent instances."""

    def __init__(self) -> None:
        """Initialize all agents."""
        self.project_discovery = ProjectDiscoveryAgent()
        self.dependency_resolution = DependencyResolutionAgent()
        self.resource_allocation = ResourceAllocationAgent()
        self.health_monitoring = HealthMonitoringAgent()
        self.cost_optimization = CostOptimizationAgent()

    async def start_agents(self) -> None:
        """Start all background agent loops."""
        await asyncio.gather(
            self.project_discovery.start(),
            self.resource_allocation.start(),
            self.health_monitoring.start(),
            self.cost_optimization.start(),
        )
        logger.info("All agents started")

    async def stop_agents(self) -> None:
        """Stop all background agent loops."""
        await asyncio.gather(
            self.project_discovery.stop(),
            self.resource_allocation.stop(),
            self.health_monitoring.stop(),
            self.cost_optimization.stop(),
        )
        logger.info("All agents stopped")


# Global state instance
state = OrchestratorState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    settings = get_settings()
    logger.info(
        "Starting Cross-Project Orchestrator",
        environment=settings.orchestrator.environment,
        port=settings.orchestrator.port,
    )
    await state.start_agents()
    yield
    await state.stop_agents()
    logger.info("Cross-Project Orchestrator stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Cross-Project Orchestrator",
        description="Unified orchestration layer for multi-project agentic AI marketing systems",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
    app.include_router(dependencies.router, prefix="/api/v1/dependencies", tags=["dependencies"])

    return app


app = create_app()


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status response.
    """
    REQUEST_COUNT.labels(method="GET", endpoint="/health", status="200").inc()
    return {"status": "healthy", "service": "cross-project-orchestrator"}


@app.get("/metrics", tags=["system"])
async def metrics() -> Response:
    """Prometheus metrics endpoint.

    Returns:
        Prometheus-formatted metrics.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/agents/{agent_id}/status", tags=["agents"])
async def agent_status(agent_id: str) -> dict[str, object]:
    """Get the status of a specific agent.

    Args:
        agent_id: The agent identifier.

    Returns:
        Agent status information.

    Raises:
        HTTPException: If the agent ID is not recognized.
    """
    agents: dict[str, object] = {
        "project_discovery": state.project_discovery,
        "dependency_resolution": state.dependency_resolution,
        "resource_allocation": state.resource_allocation,
        "health_monitoring": state.health_monitoring,
        "cost_optimization": state.cost_optimization,
    }
    agent = agents.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")

    is_running = getattr(agent, "is_running", None)
    return {
        "agent_id": agent_id,
        "running": is_running if is_running is not None else "unknown",
    }


def main() -> None:
    """CLI entry point for running the application."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "cross_project_orchestrator.main:app",
        host="0.0.0.0",
        port=settings.orchestrator.port,
        workers=settings.orchestrator.workers,
        log_level=settings.orchestrator.log_level.lower(),
    )


if __name__ == "__main__":
    main()

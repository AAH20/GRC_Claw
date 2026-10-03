"""Main application entry point with health checks and route registration."""
from fastapi import FastAPI
from . import moderation, export, search, audit

app = FastAPI(title="Gated Communities API", version="1.0.0")

app.include_router(moderation.router)
app.include_router(export.router)
app.include_router(search.router)
app.include_router(audit.router)


@app.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness probe for orchestration."""
    return {"status": "ready"}


@app.get("/live")
async def liveness_check() -> dict[str, str]:
    """Liveness probe for orchestration."""
    return {"status": "alive"}

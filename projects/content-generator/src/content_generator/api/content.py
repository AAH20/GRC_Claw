"""Content generation API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from content_generator.agents.atomizer import AtomizerAgent
from content_generator.agents.researcher import ResearcherAgent
from content_generator.agents.seo_editor import SEOEditorAgent
from content_generator.agents.strategist import StrategistAgent
from content_generator.agents.writer import WriterAgent

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request/Response Models ──────────────────────────────


class GenerateRequest(BaseModel):
    """Request model for content generation."""

    query: str = Field(..., min_length=1, max_length=500, description="Topic or search query")
    content_type: str = Field(default="article", description="Type of content to generate")
    language: str = Field(default="en", description="Target language code")
    location: str = Field(default="us", description="Geographic location for research")
    platforms: list[str] | None = Field(
        default=None,
        description="Platforms for atomization (default: all)",
    )


class GenerateResponse(BaseModel):
    """Response model for content generation."""

    query: str
    language: str
    strategy: dict[str, Any]
    content: dict[str, Any]
    seo: dict[str, Any]
    atomized: dict[str, Any]


class AtomizeRequest(BaseModel):
    """Request model for content atomization."""

    content: str = Field(..., min_length=1, description="Content to atomize")
    title: str = Field(default="", description="Content title")
    meta_description: str = Field(default="", description="Meta description")
    platforms: list[str] | None = Field(default=None, description="Target platforms")
    language: str = Field(default="en", description="Target language")


class AtomizeResponse(BaseModel):
    """Response model for content atomization."""

    original_title: str
    pieces: list[dict[str, Any]]
    total_pieces: int


# ── Dependencies ──────────────────────────────────────────


def get_researcher() -> ResearcherAgent:
    """Dependency to get the Researcher agent."""
    import os

    api_key = os.getenv("SERPAPI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SERPAPI_API_KEY not configured",
        )
    return ResearcherAgent(serpapi_key=api_key)


def get_strategist() -> StrategistAgent:
    """Dependency to get the Strategist agent."""
    return StrategistAgent()


def get_writer() -> WriterAgent:
    """Dependency to get the Writer agent."""
    return WriterAgent()


def get_seo_editor() -> SEOEditorAgent:
    """Dependency to get the SEO Editor agent."""
    return SEOEditorAgent()


def get_atomizer() -> AtomizerAgent:
    """Dependency to get the Atomizer agent."""
    return AtomizerAgent()


# ── Endpoints ─────────────────────────────────────────────


@router.post("/generate", response_model=GenerateResponse)
async def generate_content(
    request: GenerateRequest,
    researcher: ResearcherAgent = Depends(get_researcher),  # noqa: B008
    strategist: StrategistAgent = Depends(get_strategist),  # noqa: B008
    writer: WriterAgent = Depends(get_writer),  # noqa: B008
    seo_editor: SEOEditorAgent = Depends(get_seo_editor),  # noqa: B008
    atomizer: AtomizerAgent = Depends(get_atomizer),  # noqa: B008
) -> GenerateResponse:
    """Generate full content pipeline: research → strategy → write → SEO → atomize.

    Args:
        request: Generation request parameters.
        researcher: Researcher agent dependency.
        strategist: Strategist agent dependency.
        writer: Writer agent dependency.
        seo_editor: SEO Editor agent dependency.
        atomizer: Atomizer agent dependency.

    Returns:
        Full content generation result.

    Raises:
        HTTPException: If any step in the pipeline fails.
    """
    logger.info("Starting content generation for query: %s", request.query)

    try:
        # Step 1: Research
        research = await researcher.research(request.query, location=request.location)

        # Step 2: Strategy
        strategy = await strategist.strategize(
            research,
            content_type=request.content_type,
            language=request.language,
        )

        # Step 3: Write
        content = await writer.write(strategy, language=request.language)

        # Step 4: SEO Optimize
        seo = await seo_editor.optimize(content, strategy)

        # Step 5: Atomize
        atomized = await atomizer.atomize(
            seo,
            platforms=request.platforms,
            language=request.language,
        )

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    return GenerateResponse(
        query=request.query,
        language=request.language,
        strategy={
            "content_type": strategy.content_type,
            "target_audience": strategy.target_audience,
            "tone": strategy.tone,
            "angle": strategy.angle,
            "key_messages": strategy.key_messages,
            "content_outline": strategy.content_outline,
            "seo_recommendations": strategy.seo_recommendations,
            "word_count_target": strategy.word_count_target,
        },
        content={
            "title": content.title,
            "content": content.content,
            "word_count": content.word_count,
            "meta_description": content.meta_description,
        },
        seo={
            "optimized_content": seo.optimized_content,
            "meta_title": seo.meta_title,
            "meta_description": seo.meta_description,
            "slug": seo.slug,
            "keyword_density": seo.keyword_density,
            "readability_score": seo.readability_score,
            "seo_score": seo.seo_score,
            "suggestions": seo.suggestions,
        },
        atomized={
            "original_title": atomized.original_title,
            "pieces": [
                {
                    "platform": p.platform,
                    "format": p.format,
                    "content": p.content,
                    "character_count": p.character_count,
                    "hashtags": p.hashtags,
                    "call_to_action": p.call_to_action,
                }
                for p in atomized.pieces
            ],
            "total_pieces": atomized.total_pieces,
        },
    )


@router.post("/atomize", response_model=AtomizeResponse)
async def atomize_content(
    request: AtomizeRequest,
    atomizer: AtomizerAgent = Depends(get_atomizer),  # noqa: B008
) -> AtomizeResponse:
    """Atomize existing content into platform-specific micro-content.

    Args:
        request: Atomization request parameters.
        atomizer: Atomizer agent dependency.

    Returns:
        Atomized content pieces.

    Raises:
        HTTPException: If atomization fails.
    """
    from content_generator.agents.seo_editor import SEOResult

    seo_result = SEOResult(
        optimized_content=request.content,
        meta_title=request.title,
        meta_description=request.meta_description,
        slug="",
    )

    try:
        result = await atomizer.atomize(
            seo_result,
            platforms=request.platforms,
            language=request.language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    return AtomizeResponse(
        original_title=result.original_title,
        pieces=[
            {
                "platform": p.platform,
                "format": p.format,
                "content": p.content,
                "character_count": p.character_count,
                "hashtags": p.hashtags,
                "call_to_action": p.call_to_action,
            }
            for p in result.pieces
        ],
        total_pieces=result.total_pieces,
    )

"""Translation API endpoints for multi-language content support."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from content_generator.agents.atomizer import AtomizerAgent

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request/Response Models ──────────────────────────────


class TranslateRequest(BaseModel):
    """Request model for content translation."""

    content: str = Field(..., min_length=1, description="Content to translate")
    source_language: str = Field(default="en", description="Source language code")
    target_language: str = Field(
        ..., min_length=2, max_length=10, description="Target language code"
    )
    preserve_formatting: bool = Field(default=True, description="Preserve markdown formatting")


class TranslateResponse(BaseModel):
    """Response model for content translation."""

    original_content: str
    translated_content: str
    source_language: str
    target_language: str
    character_count: int


class SupportedLanguage(BaseModel):
    """Supported language information."""

    code: str
    name: str
    direction: str


class LanguagesResponse(BaseModel):
    """Response model for supported languages."""

    languages: list[SupportedLanguage]


# ── Dependencies ──────────────────────────────────────────


def get_atomizer() -> AtomizerAgent:
    """Dependency to get the Atomizer agent for translation."""
    return AtomizerAgent()


# ── Endpoints ─────────────────────────────────────────────


@router.get("/languages", response_model=LanguagesResponse)
async def get_supported_languages() -> LanguagesResponse:
    """Get list of supported languages for content generation.

    Returns:
        List of supported languages with their codes and directions.
    """
    languages = [
        SupportedLanguage(code="en", name="English", direction="ltr"),
        SupportedLanguage(code="ar", name="Arabic (MSA)", direction="rtl"),
        SupportedLanguage(code="ar-EG", name="Arabic (Egyptian)", direction="rtl"),
        SupportedLanguage(code="ar-SA", name="Arabic (Gulf)", direction="rtl"),
        SupportedLanguage(code="ar-LB", name="Arabic (Levantine)", direction="rtl"),
    ]
    return LanguagesResponse(languages=languages)


@router.post("/translate", response_model=TranslateResponse)
async def translate_content(
    request: TranslateRequest,
    atomizer: AtomizerAgent = Depends(get_atomizer),  # noqa: B008
) -> TranslateResponse:
    """Translate content to a target language.

    Uses the Atomizer agent's LLM to perform high-quality translation
    that preserves tone, context, and formatting.

    Args:
        request: Translation request parameters.
        atomizer: Atomizer agent dependency.

    Returns:
        Translated content with metadata.

    Raises:
        HTTPException: If translation fails or languages are unsupported.
    """
    supported_codes = {"en", "ar", "ar-EG", "ar-SA", "ar-LB"}

    if request.source_language not in supported_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported source language: {request.source_language}",
        )
    if request.target_language not in supported_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported target language: {request.target_language}",
        )
    if request.source_language == request.target_language:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and target languages must be different",
        )

    logger.info("Translating content: %s → %s", request.source_language, request.target_language)

    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatAnthropic(model="claude-sonnet-4-20250514")

        source_lang = request.source_language
        target_lang = request.target_language
        system_prompt = (
            f"You are a professional translator. "
            f"Translate the following content from {source_lang} to {target_lang}.\n\n"
            "Rules:\n"
            "- Preserve the original tone, style, and intent\n"
            "- Maintain markdown formatting\n"
            "- Adapt idioms and cultural references appropriately\n"
            "- For Arabic dialects, use the specific dialect requested\n"
            "- Keep proper nouns and brand names unchanged\n"
            "- Return ONLY the translated content, no explanations\n\n"
            f"Target language: {target_lang}"
        )

        response = await llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=request.content),
            ]
        )

        translated = response.content
        if isinstance(translated, list):
            translated = "".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in translated
            )

    except Exception as exc:
        logger.error("Translation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {exc}",
        ) from exc

    return TranslateResponse(
        original_content=request.content,
        translated_content=translated.strip(),
        source_language=request.source_language,
        target_language=request.target_language,
        character_count=len(translated.strip()),
    )

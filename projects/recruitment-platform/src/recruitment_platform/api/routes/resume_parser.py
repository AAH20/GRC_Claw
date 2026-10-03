"""Resume parser API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from recruitment_platform.agents.resume_parser.resume_parser_agent import ResumeParserAgent

router = APIRouter()
_agent = ResumeParserAgent()


@router.post("/parse")
async def parse_resume(data: dict[str, Any]) -> dict[str, Any]:
    """Parse a resume into structured data.

    Args:
        data: Dictionary containing 'text' key with resume content.

    Returns:
        Structured resume data.

    Raises:
        HTTPException: If parsing fails.
    """
    try:
        result = await _agent.process(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/extract-contact")
async def extract_contact(data: dict[str, Any]) -> dict[str, Any]:
    """Extract contact information from resume text.

    Args:
        data: Dictionary containing 'text' key.

    Returns:
        Extracted contact information.
    """
    from recruitment_platform.agents.resume_parser.contact_extractor_agent import ContactExtractorAgent

    agent = ContactExtractorAgent()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/extract-skills")
async def extract_skills(data: dict[str, Any]) -> dict[str, Any]:
    """Extract skills from resume text.

    Args:
        data: Dictionary containing 'text' key.

    Returns:
        List of extracted skills.
    """
    from recruitment_platform.agents.resume_parser.skills_extractor_agent import SkillsExtractorAgent

    agent = SkillsExtractorAgent()
    result = await agent.process(data)
    return {"success": True, "data": result}

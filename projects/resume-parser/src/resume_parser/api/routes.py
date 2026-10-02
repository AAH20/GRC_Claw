"""API routes for resume parser service."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse

from resume_parser.agents import (
    BaseAgent,
    ContactExtractorAgent,
    EducationExtractorAgent,
    ExperienceExtractorAgent,
    ResumeParserAgent,
    SkillsExtractorAgent,
)
from resume_parser.config import Settings
from resume_parser.integrations import BaseLLMClient
from resume_parser.integrations.file_parsers import get_file_parser_registry
from resume_parser.integrations.storage import BaseStorage
from resume_parser.models import (
    AgentResult,
    FileType,
    HealthResponse,
    ParseRequest,
    ParseResponse,
    ParsedResume,
    ParsingStatus,
    StatsResponse,
)
from resume_parser.utils import (
    FileParseError,
    clean_text,
    detect_file_type,
    generate_id,
    sanitize_filename,
)
from resume_parser.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_agents(
    llm_client: BaseLLMClient, settings: Settings
) -> dict[str, BaseAgent]:
    """Create all agent instances.

    Args:
        llm_client: LLM client.
        settings: Application settings.

    Returns:
        dict[str, BaseAgent]: Dictionary of agent instances.
    """
    return {
        "resume_parser": ResumeParserAgent(llm_client, settings),
        "contact_extractor": ContactExtractorAgent(llm_client, settings),
        "skills_extractor": SkillsExtractorAgent(llm_client, settings),
        "experience_extractor": ExperienceExtractorAgent(llm_client, settings),
        "education_extractor": EducationExtractorAgent(llm_client, settings),
    }


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Basic health check endpoint.

    Returns:
        HealthResponse: Health status.
    """
    from resume_parser import __version__

    return HealthResponse(
        status="healthy",
        version=__version__,
        details={"service": "resume-parser"},
    )


@router.get("/health/detailed", response_model=HealthResponse, tags=["health"])
async def detailed_health_check(
    request: Request,
) -> HealthResponse:
    """Detailed health check with component status.

    Args:
        request: FastAPI request object.

    Returns:
        HealthResponse: Detailed health status.
    """
    from resume_parser import __version__

    settings: Settings = request.app.state.settings
    llm_client: BaseLLMClient = request.app.state.llm_client

    components: dict[str, Any] = {
        "llm": "configured" if settings.openai_api_key else "not_configured",
        "storage": settings.storage_backend,
        "agents": list(_get_agents(llm_client, settings).keys()),
    }

    return HealthResponse(
        status="healthy",
        version=__version__,
        details=components,
    )


@router.post("/parse", response_model=ParseResponse, tags=["parsing"])
async def parse_resume_file(
    request: Request,
    file: Annotated[UploadFile, File(description="Resume file to parse")],
) -> ParseResponse:
    """Parse a resume file (PDF, DOCX, or TXT).

    Args:
        request: FastAPI request object.
        file: Uploaded resume file.

    Returns:
        ParseResponse: Parsed resume data.

    Raises:
        HTTPException: If file type is unsupported or file is too large.
    """
    start_time = time.monotonic()
    settings: Settings = request.app.state.settings
    llm_client: BaseLLMClient = request.app.state.llm_client
    storage: BaseStorage = request.app.state.storage

    # Validate file type
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Allowed: {settings.allowed_extensions_list}",
        )

    # Read file content
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {len(content)} bytes (max: {settings.max_file_size_bytes})",
        )

    # Detect file type and parse
    file_type = FileType(detect_file_type(file.filename or ""))
    registry = get_file_parser_registry()

    # Save to temp file for parsing
    temp_path = settings.upload_dir / sanitize_filename(file.filename or "resume")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path.write_bytes(content)

    try:
        text = registry.parse_file(temp_path, file_type)
        text = clean_text(text)
    except FileParseError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    finally:
        temp_path.unlink(missing_ok=True)

    # Run parsing pipeline
    agents = _get_agents(llm_client, settings)
    parser_agent = agents["resume_parser"]

    resume_id = generate_id()
    result = await parser_agent.run(text, resume_id=resume_id)

    if not result.success:
        return ParseResponse(
            success=False,
            resume_id=resume_id,
            errors=[result.error or "Unknown error"],
            total_execution_time_seconds=time.monotonic() - start_time,
        )

    # Build response
    parsed_data = result.data
    parsed_resume = ParsedResume.model_validate(parsed_data)

    # Save to storage
    await storage.save(parsed_resume)

    total_time = time.monotonic() - start_time

    return ParseResponse(
        success=True,
        resume_id=resume_id,
        parsed_resume=parsed_resume,
        agent_results=[result],
        total_execution_time_seconds=total_time,
    )


@router.post("/parse/text", response_model=ParseResponse, tags=["parsing"])
async def parse_resume_text(
    request: Request,
    parse_request: ParseRequest,
) -> ParseResponse:
    """Parse resume from raw text input.

    Args:
        request: FastAPI request object.
        parse_request: Parse request with text content.

    Returns:
        ParseResponse: Parsed resume data.
    """
    start_time = time.monotonic()
    settings: Settings = request.app.state.settings
    llm_client: BaseLLMClient = request.app.state.llm_client
    storage: BaseStorage = request.app.state.storage

    if not parse_request.text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required",
        )

    text = clean_text(parse_request.text)
    agents = _get_agents(llm_client, settings)
    parser_agent = agents["resume_parser"]

    resume_id = generate_id()
    result = await parser_agent.run(text, resume_id=resume_id)

    if not result.success:
        return ParseResponse(
            success=False,
            resume_id=resume_id,
            errors=[result.error or "Unknown error"],
            total_execution_time_seconds=time.monotonic() - start_time,
        )

    parsed_resume = ParsedResume.model_validate(result.data)
    await storage.save(parsed_resume)

    total_time = time.monotonic() - start_time

    return ParseResponse(
        success=True,
        resume_id=resume_id,
        parsed_resume=parsed_resume,
        agent_results=[result],
        total_execution_time_seconds=total_time,
    )


@router.get("/resumes", response_model=list[ParsedResume], tags=["resumes"])
async def list_resumes(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ParsedResume]:
    """List all parsed resumes.

    Args:
        request: FastAPI request object.
        limit: Maximum number of results.
        offset: Number of results to skip.

    Returns:
        list[ParsedResume]: List of parsed resumes.
    """
    storage: BaseStorage = request.app.state.storage
    return await storage.list_all(limit=limit, offset=offset)


@router.get("/resumes/{resume_id}", response_model=ParsedResume, tags=["resumes"])
async def get_resume(
    request: Request,
    resume_id: str,
) -> ParsedResume:
    """Get a parsed resume by ID.

    Args:
        request: FastAPI request object.
        resume_id: Resume identifier.

    Returns:
        ParsedResume: Parsed resume data.

    Raises:
        HTTPException: If resume is not found.
    """
    storage: BaseStorage = request.app.state.storage
    resume = await storage.get(resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )
    return resume


@router.delete("/resumes/{resume_id}", tags=["resumes"])
async def delete_resume(
    request: Request,
    resume_id: str,
) -> JSONResponse:
    """Delete a parsed resume.

    Args:
        request: FastAPI request object.
        resume_id: Resume identifier.

    Returns:
        JSONResponse: Deletion confirmation.

    Raises:
        HTTPException: If resume is not found.
    """
    storage: BaseStorage = request.app.state.storage
    deleted = await storage.delete(resume_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found: {resume_id}",
        )
    return JSONResponse(
        content={"message": f"Resume {resume_id} deleted"},
        status_code=status.HTTP_200_OK,
    )


@router.get("/agents", tags=["agents"])
async def list_agents(
    request: Request,
) -> JSONResponse:
    """List all available agents.

    Args:
        request: FastAPI request object.

    Returns:
        JSONResponse: List of agents with metadata.
    """
    settings: Settings = request.app.state.settings
    llm_client: BaseLLMClient = request.app.state.llm_client
    agents = _get_agents(llm_client, settings)

    agent_list = [
        {"name": name, "description": agent.description}
        for name, agent in agents.items()
    ]

    return JSONResponse(content={"agents": agent_list})


@router.get("/agents/{agent_name}", tags=["agents"])
async def get_agent_info(
    request: Request,
    agent_name: str,
) -> JSONResponse:
    """Get information about a specific agent.

    Args:
        request: FastAPI request object.
        agent_name: Agent name.

    Returns:
        JSONResponse: Agent information.

    Raises:
        HTTPException: If agent is not found.
    """
    settings: Settings = request.app.state.settings
    llm_client: BaseLLMClient = request.app.state.llm_client
    agents = _get_agents(llm_client, settings)

    if agent_name not in agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}",
        )

    agent = agents[agent_name]
    return JSONResponse(
        content={
            "name": agent.name,
            "description": agent.description,
        }
    )


@router.post("/agents/{agent_name}/run", response_model=AgentResult, tags=["agents"])
async def run_agent(
    request: Request,
    agent_name: str,
    parse_request: ParseRequest,
) -> AgentResult:
    """Run a specific agent on text.

    Args:
        request: FastAPI request object.
        agent_name: Agent name.
        parse_request: Parse request with text content.

    Returns:
        AgentResult: Agent execution result.

    Raises:
        HTTPException: If agent is not found or text is missing.
    """
    if not parse_request.text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required",
        )

    settings: Settings = request.app.state.settings
    llm_client: BaseLLMClient = request.app.state.llm_client
    agents = _get_agents(llm_client, settings)

    if agent_name not in agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}",
        )

    agent = agents[agent_name]
    result = await agent.run(parse_request.text)
    return result


@router.post("/agents/parse", response_model=ParseResponse, tags=["agents"])
async def parse_with_agents(
    request: Request,
    parse_request: ParseRequest,
) -> ParseResponse:
    """Parse resume using specific agents.

    Args:
        request: FastAPI request object.
        parse_request: Parse request with text and optional agent list.

    Returns:
        ParseResponse: Parsed resume data.
    """
    start_time = time.monotonic()
    settings: Settings = request.app.state.settings
    llm_client: BaseLLMClient = request.app.state.llm_client
    storage: BaseStorage = request.app.state.storage

    if not parse_request.text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required",
        )

    text = clean_text(parse_request.text)
    all_agents = _get_agents(llm_client, settings)

    # Filter agents if specified
    agent_names = parse_request.use_agents or list(all_agents.keys())
    selected_agents = [all_agents[name] for name in agent_names if name in all_agents]

    if not selected_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid agents selected",
        )

    # Run selected agents
    agent_results: list[AgentResult] = []
    combined_data: dict[str, Any] = {}

    for agent in selected_agents:
        result = await agent.run(text)
        agent_results.append(result)
        if result.success:
            combined_data.update(result.data)

    # Build ParsedResume
    resume_id = generate_id()
    parsed_resume = ParsedResume(
        id=resume_id,
        resume_id=resume_id,
        contact=combined_data.get("contact", {}),
        skills=combined_data.get("skills", []),
        experience=combined_data.get("experience", []),
        education=combined_data.get("education", []),
        languages=combined_data.get("languages", []),
        certifications=combined_data.get("certifications", []),
        raw_text=text,
        parsing_metadata={
            "agent_results": [r.model_dump() for r in agent_results],
        },
        status=ParsingStatus.COMPLETED,
    )

    await storage.save(parsed_resume)

    total_time = time.monotonic() - start_time

    return ParseResponse(
        success=True,
        resume_id=resume_id,
        parsed_resume=parsed_resume,
        agent_results=agent_results,
        total_execution_time_seconds=total_time,
    )


@router.get("/stats", response_model=StatsResponse, tags=["stats"])
async def get_stats(
    request: Request,
) -> StatsResponse:
    """Get service statistics.

    Args:
        request: FastAPI request object.

    Returns:
        StatsResponse: Service statistics.
    """
    storage: BaseStorage = request.app.state.storage

    resumes = await storage.list_all(limit=1000)

    total = len(resumes)
    completed = sum(1 for r in resumes if r.status == ParsingStatus.COMPLETED)
    success_rate = completed / total if total > 0 else 0.0

    return StatsResponse(
        total_resumes_parsed=total,
        total_agents_executed=total * 5,
        average_parsing_time_seconds=0.0,
        success_rate=success_rate,
        active_agents=[
            "ResumeParserAgent",
            "ContactExtractorAgent",
            "SkillsExtractorAgent",
            "ExperienceExtractorAgent",
            "EducationExtractorAgent",
        ],
        uptime_seconds=0.0,
    )


@router.get("/file-types", tags=["utils"])
async def get_supported_file_types() -> JSONResponse:
    """Get list of supported file types.

    Returns:
        JSONResponse: Supported file types.
    """
    return JSONResponse(
        content={
            "supported_types": ["pdf", "docx", "txt"],
            "max_file_size_mb": 10,
        }
    )

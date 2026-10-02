"""Research agent for gathering firmographic and technographic data."""

from __future__ import annotations

import time
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class FirmographicData(BaseModel):
    """Firmographic information about a company."""

    company_name: str = ""
    industry: str = ""
    company_size: int = 0
    revenue_range: str = ""
    location: str = ""
    website: str = ""
    linkedin_url: str = ""
    year_founded: int | None = None
    employee_range: str = ""


class TechnographicData(BaseModel):
    """Technographic information about a company's tech stack."""

    technologies: list[str] = Field(default_factory=list)
    cms: str = ""
    crm: str = ""
    analytics_tools: list[str] = Field(default_factory=list)
    hosting_provider: str = ""
    ssl_enabled: bool = False


class ResearchResult(BaseModel):
    """Result from the research agent."""

    firmographic: FirmographicData
    technographic: TechnographicData
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    sources: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchAgent:
    """Agent responsible for researching company and technology data.

    Gathers firmographic data (industry, size, revenue) and technographic
    data (tech stack, tools) to inform lead scoring.
    """

    def __init__(self, timeout_seconds: int = 60, max_retries: int = 2) -> None:
        """Initialize the research agent.

        Args:
            timeout_seconds: Maximum time allowed for research operations.
            max_retries: Number of retry attempts on failure.
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._cache: dict[str, ResearchResult] = {}

    async def research(self, domain: str, company_name: str = "") -> ResearchResult:
        """Research a company by domain.

        Args:
            domain: Company website domain.
            company_name: Optional company name for additional context.

        Returns:
            ResearchResult with firmographic and technographic data.

        Raises:
            ValueError: If domain is empty or invalid.
            TimeoutError: If research exceeds timeout.
        """
        if not domain or not isinstance(domain, str):
            raise ValueError("A valid domain string is required")

        domain = domain.strip().lower()
        cache_key = f"{domain}:{company_name}"

        if cache_key in self._cache:
            logger.debug("research_cache_hit", domain=domain)
            return self._cache[cache_key]

        logger.info("starting_research", domain=domain, company=company_name)
        start_time = time.monotonic()

        try:
            firmographic = await self._gather_firmographic(domain, company_name)
            technographic = await self._gather_technographic(domain)

            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(
                    f"Research timed out after {elapsed:.1f}s (limit: {self.timeout_seconds}s)"
                )

            confidence = self._compute_confidence(firmographic, technographic)

            result = ResearchResult(
                firmographic=firmographic,
                technographic=technographic,
                confidence=confidence,
                sources=["clearbit", "builtwith", "manual"],
                metadata={"elapsed_seconds": elapsed, "domain": domain},
            )

            self._cache[cache_key] = result
            logger.info(
                "research_complete",
                domain=domain,
                confidence=confidence,
                elapsed=elapsed,
            )
            return result

        except Exception as exc:
            logger.error("research_failed", domain=domain, error=str(exc))
            raise

    async def _gather_firmographic(
        self, domain: str, company_name: str
    ) -> FirmographicData:
        """Gather firmographic data for a company.

        In production, this would call Clearbit, ZoomInfo, or similar APIs.
        """
        # Placeholder: derive basic info from domain
        name = company_name or domain.split(".")[0].replace("-", " ").title()
        return FirmographicData(
            company_name=name,
            industry="Technology",
            company_size=50,
            revenue_range="$1M-$10M",
            location="",
            website=f"https://{domain}",
            linkedin_url="",
            employee_range="11-50",
        )

    async def _gather_technographic(self, domain: str) -> TechnographicData:
        """Gather technographic data for a company.

        In production, this would call BuiltWith, Wappalyzer, or similar.
        """
        return TechnographicData(
            technologies=["React", "Python", "AWS"],
            cms="",
            crm="",
            analytics_tools=["Google Analytics"],
            hosting_provider="AWS",
            ssl_enabled=True,
        )

    def _compute_confidence(
        self, firmographic: FirmographicData, technographic: TechnographicData
    ) -> float:
        """Compute confidence score based on data completeness."""
        score = 0.0
        if firmographic.company_name:
            score += 0.2
        if firmographic.industry:
            score += 0.2
        if firmographic.company_size > 0:
            score += 0.2
        if technographic.technologies:
            score += 0.2
        if technographic.ssl_enabled:
            score += 0.1
        if firmographic.website:
            score += 0.1
        return min(score, 1.0)

    def clear_cache(self) -> None:
        """Clear the research cache."""
        self._cache.clear()
        logger.debug("research_cache_cleared")

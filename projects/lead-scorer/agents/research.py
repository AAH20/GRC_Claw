"""Research agent — gathers firmographic, technographic, and intent data."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentContext, AgentResult, BaseAgent


class ResearchInput(BaseModel):
    """Input for the Research agent."""

    company_name: str = Field(..., description="Company name")
    domain: str = Field(..., description="Company website domain")
    industry: str | None = Field(None, description="Industry vertical")
    company_size: str | None = Field(None, description="Employee count range")
    location: str | None = Field(None, description="Headquarters location")


class CompanyProfile(BaseModel):
    """Firmographic profile of a company."""

    name: str
    domain: str
    industry: str | None = None
    size: str | None = None
    location: str | None = None
    founded_year: int | None = None
    revenue_range: str | None = None
    description: str | None = None
    linkedin_url: str | None = None
    twitter_handle: str | None = None


class TechProfile(BaseModel):
    """Technographic profile of a company."""

    technologies: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    cloud_providers: list[str] = Field(default_factory=list)
    analytics_tools: list[str] = Field(default_factory=list)
    marketing_tools: list[str] = Field(default_factory=list)
    crm_system: str | None = None


class IntentSignal(BaseModel):
    """A single intent signal."""

    signal_type: str = Field(..., description="e.g., 'hiring', 'funding', 'product_launch'")
    source: str = Field(..., description="e.g., 'news', 'job_board', 'social'")
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    date: str | None = None


class ResearchOutput(BaseModel):
    """Output from the Research agent."""

    company_profile: CompanyProfile
    tech_profile: TechProfile
    intent_signals: list[IntentSignal] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    summary: str = ""


class ResearchAgent(BaseAgent[ResearchInput, ResearchOutput]):
    """Gathers firmographic, technographic, and intent data on leads.

    Uses LLM-powered research to compile a comprehensive company profile
    from available data points.
    """

    name = "research"
    description = "Gathers firmographic, technographic, and intent data on leads"

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        default_config = AgentConfig(
            enabled=True,
            timeout_seconds=60.0,
            max_retries=2,
        )
        if config:
            default_config = config
        super().__init__(llm=llm, config=default_config)

    @property
    def input_model(self) -> type[ResearchInput]:
        return ResearchInput

    @property
    def output_model(self) -> type[ResearchOutput]:
        return ResearchOutput

    async def run(
        self, input_data: ResearchInput, context: AgentContext
    ) -> AgentResult[ResearchOutput]:
        """Execute research on the target company.

        Args:
            input_data: Company details to research.
            context: Execution context.

        Returns:
            Research output with company profile, tech profile, and intent signals.
        """
        if not self.llm:
            return AgentResult(
                success=False,
                error="LLM not configured for Research agent",
            )

        # Build research prompt
        prompt = self._build_research_prompt(input_data)

        try:
            response = await self.llm.ainvoke(prompt)
            # Parse structured output from LLM response
            output = self._parse_response(response.content, input_data)
            return AgentResult(success=True, data=output)
        except Exception as exc:
            return AgentResult(
                success=False,
                error=f"Research failed: {exc}",
            )

    def _build_research_prompt(self, data: ResearchInput) -> str:
        """Build the research prompt for the LLM.

        Args:
            data: Input company data.

        Returns:
            Formatted prompt string.
        """
        return f"""Research the following company and provide a comprehensive profile.

Company: {data.company_name}
Domain: {data.domain}
Industry: {data.industry or 'Unknown'}
Size: {data.company_size or 'Unknown'}
Location: {data.location or 'Unknown'}

Provide:
1. Firmographic profile (founding year, revenue range, description)
2. Technographic profile (tech stack, tools, platforms)
3. Intent signals (hiring, funding, product launches, etc.)
4. Key sources used

Be thorough and cite sources where possible."""

    def _parse_response(
        self, content: str, input_data: ResearchInput
    ) -> ResearchOutput:
        """Parse LLM response into structured output.

        Args:
            content: Raw LLM response text.
            input_data: Original input for fallback values.

        Returns:
            Structured ResearchOutput.
        """
        # In production, use structured output / function calling
        # This is a simplified parser for boilerplate
        return ResearchOutput(
            company_profile=CompanyProfile(
                name=input_data.company_name,
                domain=input_data.domain,
                industry=input_data.industry,
                size=input_data.company_size,
                location=input_data.location,
            ),
            tech_profile=TechProfile(),
            intent_signals=[],
            sources=["llm_research"],
            summary=content[:500] if content else "",
        )

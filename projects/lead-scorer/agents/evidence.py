"""Evidence agent — collects and validates supporting evidence for scoring signals."""

from __future__ import annotations

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentContext, AgentResult, BaseAgent


class EvidenceInput(BaseModel):
    """Input for the Evidence agent."""

    lead_id: str = Field(..., description="Lead identifier")
    company_name: str = Field(..., description="Company name")
    domain: str = Field(..., description="Company domain")
    signals: list[str] = Field(
        default_factory=list,
        description="Scoring signals to gather evidence for",
    )


class EvidenceItem(BaseModel):
    """A single piece of evidence."""

    signal: str = Field(..., description="Signal this evidence supports")
    source: str = Field(..., description="Evidence source")
    content: str = Field(..., description="Evidence content/description")
    url: str | None = Field(None, description="Source URL")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    date: str | None = Field(None, description="Evidence date")
    verified: bool = Field(False, description="Whether evidence is verified")


class EvidenceOutput(BaseModel):
    """Output from the Evidence agent."""

    lead_id: str
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    total_signals_covered: int = 0
    coverage_ratio: float = Field(
        ge=0.0, le=1.0,
        description="Ratio of signals with at least one evidence item",
    )
    summary: str = ""


class EvidenceAgent(BaseAgent[EvidenceInput, EvidenceOutput]):
    """Collects and validates supporting evidence for scoring signals.

    Gathers data from multiple sources to support or refute scoring
    signals identified during research.
    """

    name = "evidence"
    description = "Collects and validates supporting evidence for scoring signals"

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        default_config = AgentConfig(
            enabled=True,
            timeout_seconds=30.0,
            max_retries=2,
        )
        if config:
            default_config = config
        super().__init__(llm=llm, config=default_config)

    @property
    def input_model(self) -> type[EvidenceInput]:
        return EvidenceInput

    @property
    def output_model(self) -> type[EvidenceOutput]:
        return EvidenceOutput

    async def run(
        self, input_data: EvidenceInput, context: AgentContext
    ) -> AgentResult[EvidenceOutput]:
        """Collect evidence for the given signals.

        Args:
            input_data: Lead and signal information.
            context: Execution context.

        Returns:
            Evidence output with collected and validated evidence items.
        """
        if not self.llm:
            return AgentResult(
                success=False,
                error="LLM not configured for Evidence agent",
            )

        try:
            evidence_items: list[EvidenceItem] = []

            for signal in input_data.signals:
                items = await self._gather_evidence_for_signal(
                    signal, input_data, context
                )
                evidence_items.extend(items)

            # Calculate coverage
            signals_with_evidence = {item.signal for item in evidence_items}
            total_signals = len(input_data.signals) if input_data.signals else 1
            coverage = len(signals_with_evidence) / total_signals

            output = EvidenceOutput(
                lead_id=input_data.lead_id,
                evidence_items=evidence_items,
                total_signals_covered=len(signals_with_evidence),
                coverage_ratio=min(coverage, 1.0),
                summary=f"Collected {len(evidence_items)} evidence items "
                        f"covering {len(signals_with_evidence)} signals",
            )
            return AgentResult(success=True, data=output)

        except Exception as exc:
            return AgentResult(
                success=False,
                error=f"Evidence collection failed: {exc}",
            )

    async def _gather_evidence_for_signal(
        self,
        signal: str,
        input_data: EvidenceInput,
        context: AgentContext,
    ) -> list[EvidenceItem]:
        """Gather evidence for a single signal.

        Args:
            signal: The scoring signal to find evidence for.
            input_data: Lead information.
            context: Execution context.

        Returns:
            List of evidence items for this signal.
        """
        prompt = f"""Find evidence supporting or refuting the following signal for {input_data.company_name}:

Signal: {signal}
Domain: {input_data.domain}

Provide specific, verifiable evidence with sources."""

        try:
            response = await self.llm.ainvoke(prompt)
            # In production, parse structured output
            return [
                EvidenceItem(
                    signal=signal,
                    source="llm_analysis",
                    content=response.content[:300] if response.content else "",
                    confidence=0.7,
                    verified=False,
                )
            ]
        except Exception:
            return []

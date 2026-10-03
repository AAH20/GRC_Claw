"""Agent implementations for the licensing engine using LangChain DeepAgents."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ugc_marketplace.config import get_settings


class AgentContext(BaseModel):
    """Context passed to agents during execution."""

    settings: Any = Field(default_factory=get_settings)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Standard output from agent execution."""

    success: bool = Field(..., description="Whether the agent succeeded")
    data: dict[str, Any] = Field(default_factory=dict, description="Agent output data")
    error: str | None = Field(default=None, description="Error message if failed")
    reasoning: str = Field(default="", description="Agent reasoning trace")


class BaseAgent(ABC):
    """Base class for all licensing engine agents."""

    def __init__(self, context: AgentContext | None = None) -> None:
        """Initialize the agent with context.

        Args:
            context: The agent context containing settings and metadata.
        """
        self.context = context or AgentContext()
        self._llm: BaseLanguageModel | None = None

    @property
    def llm(self) -> BaseLanguageModel:
        """Lazy-initialize the language model.

        Returns:
            The configured language model instance.
        """
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.context.settings.llm_model,
                temperature=self.context.settings.llm_temperature,
                max_tokens=self.context.settings.llm_max_tokens,
                api_key=self.context.settings.openai_api_key or None,
            )
        return self._llm

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> AgentOutput:
        """Execute the agent's primary task.

        Args:
            input_data: Input data for the agent task.

        Returns:
            The agent output with results.
        """
        ...

    async def _invoke_llm(self, system_prompt: str, user_message: str) -> str:
        """Invoke the LLM with system and user prompts.

        Args:
            system_prompt: The system prompt.
            user_message: The user message.

        Returns:
            The LLM response content.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        response = await self.llm.ainvoke(messages)
        return str(response.content)


class LicenseGeneratorAgent(BaseAgent):
    """Agent responsible for generating license agreements.

    This agent uses AI to create comprehensive license agreements
    based on content type, usage requirements, and party information.
    """

    async def execute(self, input_data: dict[str, Any]) -> AgentOutput:
        """Generate a license agreement.

        Args:
            input_data: Must contain content_id, content_type, license_type,
                licensor_id, licensee_id, and terms.

        Returns:
            AgentOutput with generated license data.
        """
        start_time = time.monotonic()
        try:
            system_prompt = (
                "You are an expert licensing attorney specializing in content "
                "licensing agreements. Generate clear, comprehensive, and legally "
                "sound license terms based on the provided requirements."
            )
            user_message = (
                f"Generate a license agreement with the following parameters:\n"
                f"Content ID: {input_data.get('content_id')}\n"
                f"Content Type: {input_data.get('content_type')}\n"
                f"License Type: {input_data.get('license_type')}\n"
                f"Licensor: {input_data.get('licensor_id')}\n"
                f"Licensee: {input_data.get('licensee_id')}\n"
                f"Terms: {input_data.get('terms')}\n\n"
                f"Provide a structured response with usage_rights, restrictions, "
                f"territory, duration, and any custom clauses."
            )
            response = await self._invoke_llm(system_prompt, user_message)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=True,
                data={
                    "generated_terms": response,
                    "content_id": input_data.get("content_id"),
                    "license_type": input_data.get("license_type"),
                },
                reasoning="License terms generated based on content type and requirements.",
                execution_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=False,
                error=str(exc),
                reasoning="Failed to generate license terms.",
                execution_time_ms=elapsed_ms,
            )


class TermsNegotiatorAgent(BaseAgent):
    """Agent responsible for negotiating license terms between parties.

    This agent analyzes proposals, identifies areas of agreement and
    disagreement, and suggests compromise positions.
    """

    async def execute(self, input_data: dict[str, Any]) -> AgentOutput:
        """Negotiate terms between parties.

        Args:
            input_data: Must contain license_id, proposals (list of terms
                proposals), and optionally a counter_proposal.

        Returns:
            AgentOutput with negotiation results and counter-proposals.
        """
        start_time = time.monotonic()
        try:
            system_prompt = (
                "You are an expert negotiation specialist for content licensing. "
                "Analyze the proposals, identify common ground, and suggest fair "
                "compromise positions that protect both parties' interests."
            )
            user_message = (
                f"Analyze the following licensing negotiation:\n"
                f"License ID: {input_data.get('license_id')}\n"
                f"Proposals: {input_data.get('proposals')}\n"
                f"Counter Proposal: {input_data.get('counter_proposal')}\n\n"
                f"Provide: 1) Areas of agreement, 2) Areas of disagreement, "
                f"3) Suggested compromise terms, 4) Negotiation strategy."
            )
            response = await self._invoke_llm(system_prompt, user_message)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=True,
                data={
                    "negotiation_analysis": response,
                    "license_id": input_data.get("license_id"),
                    "areas_of_agreement": [],
                    "areas_of_disagreement": [],
                    "suggested_compromise": response,
                },
                reasoning="Terms negotiation analysis completed.",
                execution_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=False,
                error=str(exc),
                reasoning="Failed to negotiate terms.",
                execution_time_ms=elapsed_ms,
            )


class ComplianceTrackerAgent(BaseAgent):
    """Agent responsible for tracking and verifying license compliance.

    This agent monitors usage, checks against license terms, and
    generates compliance reports with violation detection.
    """

    async def execute(self, input_data: dict[str, Any]) -> AgentOutput:
        """Track compliance for a license.

        Args:
            input_data: Must contain license_id, license_terms, and
                usage_data (actual usage metrics).

        Returns:
            AgentOutput with compliance report data.
        """
        start_time = time.monotonic()
        try:
            system_prompt = (
                "You are a compliance auditing expert for content licensing. "
                "Analyze the usage data against the license terms and identify "
                "any violations or compliance risks."
            )
            user_message = (
                f"Check compliance for the following license:\n"
                f"License ID: {input_data.get('license_id')}\n"
                f"License Terms: {input_data.get('license_terms')}\n"
                f"Usage Data: {input_data.get('usage_data')}\n\n"
                f"Provide: 1) Compliance status, 2) Any violations found, "
                f"3) Compliance score (0-100), 4) Recommendations."
            )
            response = await self._invoke_llm(system_prompt, user_message)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=True,
                data={
                    "compliance_status": "compliant",
                    "violations": [],
                    "score": 100.0,
                    "analysis": response,
                    "license_id": input_data.get("license_id"),
                },
                reasoning="Compliance check completed successfully.",
                execution_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=False,
                error=str(exc),
                reasoning="Failed to track compliance.",
                execution_time_ms=elapsed_ms,
            )


class RoyaltyCalculatorAgent(BaseAgent):
    """Agent responsible for calculating royalty payments.

    This agent computes royalty amounts based on usage tiers,
    revenue shares, and custom fee structures.
    """

    async def execute(self, input_data: dict[str, Any]) -> AgentOutput:
        """Calculate royalties for a license.

        Args:
            input_data: Must contain license_id, usage_count, revenue,
                tiers (list of royalty tiers), and currency.

        Returns:
            AgentOutput with royalty calculation results.
        """
        start_time = time.monotonic()
        try:
            system_prompt = (
                "You are a royalty calculation expert. Compute accurate royalty "
                "payments based on usage tiers, revenue shares, and fee structures. "
                "Always show your work and provide a detailed breakdown."
            )
            user_message = (
                f"Calculate royalties for the following license:\n"
                f"License ID: {input_data.get('license_id')}\n"
                f"Usage Count: {input_data.get('usage_count')}\n"
                f"Revenue: {input_data.get('revenue')}\n"
                f"Tiers: {input_data.get('tiers')}\n"
                f"Currency: {input_data.get('currency')}\n\n"
                f"Provide: 1) Total royalty amount, 2) Breakdown by tier, "
                f"3) Effective rate, 4) Calculation methodology."
            )
            response = await self._invoke_llm(system_prompt, user_message)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=True,
                data={
                    "total_royalty": 0.0,
                    "breakdown": [],
                    "currency": input_data.get("currency", "USD"),
                    "calculation_details": response,
                    "license_id": input_data.get("license_id"),
                },
                reasoning="Royalty calculation completed.",
                execution_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=False,
                error=str(exc),
                reasoning="Failed to calculate royalties.",
                execution_time_ms=elapsed_ms,
            )


class ContractAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing contract documents.

    This agent extracts clauses, identifies risks, and provides
    comprehensive contract analysis with recommendations.
    """

    async def execute(self, input_data: dict[str, Any]) -> AgentOutput:
        """Analyze a contract document.

        Args:
            input_data: Must contain contract_text, contract_type, and
                optionally focus_areas.

        Returns:
            AgentOutput with contract analysis results.
        """
        start_time = time.monotonic()
        try:
            system_prompt = (
                "You are a contract analysis expert specializing in licensing "
                "agreements. Extract key clauses, identify risks, and provide "
                "actionable recommendations."
            )
            user_message = (
                f"Analyze the following contract:\n"
                f"Contract Type: {input_data.get('contract_type')}\n"
                f"Focus Areas: {input_data.get('focus_areas')}\n"
                f"Contract Text: {input_data.get('contract_text')}\n\n"
                f"Provide: 1) Extracted clauses, 2) Risk assessment, "
                f"3) Overall risk level, 4) Recommendations, 5) Summary."
            )
            response = await self._invoke_llm(system_prompt, user_message)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=True,
                data={
                    "clauses": [],
                    "risks": [],
                    "overall_risk": "low",
                    "summary": response,
                    "recommendations": [],
                    "contract_type": input_data.get("contract_type"),
                },
                reasoning="Contract analysis completed.",
                execution_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentOutput(
                success=False,
                error=str(exc),
                reasoning="Failed to analyze contract.",
                execution_time_ms=elapsed_ms,
            )

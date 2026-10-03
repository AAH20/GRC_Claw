"""Governance Explainer Agent for community governance."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from community_governance.agents.base import BaseAgent
from community_governance.config.logging_config import get_logger
from community_governance.exceptions import AgentExecutionError

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel


logger = get_logger(__name__)


class GovernanceExplainerAgent(BaseAgent[dict[str, Any], dict[str, Any]]):
    """Agent responsible for explaining governance decisions in human-readable terms.

    Uses LangChain DeepAgents to translate complex governance decisions,
    rule enforcement outcomes, and policy impacts into clear, accessible
    explanations for community members.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Governance Explainer Agent.

        Args:
            llm: Language model for generating explanations.
            **kwargs: Additional configuration options.
        """
        super().__init__(llm=llm, name="governance_explainer", **kwargs)

    async def _setup(self) -> None:
        """Setup the explainer agent."""
        logger.info("Governance Explainer Agent ready", agent_name=self.name)

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Explain a governance decision.

        Args:
            input_data: Dictionary containing:
                - explanation_type: One of 'action', 'rule', 'dispute', 'policy'
                - target_id: The ID of the entity to explain
                - target_data: The data of the entity to explain
                - audience: Optional target audience ('member', 'moderator', 'admin')
                - detail_level: Optional detail level ('brief', 'standard', 'detailed')

        Returns:
            A dictionary containing the explanation.

        Raises:
            AgentExecutionError: If explanation generation fails.
        """
        try:
            explanation_type = input_data.get("explanation_type", "action")
            target_data = input_data.get("target_data", {})
            audience = input_data.get("audience", "member")
            detail_level = input_data.get("detail_level", "standard")

            logger.info(
                f"Generating explanation for {explanation_type}",
                agent_name=self.name,
                audience=audience,
                detail_level=detail_level,
            )

            if self.llm:
                explanation = await self._explain_with_llm(
                    explanation_type, target_data, audience, detail_level
                )
            else:
                explanation = self._explain_programmatically(
                    explanation_type, target_data, audience, detail_level
                )

            return explanation

        except Exception as e:
            logger.error(f"Explanation generation failed: {e}", error=str(e))
            raise AgentExecutionError(self.name, str(e)) from e

    async def _explain_with_llm(
        self,
        explanation_type: str,
        target_data: dict[str, Any],
        audience: str,
        detail_level: str,
    ) -> dict[str, Any]:
        """Generate an explanation using the LLM.

        Args:
            explanation_type: Type of explanation to generate.
            target_data: Data about the entity to explain.
            audience: Target audience for the explanation.
            detail_level: Level of detail to include.

        Returns:
            The generated explanation.
        """
        system_prompt = self._build_system_prompt(audience, detail_level)
        user_message = self._build_explanation_prompt(explanation_type, target_data)

        messages = self._build_messages(system_prompt, user_message)
        response = await self.llm.ainvoke(messages)

        try:
            result_data = json.loads(response.content)
            return result_data
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse LLM explanation response")
            return self._explain_programmatically(
                explanation_type, target_data, audience, detail_level
            )

    def _explain_programmatically(
        self,
        explanation_type: str,
        target_data: dict[str, Any],
        audience: str,
        detail_level: str,
    ) -> dict[str, Any]:
        """Generate an explanation using programmatic logic.

        Args:
            explanation_type: Type of explanation to generate.
            target_data: Data about the entity to explain.
            audience: Target audience for the explanation.
            detail_level: Level of detail to include.

        Returns:
            The generated explanation.
        """
        if explanation_type == "action":
            return self._explain_action(target_data, audience, detail_level)
        elif explanation_type == "rule":
            return self._explain_rule(target_data, audience, detail_level)
        elif explanation_type == "dispute":
            return self._explain_dispute(target_data, audience, detail_level)
        elif explanation_type == "policy":
            return self._explain_policy(target_data, audience, detail_level)
        else:
            return {
                "explanation_type": explanation_type,
                "summary": f"Explanation for {explanation_type}",
                "details": "No specific explanation available for this type.",
                "audience": audience,
                "detail_level": detail_level,
            }

    def _explain_action(
        self, action_data: dict[str, Any], audience: str, detail_level: str
    ) -> dict[str, Any]:
        """Explain a governance action."""
        action_type = action_data.get("action_type", "unknown")
        status = action_data.get("status", "unknown")
        reason = action_data.get("reason", "No reason provided")

        summary = f"A {action_type} action was taken and is currently {status}."
        details = f"The action was performed because: {reason}"

        if detail_level == "detailed":
            details += (
                f"\n\nTarget: {action_data.get('target_type', 'unknown')} "
                f"({action_data.get('target_id', 'unknown')})"
                f"\nActor: {action_data.get('actor_id', 'unknown')}"
                f"\nMetadata: {json.dumps(action_data.get('metadata', {}), indent=2)}"
            )

        return {
            "explanation_type": "action",
            "summary": summary,
            "details": details,
            "audience": audience,
            "detail_level": detail_level,
            "action_type": action_type,
            "status": status,
        }

    def _explain_rule(
        self, rule_data: dict[str, Any], audience: str, detail_level: str
    ) -> dict[str, Any]:
        """Explain a governance rule."""
        name = rule_data.get("name", "Unknown Rule")
        description = rule_data.get("description", "No description available")
        category = rule_data.get("category", "unknown")
        severity = rule_data.get("severity", "medium")

        summary = f"Rule '{name}' belongs to the {category} category with {severity} severity."
        details = description

        if detail_level == "detailed":
            conditions = rule_data.get("conditions", {})
            actions = rule_data.get("actions", [])
            details += f"\n\nConditions: {json.dumps(conditions, indent=2)}"
            if actions:
                details += f"\n\nActions on violation: {', '.join(actions)}"

        return {
            "explanation_type": "rule",
            "summary": summary,
            "details": details,
            "audience": audience,
            "detail_level": detail_level,
            "rule_name": name,
            "category": category,
            "severity": severity,
        }

    def _explain_dispute(
        self, dispute_data: dict[str, Any], audience: str, detail_level: str
    ) -> dict[str, Any]:
        """Explain a dispute resolution."""
        title = dispute_data.get("title", "Unknown Dispute")
        status = dispute_data.get("status", "unknown")
        resolution = dispute_data.get("resolution")

        summary = f"Dispute '{title}' is currently {status}."
        details = ""

        if resolution:
            details = (
                f"Resolution: {resolution.get('outcome', 'N/A')}\n"
                f"Rationale: {resolution.get('rationale', 'N/A')}"
            )
        else:
            details = "This dispute is still being processed."

        if detail_level == "detailed":
            details += (
                f"\n\nCategory: {dispute_data.get('category', 'unknown')}"
                f"\nPriority: {dispute_data.get('priority', 'unknown')}"
                f"\nInitiator: {dispute_data.get('initiator_id', 'unknown')}"
            )

        return {
            "explanation_type": "dispute",
            "summary": summary,
            "details": details,
            "audience": audience,
            "detail_level": detail_level,
            "dispute_title": title,
            "status": status,
        }

    def _explain_policy(
        self, policy_data: dict[str, Any], audience: str, detail_level: str
    ) -> dict[str, Any]:
        """Explain a governance policy."""
        name = policy_data.get("name", "Unknown Policy")
        description = policy_data.get("description", "No description available")
        status = policy_data.get("status", "unknown")
        scope = policy_data.get("scope", "unknown")

        summary = f"Policy '{name}' is {status} and applies to {scope} scope."
        details = description

        if detail_level == "detailed":
            guidelines = policy_data.get("guidelines", [])
            if guidelines:
                details += "\n\nKey Guidelines:"
                for guideline in guidelines:
                    details += f"\n- {guideline}"

        return {
            "explanation_type": "policy",
            "summary": summary,
            "details": details,
            "audience": audience,
            "detail_level": detail_level,
            "policy_name": name,
            "status": status,
            "scope": scope,
        }

    def _build_system_prompt(self, audience: str, detail_level: str) -> str:
        """Build the system prompt for the LLM."""
        audience_instructions = {
            "member": (
                "You are explaining governance decisions to community members. "
                "Use simple, friendly language. Avoid jargon. Focus on what the "
                "decision means for them."
            ),
            "moderator": (
                "You are explaining governance decisions to community moderators. "
                "Use professional language. Include relevant policy references and "
                "enforcement details."
            ),
            "admin": (
                "You are explaining governance decisions to administrators. "
                "Use technical language. Include all relevant details, metadata, "
                "and system-level information."
            ),
        }

        detail_instructions = {
            "brief": "Keep the explanation to 1-2 sentences.",
            "standard": "Provide a clear explanation with key details.",
            "detailed": "Provide a comprehensive explanation with all relevant details.",
        }

        base_prompt = (
            "You are a community governance explainer. Your job is to make "
            "governance decisions understandable to the target audience."
        )

        return (
            f"{base_prompt}\n\n"
            f"{audience_instructions.get(audience, audience_instructions['member'])}\n\n"
            f"{detail_instructions.get(detail_level, detail_instructions['standard'])}\n\n"
            "Respond with a JSON object containing: summary (string), details (string), "
            "and any additional relevant fields."
        )

    def _build_explanation_prompt(
        self, explanation_type: str, target_data: dict[str, Any]
    ) -> str:
        """Build the explanation prompt for the LLM."""
        return f"""Explain the following {explanation_type}:

{json.dumps(target_data, indent=2)}

Provide a clear, audience-appropriate explanation. Respond with JSON only."""

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the Governance Explainer Agent."""
        base_health = await super().health_check()
        base_health.update(
            {
                "supported_explanation_types": [
                    "action",
                    "rule",
                    "dispute",
                    "policy",
                ],
                "supported_audiences": ["member", "moderator", "admin"],
            }
        )
        return base_health

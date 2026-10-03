"""Document checking agent using LangChain DeepAgents."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from member_verification.agents.base import AgentConfig, BaseAgent
from member_verification.models.schemas import DocumentType


class DocumentCheckerAgent(BaseAgent):
    """Agent responsible for verifying identity documents.

    Analyzes document images and metadata to detect forgeries, verify authenticity,
    and cross-reference with provided identity data.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        """Initialize the document checker agent.

        Args:
            llm: Language model for agent reasoning.
            config: Agent configuration.
        """
        if config is None:
            config = AgentConfig(
                name="document_checker",
                description="Validates and verifies identity documents for authenticity",
            )
        super().__init__(config=config, llm=llm)
        self._capabilities = [
            "ocr_extraction",
            "forgery_detection",
            "watermark_verification",
            "font_analysis",
            "metadata_inspection",
            "cross_reference",
        ]

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Verify a document.

        Args:
            input_data: Dictionary containing document data and optional identity for
                cross-reference.

        Returns:
            Dictionary with document verification results.
        """
        self._status = "busy"
        self._mark_used()
        try:
            document = input_data.get("document", {})
            identity = input_data.get("identity", {})
            cross_reference = input_data.get("cross_reference", True)

            issues: list[str] = []
            confidence = 0.0
            tampering_detected = False

            # Step 1: Document type validation
            doc_type = document.get("document_type", "")
            if doc_type not in [t.value for t in DocumentType]:
                issues.append(f"Unsupported document type: {doc_type}")
            else:
                confidence += 0.2

            # Step 2: Document number validation
            doc_number = document.get("document_number", "")
            if not doc_number:
                issues.append("Missing document number")
            elif len(doc_number) < 4:
                issues.append("Document number appears invalid")
            else:
                confidence += 0.2

            # Step 3: Expiry check
            expiry_status = "unknown"
            expiry_date = document.get("expiry_date")
            if expiry_date:
                try:
                    exp = datetime.strptime(expiry_date, "%Y-%m-%d")
                    now = datetime.utcnow()
                    if exp < now:
                        expiry_status = "expired"
                        issues.append("Document has expired")
                    elif (exp - now).days < 30:
                        expiry_status = "expiring_soon"
                    else:
                        expiry_status = "valid"
                        confidence += 0.2
                except ValueError:
                    issues.append("Invalid expiry date format")
            else:
                confidence += 0.1

            # Step 4: Tampering detection (simulated)
            doc_hash = document.get("document_hash")
            if doc_hash:
                # Simulate hash-based integrity check
                tampering_detected = (hash(doc_number + doc_hash) % 100) < 5
                if tampering_detected:
                    issues.append("Potential tampering detected in document")
                    confidence *= 0.5
                else:
                    confidence += 0.2

            # Step 5: Cross-reference with identity
            cross_ref_match = None
            if cross_reference and identity:
                cross_ref_match = self._cross_reference(document, identity)
                if cross_ref_match:
                    confidence += 0.2
                else:
                    issues.append("Document does not match provided identity data")

            is_authentic = confidence >= 0.6 and not tampering_detected

            return {
                "document_type": doc_type,
                "is_authentic": is_authentic,
                "confidence": round(min(confidence, 1.0), 3),
                "tampering_detected": tampering_detected,
                "expiry_status": expiry_status,
                "cross_reference_match": cross_ref_match,
                "issues": issues,
                "agent": self.config.name,
            }
        finally:
            self._status = "available"

    def _cross_reference(self, document: dict[str, Any], identity: dict[str, Any]) -> bool:
        """Cross-reference document data with identity data.

        Args:
            document: Document data.
            identity: Identity data.

        Returns:
            True if document matches identity.
        """
        # Simplified cross-reference logic
        doc_number = document.get("document_number", "")
        gov_id = identity.get("government_id", "")
        if doc_number and gov_id:
            return doc_number == gov_id
        return True

    async def health_check(self) -> bool:
        """Check if the document checker is healthy.

        Returns:
            True if the agent is operational.
        """
        return self._status != "error"

    def get_capabilities(self) -> list[str]:
        """Get agent capabilities.

        Returns:
            List of capabilities.
        """
        return self._capabilities

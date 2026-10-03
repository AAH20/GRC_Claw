"""External service integrations."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, Field


class IntegrationConfig(BaseModel):
    """Configuration for external integrations."""

    base_url: str = Field(..., description="Base URL for the service")
    api_key: str | None = Field(default=None, description="API key for authentication")
    timeout: float = Field(default=10.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class BaseIntegration(ABC):
    """Abstract base class for external service integrations."""

    def __init__(self, config: IntegrationConfig) -> None:
        """Initialize the integration.

        Args:
            config: Integration configuration.
        """
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            Configured async HTTP client.
        """
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the integration is healthy.

        Returns:
            True if the integration is available.
        """
        ...


class IdentityProviderIntegration(BaseIntegration):
    """Integration with identity provider services."""

    async def verify_identity(self, identity_data: dict[str, Any]) -> dict[str, Any]:
        """Verify identity with external provider.

        Args:
            identity_data: Identity information to verify.

        Returns:
            Verification result from the provider.
        """
        client = await self._get_client()
        try:
            response = await client.post("/verify", json=identity_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return {"verified": False, "confidence": 0.0, "source": "fallback"}

    async def health_check(self) -> bool:
        """Check identity provider health.

        Returns:
            True if the provider is available.
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False


class DocumentVerificationIntegration(BaseIntegration):
    """Integration with document verification services."""

    async def verify_document(self, document_data: dict[str, Any]) -> dict[str, Any]:
        """Verify a document with external service.

        Args:
            document_data: Document information to verify.

        Returns:
            Document verification result.
        """
        client = await self._get_client()
        try:
            response = await client.post("/documents/verify", json=document_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return {
                "authentic": False,
                "confidence": 0.0,
                "tampering_detected": False,
                "source": "fallback",
            }

    async def health_check(self) -> bool:
        """Check document service health.

        Returns:
            True if the service is available.
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False


class FraudDatabaseIntegration(BaseIntegration):
    """Integration with fraud detection databases."""

    async def check_fraud_indicators(self, data: dict[str, Any]) -> dict[str, Any]:
        """Check for fraud indicators in external database.

        Args:
            data: Data to check against fraud database.

        Returns:
            Fraud indicators found.
        """
        client = await self._get_client()
        try:
            response = await client.post("/fraud/check", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return {"indicators": [], "risk_score": 0.0, "source": "fallback"}

    async def report_fraud(self, report: dict[str, Any]) -> bool:
        """Report a fraud case to the database.

        Args:
            report: Fraud report data.

        Returns:
            True if the report was submitted successfully.
        """
        client = await self._get_client()
        try:
            response = await client.post("/fraud/report", json=report)
            return response.status_code == 201
        except httpx.HTTPError:
            return False

    async def health_check(self) -> bool:
        """Check fraud database health.

        Returns:
            True if the database is available.
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False


def compute_document_hash(content: bytes) -> str:
    """Compute SHA-256 hash of document content.

    Args:
        content: Raw document bytes.

    Returns:
        Hex digest of the document hash.
    """
    return hashlib.sha256(content).hexdigest()

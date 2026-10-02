"""Integration Automation Agent - manages connections to n8n, Zapier, and Make."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class IntegrationProvider(StrEnum):
    """Supported integration providers."""

    N8N = "n8n"
    ZAPIER = "zapier"
    MAKE = "make"


class IntegrationStatus(StrEnum):
    """Integration connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    SYNCING = "syncing"


class IntegrationConfig(BaseModel):
    """Configuration for an integration."""

    provider: IntegrationProvider
    base_url: str = ""
    api_key: str = ""
    webhook_url: str = ""
    team_id: str = ""
    timeout_seconds: int = 30
    extra_config: dict[str, Any] = Field(default_factory=dict)


class IntegrationHealth(BaseModel):
    """Health status of an integration."""

    provider: IntegrationProvider
    status: IntegrationStatus
    last_sync: datetime | None = None
    last_error: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SyncRequest(BaseModel):
    """Request to sync data with an integration provider."""

    provider: IntegrationProvider
    sync_type: str = "full"  # full, incremental
    entity_types: list[str] = Field(default_factory=list)
    since: datetime | None = None


class SyncResult(BaseModel):
    """Result of a sync operation."""

    sync_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: IntegrationProvider
    status: str = "pending"  # pending, running, completed, failed
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    errors: list[str] = Field(default_factory=list)


@dataclass
class IntegrationAutomationAgent:
    """Agent responsible for managing integrations with external platforms.

    This agent handles connections, data synchronization, and health monitoring
    for n8n, Zapier, and Make integrations.
    """

    _configs: dict[str, IntegrationConfig] = field(default_factory=dict)
    _health: dict[str, IntegrationHealth] = field(default_factory=dict)
    _sync_history: dict[str, list[SyncResult]] = field(default_factory=dict)
    _is_initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the integration automation agent."""
        logger.info("Initializing IntegrationAutomationAgent")
        self._is_initialized = True

    async def configure_integration(self, config: IntegrationConfig) -> IntegrationConfig:
        """Configure an integration provider.

        Args:
            config: Integration configuration.

        Returns:
            The stored configuration.

        Raises:
            RuntimeError: If the agent is not initialized.
        """
        if not self._is_initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        self._configs[config.provider.value] = config

        # Initialize health status
        self._health[config.provider.value] = IntegrationHealth(
            provider=config.provider,
            status=IntegrationStatus.DISCONNECTED,
        )

        logger.info(
            "Configured integration",
            provider=config.provider.value,
            base_url=config.base_url,
        )

        return config

    async def check_health(self, provider: IntegrationProvider) -> IntegrationHealth:
        """Check the health of an integration.

        Args:
            provider: The integration provider to check.

        Returns:
            Current health status.

        Raises:
            RuntimeError: If the agent is not initialized.
            ValueError: If the provider is not configured.
        """
        if not self._is_initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        config = self._configs.get(provider.value)
        if not config:
            raise ValueError(f"Provider not configured: {provider.value}")

        logger.info("Checking integration health", provider=provider.value)

        try:
            # Attempt to connect to the provider
            is_connected = await self._ping_provider(config)

            health = IntegrationHealth(
                provider=provider,
                status=IntegrationStatus.CONNECTED if is_connected else IntegrationStatus.ERROR,
                last_sync=datetime.utcnow() if is_connected else None,
                metadata={"base_url": config.base_url},
            )

            self._health[provider.value] = health

            logger.info(
                "Integration health check completed",
                provider=provider.value,
                status=health.status.value,
            )

            return health

        except Exception as e:
            health = IntegrationHealth(
                provider=provider,
                status=IntegrationStatus.ERROR,
                last_error=str(e),
            )
            self._health[provider.value] = health

            logger.error(
                "Integration health check failed",
                provider=provider.value,
                error=str(e),
            )

            return health

    async def _ping_provider(self, config: IntegrationConfig) -> bool:
        """Ping an integration provider to check connectivity.

        Args:
            config: Integration configuration.

        Returns:
            True if the provider is reachable.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
                if config.provider == IntegrationProvider.N8N:
                    response = await client.get(f"{config.base_url}/healthz")
                elif config.provider == IntegrationProvider.MAKE:
                    response = await client.get(
                        f"{config.base_url}/api/v2/teams/{config.team_id}",
                        headers={"Authorization": f"Bearer {config.api_key}"},
                    )
                else:
                    # Zapier doesn't have a health endpoint, just check webhook URL
                    response = await client.get(config.webhook_url)

                return response.status_code < 500
        except Exception:
            return False

    async def sync(self, request: SyncRequest) -> SyncResult:
        """Synchronize data with an integration provider.

        Args:
            request: Sync request parameters.

        Returns:
            Sync result with details of the operation.

        Raises:
            RuntimeError: If the agent is not initialized.
            ValueError: If the provider is not configured.
        """
        if not self._is_initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        config = self._configs.get(request.provider.value)
        if not config:
            raise ValueError(f"Provider not configured: {request.provider.value}")

        result = SyncResult(provider=request.provider, status="running")

        logger.info(
            "Starting sync",
            provider=request.provider.value,
            sync_type=request.sync_type,
        )

        try:
            # Perform sync based on provider
            if request.provider == IntegrationProvider.N8N:
                sync_data = await self._sync_n8n(config, request)
            elif request.provider == IntegrationProvider.ZAPIER:
                sync_data = await self._sync_zapier(config, request)
            elif request.provider == IntegrationProvider.MAKE:
                sync_data = await self._sync_make(config, request)
            else:
                raise ValueError(f"Unsupported provider: {request.provider}")

            result.status = "completed"
            result.records_processed = sync_data.get("processed", 0)
            result.records_created = sync_data.get("created", 0)
            result.records_updated = sync_data.get("updated", 0)
            result.records_failed = sync_data.get("failed", 0)

            # Update health
            if request.provider.value in self._health:
                self._health[request.provider.value].last_sync = datetime.utcnow()
                self._health[request.provider.value].status = IntegrationStatus.CONNECTED

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            logger.error(
                "Sync failed",
                provider=request.provider.value,
                error=str(e),
            )

        result.completed_at = datetime.utcnow()

        # Store in history
        if request.provider.value not in self._sync_history:
            self._sync_history[request.provider.value] = []
        self._sync_history[request.provider.value].append(result)

        logger.info(
            "Sync completed",
            provider=request.provider.value,
            status=result.status,
            records_processed=result.records_processed,
        )

        return result

    async def _sync_n8n(
        self, config: IntegrationConfig, request: SyncRequest
    ) -> dict[str, int]:
        """Sync data with n8n.

        Args:
            config: n8n configuration.
            request: Sync request.

        Returns:
            Sync statistics.
        """
        import httpx

        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            headers = {"X-N8N-API-KEY": config.api_key}

            # Fetch workflows from n8n
            response = await client.get(
                f"{config.base_url}/api/v1/workflows", headers=headers
            )
            response.raise_for_status()
            workflows = response.json().get("data", [])

            return {
                "processed": len(workflows),
                "created": 0,
                "updated": len(workflows),
                "failed": 0,
            }

    async def _sync_zapier(
        self, config: IntegrationConfig, request: SyncRequest
    ) -> dict[str, int]:
        """Sync data with Zapier.

        Args:
            config: Zapier configuration.
            request: Sync request.

        Returns:
            Sync statistics.
        """
        # Zapier doesn't have a direct API for reading zaps
        # This would typically use webhooks or the Zapier Platform API
        logger.info("Zapier sync - webhook-based integration")

        return {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
        }

    async def _sync_make(
        self, config: IntegrationConfig, request: SyncRequest
    ) -> dict[str, int]:
        """Sync data with Make.

        Args:
            config: Make configuration.
            request: Sync request.

        Returns:
            Sync statistics.
        """
        import httpx

        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            headers = {"Authorization": f"Bearer {config.api_key}"}

            # Fetch scenarios from Make
            response = await client.get(
                f"{config.base_url}/api/v2/scenarios",
                headers=headers,
                params={"teamId": config.team_id},
            )
            response.raise_for_status()
            scenarios = response.json()

            return {
                "processed": len(scenarios),
                "created": 0,
                "updated": len(scenarios),
                "failed": 0,
            }

    async def get_sync_history(
        self, provider: IntegrationProvider, limit: int = 10
    ) -> list[SyncResult]:
        """Get sync history for a provider.

        Args:
            provider: The integration provider.
            limit: Maximum number of results to return.

        Returns:
            List of recent sync results.
        """
        history = self._sync_history.get(provider.value, [])
        return sorted(history, key=lambda r: r.started_at, reverse=True)[:limit]

    async def get_all_health(self) -> dict[str, IntegrationHealth]:
        """Get health status for all configured integrations.

        Returns:
            Dictionary mapping provider names to health status.
        """
        return dict(self._health)

    async def disconnect(self, provider: IntegrationProvider) -> bool:
        """Disconnect an integration.

        Args:
            provider: The integration provider to disconnect.

        Returns:
            True if disconnected successfully.
        """
        if provider.value in self._health:
            self._health[provider.value].status = IntegrationStatus.DISCONNECTED
            logger.info("Disconnected integration", provider=provider.value)
            return True
        return False

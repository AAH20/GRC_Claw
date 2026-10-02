"""GRC Marketing SDK — Python client library.

Provides a high-level, typed interface to the GRC Marketing API for managing
campaigns, leads, journeys, and analytics.
"""

from __future__ import annotations

from typing import Optional

from .analytics import AnalyticsClient
from .auth import Authenticator
from .campaigns import CampaignClient
from .client import APIClient
from .errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    GRCMarketingError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .journeys import JourneyClient
from .leads import LeadClient
from .types import (
    AnalyticsReport,
    AuthToken,
    Campaign,
    CampaignCreatePayload,
    CampaignStatus,
    CampaignUpdatePayload,
    Channel,
    Journey,
    JourneyCreatePayload,
    JourneyStatus,
    JourneyUpdatePayload,
    Lead,
    LeadCreatePayload,
    LeadStatus,
    LeadUpdatePayload,
)

__version__ = "1.0.0"
__all__ = [
    "GRCMarketing",
    "Authenticator",
    "APIClient",
    "CampaignClient",
    "LeadClient",
    "JourneyClient",
    "AnalyticsClient",
    "Campaign",
    "Lead",
    "Journey",
    "AnalyticsReport",
    "AuthToken",
    "CampaignStatus",
    "LeadStatus",
    "JourneyStatus",
    "Channel",
    "CampaignCreatePayload",
    "CampaignUpdatePayload",
    "LeadCreatePayload",
    "LeadUpdatePayload",
    "JourneyCreatePayload",
    "JourneyUpdatePayload",
    "GRCMarketingError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "TimeoutError",
    "ConfigurationError",
]


class GRCMarketing:
    """Main entry point for the GRC Marketing SDK.

    Provides authenticated access to campaigns, leads, journeys, and analytics.

    Example:
        >>> from grc_marketing import GRCMarketing
        >>> sdk = GRCMarketing(base_url="https://api.grc.example.com", api_key="your-key")
        >>> sdk.authenticate()
        >>> campaigns = sdk.campaigns.list()
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the GRC Marketing SDK.

        Args:
            base_url: The base URL of the GRC Marketing API.
            api_key: API key for key-based authentication.
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret.
            token_url: OAuth2 token endpoint URL.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for transient errors.
        """
        self.authenticator = Authenticator(
            base_url=base_url,
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            timeout=timeout,
        )
        self._api_client = APIClient(
            base_url=base_url,
            authenticator=self.authenticator,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.campaigns = CampaignClient(self._api_client)
        self.leads = LeadClient(self._api_client)
        self.journeys = JourneyClient(self._api_client)
        self.analytics = AnalyticsClient(self._api_client)

    def authenticate(self) -> AuthToken:
        """Authenticate with the configured credentials.

        Uses API key if provided, otherwise OAuth2 client credentials.

        Returns:
            The authentication token.

        Raises:
            ConfigurationError: If no credentials are configured.
            AuthenticationError: If authentication fails.
        """
        if self.authenticator.api_key:
            return self.authenticator.authenticate_api_key(self.authenticator.api_key)
        if self.authenticator.client_id and self.authenticator.client_secret:
            return self.authenticator.authenticate_oauth2()
        raise ConfigurationError(
            message="No credentials configured. Provide api_key or client_id/client_secret."
        )

    def is_authenticated(self) -> bool:
        """Check if the SDK has a valid authentication token."""
        return self.authenticator.is_authenticated()

    def logout(self) -> None:
        """Clear the current authentication token."""
        self.authenticator.logout()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._api_client.close()

    def __enter__(self) -> GRCMarketing:
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()

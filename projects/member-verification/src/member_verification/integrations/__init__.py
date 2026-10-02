"""Integrations module for member verification service."""

from member_verification.integrations.external import (
    BaseIntegration,
    DocumentVerificationIntegration,
    FraudDatabaseIntegration,
    IdentityProviderIntegration,
    IntegrationConfig,
    compute_document_hash,
)

__all__ = [
    "BaseIntegration",
    "DocumentVerificationIntegration",
    "FraudDatabaseIntegration",
    "IdentityProviderIntegration",
    "IntegrationConfig",
    "compute_document_hash",
]

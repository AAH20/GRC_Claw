"""API routes module for member verification service."""

from member_verification.api.routes import agents, documents, fraud, health, trust, verification

__all__ = [
    "agents",
    "documents",
    "fraud",
    "health",
    "trust",
    "verification",
]

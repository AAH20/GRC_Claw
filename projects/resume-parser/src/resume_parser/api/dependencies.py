"""API dependencies for FastAPI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from fastapi import Request

    from resume_parser.config import Settings
    from resume_parser.integrations import BaseLLMClient
    from resume_parser.integrations.storage import BaseStorage

logger = structlog.get_logger(__name__)


def get_llm_client(request: Request) -> BaseLLMClient:
    """Get LLM client from app state.

    Args:
        request: FastAPI request object.

    Returns:
        BaseLLMClient: LLM client instance.
    """
    return request.app.state.llm_client


def get_storage(request: Request) -> BaseStorage:
    """Get storage backend from app state.

    Args:
        request: FastAPI request object.

    Returns:
        BaseStorage: Storage backend instance.
    """
    return request.app.state.storage


def get_settings_from_request(request: Request) -> Settings:
    """Get settings from app state.

    Args:
        request: FastAPI request object.

    Returns:
        Settings: Application settings.
    """
    return request.app.state.settings

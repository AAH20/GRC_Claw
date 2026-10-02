"""Custom exceptions for candidate-matcher."""

from __future__ import annotations


class CandidateMatcherError(Exception):
    """Base exception for all candidate-matcher errors."""


class AgentExecutionError(CandidateMatcherError):
    """Raised when an agent fails to execute."""

    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        super().__init__(f"Agent '{agent_name}' failed: {message}")


class LLMConnectionError(CandidateMatcherError):
    """Raised when LLM service is unreachable."""


class EmbeddingError(CandidateMatcherError):
    """Raised when embedding generation fails."""


class VectorStoreError(CandidateMatcherError):
    """Raised when vector store operation fails."""


class ValidationError(CandidateMatcherError):
    """Raised when input validation fails."""


class ResourceNotFoundError(CandidateMatcherError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with id '{resource_id}' not found")


class RateLimitError(CandidateMatcherError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class ConfigurationError(CandidateMatcherError):
    """Raised when there is a configuration error."""

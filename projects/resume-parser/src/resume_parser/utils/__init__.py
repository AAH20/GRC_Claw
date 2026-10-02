"""Custom exceptions for resume-parser service."""

from __future__ import annotations


class ResumeParserError(Exception):
    """Base exception for resume parser errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error message.
            details: Optional error details dictionary.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FileParseError(ResumeParserError):
    """Raised when a resume file cannot be parsed."""


class UnsupportedFileTypeError(ResumeParserError):
    """Raised when an unsupported file type is encountered."""

    def __init__(self, file_type: str, supported: list[str] | None = None) -> None:
        """Initialize the error.

        Args:
            file_type: The unsupported file type.
            supported: List of supported file types.
        """
        supported = supported or [".pdf", ".docx", ".txt"]
        super().__init__(
            f"Unsupported file type: {file_type}. Supported: {', '.join(supported)}",
            {"file_type": file_type, "supported": supported},
        )


class FileTooLargeError(ResumeParserError):
    """Raised when a file exceeds the maximum allowed size."""

    def __init__(self, size_bytes: int, max_size_bytes: int) -> None:
        """Initialize the error.

        Args:
            size_bytes: Actual file size in bytes.
            max_size_bytes: Maximum allowed size in bytes.
        """
        super().__init__(
            f"File too large: {size_bytes} bytes (max: {max_size_bytes} bytes)",
            {"size_bytes": size_bytes, "max_size_bytes": max_size_bytes},
        )


class AgentExecutionError(ResumeParserError):
    """Raised when an agent fails to execute."""

    def __init__(self, agent_name: str, reason: str) -> None:
        """Initialize the error.

        Args:
            agent_name: Name of the agent that failed.
            reason: Reason for the failure.
        """
        super().__init__(
            f"Agent '{agent_name}' failed: {reason}",
            {"agent_name": agent_name, "reason": reason},
        )


class LLMError(ResumeParserError):
    """Raised when the LLM service returns an error."""


class StorageError(ResumeParserError):
    """Raised when a storage operation fails."""


class ValidationError(ResumeParserError):
    """Raised when input validation fails."""

    def __init__(self, field: str, reason: str) -> None:
        """Initialize the error.

        Args:
            field: The field that failed validation.
            reason: Reason for the validation failure.
        """
        super().__init__(
            f"Validation error on '{field}': {reason}",
            {"field": field, "reason": reason},
        )


class ResumeNotFoundError(ResumeParserError):
    """Raised when a resume is not found in storage."""

    def __init__(self, resume_id: str) -> None:
        """Initialize the error.

        Args:
            resume_id: The resume ID that was not found.
        """
        super().__init__(
            f"Resume not found: {resume_id}",
            {"resume_id": resume_id},
        )

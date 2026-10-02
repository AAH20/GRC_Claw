"""Custom exceptions for the Sales Forecaster."""


class SalesForecasterError(Exception):
    """Base exception for all Sales Forecaster errors."""


class ConfigurationError(SalesForecasterError):
    """Raised when there is a configuration problem."""


class IntegrationError(SalesForecasterError):
    """Raised when an external integration fails."""

    def __init__(self, message: str, source: str = "", status_code: int | None = None) -> None:
        super().__init__(message)
        self.source = source
        self.status_code = status_code


class DataCollectionError(IntegrationError):
    """Raised when data collection from a source fails."""


class AnalysisError(SalesForecasterError):
    """Raised when the analysis agent encounters an error."""


class PredictionError(SalesForecasterError):
    """Raised when the prediction agent encounters an error."""


class PipelineError(SalesForecasterError):
    """Raised when the pipeline execution fails."""


class ValidationError(SalesForecasterError):
    """Raised when input validation fails."""


class AuthenticationError(IntegrationError):
    """Raised when authentication with an external system fails."""


class RateLimitError(IntegrationError):
    """Raised when an external API rate limit is hit."""

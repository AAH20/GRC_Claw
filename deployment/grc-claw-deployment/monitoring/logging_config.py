"""
GRC_Claw Structured Logging Configuration
==========================================
Unified structured logging for all GRC_Claw Python services.
Outputs JSON-formatted logs compatible with Loki/Promtail pipeline.

Usage:
    from logging_config import setup_logging
    logger = setup_logging(service_name="pdp-service")
    logger.info("Policy decision made", extra={"decision_id": "abc-123", "outcome": "allow"})
"""

import json
import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ── Constants ──────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv("GRC_CLAW_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("GRC_CLAW_LOG_FORMAT", "json")  # json | text
LOG_OUTPUT = os.getenv("GRC_CLAW_LOG_OUTPUT", "stdout")  # stdout | file | both
LOG_FILE_PATH = os.getenv("GRC_CLAW_LOG_FILE", "/var/log/grc-claw/app.log")
LOG_MAX_BYTES = int(os.getenv("GRC_CLAW_LOG_MAX_BYTES", str(50 * 1024 * 1024)))  # 50MB
LOG_BACKUP_COUNT = int(os.getenv("GRC_CLAW_LOG_BACKUP_COUNT", "5"))

# Fields that should be excluded from structured output
_RESERVED_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "asctime", "taskName",
})


# ── JSON Formatter ─────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for Loki/Promtail ingestion."""

    def __init__(self, service_name: str, environment: str):
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": self.service_name,
            "environment": self.environment,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stacktrace": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                # Handle non-serializable objects
                try:
                    json.dumps(value)
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for local development."""

    def __init__(self, service_name: str, environment: str):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self._fmt = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            f"service={self.service_name} env={self.environment} | %(message)s"
        )

    def format(self, record: logging.LogRecord) -> str:
        formatter = logging.Formatter(self._fmt, datefmt="%Y-%m-%dT%H:%M:%S%z")
        return formatter.format(record)


# ── Logger Setup ───────────────────────────────────────────────────────────

def setup_logging(
    service_name: str,
    environment: Optional[str] = None,
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_output: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a structured logger for a GRC_Claw service.

    Args:
        service_name: Name of the service (e.g., "pdp-service", "pep-gateway")
        environment: Deployment environment (e.g., "production", "staging")
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Override format ("json" or "text")
        log_output: Override output ("stdout", "file", or "both")

    Returns:
        Configured logger instance
    """
    env = environment or os.getenv("GRC_CLAW_ENV", "development")
    level = (log_level or LOG_LEVEL).upper()
    fmt = (log_format or LOG_FORMAT).lower()
    output = (log_output or LOG_OUTPUT).lower()

    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.propagate = False

    # Clear existing handlers to avoid duplicates on reconfiguration
    logger.handlers.clear()

    # Choose formatter
    if fmt == "json":
        formatter: logging.Formatter = JSONFormatter(service_name, env)
    else:
        formatter = TextFormatter(service_name, env)

    # Stdout handler
    if output in ("stdout", "both"):
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    # File handler with rotation
    if output in ("file", "both"):
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(service_name: str) -> logging.Logger:
    """Get or create a logger for the given service name."""
    return logging.getLogger(service_name)


# ── Request Context Logging ─────────────────────────────────────────────────

class RequestContextFilter(logging.Filter):
    """Injects request context (trace_id, span_id, tenant_id) into log records."""

    def __init__(self):
        super().__init__()
        self._context = {}

    def set_context(self, **kwargs):
        self._context.update(kwargs)

    def clear_context(self):
        self._context.clear()

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in self._context.items():
            setattr(record, key, value)
        return True


# Global context filter instance
request_context = RequestContextFilter()


def bind_request_context(logger: logging.Logger, **context):
    """Bind request-scoped context to a logger."""
    logger.addFilter(request_context)
    request_context.set_context(**context)


def unbind_request_context(logger: logging.Logger):
    """Remove request-scoped context from a logger."""
    request_context.clear_context()
    logger.removeFilter(request_context)


# ── Service-Specific Loggers ───────────────────────────────────────────────

SERVICE_LOGGERS: Dict[str, logging.Logger] = {}


def get_service_logger(service_name: str) -> logging.Logger:
    """Get or create a service-specific logger with standard configuration."""
    if service_name not in SERVICE_LOGGERS:
        SERVICE_LOGGERS[service_name] = setup_logging(service_name)
    return SERVICE_LOGGERS[service_name]


# ── Initialization ──────────────────────────────────────────────────────────

def initialize_all_loggers():
    """Initialize loggers for all known GRC_Claw services."""
    services = [
        "pdp-service",
        "pep-gateway",
        "policy-api",
        "evidence-collector",
        "audit-service",
        "compliance-engine",
        "enforcement-service",
        "webhook-dispatcher",
        "grpc-server",
        "graphql-api",
    ]
    for service in services:
        get_service_logger(service)


# ── Main (for testing) ──────────────────────────────────────────────────────

if __name__ == "__main__":
    logger = setup_logging("test-service", environment="development", log_format="text")
    logger.info("Logging system initialized", extra={"version": "1.0.0"})
    logger.warning("This is a warning", extra={"component": "test"})
    try:
        raise ValueError("Something went wrong")
    except ValueError:
        logger.exception("An error occurred", extra={"error_code": "E001"})

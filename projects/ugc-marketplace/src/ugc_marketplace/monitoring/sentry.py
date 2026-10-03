"""Sentry integration for UGC Marketplace."""

from __future__ import annotations

from typing import Any

from ugc_marketplace.config import get_settings
from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)
_sentry_initialized = False


def init_sentry(dsn: str | None = None, **kwargs: Any) -> bool:
    """Initialize Sentry SDK."""
    global _sentry_initialized
    settings = get_settings()
    dsn = dsn or getattr(settings, "sentry_dsn", None)
    if not dsn:
        logger.debug("Sentry DSN not configured, skipping initialization")
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=settings.app_env,
            release=kwargs.get("release"),
            traces_sample_rate=kwargs.get("traces_sample_rate", 0.1),
            profiles_sample_rate=kwargs.get("profiles_sample_rate", 0.1),
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            send_default_pii=False,
            before_send=kwargs.get("before_send"),
        )
        _sentry_initialized = True
        logger.info("Sentry initialized", environment=settings.app_env)
        return True
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry initialization")
        return False
    except Exception as exc:
        logger.error("Failed to initialize Sentry", error=str(exc))
        return False


def get_sentry() -> Any:
    """Get Sentry SDK module."""
    try:
        import sentry_sdk

        return sentry_sdk
    except ImportError:
        return None


def capture_exception(exc: Exception, **context: Any) -> None:
    """Capture exception in Sentry."""
    sentry = get_sentry()
    if sentry and _sentry_initialized:
        with sentry.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            sentry.capture_exception(exc)


def capture_message(message: str, level: str = "info", **context: Any) -> None:
    """Capture message in Sentry."""
    sentry = get_sentry()
    if sentry and _sentry_initialized:
        with sentry.push_scope() as scope:
            scope.set_level(level)
            for key, value in context.items():
                scope.set_extra(key, value)
            sentry.capture_message(message)

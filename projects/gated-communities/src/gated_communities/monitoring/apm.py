"""OpenTelemetry APM integration."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def init_tracing(app: Any) -> None:
    """Initialize OpenTelemetry tracing."""
    if not os.getenv("TRACING_ENABLED", "false").lower() == "true":
        logger.info("Tracing not enabled, skipping initialization")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": "gated-communities",
                "service.version": os.getenv("APP_VERSION", "1.0.0"),
                "deployment.environment": os.getenv("ENVIRONMENT", "production"),
            }
        )

        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(OTLPSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry tracing initialized successfully")
    except ImportError:
        logger.warning("opentelemetry not installed, skipping initialization")
    except Exception as e:
        logger.error("Failed to initialize tracing", error=str(e))


def get_tracer(name: str) -> Any:
    """Get a tracer instance."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return None

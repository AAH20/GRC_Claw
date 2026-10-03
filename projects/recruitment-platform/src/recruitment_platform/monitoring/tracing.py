"""Distributed tracing module."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from opentelemetry import trace

logger = logging.getLogger(__name__)

try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    def setup_tracing(
        service_name: str = "recruitment-platform", jaeger_host: str = "localhost"
    ) -> trace.Tracer:
        """Initialize distributed tracing with Jaeger."""
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=6831,
        )

        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        trace.set_tracer_provider(provider)

        return trace.get_tracer(service_name)

    tracer = setup_tracing()
except ImportError:
    logger.warning("OpenTelemetry Jaeger exporter not available, using no-op tracer")

    def setup_tracing(
        service_name: str = "recruitment-platform", jaeger_host: str = "localhost"
    ) -> trace.Tracer:
        """Fallback no-op tracing setup."""
        return trace.get_tracer(service_name)

    tracer = setup_tracing()


@asynccontextmanager
async def trace_span(name: str, attributes: dict[str, Any] | None = None):
    """Context manager for creating trace spans."""
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span

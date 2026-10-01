"""
GRC_Claw Distributed Tracing Setup (OpenTelemetry)
==================================================
Configures OpenTelemetry tracing for all GRC_Claw Python services.
Exports traces to the OTel Collector which forwards to Tempo.

Usage:
    from tracing_setup import setup_tracing
    tracer = setup_tracing(service_name="pdp-service")

    with tracer.start_as_current_span("evaluate_policy") as span:
        span.set_attribute("policy.id", policy_id)
        span.set_attribute("decision", "allow")
"""

import os
from contextlib import contextmanager
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


# ── Configuration ───────────────────────────────────────────────────────────

OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv(
    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"
)
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "grc-claw-service")
OTEL_ENVIRONMENT = os.getenv("GRC_CLAW_ENV", "production")
OTEL_TRACES_SAMPLER = os.getenv("OTEL_TRACES_SAMPLER", "parentbased_traceidratio")
OTEL_TRACES_SAMPLER_ARG = float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "0.1"))
OTEL_EXPORT_TIMEOUT = int(os.getenv("OTEL_EXPORT_TIMEOUT", "30"))

# Standard GRC_Claw resource attributes
GRC_CLAW_RESOURCE_ATTRIBUTES = {
    "service.name": OTEL_SERVICE_NAME,
    "service.version": os.getenv("GRC_CLAW_VERSION", "1.0.0"),
    "service.namespace": "grc-claw",
    "deployment.environment": OTEL_ENVIRONMENT,
    "cluster": "grc-claw-production",
    "region": os.getenv("AWS_REGION", "us-east-1"),
}


# ── Tracing Setup ───────────────────────────────────────────────────────────

_tracer_provider: Optional[TracerProvider] = None


def setup_tracing(
    service_name: Optional[str] = None,
    environment: Optional[str] = None,
    sampler_rate: Optional[float] = None,
) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing for a GRC_Claw service.

    Args:
        service_name: Override the service name (defaults to OTEL_SERVICE_NAME)
        environment: Override the environment (defaults to GRC_CLAW_ENV)
        sampler_rate: Trace sampling ratio 0.0-1.0 (defaults to 0.1)

    Returns:
        OpenTelemetry Tracer instance
    """
    global _tracer_provider

    if _tracer_provider is not None:
        return _tracer_provider.get_tracer(service_name or OTEL_SERVICE_NAME)

    # Build resource
    resource_attrs = dict(GRC_CLAW_RESOURCE_ATTRIBUTES)
    if service_name:
        resource_attrs["service.name"] = service_name
    if environment:
        resource_attrs["deployment.environment"] = environment

    resource = Resource.create(resource_attrs)

    # Configure sampler
    from opentelemetry.sdk.trace.sampling import (
        ParentBasedTraceIdRatio,
        TraceIdRatioBased,
        ALWAYS_ON,
        ALWAYS_OFF,
    )

    rate = sampler_rate if sampler_rate is not None else OTEL_TRACES_SAMPLER_ARG
    if OTEL_TRACES_SAMPLER == "always_on":
        sampler = ALWAYS_ON
    elif OTEL_TRACES_SAMPLER == "always_off":
        sampler = ALWAYS_OFF
    elif OTEL_TRACES_SAMPLER == "traceidratio":
        sampler = TraceIdRatioBased(rate)
    else:
        sampler = ParentBasedTraceIdRatio(rate)

    # Create provider
    _tracer_provider = TracerProvider(
        resource=resource,
        sampler=sampler,
    )

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=OTEL_EXPORTER_OTLP_ENDPOINT,
        timeout=OTEL_EXPORT_TIMEOUT,
        insecure=True,
    )
    _tracer_provider.add_span_processor(
        BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            schedule_delay_millis=5000,
        )
    )

    # Set global propagator (W3C Trace Context + Baggage)
    set_global_textmap(
        CompositePropagator([
            TraceContextTextMapPropagator(),
            W3CBaggagePropagator(),
        ])
    )

    trace.set_tracer_provider(_tracer_provider)

    return _tracer_provider.get_tracer(service_name or OTEL_SERVICE_NAME)


def get_tracer(service_name: Optional[str] = None) -> trace.Tracer:
    """Get the tracer for a service, initializing if needed."""
    if _tracer_provider is None:
        return setup_tracing(service_name)
    return _tracer_provider.get_tracer(service_name or OTEL_SERVICE_NAME)


def shutdown_tracing():
    """Flush and shutdown the tracer provider."""
    global _tracer_provider
    if _tracer_provider is not None:
        _tracer_provider.shutdown()
        _tracer_provider = None


# ── Decorator for Automatic Span Creation ───────────────────────────────────

def trace_operation(
    operation_name: Optional[str] = None,
    attributes: Optional[dict] = None,
    record_exception: bool = True,
):
    """
    Decorator that automatically creates a span for the decorated function.

    Usage:
        @trace_operation("evaluate_policy", attributes={"policy.type": "rbac"})
        def evaluate_policy(request):
            ...
    """
    def decorator(func):
        tracer = get_tracer()
        span_name = operation_name or f"{func.__module__}.{func.__name__}"

        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                # Set initial attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Set function metadata
                span.set_attribute("code.function", func.__name__)
                span.set_attribute("code.namespace", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as exc:
                    if record_exception:
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR, str(exc)))
                    raise

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


# ── Context Manager for Manual Span Creation ────────────────────────────────

@contextmanager
def start_span(
    name: str,
    attributes: Optional[dict] = None,
    kind: Optional[trace.SpanKind] = None,
):
    """
    Context manager for creating spans with automatic error handling.

    Usage:
        with start_span("database_query", attributes={"db.system": "postgresql"}):
            result = db.execute(query)
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


# ── Service-Specific Instrumentation Helpers ─────────────────────────────────

def instrument_fastapi(app, service_name: str):
    """Instrument a FastAPI application with OpenTelemetry."""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    setup_tracing(service_name)
    FastAPIInstrumentor.instrument_app(app)


def instrument_grpc_server(server, service_name: str):
    """Instrument a gRPC server with OpenTelemetry."""
    from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
    setup_tracing(service_name)
    GrpcInstrumentorServer().instrument()


def instrument_sqlalchemy(engine, service_name: str):
    """Instrument SQLAlchemy engine with OpenTelemetry."""
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    setup_tracing(service_name)
    SQLAlchemyInstrumentor().instrument(engine=engine)


def instrument_redis(client, service_name: str):
    """Instrument Redis client with OpenTelemetry."""
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    setup_tracing(service_name)
    RedisInstrumentor().instrument()


def instrument_requests(session, service_name: str):
    """Instrument requests session with OpenTelemetry."""
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    setup_tracing(service_name)
    RequestsInstrumentor().instrument()


# ── Initialization ───────────────────────────────────────────────────────────

def initialize_all_tracing():
    """Initialize tracing for all known GRC_Claw services."""
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
        setup_tracing(service)


# ── Main (for testing) ──────────────────────────────────────────────────────

if __name__ == "__main__":
    tracer = setup_tracing("test-service", environment="development")

    with start_span("test_operation", attributes={"test.key": "test_value"}) as span:
        span.set_attribute("custom.attribute", "hello")
        print("Trace span created successfully")

    shutdown_tracing()
    print("Tracing shutdown complete")

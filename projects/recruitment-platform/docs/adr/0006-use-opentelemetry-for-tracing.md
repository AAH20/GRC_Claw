# ADR 0006: Use OpenTelemetry for Distributed Tracing

## Status
Accepted

## Context
The platform's distributed architecture requires end-to-end request tracing for debugging and performance monitoring.

## Decision
Use OpenTelemetry with Jaeger exporter for distributed tracing, with probabilistic sampling.

## Consequences
- Standardized tracing across services
- Probabilistic sampling balances overhead and visibility
- Jaeger UI enables trace visualization

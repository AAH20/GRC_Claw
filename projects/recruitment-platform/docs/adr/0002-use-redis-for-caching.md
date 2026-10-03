# ADR 0002: Use Redis for Caching

## Status
Accepted

## Context
The platform needs a distributed caching layer for session storage, rate limiting, and query result caching.

## Decision
Use Redis as the primary caching backend with connection pooling and automatic serialization.

## Consequences
- Fast in-memory caching reduces database load
- Distributed cache supports multi-instance deployments
- TTL support enables automatic cache invalidation

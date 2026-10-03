# ADR 0003: Use Celery for Background Tasks

## Status
Accepted

## Context
Long-running tasks like resume parsing, candidate matching, and report generation should not block API responses.

## Decision
Use Celery with Redis as the message broker for asynchronous task processing.

## Consequences
- Non-blocking API responses improve user experience
- Task retries with exponential backoff improve reliability
- Worker scaling is independent of API scaling

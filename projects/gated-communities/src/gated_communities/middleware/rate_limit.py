"""Rate limiting middleware."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm."""

    def __init__(
        self,
        app: Any,
        requests_per_minute: int = 100,
        burst_size: int = 10,
    ) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.clients: dict[str, dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if client_ip not in self.clients:
            self.clients[client_ip] = {
                "tokens": self.burst_size,
                "last_update": now,
            }

        client = self.clients[client_ip]
        time_passed = now - client["last_update"]
        client["tokens"] = min(
            self.burst_size,
            client["tokens"] + time_passed * (self.requests_per_minute / 60),
        )
        client["last_update"] = now

        if client["tokens"] < 1:
            logger.warning("rate_limit_exceeded", client_ip=client_ip)
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        client["tokens"] -= 1
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(client["tokens"]))
        return response

"""Laya integration for model routing.

Provides a client for the Laya model gateway, enabling seamless
integration with the routing system for multi-provider model access.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


@dataclass
class LayaConfig:
    """Configuration for Laya API connection.

    Attributes:
        api_key: Laya API key for authentication.
        base_url: Laya API base URL.
        timeout_seconds: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        retry_delay_seconds: Delay between retries in seconds.
        default_model: Default model to use if none specified.
        enable_caching: Whether to enable response caching.
    """

    api_key: str
    base_url: str = "https://api.laya.ai/v1"
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    default_model: str = "auto"
    enable_caching: bool = True


@dataclass
class LayaResponse:
    """Structured response from Laya API.

    Attributes:
        content: The generated text content.
        model: The model that generated the response.
        usage: Token usage statistics.
        metadata: Additional response metadata.
        latency_ms: Request latency in milliseconds.
        cached: Whether the response was served from cache.
    """

    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    cached: bool = False


class LayaError(Exception):
    """Base exception for Laya integration errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        """Initialize LayaError.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message)
        self.status_code = status_code


class LayaAuthenticationError(LayaError):
    """Raised when authentication with Laya fails."""

    pass


class LayaRateLimitError(LayaError):
    """Raised when Laya rate limit is exceeded."""

    pass


class LayaClient:
    """Client for the Laya model gateway API.

    Provides a unified interface for making requests to various
    models through the Laya gateway, with retry logic, caching,
    and error handling.

    Example:
        >>> config = LayaConfig(api_key="sk-...")
        >>> client = LayaClient(config)
        >>> response = client.generate("Hello, world!")
        >>> print(response.content)
    """

    def __init__(self, config: LayaConfig) -> None:
        """Initialize the Laya client.

        Args:
            config: Laya configuration.
        """
        self._config = config
        self._cache: Dict[str, LayaResponse] = {}
        self._session_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "cache_hits": 0,
            "errors": 0,
        }

    @property
    def config(self) -> LayaConfig:
        """Get the client configuration.

        Returns:
            The Laya configuration.
        """
        return self._config

    @property
    def stats(self) -> Dict[str, Union[int, float]]:
        """Get session statistics.

        Returns:
            Dictionary of session statistics.
        """
        return dict(self._session_stats)

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_message: Optional[str] = None,
        use_cache: Optional[bool] = None,
    ) -> LayaResponse:
        """Generate a completion through Laya.

        Args:
            prompt: The prompt to send.
            model: Model to use. Uses config default if None.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            system_message: Optional system message.
            use_cache: Override config caching setting.

        Returns:
            LayaResponse with the generated content.

        Raises:
            LayaError: If the request fails after all retries.
            LayaAuthenticationError: If authentication fails.
            LayaRateLimitError: If rate limit is exceeded.
        """
        target_model = model or self._config.default_model
        should_cache = use_cache if use_cache is not None else self._config.enable_caching

        # Check cache
        if should_cache:
            cache_key = self._make_cache_key(prompt, target_model, temperature)
            if cache_key in self._cache:
                self._session_stats["cache_hits"] += 1
                cached = self._cache[cache_key]
                logger.debug("Cache hit for key: %s", cache_key[:16])
                return LayaResponse(
                    content=cached.content,
                    model=cached.model,
                    usage=cached.usage,
                    metadata={**cached.metadata, "cache_hit": True},
                    latency_ms=0.0,
                    cached=True,
                )

        # Build request
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": [],
            "temperature": temperature,
        }

        if system_message:
            payload["messages"].append({
                "role": "system",
                "content": system_message,
            })

        payload["messages"].append({
            "role": "user",
            "content": prompt,
        })

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Execute with retries
        start_time = time.time()
        last_error: Optional[Exception] = None

        for attempt in range(self._config.max_retries):
            try:
                response = self._execute_request(payload)
                latency_ms = (time.time() - start_time) * 1000

                result = LayaResponse(
                    content=response["content"],
                    model=response.get("model", target_model),
                    usage=response.get("usage", {}),
                    metadata=response.get("metadata", {}),
                    latency_ms=latency_ms,
                )

                # Update stats
                self._session_stats["total_requests"] += 1
                self._session_stats["total_tokens"] += result.usage.get("total_tokens", 0)

                # Cache if enabled
                if should_cache:
                    self._cache[cache_key] = result

                return result

            except LayaAuthenticationError:
                raise  # Don't retry auth errors
            except LayaRateLimitError as exc:
                last_error = exc
                wait_time = self._config.retry_delay_seconds * (2 ** attempt)
                logger.warning(
                    "Rate limited, waiting %.1fs (attempt %d/%d)",
                    wait_time, attempt + 1, self._config.max_retries,
                )
                time.sleep(wait_time)
            except LayaError as exc:
                last_error = exc
                if attempt < self._config.max_retries - 1:
                    time.sleep(self._config.retry_delay_seconds)

        self._session_stats["errors"] += 1
        raise LayaError(
            f"Request failed after {self._config.max_retries} attempts: {last_error}"
        )

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models from Laya.

        Returns:
            List of model information dictionaries.

        Raises:
            LayaError: If the request fails.
        """
        try:
            response = self._execute_request({}, endpoint="/models")
            return response.get("models", [])
        except LayaError:
            raise
        except Exception as exc:
            raise LayaError(f"Failed to list models: {exc}") from exc

    def health_check(self) -> bool:
        """Check if the Laya API is reachable.

        Returns:
            True if the API is healthy, False otherwise.
        """
        try:
            self._execute_request({}, endpoint="/health")
            return True
        except Exception:
            return False

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()
        logger.info("Laya response cache cleared")

    def _execute_request(
        self,
        payload: Dict[str, Any],
        endpoint: str = "/chat/completions",
    ) -> Dict[str, Any]:
        """Execute an HTTP request to the Laya API.

        Args:
            payload: The request payload.
            endpoint: API endpoint path.

        Returns:
            Parsed JSON response.

        Raises:
            LayaAuthenticationError: If authentication fails.
            LayaRateLimitError: If rate limit is exceeded.
            LayaError: For other request failures.
        """
        url = f"{self._config.base_url}{endpoint}"
        data = json.dumps(payload).encode("utf-8")

        request = Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._config.api_key}",
            },
        )

        try:
            with urlopen(request, timeout=self._config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except HTTPError as exc:
            if exc.code == 401:
                raise LayaAuthenticationError("Invalid API key", status_code=401)
            elif exc.code == 429:
                raise LayaRateLimitError("Rate limit exceeded", status_code=429)
            else:
                raise LayaError(
                    f"HTTP {exc.code}: {exc.reason}",
                    status_code=exc.code,
                )
        except URLError as exc:
            raise LayaError(f"Connection failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise LayaError(f"Invalid JSON response: {exc}") from exc

    def _make_cache_key(self, prompt: str, model: str, temperature: float) -> str:
        """Generate a cache key for a request.

        Args:
            prompt: The prompt text.
            model: The model name.
            temperature: The temperature setting.

        Returns:
            Hash string for cache lookup.
        """
        key_data = f"{prompt}|{model}|{temperature}"
        import hashlib
        return hashlib.sha256(key_data.encode()).hexdigest()

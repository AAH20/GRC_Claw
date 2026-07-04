"""Main client for GRC_Claw API."""

import time
import threading
from typing import Optional
from urllib.parse import urljoin

import requests

from grc_claw.exceptions import AuthenticationError, APIError, RateLimitError


class GRCClient:
    """Client for interacting with the GRC_Claw compliance platform.

    Args:
        api_key: Your GRC_Claw API key.
        base_url: Base URL of the GRC_Claw API. Defaults to production.
        timeout: Request timeout in seconds. Defaults to 30.
        max_retries: Maximum retry attempts for rate-limited requests. Defaults to 3.

    Example:
        >>> from grc_claw import GRCClient
        >>> client = GRCClient(api_key="your-api-key")
        >>> result = client.scan("/path/to/project")
    """

    DEFAULT_BASE_URL = "https://api.grc-claw.a2z-soc.com/v1"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3

    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        timeout: int = None,
        max_retries: int = None,
    ):
        if not api_key:
            raise AuthenticationError("API key is required")

        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else self.MAX_RETRIES

        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"grc-claw-python/1.0.0",
        })

        # Simple rate limiter: track request timestamps
        self._rate_lock = threading.Lock()
        self._request_times: list[float] = []
        self._max_rpm = 60  # default requests per minute

    def _url(self, path: str) -> str:
        """Build full API URL from path."""
        return f"{self.base_url}/{path.lstrip('/')}"

    def _check_rate_limit(self) -> None:
        """Enforce client-side rate limiting."""
        now = time.time()
        window = 60.0

        with self._rate_lock:
            # Remove timestamps older than 1 minute
            self._request_times = [t for t in self._request_times if now - t < window]

            if len(self._request_times) >= self._max_rpm:
                oldest = self._request_times[0]
                wait_time = window - (now - oldest)
                if wait_time > 0:
                    time.sleep(wait_time)
                    self._request_times = [
                        t for t in self._request_times if time.time() - t < window
                    ]

            self._request_times.append(time.time())

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an API request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API endpoint path.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Parsed JSON response.

        Raises:
            AuthenticationError: If API key is invalid.
            RateLimitError: If rate limit exceeded after retries.
            APIError: For other API errors.
        """
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)

        last_exception = None

        for attempt in range(self.max_retries + 1):
            self._check_rate_limit()

            try:
                response = self._session.request(method, url, **kwargs)
            except requests.RequestException as e:
                raise APIError(f"Request failed: {e}")

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                if attempt < self.max_retries:
                    time.sleep(retry_after)
                    continue
                raise RateLimitError(
                    f"Rate limit exceeded after {self.max_retries} retries",
                    retry_after=retry_after,
                )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                except ValueError:
                    error_data = {"message": response.text}
                raise APIError(
                    message=error_data.get("message", f"API error: {response.status_code}"),
                    status_code=response.status_code,
                    response=error_data,
                )

            if response.content:
                return response.json()
            return {}

        raise APIError("Max retries exceeded", status_code=429)

    def scan(
        self,
        path: str,
        frameworks: Optional[list[str]] = None,
        severity_threshold: str = "medium",
    ) -> dict:
        """Scan a directory for compliance issues.

        Args:
            path: Directory path to scan.
            frameworks: List of frameworks to check against (e.g., ["CMMC", "SOC2"]).
            severity_threshold: Minimum severity to report (low, medium, high, critical).

        Returns:
            Scan results with findings, scores, and recommendations.

        Example:
            >>> result = client.scan("/path/to/project", frameworks=["CMMC", "NIST"])
            >>> print(f"Found {result['total_findings']} issues")
        """
        payload = {
            "path": path,
            "severity_threshold": severity_threshold,
        }
        if frameworks:
            payload["frameworks"] = frameworks

        return self._request("POST", "/scan", json=payload)

    def cmmc_assess(
        self,
        path: str,
        level: int = 1,
        practice_domain: Optional[str] = None,
    ) -> dict:
        """Run a CMMC assessment against a directory.

        Args:
            path: Directory path to assess.
            level: CMMC level (1, 2, or 3).
            practice_domain: Optional domain to focus on (e.g., "Access Control").

        Returns:
            Assessment results with maturity scores per practice.

        Example:
            >>> result = client.cmmc_assess("/path/to/project", level=2)
            >>> print(f"Overall score: {result['overall_score']}%")
        """
        payload = {
            "path": path,
            "level": level,
        }
        if practice_domain:
            payload["practice_domain"] = practice_domain

        return self._request("POST", "/cmmc/assess", json=payload)

    def trust_score(self, entity_id: str, entity_type: str = "organization") -> dict:
        """Get the trust score for an entity.

        Args:
            entity_id: UUID or identifier of the entity.
            entity_type: Type of entity (organization, agent, service).

        Returns:
            Trust score breakdown with component scores.

        Example:
            >>> score = client.trust_score("org-123", "organization")
            >>> print(f"Trust score: {score['score']}/100")
        """
        return self._request("GET", f"/trust-score/{entity_type}/{entity_id}")

    def list_controls(self, framework: str = "CMMC") -> list[dict]:
        """List available controls for a framework.

        Args:
            framework: Framework name (CMMC, NIST, SOC2, ISO27001).

        Returns:
            List of control definitions.

        Example:
            >>> controls = client.list_controls("CMMC")
            >>> for c in controls:
            ...     print(f"{c['id']}: {c['name']}")
        """
        result = self._request("GET", "/controls", params={"framework": framework})
        return result.get("controls", result)

    def list_frameworks(self) -> list[dict]:
        """List all supported compliance frameworks.

        Returns:
            List of framework metadata.

        Example:
            >>> frameworks = client.list_frameworks()
            >>> for fw in frameworks:
            ...     print(f"{fw['name']}: {fw['version']}")
        """
        result = self._request("GET", "/frameworks")
        return result.get("frameworks", result)

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __repr__(self) -> str:
        return f"GRCClient(base_url='{self.base_url}')"

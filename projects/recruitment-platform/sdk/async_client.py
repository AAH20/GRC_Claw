"""Enhanced asynchronous Recruitment Platform API client.

Provides full async/await support with:
- Exponential backoff retry logic via tenacity and custom retry module
- Token bucket rate limiting (async)
- Redis-backed response caching
- Structured JSON logging
- Custom exception hierarchy
- Full type hints for mypy compliance
- Comprehensive docstrings
- Connection pooling with configurable limits
- Request/response middleware hooks
- Circuit breaker pattern for fault tolerance
- Request metrics and observability
- Batch request support with concurrency control
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, Union

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .cache import RedisCache
from .exceptions import (
    AuthenticationError,
    CircuitBreakerOpenError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    RecruitmentPlatformError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .logging_config import get_logger, setup_logging
from .models import (
    APIResponse,
    ATSCompatibilityRequest,
    ATSCompatibilityResponse,
    BiasLanguageRequest,
    BiasLanguageResponse,
    BiasRecommendationRequest,
    BiasRecommendationResponse,
    BiasRemovalRequest,
    BiasRemovalResponse,
    BrandStrategyRequest,
    BrandStrategyResponse,
    CandidateMatchRequest,
    CandidateMatchResponse,
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    ConflictDetectionRequest,
    ConflictDetectionResponse,
    ContentGenerationRequest,
    ContentGenerationResponse,
    CostAnalysisRequest,
    CostAnalysisResponse,
    DemographicAnalysisRequest,
    DemographicAnalysisResponse,
    DiversityMetricsRequest,
    DiversityMetricsResponse,
    DocumentGenerationRequest,
    DocumentGenerationResponse,
    EngagementTrackRequest,
    EngagementTrackResponse,
    FairnessScoreRequest,
    FairnessScoreResponse,
    FunnelAnalysisRequest,
    FunnelAnalysisResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
    HealthResponse,
    HiringPredictionRequest,
    HiringPredictionResponse,
    InterviewSlotRequest,
    InterviewSlotResponse,
    KeywordOptimizationRequest,
    KeywordOptimizationResponse,
    LearningPathRequest,
    LearningPathResponse,
    MatchExplanationRequest,
    MatchExplanationResponse,
    PoolAnalysisRequest,
    PoolAnalysisResponse,
    ProgressTrackRequest,
    ProgressTrackResponse,
    ReminderRequest,
    ReminderResponse,
    ReputationManagementRequest,
    ReputationManagementResponse,
    ResumeParseRequest,
    ResumeParseResponse,
    ReviewAnalysisRequest,
    ReviewAnalysisResponse,
    SEOOptimizationRequest,
    SEOOptimizationResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    SkillValidationRequest,
    SkillValidationResponse,
    SkillsAssessmentRequest,
    SkillsAssessmentResponse,
    SkillsExtractionRequest,
    SkillsExtractionResponse,
    SourceEffectivenessRequest,
    SourceEffectivenessResponse,
    TalentRecommendRequest,
    TalentRecommendResponse,
    TalentSourceRequest,
    TalentSourceResponse,
    TaskScheduleRequest,
    TaskScheduleResponse,
    ToneAnalysisRequest,
    ToneAnalysisResponse,
    WelcomeMessageRequest,
    WelcomeMessageResponse,
)
from .rate_limiter import AsyncTokenBucketRateLimiter

logger = get_logger()


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance.

    Prevents cascading failures by stopping requests after consecutive failures.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    _failures: int = 0
    _last_failure_time: float = 0.0
    _state: str = "closed"
    _half_open_calls: int = 0

    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self._state == "closed":
            return True
        if self._state == "open":
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = "half-open"
                self._half_open_calls = 0
                return True
            return False
        if self._state == "half-open":
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
        return False

    def record_success(self) -> None:
        """Record a successful request."""
        self._failures = 0
        self._state = "closed"
        self._half_open_calls = 0

    def record_failure(self) -> None:
        """Record a failed request."""
        self._failures += 1
        self._last_failure_time = time.time()
        if self._failures >= self.failure_threshold:
            self._state = "open"


@dataclass
class RequestMetrics:
    """Track request metrics for observability."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)

    def record_success(self, latency: float) -> None:
        """Record a successful request."""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency += latency

    def record_failure(self, error_type: str, latency: float) -> None:
        """Record a failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.total_latency += latency
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

    @property
    def average_latency(self) -> float:
        """Calculate average request latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


class AsyncRecruitmentPlatformClient:
    """Production-grade asynchronous client for the Recruitment Platform REST API.

    Provides typed access to all 42 endpoints across 10 recruitment domains
    with automatic retries, rate limiting, caching, authentication, circuit breaker,
    and comprehensive error handling. All methods support async/await.

    Args:
        base_url: The base URL of the Recruitment Platform API.
        api_key: Optional API key for authentication.
        timeout: Request timeout in seconds (default: 30).
        max_retries: Maximum number of retry attempts (default: 3).
        rate_limit_rate: Token bucket refill rate in tokens/second (default: 10).
        rate_limit_capacity: Token bucket capacity (default: 100).
        cache_ttl: Cache TTL in seconds (default: 300).
        cache_redis_url: Redis URL for response caching (default: redis://localhost:6379).
        enable_cache: Whether to enable response caching (default: True).
        enable_rate_limit: Whether to enable rate limiting (default: True).
        log_level: Logging level (default: logging.INFO).
        max_connections: Maximum number of concurrent connections (default: 100).
        max_keepalive_connections: Maximum keepalive connections (default: 20).
        circuit_breaker_threshold: Failure threshold for circuit breaker (default: 5).
        circuit_breaker_recovery: Recovery timeout in seconds (default: 30).
        request_hooks: Optional list of async request hooks.
        response_hooks: Optional list of async response hooks.

    Example:
        >>> async with AsyncRecruitmentPlatformClient(
        ...     base_url="http://localhost:8000",
        ...     api_key="your-api-key",
        ... ) as client:
        ...     health = await client.health_check()
        ...     print(health.status)
        'healthy'

    Example with manual lifecycle:
        >>> client = AsyncRecruitmentPlatformClient(base_url="http://localhost:8000")
        >>> health = await client.health_check()
        >>> await client.aclose()
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_rate: float = 10.0,
        rate_limit_capacity: int = 100,
        cache_ttl: int = 300,
        cache_redis_url: str = "redis://localhost:6379",
        enable_cache: bool = True,
        enable_rate_limit: bool = True,
        log_level: int = logging.INFO,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_recovery: float = 30.0,
        request_hooks: Optional[List[Callable[[httpx.Request], Awaitable[None]]]] = None,
        response_hooks: Optional[List[Callable[[httpx.Response], Awaitable[None]]]] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._enable_cache = enable_cache
        self._enable_rate_limit = enable_rate_limit

        setup_logging(log_level)

        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers=self._build_headers(),
            limits=limits,
        )

        self._rate_limiter: AsyncTokenBucketRateLimiter | None = None
        if enable_rate_limit:
            self._rate_limiter = AsyncTokenBucketRateLimiter(
                rate=rate_limit_rate,
                capacity=rate_limit_capacity,
            )

        self._cache: RedisCache | None = None
        if enable_cache:
            self._cache = RedisCache(
                redis_url=cache_redis_url,
                ttl=cache_ttl,
            )

        self._circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=circuit_breaker_recovery,
        )

        self._metrics = RequestMetrics()
        self._request_hooks = request_hooks or []
        self._response_hooks = response_hooks or []

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with optional authentication."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Process HTTP response and raise appropriate exceptions."""
        if response.is_success:
            return response.json()

        error_body: Any = None
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text

        message = ""
        if isinstance(error_body, dict):
            message = str(error_body.get("detail", error_body.get("message", "")))
        if not message:
            message = f"HTTP {response.status_code}: {response.reason_phrase}"

        status = response.status_code
        request_id = response.headers.get("x-request-id")

        if status == 401:
            raise AuthenticationError(message, status, error_body, request_id)
        if status == 404:
            raise NotFoundError(message, status, error_body, request_id)
        if status == 422:
            raise ValidationError(message, status, error_body, request_id)
        if status == 429:
            raise RateLimitError(message, status, error_body, request_id)
        if status >= 500:
            raise ServerError(message, status, error_body, request_id)
        raise RecruitmentPlatformError(message, status, error_body, request_id)

    def _get_cached(self, method: str, path: str, params: dict[str, Any] | None) -> dict[str, Any] | None:
        """Get cached response if available."""
        if self._cache is None:
            return None
        return self._cache.get(method, path, params)

    def _set_cached(self, method: str, path: str, params: dict[str, Any] | None, data: dict[str, Any]) -> None:
        """Cache a response."""
        if self._cache is None:
            return
        self._cache.set(method, path, params, data)

    async def _acquire_rate_limit(self) -> None:
        """Acquire a rate limit token, blocking if necessary."""
        if self._rate_limiter is not None:
            await self._rate_limiter.acquire(blocking=True)

    async def _execute_request_hooks(self, request: httpx.Request) -> None:
        """Execute all registered request hooks."""
        for hook in self._request_hooks:
            await hook(request)

    async def _execute_response_hooks(self, response: httpx.Response) -> None:
        """Execute all registered response hooks."""
        for hook in self._response_hooks:
            await hook(response)

    @retry(
        retry=retry_if_exception_type((RateLimitError, ServerError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an async HTTP request with retry logic, rate limiting, caching, and circuit breaker."""
        if not self._circuit_breaker.can_execute():
            raise CircuitBreakerOpenError("Circuit breaker is open")

        if method == "GET" and self._cache is not None:
            cached = self._get_cached(method, path, params)
            if cached is not None:
                logger.debug("Cache hit", extra={"method": method, "path": path})
                return cached

        await self._acquire_rate_limit()

        start_time = time.time()
        try:
            logger.debug(
                "Making async request",
                extra={"method": method, "path": path},
            )

            request = self._client.build_request(
                method,
                path,
                json=json,
                params=params,
            )
            await self._execute_request_hooks(request)

            response = await self._client.send(request)
            await self._execute_response_hooks(response)

            data = self._handle_response(response)

            if method == "GET" and self._cache is not None:
                self._set_cached(method, path, params, data)

            self._circuit_breaker.record_success()
            latency = time.time() - start_time
            self._metrics.record_success(latency)

            return data
        except (RateLimitError, ServerError) as e:
            self._circuit_breaker.record_failure()
            latency = time.time() - start_time
            self._metrics.record_failure(type(e).__name__, latency)
            raise
        except httpx.TimeoutException as e:
            self._circuit_breaker.record_failure()
            latency = time.time() - start_time
            self._metrics.record_failure("TimeoutError", latency)
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            self._circuit_breaker.record_failure()
            latency = time.time() - start_time
            self._metrics.record_failure("ConnectionError", latency)
            raise ConnectionError(f"Connection failed: {e}") from e
        except httpx.HTTPError as e:
            self._circuit_breaker.record_failure()
            latency = time.time() - start_time
            self._metrics.record_failure("HTTPError", latency)
            raise RecruitmentPlatformError(f"HTTP error: {e}") from e

    async def aclose(self) -> None:
        """Close the underlying async HTTP client and cache connections."""
        await self._client.aclose()
        if self._cache is not None:
            self._cache.close()

    async def __aenter__(self) -> AsyncRecruitmentPlatformClient:
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager and close the client."""
        await self.aclose()

    def get_metrics(self) -> dict[str, Any]:
        """Get current request metrics.

        Returns:
            Dictionary with request metrics including total requests,
            success rate, average latency, and errors by type.
        """
        return {
            "total_requests": self._metrics.total_requests,
            "successful_requests": self._metrics.successful_requests,
            "failed_requests": self._metrics.failed_requests,
            "success_rate": self._metrics.success_rate,
            "average_latency": self._metrics.average_latency,
            "errors_by_type": self._metrics.errors_by_type,
        }

    async def batch_request(
        self,
        requests: List[Dict[str, Any]],
        max_concurrency: int = 10,
    ) -> List[dict[str, Any]]:
        """Execute multiple requests concurrently with controlled concurrency.

        Args:
            requests: List of request configs, each with 'method', 'path', and optional 'json'/'params'.
            max_concurrency: Maximum number of concurrent requests.

        Returns:
            List of response data dictionaries.
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _execute(req: Dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                return await self._request(
                    req["method"],
                    req["path"],
                    json=req.get("json"),
                    params=req.get("params"),
                )

        tasks = [_execute(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)

    # ─── Health ───────────────────────────────────────────────────────────────

    async def health_check(self) -> HealthResponse:
        """Check the health status of the API."""
        data = await self._request("GET", "/api/v1/health")
        return HealthResponse(**data)

    async def readiness_check(self) -> HealthResponse:
        """Check the readiness status of the API."""
        data = await self._request("GET", "/api/v1/ready")
        return HealthResponse(**data)

    # ─── Resume Parser ────────────────────────────────────────────────────────

    async def parse_resume(self, request: ResumeParseRequest) -> ResumeParseResponse:
        """Parse a resume into structured data."""
        data = await self._request("POST", "/api/v1/resume-parser/parse", json=request.model_dump())
        return ResumeParseResponse(**data.get("data", data))

    async def extract_contact(self, request: ResumeParseRequest) -> Any:
        """Extract contact information from resume text."""
        data = await self._request("POST", "/api/v1/resume-parser/extract-contact", json=request.model_dump())
        return data.get("data", data)

    async def extract_skills(self, request: SkillsExtractionRequest) -> SkillsExtractionResponse:
        """Extract skills from resume text."""
        data = await self._request("POST", "/api/v1/resume-parser/extract-skills", json=request.model_dump())
        return SkillsExtractionResponse(**data.get("data", data))

    # ─── Candidate Matcher ────────────────────────────────────────────────────

    async def match_candidates(self, request: CandidateMatchRequest) -> CandidateMatchResponse:
        """Match candidates to a job description."""
        data = await self._request("POST", "/api/v1/candidate-matcher/match", json=request.model_dump())
        return CandidateMatchResponse(**data.get("data", data))

    async def explain_match(self, request: MatchExplanationRequest) -> MatchExplanationResponse:
        """Explain a candidate match."""
        data = await self._request("POST", "/api/v1/candidate-matcher/explain", json=request.model_dump())
        return MatchExplanationResponse(**data.get("data", data))

    async def analyze_gap(self, request: GapAnalysisRequest) -> GapAnalysisResponse:
        """Analyze skills gap."""
        data = await self._request("POST", "/api/v1/candidate-matcher/gap-analysis", json=request.model_dump())
        return GapAnalysisResponse(**data.get("data", data))

    # ─── Interview Scheduler ──────────────────────────────────────────────────

    async def optimize_slots(self, request: InterviewSlotRequest) -> InterviewSlotResponse:
        """Find optimal interview time slots."""
        data = await self._request("POST", "/api/v1/interview-scheduler/optimize-slots", json=request.model_dump())
        return InterviewSlotResponse(**data.get("data", data))

    async def detect_conflicts(self, request: ConflictDetectionRequest) -> ConflictDetectionResponse:
        """Detect scheduling conflicts."""
        data = await self._request("POST", "/api/v1/interview-scheduler/detect-conflicts", json=request.model_dump())
        return ConflictDetectionResponse(**data.get("data", data))

    async def send_reminder(self, request: ReminderRequest) -> ReminderResponse:
        """Send interview reminder."""
        data = await self._request("POST", "/api/v1/interview-scheduler/send-reminder", json=request.model_dump())
        return ReminderResponse(**data.get("data", data))

    # ─── Skills Assessor ──────────────────────────────────────────────────────

    async def assess_skills(self, request: SkillsAssessmentRequest) -> SkillsAssessmentResponse:
        """Assess candidate skills."""
        data = await self._request("POST", "/api/v1/skills-assessor/assess", json=request.model_dump())
        return SkillsAssessmentResponse(**data.get("data", data))

    async def recommend_learning_path(self, request: LearningPathRequest) -> LearningPathResponse:
        """Recommend learning path."""
        data = await self._request("POST", "/api/v1/skills-assessor/learning-path", json=request.model_dump())
        return LearningPathResponse(**data.get("data", data))

    async def validate_skills(self, request: SkillValidationRequest) -> SkillValidationResponse:
        """Validate claimed skills."""
        data = await self._request("POST", "/api/v1/skills-assessor/validate-skills", json=request.model_dump())
        return SkillValidationResponse(**data.get("data", data))

    # ─── Bias Detector ────────────────────────────────────────────────────────

    async def analyze_language(self, request: BiasLanguageRequest) -> BiasLanguageResponse:
        """Detect biased language in text."""
        data = await self._request("POST", "/api/v1/bias-detector/analyze-language", json=request.model_dump())
        return BiasLanguageResponse(**data.get("data", data))

    async def compute_fairness(self, request: FairnessScoreRequest) -> FairnessScoreResponse:
        """Compute fairness metrics."""
        data = await self._request("POST", "/api/v1/bias-detector/fairness-score", json=request.model_dump())
        return FairnessScoreResponse(**data.get("data", data))

    async def analyze_demographics(self, request: DemographicAnalysisRequest) -> DemographicAnalysisResponse:
        """Analyze demographic patterns."""
        data = await self._request("POST", "/api/v1/bias-detector/demographic-analysis", json=request.model_dump())
        return DemographicAnalysisResponse(**data.get("data", data))

    async def get_bias_recommendations(self, request: BiasRecommendationRequest) -> BiasRecommendationResponse:
        """Get bias mitigation recommendations."""
        data = await self._request("POST", "/api/v1/bias-detector/recommendations", json=request.model_dump())
        return BiasRecommendationResponse(**data.get("data", data))

    # ─── Talent Pool Manager ──────────────────────────────────────────────────

    async def source_candidates(self, request: TalentSourceRequest) -> TalentSourceResponse:
        """Source candidates from talent pool."""
        data = await self._request("POST", "/api/v1/talent-pool/source", json=request.model_dump())
        return TalentSourceResponse(**data.get("data", data))

    async def analyze_pool(self, request: PoolAnalysisRequest) -> PoolAnalysisResponse:
        """Analyze talent pool health."""
        data = await self._request("POST", "/api/v1/talent-pool/analyze-pool", json=request.model_dump())
        return PoolAnalysisResponse(**data.get("data", data))

    async def recommend_talent(self, request: TalentRecommendRequest) -> TalentRecommendResponse:
        """Recommend talent for a position."""
        data = await self._request("POST", "/api/v1/talent-pool/recommend", json=request.model_dump())
        return TalentRecommendResponse(**data.get("data", data))

    async def track_engagement(self, request: EngagementTrackRequest) -> EngagementTrackResponse:
        """Track candidate engagement."""
        data = await self._request("POST", "/api/v1/talent-pool/track-engagement", json=request.model_dump())
        return EngagementTrackResponse(**data.get("data", data))

    # ─── Recruitment Analytics ────────────────────────────────────────────────

    async def analyze_cost(self, request: CostAnalysisRequest) -> CostAnalysisResponse:
        """Analyze recruitment costs."""
        data = await self._request("POST", "/api/v1/analytics/cost-analysis", json=request.model_dump())
        return CostAnalysisResponse(**data.get("data", data))

    async def analyze_funnel(self, request: FunnelAnalysisRequest) -> FunnelAnalysisResponse:
        """Analyze recruitment funnel."""
        data = await self._request("POST", "/api/v1/analytics/funnel-analysis", json=request.model_dump())
        return FunnelAnalysisResponse(**data.get("data", data))

    async def get_diversity_metrics(self, request: DiversityMetricsRequest) -> DiversityMetricsResponse:
        """Get diversity metrics."""
        data = await self._request("POST", "/api/v1/analytics/diversity-metrics", json=request.model_dump())
        return DiversityMetricsResponse(**data.get("data", data))

    async def predict_hiring(self, request: HiringPredictionRequest) -> HiringPredictionResponse:
        """Generate hiring predictions."""
        data = await self._request("POST", "/api/v1/analytics/predict", json=request.model_dump())
        return HiringPredictionResponse(**data.get("data", data))

    async def analyze_source_effectiveness(self, request: SourceEffectivenessRequest) -> SourceEffectivenessResponse:
        """Analyze source effectiveness."""
        data = await self._request("POST", "/api/v1/analytics/source-effectiveness", json=request.model_dump())
        return SourceEffectivenessResponse(**data.get("data", data))

    # ─── Onboarding Automator ────────────────────────────────────────────────

    async def check_compliance(self, request: ComplianceCheckRequest) -> ComplianceCheckResponse:
        """Check onboarding compliance."""
        data = await self._request("POST", "/api/v1/onboarding/check-compliance", json=request.model_dump())
        return ComplianceCheckResponse(**data.get("data", data))

    async def generate_documents(self, request: DocumentGenerationRequest) -> DocumentGenerationResponse:
        """Generate onboarding documents."""
        data = await self._request("POST", "/api/v1/onboarding/generate-documents", json=request.model_dump())
        return DocumentGenerationResponse(**data.get("data", data))

    async def track_progress(self, request: ProgressTrackRequest) -> ProgressTrackResponse:
        """Track onboarding progress."""
        data = await self._request("POST", "/api/v1/onboarding/track-progress", json=request.model_dump())
        return ProgressTrackResponse(**data.get("data", data))

    async def schedule_tasks(self, request: TaskScheduleRequest) -> TaskScheduleResponse:
        """Schedule onboarding tasks."""
        data = await self._request("POST", "/api/v1/onboarding/schedule-tasks", json=request.model_dump())
        return TaskScheduleResponse(**data.get("data", data))

    async def generate_welcome_message(self, request: WelcomeMessageRequest) -> WelcomeMessageResponse:
        """Generate welcome message."""
        data = await self._request("POST", "/api/v1/onboarding/welcome-message", json=request.model_dump())
        return WelcomeMessageResponse(**data.get("data", data))

    # ─── Job Description Optimizer ────────────────────────────────────────────

    async def check_ats(self, request: ATSCompatibilityRequest) -> ATSCompatibilityResponse:
        """Check ATS compatibility."""
        data = await self._request("POST", "/api/v1/job-description/check-ats", json=request.model_dump())
        return ATSCompatibilityResponse(**data.get("data", data))

    async def remove_bias(self, request: BiasRemovalRequest) -> BiasRemovalResponse:
        """Remove biased language."""
        data = await self._request("POST", "/api/v1/job-description/remove-bias", json=request.model_dump())
        return BiasRemovalResponse(**data.get("data", data))

    async def optimize_keywords(self, request: KeywordOptimizationRequest) -> KeywordOptimizationResponse:
        """Optimize keywords."""
        data = await self._request("POST", "/api/v1/job-description/optimize-keywords", json=request.model_dump())
        return KeywordOptimizationResponse(**data.get("data", data))

    async def optimize_seo(self, request: SEOOptimizationRequest) -> SEOOptimizationResponse:
        """Optimize for SEO."""
        data = await self._request("POST", "/api/v1/job-description/optimize-seo", json=request.model_dump())
        return SEOOptimizationResponse(**data.get("data", data))

    async def analyze_tone(self, request: ToneAnalysisRequest) -> ToneAnalysisResponse:
        """Analyze tone."""
        data = await self._request("POST", "/api/v1/job-description/analyze-tone", json=request.model_dump())
        return ToneAnalysisResponse(**data.get("data", data))

    # ─── Employer Branding ────────────────────────────────────────────────────

    async def develop_brand_strategy(self, request: BrandStrategyRequest) -> BrandStrategyResponse:
        """Develop brand strategy."""
        data = await self._request("POST", "/api/v1/employer-branding/brand-strategy", json=request.model_dump())
        return BrandStrategyResponse(**data.get("data", data))

    async def generate_content(self, request: ContentGenerationRequest) -> ContentGenerationResponse:
        """Generate branding content."""
        data = await self._request("POST", "/api/v1/employer-branding/generate-content", json=request.model_dump())
        return ContentGenerationResponse(**data.get("data", data))

    async def manage_reputation(self, request: ReputationManagementRequest) -> ReputationManagementResponse:
        """Manage employer reputation."""
        data = await self._request("POST", "/api/v1/employer-branding/manage-reputation", json=request.model_dump())
        return ReputationManagementResponse(**data.get("data", data))

    async def analyze_reviews(self, request: ReviewAnalysisRequest) -> ReviewAnalysisResponse:
        """Analyze reviews."""
        data = await self._request("POST", "/api/v1/employer-branding/analyze-reviews", json=request.model_dump())
        return ReviewAnalysisResponse(**data.get("data", data))

    async def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResponse:
        """Analyze sentiment."""
        data = await self._request("POST", "/api/v1/employer-branding/analyze-sentiment", json=request.model_dump())
        return SentimentAnalysisResponse(**data.get("data", data))
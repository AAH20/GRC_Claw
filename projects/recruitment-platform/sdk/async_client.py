"""Asynchronous Recruitment Platform API client.

Provides full async/await support with the same features as the synchronous client:
- Exponential backoff retry logic
- Token bucket rate limiting
- Redis-backed response caching
- Structured JSON logging
- Custom exception hierarchy
- Full type hints for mypy compliance
- Comprehensive docstrings
"""
from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Type

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


class AsyncRecruitmentPlatformClient:
    """Production-grade asynchronous client for the Recruitment Platform REST API.

    Provides typed access to all 42 endpoints across 10 recruitment domains
    with automatic retries, rate limiting, caching, authentication, and
    comprehensive error handling. All methods support async/await.

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
    ) -> None:
        """Initialize the asynchronous client.

        Args:
            base_url: The base URL of the Recruitment Platform API.
            api_key: Optional API key for authentication.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            rate_limit_rate: Token bucket refill rate in tokens/second.
            rate_limit_capacity: Token bucket capacity.
            cache_ttl: Cache TTL in seconds.
            cache_redis_url: Redis URL for response caching.
            enable_cache: Whether to enable response caching.
            enable_rate_limit: Whether to enable rate limiting.
            log_level: Logging level.
        """
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._enable_cache = enable_cache
        self._enable_rate_limit = enable_rate_limit

        setup_logging(log_level)

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers=self._build_headers(),
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

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with optional authentication.

        Returns:
            Dictionary of HTTP headers including Content-Type, Accept,
            and Authorization if an API key is configured.
        """
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Process HTTP response and raise appropriate exceptions.

        Args:
            response: The HTTP response to process.

        Returns:
            Parsed JSON response body.

        Raises:
            AuthenticationError: If authentication fails (401).
            NotFoundError: If resource is not found (404).
            RateLimitError: If rate limit is exceeded (429).
            ValidationError: If request validation fails (422).
            ServerError: If server returns a 5xx error.
            RecruitmentPlatformError: For other HTTP errors.
        """
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
        """Get cached response if available.

        Args:
            method: HTTP method.
            path: API path.
            params: Query parameters.

        Returns:
            Cached response data or None.
        """
        if self._cache is None:
            return None
        return self._cache.get(method, path, params)

    def _set_cached(self, method: str, path: str, params: dict[str, Any] | None, data: dict[str, Any]) -> None:
        """Cache a response.

        Args:
            method: HTTP method.
            path: API path.
            params: Query parameters.
            data: Response data to cache.
        """
        if self._cache is None:
            return
        self._cache.set(method, path, params, data)

    async def _acquire_rate_limit(self) -> None:
        """Acquire a rate limit token, blocking if necessary."""
        if self._rate_limiter is not None:
            await self._rate_limiter.acquire(blocking=True)

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
        """Execute an async HTTP request with retry logic, rate limiting, and caching.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API path relative to base URL.
            json: Optional JSON request body.
            params: Optional query parameters.

        Returns:
            Parsed JSON response body.

        Raises:
            RecruitmentPlatformError: If the request fails after retries.
            TimeoutError: If the request times out.
            ConnectionError: If the connection fails.
        """
        # Check cache for GET requests
        if method == "GET" and self._cache is not None:
            cached = self._get_cached(method, path, params)
            if cached is not None:
                logger.debug("Cache hit", extra={"method": method, "path": path})
                return cached

        # Rate limiting
        await self._acquire_rate_limit()

        try:
            logger.debug(
                "Making async request",
                extra={"method": method, "path": path},
            )
            response = await self._client.request(
                method,
                path,
                json=json,
                params=params,
            )
            data = self._handle_response(response)

            # Cache successful GET responses
            if method == "GET" and self._cache is not None:
                self._set_cached(method, path, params, data)

            return data
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Connection failed: {e}") from e
        except httpx.HTTPError as e:
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

    # ─── Health ───────────────────────────────────────────────────────────────

    async def health_check(self) -> HealthResponse:
        """Check the health status of the API.

        Returns:
            Health status response with status and service name.

        Example:
            >>> health = await client.health_check()
            >>> print(health.status)
            'healthy'
        """
        data = await self._request("GET", "/api/v1/health")
        return HealthResponse(**data)

    async def readiness_check(self) -> HealthResponse:
        """Check the readiness status of the API.

        Returns:
            Readiness status response indicating if the API is ready
            to accept traffic.
        """
        data = await self._request("GET", "/api/v1/ready")
        return HealthResponse(**data)

    # ─── Resume Parser ────────────────────────────────────────────────────────

    async def parse_resume(self, request: ResumeParseRequest) -> ResumeParseResponse:
        """Parse a resume into structured data.

        Args:
            request: Resume parse request with text content.

        Returns:
            Structured resume data including name, email, phone,
            skills, experience, and education.
        """
        data = await self._request("POST", "/api/v1/resume-parser/parse", json=request.model_dump())
        return ResumeParseResponse(**data.get("data", data))

    async def extract_contact(self, request: ResumeParseRequest) -> Any:
        """Extract contact information from resume text.

        Args:
            request: Contact extraction request with text content.

        Returns:
            Extracted contact information including email, phone,
            address, and LinkedIn profile.
        """
        data = await self._request("POST", "/api/v1/resume-parser/extract-contact", json=request.model_dump())
        return data.get("data", data)

    async def extract_skills(self, request: SkillsExtractionRequest) -> SkillsExtractionResponse:
        """Extract skills from resume text.

        Args:
            request: Skills extraction request with text content.

        Returns:
            List of extracted skills from the resume.
        """
        data = await self._request("POST", "/api/v1/resume-parser/extract-skills", json=request.model_dump())
        return SkillsExtractionResponse(**data.get("data", data))

    # ─── Candidate Matcher ────────────────────────────────────────────────────

    async def match_candidates(self, request: CandidateMatchRequest) -> CandidateMatchResponse:
        """Match candidates to a job description.

        Args:
            request: Candidate match request with candidates and job requirements.

        Returns:
            Ranked candidate matches with scores.
        """
        data = await self._request("POST", "/api/v1/candidate-matcher/match", json=request.model_dump())
        return CandidateMatchResponse(**data.get("data", data))

    async def explain_match(self, request: MatchExplanationRequest) -> MatchExplanationResponse:
        """Explain a candidate match.

        Args:
            request: Match explanation request with candidate, job, and match result.

        Returns:
            Human-readable explanation of the match decision.
        """
        data = await self._request("POST", "/api/v1/candidate-matcher/explain", json=request.model_dump())
        return MatchExplanationResponse(**data.get("data", data))

    async def analyze_gap(self, request: GapAnalysisRequest) -> GapAnalysisResponse:
        """Analyze skills gap.

        Args:
            request: Gap analysis request with candidate and required skills.

        Returns:
            Gap analysis results showing missing skills, matches, and coverage.
        """
        data = await self._request("POST", "/api/v1/candidate-matcher/gap-analysis", json=request.model_dump())
        return GapAnalysisResponse(**data.get("data", data))

    # ─── Interview Scheduler ──────────────────────────────────────────────────

    async def optimize_slots(self, request: InterviewSlotRequest) -> InterviewSlotResponse:
        """Find optimal interview time slots.

        Args:
            request: Interview slot request with participants and availabilities.

        Returns:
            Optimal time slots for the interview.
        """
        data = await self._request("POST", "/api/v1/interview-scheduler/optimize-slots", json=request.model_dump())
        return InterviewSlotResponse(**data.get("data", data))

    async def detect_conflicts(self, request: ConflictDetectionRequest) -> ConflictDetectionResponse:
        """Detect scheduling conflicts.

        Args:
            request: Conflict detection request with proposed slot and existing events.

        Returns:
            Detected scheduling conflicts.
        """
        data = await self._request("POST", "/api/v1/interview-scheduler/detect-conflicts", json=request.model_dump())
        return ConflictDetectionResponse(**data.get("data", data))

    async def send_reminder(self, request: ReminderRequest) -> ReminderResponse:
        """Send interview reminder.

        Args:
            request: Reminder request with interview details and reminder type.

        Returns:
            Reminder delivery status.
        """
        data = await self._request("POST", "/api/v1/interview-scheduler/send-reminder", json=request.model_dump())
        return ReminderResponse(**data.get("data", data))

    # ─── Skills Assessor ──────────────────────────────────────────────────────

    async def assess_skills(self, request: SkillsAssessmentRequest) -> SkillsAssessmentResponse:
        """Assess candidate skills.

        Args:
            request: Skills assessment request with assessment data.

        Returns:
            Assessment results with proficiency scores.
        """
        data = await self._request("POST", "/api/v1/skills-assessor/assess", json=request.model_dump())
        return SkillsAssessmentResponse(**data.get("data", data))

    async def recommend_learning_path(self, request: LearningPathRequest) -> LearningPathResponse:
        """Recommend learning path.

        Args:
            request: Learning path request with skill gaps and career goals.

        Returns:
            Learning path recommendations.
        """
        data = await self._request("POST", "/api/v1/skills-assessor/learning-path", json=request.model_dump())
        return LearningPathResponse(**data.get("data", data))

    async def validate_skills(self, request: SkillValidationRequest) -> SkillValidationResponse:
        """Validate claimed skills.

        Args:
            request: Skill validation request with claimed skills and evidence.

        Returns:
            Validation results for each claimed skill.
        """
        data = await self._request("POST", "/api/v1/skills-assessor/validate-skills", json=request.model_dump())
        return SkillValidationResponse(**data.get("data", data))

    # ─── Bias Detector ────────────────────────────────────────────────────────

    async def analyze_language(self, request: BiasLanguageRequest) -> BiasLanguageResponse:
        """Detect biased language in text.

        Args:
            request: Bias language request with text to analyze.

        Returns:
            Detected biased phrases with suggestions for alternatives.
        """
        data = await self._request("POST", "/api/v1/bias-detector/analyze-language", json=request.model_dump())
        return BiasLanguageResponse(**data.get("data", data))

    async def compute_fairness(self, request: FairnessScoreRequest) -> FairnessScoreResponse:
        """Compute fairness metrics.

        Args:
            request: Fairness score request with decisions and protected attributes.

        Returns:
            Fairness metric scores across protected attributes.
        """
        data = await self._request("POST", "/api/v1/bias-detector/fairness-score", json=request.model_dump())
        return FairnessScoreResponse(**data.get("data", data))

    async def analyze_demographics(self, request: DemographicAnalysisRequest) -> DemographicAnalysisResponse:
        """Analyze demographic patterns.

        Args:
            request: Demographic analysis request with hiring data and demographics.

        Returns:
            Demographic analysis results.
        """
        data = await self._request("POST", "/api/v1/bias-detector/demographic-analysis", json=request.model_dump())
        return DemographicAnalysisResponse(**data.get("data", data))

    async def get_bias_recommendations(self, request: BiasRecommendationRequest) -> BiasRecommendationResponse:
        """Get bias mitigation recommendations.

        Args:
            request: Bias recommendation request with bias analysis results.

        Returns:
            Actionable recommendations for mitigating bias.
        """
        data = await self._request("POST", "/api/v1/bias-detector/recommendations", json=request.model_dump())
        return BiasRecommendationResponse(**data.get("data", data))

    # ─── Talent Pool Manager ──────────────────────────────────────────────────

    async def source_candidates(self, request: TalentSourceRequest) -> TalentSourceResponse:
        """Source candidates from talent pool.

        Args:
            request: Talent source request with job requirements and pool criteria.

        Returns:
            Sourced candidates with match scores.
        """
        data = await self._request("POST", "/api/v1/talent-pool/source", json=request.model_dump())
        return TalentSourceResponse(**data.get("data", data))

    async def analyze_pool(self, request: PoolAnalysisRequest) -> PoolAnalysisResponse:
        """Analyze talent pool health.

        Args:
            request: Pool analysis request with pool data and hiring needs.

        Returns:
            Pool analysis results with health score and insights.
        """
        data = await self._request("POST", "/api/v1/talent-pool/analyze-pool", json=request.model_dump())
        return PoolAnalysisResponse(**data.get("data", data))

    async def recommend_talent(self, request: TalentRecommendRequest) -> TalentRecommendResponse:
        """Recommend talent for a position.

        Args:
            request: Talent recommendation request with job and pool members.

        Returns:
            Ranked talent recommendations.
        """
        data = await self._request("POST", "/api/v1/talent-pool/recommend", json=request.model_dump())
        return TalentRecommendResponse(**data.get("data", data))

    async def track_engagement(self, request: EngagementTrackRequest) -> EngagementTrackResponse:
        """Track candidate engagement.

        Args:
            request: Engagement track request with candidate ID and interactions.

        Returns:
            Engagement metrics and score.
        """
        data = await self._request("POST", "/api/v1/talent-pool/track-engagement", json=request.model_dump())
        return EngagementTrackResponse(**data.get("data", data))

    # ─── Recruitment Analytics ────────────────────────────────────────────────

    async def analyze_cost(self, request: CostAnalysisRequest) -> CostAnalysisResponse:
        """Analyze recruitment costs.

        Args:
            request: Cost analysis request with hiring data and cost data.

        Returns:
            Cost analysis results with total cost and breakdown.
        """
        data = await self._request("POST", "/api/v1/analytics/cost-analysis", json=request.model_dump())
        return CostAnalysisResponse(**data.get("data", data))

    async def analyze_funnel(self, request: FunnelAnalysisRequest) -> FunnelAnalysisResponse:
        """Analyze recruitment funnel.

        Args:
            request: Funnel analysis request with funnel stage data.

        Returns:
            Funnel analysis results with conversion rates and bottlenecks.
        """
        data = await self._request("POST", "/api/v1/analytics/funnel-analysis", json=request.model_dump())
        return FunnelAnalysisResponse(**data.get("data", data))

    async def get_diversity_metrics(self, request: DiversityMetricsRequest) -> DiversityMetricsResponse:
        """Get diversity metrics.

        Args:
            request: Diversity metrics request with pipeline data and demographics.

        Returns:
            Diversity metrics across the recruitment pipeline.
        """
        data = await self._request("POST", "/api/v1/analytics/diversity-metrics", json=request.model_dump())
        return DiversityMetricsResponse(**data.get("data", data))

    async def predict_hiring(self, request: HiringPredictionRequest) -> HiringPredictionResponse:
        """Generate hiring predictions.

        Args:
            request: Hiring prediction request with historical data and current pipeline.

        Returns:
            Predictive metrics for hiring outcomes.
        """
        data = await self._request("POST", "/api/v1/analytics/predict", json=request.model_dump())
        return HiringPredictionResponse(**data.get("data", data))

    async def analyze_source_effectiveness(self, request: SourceEffectivenessRequest) -> SourceEffectivenessResponse:
        """Analyze source effectiveness.

        Args:
            request: Source effectiveness request with source data and outcomes.

        Returns:
            Source effectiveness metrics.
        """
        data = await self._request("POST", "/api/v1/analytics/source-effectiveness", json=request.model_dump())
        return SourceEffectivenessResponse(**data.get("data", data))

    # ─── Onboarding Automator ────────────────────────────────────────────────

    async def check_compliance(self, request: ComplianceCheckRequest) -> ComplianceCheckResponse:
        """Check onboarding compliance.

        Args:
            request: Compliance check request with employee data and jurisdiction.

        Returns:
            Compliance status with any violations.
        """
        data = await self._request("POST", "/api/v1/onboarding/check-compliance", json=request.model_dump())
        return ComplianceCheckResponse(**data.get("data", data))

    async def generate_documents(self, request: DocumentGenerationRequest) -> DocumentGenerationResponse:
        """Generate onboarding documents.

        Args:
            request: Document generation request with employee and template config.

        Returns:
            Generated onboarding documents.
        """
        data = await self._request("POST", "/api/v1/onboarding/generate-documents", json=request.model_dump())
        return DocumentGenerationResponse(**data.get("data", data))

    async def track_progress(self, request: ProgressTrackRequest) -> ProgressTrackResponse:
        """Track onboarding progress.

        Args:
            request: Progress track request with employee ID and onboarding plan.

        Returns:
            Progress status with completed and pending tasks.
        """
        data = await self._request("POST", "/api/v1/onboarding/track-progress", json=request.model_dump())
        return ProgressTrackResponse(**data.get("data", data))

    async def schedule_tasks(self, request: TaskScheduleRequest) -> TaskScheduleResponse:
        """Schedule onboarding tasks.

        Args:
            request: Task schedule request with employee and start date.

        Returns:
            Scheduled onboarding tasks.
        """
        data = await self._request("POST", "/api/v1/onboarding/schedule-tasks", json=request.model_dump())
        return TaskScheduleResponse(**data.get("data", data))

    async def generate_welcome_message(self, request: WelcomeMessageRequest) -> WelcomeMessageResponse:
        """Generate welcome message.

        Args:
            request: Welcome message request with employee and team info.

        Returns:
            Welcome message content.
        """
        data = await self._request("POST", "/api/v1/onboarding/welcome-message", json=request.model_dump())
        return WelcomeMessageResponse(**data.get("data", data))

    # ─── Job Description Optimizer ────────────────────────────────────────────

    async def check_ats(self, request: ATSCompatibilityRequest) -> ATSCompatibilityResponse:
        """Check ATS compatibility.

        Args:
            request: ATS compatibility request with job description text.

        Returns:
            Compatibility results with any issues found.
        """
        data = await self._request("POST", "/api/v1/job-description/check-ats", json=request.model_dump())
        return ATSCompatibilityResponse(**data.get("data", data))

    async def remove_bias(self, request: BiasRemovalRequest) -> BiasRemovalResponse:
        """Remove biased language.

        Args:
            request: Bias removal request with job description text.

        Returns:
            Cleaned text with bias report.
        """
        data = await self._request("POST", "/api/v1/job-description/remove-bias", json=request.model_dump())
        return BiasRemovalResponse(**data.get("data", data))

    async def optimize_keywords(self, request: KeywordOptimizationRequest) -> KeywordOptimizationResponse:
        """Optimize keywords.

        Args:
            request: Keyword optimization request with job description and target role.

        Returns:
            Optimized text with keyword suggestions.
        """
        data = await self._request("POST", "/api/v1/job-description/optimize-keywords", json=request.model_dump())
        return KeywordOptimizationResponse(**data.get("data", data))

    async def optimize_seo(self, request: SEOOptimizationRequest) -> SEOOptimizationResponse:
        """Optimize for SEO.

        Args:
            request: SEO optimization request with job description and platform.

        Returns:
            SEO recommendations.
        """
        data = await self._request("POST", "/api/v1/job-description/optimize-seo", json=request.model_dump())
        return SEOOptimizationResponse(**data.get("data", data))

    async def analyze_tone(self, request: ToneAnalysisRequest) -> ToneAnalysisResponse:
        """Analyze tone.

        Args:
            request: Tone analysis request with job description and brand voice.

        Returns:
            Tone analysis with brand voice alignment score.
        """
        data = await self._request("POST", "/api/v1/job-description/analyze-tone", json=request.model_dump())
        return ToneAnalysisResponse(**data.get("data", data))

    # ─── Employer Branding ────────────────────────────────────────────────────

    async def develop_brand_strategy(self, request: BrandStrategyRequest) -> BrandStrategyResponse:
        """Develop brand strategy.

        Args:
            request: Brand strategy request with company data and target audience.

        Returns:
            Brand strategy recommendations.
        """
        data = await self._request("POST", "/api/v1/employer-branding/brand-strategy", json=request.model_dump())
        return BrandStrategyResponse(**data.get("data", data))

    async def generate_content(self, request: ContentGenerationRequest) -> ContentGenerationResponse:
        """Generate branding content.

        Args:
            request: Content generation request with content type and brand guidelines.

        Returns:
            Generated content.
        """
        data = await self._request("POST", "/api/v1/employer-branding/generate-content", json=request.model_dump())
        return ContentGenerationResponse(**data.get("data", data))

    async def manage_reputation(self, request: ReputationManagementRequest) -> ReputationManagementResponse:
        """Manage employer reputation.

        Args:
            request: Reputation management request with platform data and metrics.

        Returns:
            Reputation status and recommended actions.
        """
        data = await self._request("POST", "/api/v1/employer-branding/manage-reputation", json=request.model_dump())
        return ReputationManagementResponse(**data.get("data", data))

    async def analyze_reviews(self, request: ReviewAnalysisRequest) -> ReviewAnalysisResponse:
        """Analyze reviews.

        Args:
            request: Review analysis request with reviews and platform.

        Returns:
            Review analysis with summary and themes.
        """
        data = await self._request("POST", "/api/v1/employer-branding/analyze-reviews", json=request.model_dump())
        return ReviewAnalysisResponse(**data.get("data", data))

    async def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResponse:
        """Analyze sentiment.

        Args:
            request: Sentiment analysis request with texts to analyze.

        Returns:
            Sentiment analysis with overall sentiment and scores.
        """
        data = await self._request("POST", "/api/v1/employer-branding/analyze-sentiment", json=request.model_dump())
        return SentimentAnalysisResponse(**data.get("data", data))

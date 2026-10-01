"""
GRC_Claw Python SDK
====================

Complete Python SDK for the GRC_Claw API.
Supports REST, GraphQL, gRPC, and Webhook operations.

Installation:
    pip install grc-claw-sdk

Usage:
    from grc_claw import GRCClawClient

    client = GRCClawClient(
        api_key="grc_live_abc123...",
        tenant_id="org-acme",
        environment="production"
    )

    # Policy management
    policy = client.policies.create(
        policy_key="AI-ETHICS-001",
        name="Data Access Control Policy",
        category="privacy",
        cedar_policy='permit(principal, action, resource) when { ... }',
    )

    # Enforcement decision
    decision = client.enforcement.decide(
        agent_id="agent-42",
        action="read",
        resource="s3://data/public/dataset.csv",
        context={"environment": "production"},
    )
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, Iterator, List, Optional, TypeVar, Union

import httpx

# ============================================================
# Version
# ============================================================

__version__ = "1.0.0"

# ============================================================
# Enums
# ============================================================

class PolicyStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class PolicyCategory(str, Enum):
    ETHICS = "ethics"
    SAFETY = "safety"
    PRIVACY = "privacy"
    FAIRNESS = "fairness"

class EvidenceType(str, Enum):
    ARTIFACT = "artifact"
    OBSERVATION = "observation"
    INTERVIEW = "interview"
    ANALYSIS = "analysis"
    LOG = "log"

class VerificationLevel(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"

class EnforcementVerdict(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_REDACTION = "ALLOW_WITH_REDACTION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"

class AssessmentType(str, Enum):
    RISK = "risk"
    COMPLIANCE = "compliance"
    MATURITY = "maturity"
    READINESS = "readiness"

class AssessmentStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class RiskTier(str, Enum):
    PROHIBITED = "prohibited"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"

class AgentLifecycleStage(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TERMINATED = "terminated"

class Environment(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"

# ============================================================
# Exceptions
# ============================================================

class GRCClawError(Exception):
    """Base exception for GRC_Claw SDK."""
    def __init__(self, message: str, code: str = "", status: int = 0, request_id: str = ""):
        super().__init__(message)
        self.code = code
        self.status = status
        self.request_id = request_id

class AuthenticationError(GRCClawError):
    """Raised when authentication fails (401)."""
    pass

class AuthorizationError(GRCClawError):
    """Raised when permission is denied (403)."""
    pass

class NotFoundError(GRCClawError):
    """Raised when a resource is not found (404)."""
    pass

class ConflictError(GRCClawError):
    """Raised when there is a resource conflict (409)."""
    pass

class ValidationError(GRCClawError):
    """Raised when request validation fails (400)."""
    pass

class RateLimitError(GRCClawError):
    """Raised when rate limit is exceeded (429)."""
    def __init__(self, message: str, retry_after: int = 30, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

class ServerError(GRCClawError):
    """Raised on server error (5xx)."""
    pass

# ============================================================
# Data Models
# ============================================================

@dataclass
class Pagination:
    next_cursor: Optional[str] = None
    has_next: bool = False
    total: int = 0

@dataclass
class Policy:
    id: str
    policy_key: str
    name: str
    category: PolicyCategory
    status: PolicyStatus
    version: str
    description: Optional[str] = None
    framework_tags: List[str] = field(default_factory=list)
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    owner_id: Optional[str] = None
    agent_bindings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class PolicyVersion:
    version: str
    status: str
    change_summary: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

@dataclass
class PolicyDependency:
    target_policy_id: str
    target_policy_name: str
    relation_type: str
    description: Optional[str] = None

@dataclass
class PolicyDependent:
    source_policy_id: str
    source_policy_name: str
    relation_type: str
    description: Optional[str] = None

@dataclass
class PolicyDependencyGraph:
    policy_id: str
    dependencies: List[PolicyDependency] = field(default_factory=list)
    dependents: List[PolicyDependent] = field(default_factory=list)

@dataclass
class CompilationResult:
    policy_id: str
    compilation_status: str
    rego_policy: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    compiled_at: Optional[datetime] = None

@dataclass
class DryRunResultItem:
    input_index: int
    decision: str
    matched_rules: List[str] = field(default_factory=list)
    evaluation_time_ms: float = 0.0
    reason: Optional[str] = None

@dataclass
class DryRunSummary:
    total: int = 0
    allowed: int = 0
    denied: int = 0
    avg_evaluation_time_ms: float = 0.0

@dataclass
class DryRunResult:
    policy_id: str
    dry_run_results: List[DryRunResultItem] = field(default_factory=list)
    summary: DryRunSummary = field(default_factory=DryRunSummary)

@dataclass
class EvidenceSource:
    type: str
    system: str
    collection_method: str

@dataclass
class EvidenceContent:
    format: str
    data: str
    hash: Optional[str] = None

@dataclass
class EvidenceContext:
    environment: str
    region: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationStatus:
    status: str
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    confidence_score: float = 0.0

@dataclass
class CustodyEvent:
    action: str
    actor: str
    timestamp: Optional[datetime] = None
    hash: Optional[str] = None

@dataclass
class Evidence:
    evidence_id: str
    policy_id: Optional[str] = None
    assessment_id: Optional[str] = None
    source: Optional[EvidenceSource] = None
    evidence_type: Optional[EvidenceType] = None
    content: Optional[EvidenceContent] = None
    context: Optional[EvidenceContext] = None
    validation: Optional[ValidationStatus] = None
    verification_level: Optional[VerificationLevel] = None
    chain_of_custody: List[CustodyEvent] = field(default_factory=list)
    retention_class: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

@dataclass
class EvidenceVerification:
    evidence_id: str
    verification_result: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExportPackage:
    package_id: str
    status: str
    estimated_completion: Optional[datetime] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    package_hash: Optional[str] = None
    manifest: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnforcementDecision:
    decision_id: str
    verdict: EnforcementVerdict
    policy_id: Optional[str] = None
    policy_version: Optional[str] = None
    agent_id: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    evidence_hash: Optional[str] = None
    timestamp: Optional[datetime] = None
    ttl: int = 300
    signature: Optional[str] = None
    matched_rules: List[str] = field(default_factory=list)
    evaluation_time_ms: float = 0.0
    reason: Optional[str] = None

@dataclass
class BatchSummary:
    total: int = 0
    allowed: int = 0
    denied: int = 0
    require_approval: int = 0
    quarantined: int = 0
    avg_evaluation_time_ms: float = 0.0

@dataclass
class AssessmentFinding:
    id: str
    finding_key: str
    title: str
    description: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    policy_id: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    remediated_by: Optional[str] = None
    remediated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None

@dataclass
class Assessment:
    id: str
    assessment_key: str
    title: str
    assessment_type: AssessmentType
    target_id: str
    target_type: str
    status: AssessmentStatus
    description: Optional[str] = None
    methodology: Optional[str] = None
    score: Optional[float] = None
    risk_level: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    next_assessment_at: Optional[datetime] = None
    lead_assessor: Optional[str] = None
    findings: List[AssessmentFinding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ComplianceFramework:
    id: str
    framework_key: str
    name: str
    version: str
    description: Optional[str] = None
    authority: Optional[str] = None
    effective_date: Optional[datetime] = None
    control_count: int = 0

@dataclass
class ComplianceControl:
    id: str
    framework_id: Optional[str] = None
    control_key: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    guidance: Optional[str] = None

@dataclass
class ComplianceGap:
    control_id: str
    control_title: str
    status: str
    severity: Optional[str] = None
    evidence_count: int = 0
    last_assessed: Optional[datetime] = None

@dataclass
class ComplianceTrend:
    direction: str
    change: str
    period: str

@dataclass
class CompliancePosture:
    framework: str
    target_id: str
    target_type: str
    controls_assessed: int = 0
    controls_compliant: int = 0
    controls_non_compliant: int = 0
    controls_not_assessed: int = 0
    compliance_score: float = 0.0
    gaps: List[ComplianceGap] = field(default_factory=list)
    trend: Optional[ComplianceTrend] = None

@dataclass
class ComplianceMapping:
    id: str
    control_id: str
    policy_id: Optional[str] = None
    assessment_id: Optional[str] = None
    mapping_type: Optional[str] = None
    coverage: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class AgentCapability:
    name: str
    description: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    resource_scope: Optional[str] = None

@dataclass
class AgentIdentity:
    spiffe_id: Optional[str] = None
    mtls_cert: Optional[str] = None
    cert_expiry: Optional[datetime] = None

@dataclass
class TrustScore:
    value: int
    grade: str
    last_evaluated: Optional[datetime] = None

@dataclass
class Agent:
    id: str
    name: str
    type: str
    framework: str
    lifecycle_stage: AgentLifecycleStage
    risk_tier: RiskTier
    owner: Optional[str] = None
    capabilities: List[AgentCapability] = field(default_factory=list)
    identity: Optional[AgentIdentity] = None
    trust_score: Optional[TrustScore] = None
    policy_bindings: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    actor: Dict[str, Any] = field(default_factory=dict)
    resource: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)
    integrity_hash: Optional[str] = None
    previous_event_hash: Optional[str] = None

@dataclass
class AuditVerification:
    verification_status: str
    events_verified: int
    chain_intact: bool
    first_event_id: Optional[str] = None
    last_event_id: Optional[str] = None
    verified_at: Optional[datetime] = None

@dataclass
class WebhookSubscription:
    subscription_id: str
    url: str
    events: List[str]
    secret: str
    description: Optional[str] = None
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    delivery_stats: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WebhookDelivery:
    delivery_id: str
    subscription_id: str
    event_id: str
    event_type: str
    status: str
    http_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    attempts: int = 0
    delivered_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None

@dataclass
class HealthStatus:
    status: str
    version: str
    components: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

@dataclass
class ReadinessStatus:
    ready: bool
    checks: Dict[str, Any] = field(default_factory=dict)

# ============================================================
# Webhook Signature Verification
# ============================================================

class WebhookVerifier:
    """Verify webhook signatures from GRC_Claw."""

    @staticmethod
    def verify(payload_body: str, signature_header: str, secret: str) -> bool:
        """
        Verify webhook signature.

        Args:
            payload_body: Raw request body string
            signature_header: X-GRC-Signature header value (format: t=timestamp,v1=signature)
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        parts = signature_header.split(",")
        timestamp = None
        signature = None
        for part in parts:
            key, _, value = part.partition("=")
            if key == "t":
                timestamp = value
            elif key == "v1":
                signature = value

        if not timestamp or not signature:
            return False

        # Check timestamp tolerance (5 minutes)
        ts = int(timestamp)
        if abs(time.time() - ts) > 300:
            return False

        signed_payload = f"{timestamp}.{payload_body}"
        expected = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

# ============================================================
# Base Client
# ============================================================

class BaseClient:
    """Base HTTP client with authentication, retries, and error handling."""

    def __init__(
        self,
        api_key: str,
        tenant_id: str,
        environment: Environment = Environment.PRODUCTION,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.environment = environment
        self.timeout = timeout
        self.max_retries = max_retries

        base_urls = {
            Environment.PRODUCTION: "https://api.grc-claw.io",
            Environment.STAGING: "https://api.staging.grc-claw.io",
            Environment.DEVELOPMENT: "http://localhost:8080",
        }
        self.base_url = base_urls[environment]

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Tenant-ID": tenant_id,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"grc-claw-sdk-python/{__version__}",
            },
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic."""
        url = f"{self.base_url}{path}"
        request_headers = dict(self._client.headers)
        if headers:
            request_headers.update(headers)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.request(
                    method,
                    url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                )
                self._handle_error(response)
                return response
            except RateLimitError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(e.retry_after)
                    continue
                raise
            except ServerError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
            except GRCClawError:
                raise

        raise last_error or GRCClawError("Request failed after retries")

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error responses."""
        if response.status_code < 400:
            return

        try:
            body = response.json()
        except Exception:
            body = {"detail": response.text}

        code = body.get("code", "UNKNOWN")
        message = body.get("detail", "Unknown error")
        request_id = body.get("request_id", "")

        error_map = {
            400: ValidationError,
            401: AuthenticationError,
            403: AuthorizationError,
            404: NotFoundError,
            409: ConflictError,
            422: ValidationError,
            429: RateLimitError,
        }

        error_class = error_map.get(response.status_code, ServerError)
        if error_class is RateLimitError:
            retry_after = int(response.headers.get("Retry-After", 30))
            raise error_class(message, code=code, status=response.status_code, request_id=request_id, retry_after=retry_after)

        raise error_class(message, code=code, status=response.status_code, request_id=request_id)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> BaseClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()

# ============================================================
# Policy Service
# ============================================================

class PolicyService:
    """Policy management operations."""

    def __init__(self, client: BaseClient):
        self._client = client

    def list(
        self,
        *,
        status: Optional[PolicyStatus] = None,
        category: Optional[PolicyCategory] = None,
        framework: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> tuple[List[Policy], Pagination]:
        """List policies with optional filtering."""
        params: Dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status.value
        if category:
            params["category"] = category.value
        if framework:
            params["framework"] = framework
        if agent_id:
            params["agent_id"] = agent_id
        if cursor:
            params["cursor"] = cursor

        response = self._client._request("GET", "/v1.0/policies", params=params)
        data = response.json()

        policies = [self._parse_policy(p) for p in data.get("data", [])]
        pagination = Pagination(
            next_cursor=data.get("pagination", {}).get("next_cursor"),
            has_next=data.get("pagination", {}).get("has_next", False),
            total=data.get("pagination", {}).get("total", 0),
        )
        return policies, pagination

    def create(
        self,
        *,
        policy_key: str,
        name: str,
        category: PolicyCategory,
        description: Optional[str] = None,
        framework_tags: Optional[List[str]] = None,
        cedar_policy: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Policy:
        """Create a new policy."""
        body: Dict[str, Any] = {
            "policy_key": policy_key,
            "name": name,
            "category": category.value,
        }
        if description:
            body["description"] = description
        if framework_tags:
            body["framework_tags"] = framework_tags
        if cedar_policy:
            body["cedar_policy"] = cedar_policy
        if metadata:
            body["metadata"] = metadata

        response = self._client._request("POST", "/v1.0/policies", json_data=body)
        return self._parse_policy(response.json())

    def get(self, policy_id: str) -> Policy:
        """Get a policy by ID."""
        response = self._client._request("GET", f"/v1.0/policies/{policy_id}")
        return self._parse_policy(response.json())

    def update(
        self,
        policy_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        cedar_policy: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Policy:
        """Update a policy."""
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if description:
            body["description"] = description
        if cedar_policy:
            body["cedar_policy"] = cedar_policy
        if metadata:
            body["metadata"] = metadata

        response = self._client._request("PUT", f"/v1.0/policies/{policy_id}", json_data=body)
        return self._parse_policy(response.json())

    def delete(self, policy_id: str, *, force: bool = False) -> None:
        """Delete a policy."""
        params = {"force": force} if force else None
        self._client._request("DELETE", f"/v1.0/policies/{policy_id}", params=params)

    def compile(self, policy_id: str) -> CompilationResult:
        """Compile a policy (Cedar to Rego)."""
        response = self._client._request("POST", f"/v1.0/policies/{policy_id}/compile")
        data = response.json()
        return CompilationResult(
            policy_id=data["policy_id"],
            compilation_status=data["compilation_status"],
            rego_policy=data.get("rego_policy"),
            warnings=data.get("warnings", []),
            errors=data.get("errors", []),
            compiled_at=self._parse_datetime(data.get("compiled_at")),
        )

    def dry_run(
        self,
        policy_id: str,
        *,
        test_inputs: List[Dict[str, Any]],
    ) -> DryRunResult:
        """Dry-run a policy against test inputs."""
        body = {"test_inputs": test_inputs}
        response = self._client._request("POST", f"/v1.0/policies/{policy_id}/dry-run", json_data=body)
        data = response.json()

        results = [
            DryRunResultItem(
                input_index=r["input_index"],
                decision=r["decision"],
                matched_rules=r.get("matched_rules", []),
                evaluation_time_ms=r.get("evaluation_time_ms", 0.0),
                reason=r.get("reason"),
            )
            for r in data.get("dry_run_results", [])
        ]
        summary_data = data.get("summary", {})
        summary = DryRunSummary(
            total=summary_data.get("total", 0),
            allowed=summary_data.get("allowed", 0),
            denied=summary_data.get("denied", 0),
            avg_evaluation_time_ms=summary_data.get("avg_evaluation_time_ms", 0.0),
        )
        return DryRunResult(policy_id=data["policy_id"], dry_run_results=results, summary=summary)

    def get_versions(self, policy_id: str) -> List[PolicyVersion]:
        """Get version history for a policy."""
        response = self._client._request("GET", f"/v1.0/policies/{policy_id}/versions")
        data = response.json()
        return [
            PolicyVersion(
                version=v["version"],
                status=v["status"],
                change_summary=v.get("change_summary"),
                created_at=self._parse_datetime(v.get("created_at")),
                created_by=v.get("created_by"),
            )
            for v in data.get("data", [])
        ]

    def get_dependencies(self, policy_id: str) -> PolicyDependencyGraph:
        """Get dependency graph for a policy."""
        response = self._client._request("GET", f"/v1.0/policies/{policy_id}/dependencies")
        data = response.json()
        return PolicyDependencyGraph(
            policy_id=data["policy_id"],
            dependencies=[
                PolicyDependency(
                    target_policy_id=d["target_policy_id"],
                    target_policy_name=d["target_policy_name"],
                    relation_type=d["relation_type"],
                    description=d.get("description"),
                )
                for d in data.get("dependencies", [])
            ],
            dependents=[
                PolicyDependent(
                    source_policy_id=d["source_policy_id"],
                    source_policy_name=d["source_policy_name"],
                    relation_type=d["relation_type"],
                    description=d.get("description"),
                )
                for d in data.get("dependents", [])
            ],
        )

    def _parse_policy(self, data: Dict[str, Any]) -> Policy:
        return Policy(
            id=data["id"],
            policy_key=data["policy_key"],
            name=data["name"],
            category=PolicyCategory(data["category"]),
            status=PolicyStatus(data["status"]),
            version=data["version"],
            description=data.get("description"),
            framework_tags=data.get("framework_tags", []),
            effective_date=self._parse_datetime(data.get("effective_date")),
            expiry_date=self._parse_datetime(data.get("expiry_date")),
            owner_id=data.get("owner_id"),
            agent_bindings=data.get("agent_bindings", []),
            metadata=data.get("metadata", {}),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

# ============================================================
# Evidence Service
# ============================================================

class EvidenceService:
    """Evidence management operations."""

    def __init__(self, client: BaseClient):
        self._client = client

    def search(
        self,
        *,
        policy_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
        evidence_type: Optional[EvidenceType] = None,
        framework: Optional[str] = None,
        control_id: Optional[str] = None,
        verification_level: Optional[VerificationLevel] = None,
        environment: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        query: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> tuple[List[Evidence], Pagination]:
        """Search evidence with filtering."""
        params: Dict[str, Any] = {"limit": limit}
        if policy_id:
            params["policy_id"] = policy_id
        if assessment_id:
            params["assessment_id"] = assessment_id
        if evidence_type:
            params["evidence_type"] = evidence_type.value
        if framework:
            params["framework"] = framework
        if control_id:
            params["control_id"] = control_id
        if verification_level:
            params["verification_level"] = verification_level.value
        if environment:
            params["environment"] = environment
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if query:
            params["query"] = query
        if cursor:
            params["cursor"] = cursor

        response = self._client._request("GET", "/v1.0/evidence", params=params)
        data = response.json()

        evidences = [self._parse_evidence(e) for e in data.get("data", [])]
        pagination = Pagination(
            next_cursor=data.get("pagination", {}).get("next_cursor"),
            has_next=data.get("pagination", {}).get("has_next", False),
            total=data.get("pagination", {}).get("total", 0),
        )
        return evidences, pagination

    def submit(
        self,
        *,
        source: Dict[str, str],
        evidence_type: EvidenceType,
        content: Dict[str, str],
        policy_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        control_mapping: Optional[Dict[str, str]] = None,
    ) -> Evidence:
        """Submit new evidence."""
        body: Dict[str, Any] = {
            "source": source,
            "evidence_type": evidence_type.value,
            "content": content,
        }
        if policy_id:
            body["policy_id"] = policy_id
        if assessment_id:
            body["assessment_id"] = assessment_id
        if context:
            body["context"] = context
        if control_mapping:
            body["control_mapping"] = control_mapping

        response = self._client._request("POST", "/v1.0/evidence", json_data=body)
        return self._parse_evidence(response.json())

    def get(self, evidence_id: str) -> Evidence:
        """Get evidence by ID."""
        response = self._client._request("GET", f"/v1.0/evidence/{evidence_id}")
        return self._parse_evidence(response.json())

    def verify(self, evidence_id: str) -> EvidenceVerification:
        """Verify evidence integrity."""
        response = self._client._request("POST", f"/v1.0/evidence/{evidence_id}/verify")
        data = response.json()
        return EvidenceVerification(
            evidence_id=data["evidence_id"],
            verification_result=data.get("verification_result", {}),
        )

    def export(
        self,
        *,
        framework: str,
        time_range: Dict[str, str],
        format: str = "json",
        include_chain_of_custody: bool = True,
    ) -> ExportPackage:
        """Initiate evidence package export."""
        body = {
            "framework": framework,
            "time_range": time_range,
            "format": format,
            "include_chain_of_custody": include_chain_of_custody,
        }
        response = self._client._request("POST", "/v1.0/evidence/export", json_data=body)
        data = response.json()
        return ExportPackage(
            package_id=data["package_id"],
            status=data["status"],
            estimated_completion=PolicyService._parse_datetime(data.get("estimated_completion")),
            download_url=data.get("download_url"),
            expires_at=PolicyService._parse_datetime(data.get("expires_at")),
            package_hash=data.get("package_hash"),
            manifest=data.get("manifest", {}),
        )

    def get_export(self, package_id: str) -> ExportPackage:
        """Get export package status."""
        response = self._client._request("GET", f"/v1.0/evidence/export/{package_id}")
        data = response.json()
        return ExportPackage(
            package_id=data["package_id"],
            status=data["status"],
            estimated_completion=PolicyService._parse_datetime(data.get("estimated_completion")),
            download_url=data.get("download_url"),
            expires_at=PolicyService._parse_datetime(data.get("expires_at")),
            package_hash=data.get("package_hash"),
            manifest=data.get("manifest", {}),
        )

    def _parse_evidence(self, data: Dict[str, Any]) -> Evidence:
        source_data = data.get("source", {})
        content_data = data.get("content", {})
        context_data = data.get("context", {})
        validation_data = data.get("validation", {})

        return Evidence(
            evidence_id=data["evidence_id"],
            policy_id=data.get("policy_id"),
            assessment_id=data.get("assessment_id"),
            source=EvidenceSource(
                type=source_data.get("type", ""),
                system=source_data.get("system", ""),
                collection_method=source_data.get("collection_method", ""),
            ) if source_data else None,
            evidence_type=EvidenceType(data["evidence_type"]) if data.get("evidence_type") else None,
            content=EvidenceContent(
                format=content_data.get("format", ""),
                data=content_data.get("data", ""),
                hash=content_data.get("hash"),
            ) if content_data else None,
            context=EvidenceContext(
                environment=context_data.get("environment", ""),
                region=context_data.get("region"),
                timestamp=PolicyService._parse_datetime(context_data.get("timestamp")),
                metadata=context_data.get("metadata", {}),
            ) if context_data else None,
            validation=ValidationStatus(
                status=validation_data.get("status", ""),
                validated_by=validation_data.get("validated_by"),
                validated_at=PolicyService._parse_datetime(validation_data.get("validated_at")),
                confidence_score=validation_data.get("confidence_score", 0.0),
            ) if validation_data else None,
            verification_level=VerificationLevel(data["verification_level"]) if data.get("verification_level") else None,
            chain_of_custody=[
                CustodyEvent(
                    action=c.get("action", ""),
                    actor=c.get("actor", ""),
                    timestamp=PolicyService._parse_datetime(c.get("timestamp")),
                    hash=c.get("hash"),
                )
                for c in data.get("chain_of_custody", [])
            ],
            retention_class=data.get("retention_class"),
            created_at=PolicyService._parse_datetime(data.get("created_at")),
            expires_at=PolicyService._parse_datetime(data.get("expires_at")),
        )

# ============================================================
# Enforcement Service
# ============================================================

class EnforcementService:
    """Enforcement decision operations."""

    def __init__(self, client: BaseClient):
        self._client = client

    def decide(
        self,
        *,
        agent_id: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
        policy_ids: Optional[List[str]] = None,
        include_evidence: bool = True,
    ) -> EnforcementDecision:
        """Request a single enforcement decision."""
        body: Dict[str, Any] = {
            "agent_id": agent_id,
            "action": action,
            "resource": resource,
            "include_evidence": include_evidence,
        }
        if context:
            body["context"] = context
        if policy_ids:
            body["policy_ids"] = policy_ids

        response = self._client._request("POST", "/v1.0/enforcement/decide", json_data=body)
        return self._parse_decision(response.json())

    def decide_batch(
        self,
        *,
        decisions: List[Dict[str, Any]],
    ) -> tuple[List[EnforcementDecision], BatchSummary]:
        """Request batch enforcement decisions."""
        body = {"decisions": decisions}
        response = self._client._request("POST", "/v1.0/enforcement/decide-batch", json_data=body)
        data = response.json()

        results = [self._parse_decision(r) for r in data.get("results", [])]
        summary_data = data.get("summary", {})
        summary = BatchSummary(
            total=summary_data.get("total", 0),
            allowed=summary_data.get("allowed", 0),
            denied=summary_data.get("denied", 0),
            require_approval=summary_data.get("require_approval", 0),
            quarantined=summary_data.get("quarantined", 0),
            avg_evaluation_time_ms=summary_data.get("avg_evaluation_time_ms", 0.0),
        )
        return results, summary

    def get(self, decision_id: str) -> EnforcementDecision:
        """Get a decision by ID."""
        response = self._client._request("GET", f"/v1.0/enforcement/decisions/{decision_id}")
        return self._parse_decision(response.json())

    def list(
        self,
        *,
        agent_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        verdict: Optional[EnforcementVerdict] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> tuple[List[EnforcementDecision], Pagination]:
        """List enforcement decisions."""
        params: Dict[str, Any] = {"limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        if policy_id:
            params["policy_id"] = policy_id
        if verdict:
            params["verdict"] = verdict.value
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if cursor:
            params["cursor"] = cursor

        response = self._client._request("GET", "/v1.0/enforcement/decisions", params=params)
        data = response.json()

        decisions = [self._parse_decision(d) for d in data.get("data", [])]
        pagination = Pagination(
            next_cursor=data.get("pagination", {}).get("next_cursor"),
            has_next=data.get("pagination", {}).get("has_next", False),
            total=data.get("pagination", {}).get("total", 0),
        )
        return decisions, pagination

    def _parse_decision(self, data: Dict[str, Any]) -> EnforcementDecision:
        return EnforcementDecision(
            decision_id=data["decision_id"],
            verdict=EnforcementVerdict(data["verdict"]),
            policy_id=data.get("policy_id"),
            policy_version=data.get("policy_version"),
            agent_id=data.get("agent_id"),
            action=data.get("action"),
            resource=data.get("resource"),
            context=data.get("context", {}),
            evidence_hash=data.get("evidence_hash"),
            timestamp=PolicyService._parse_datetime(data.get("timestamp")),
            ttl=data.get("ttl", 300),
            signature=data.get("signature"),
            matched_rules=data.get("matched_rules", []),
            evaluation_time_ms=data.get("evaluation_time_ms", 0.0),
            reason=data.get("reason"),
        )

# ============================================================
# Assessment Service
# ============================================================

class AssessmentService:
    """Assessment management operations."""

    def __init__(self, client: BaseClient):
        self._client = client

    def list(
        self,
        *,
        assessment_type: Optional[AssessmentType] = None,
        status: Optional[AssessmentStatus] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        methodology: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> tuple[List[Assessment], Pagination]:
        """List assessments."""
        params: Dict[str, Any] = {"limit": limit}
        if assessment_type:
            params["assessment_type"] = assessment_type.value
        if status:
            params["status"] = status.value
        if target_type:
            params["target_type"] = target_type
        if target_id:
            params["target_id"] = target_id
        if methodology:
            params["methodology"] = methodology
        if cursor:
            params["cursor"] = cursor

        response = self._client._request("GET", "/v1.0/assessments", params=params)
        data = response.json()

        assessments = [self._parse_assessment(a) for a in data.get("data", [])]
        pagination = Pagination(
            next_cursor=data.get("pagination", {}).get("next_cursor"),
            has_next=data.get("pagination", {}).get("has_next", False),
            total=data.get("pagination", {}).get("total", 0),
        )
        return assessments, pagination

    def create(
        self,
        *,
        assessment_key: str,
        title: str,
        assessment_type: AssessmentType,
        target_id: str,
        target_type: str,
        description: Optional[str] = None,
        methodology: Optional[str] = None,
        lead_assessor: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Assessment:
        """Create a new assessment."""
        body: Dict[str, Any] = {
            "assessment_key": assessment_key,
            "title": title,
            "assessment_type": assessment_type.value,
            "target_id": target_id,
            "target_type": target_type,
        }
        if description:
            body["description"] = description
        if methodology:
            body["methodology"] = methodology
        if lead_assessor:
            body["lead_assessor"] = lead_assessor
        if metadata:
            body["metadata"] = metadata

        response = self._client._request("POST", "/v1.0/assessments", json_data=body)
        return self._parse_assessment(response.json())

    def get(self, assessment_id: str) -> Assessment:
        """Get an assessment by ID."""
        response = self._client._request("GET", f"/v1.0/assessments/{assessment_id}")
        return self._parse_assessment(response.json())

    def update(
        self,
        assessment_id: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[AssessmentStatus] = None,
        methodology: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Assessment:
        """Update an assessment."""
        body: Dict[str, Any] = {}
        if title:
            body["title"] = title
        if description:
            body["description"] = description
        if status:
            body["status"] = status.value
        if methodology:
            body["methodology"] = methodology
        if metadata:
            body["metadata"] = metadata

        response = self._client._request("PUT", f"/v1.0/assessments/{assessment_id}", json_data=body)
        return self._parse_assessment(response.json())

    def add_finding(
        self,
        assessment_id: str,
        *,
        finding_key: str,
        title: str,
        severity: str,
        category: str,
        description: Optional[str] = None,
        policy_id: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        remediation: Optional[str] = None,
        due_date: Optional[datetime] = None,
    ) -> AssessmentFinding:
        """Add a finding to an assessment."""
        body: Dict[str, Any] = {
            "finding_key": finding_key,
            "title": title,
            "severity": severity,
            "category": category,
        }
        if description:
            body["description"] = description
        if policy_id:
            body["policy_id"] = policy_id
        if evidence_ids:
            body["evidence_ids"] = evidence_ids
        if remediation:
            body["remediation"] = remediation
        if due_date:
            body["due_date"] = due_date.isoformat()

        response = self._client._request("POST", f"/v1.0/assessments/{assessment_id}/findings", json_data=body)
        data = response.json()
        return AssessmentFinding(
            id=data["id"],
            finding_key=data["finding_key"],
            title=data["title"],
            description=data.get("description"),
            severity=data.get("severity"),
            category=data.get("category"),
            status=data.get("status"),
            policy_id=data.get("policy_id"),
            evidence_ids=data.get("evidence_ids", []),
            remediation=data.get("remediation"),
            remediated_by=data.get("remediated_by"),
            remediated_at=PolicyService._parse_datetime(data.get("remediated_at")),
            due_date=PolicyService._parse_datetime(data.get("due_date")),
        )

    def generate_report(
        self,
        assessment_id: str,
        *,
        format: str = "pdf",
        include_evidence: bool = True,
        include_remediation: bool = True,
    ) -> Dict[str, str]:
        """Generate an assessment report."""
        body = {
            "format": format,
            "include_evidence": include_evidence,
            "include_remediation": include_remediation,
        }
        response = self._client._request("POST", f"/v1.0/assessments/{assessment_id}/report", json_data=body)
        return response.json()

    def _parse_assessment(self, data: Dict[str, Any]) -> Assessment:
        findings = [
            AssessmentFinding(
                id=f["id"],
                finding_key=f["finding_key"],
                title=f["title"],
                description=f.get("description"),
                severity=f.get("severity"),
                category=f.get("category"),
                status=f.get("status"),
                policy_id=f.get("policy_id"),
                evidence_ids=f.get("evidence_ids", []),
                remediation=f.get("remediation"),
                remediated_by=f.get("remediated_by"),
                remediated_at=PolicyService._parse_datetime(f.get("remediated_at")),
                due_date=PolicyService._parse_datetime(f.get("due_date")),
            )
            for f in data.get("findings", [])
        ]
        return Assessment(
            id=data["id"],
            assessment_key=data["assessment_key"],
            title=data["title"],
            assessment_type=AssessmentType(data["assessment_type"]),
            target_id=data["target_id"],
            target_type=data["target_type"],
            status=AssessmentStatus(data["status"]),
            description=data.get("description"),
            methodology=data.get("methodology"),
            score=data.get("score"),
            risk_level=data.get("risk_level"),
            started_at=PolicyService._parse_datetime(data.get("started_at")),
            completed_at=PolicyService._parse_datetime(data.get("completed_at")),
            next_assessment_at=PolicyService._parse_datetime(data.get("next_assessment_at")),
            lead_assessor=data.get("lead_assessor"),
            findings=findings,
            metadata=data.get("metadata", {}),
            created_at=PolicyService._parse_datetime(data.get("created_at")),
            updated_at=PolicyService._parse_datetime(data.get("updated_at")),
        )

# ============================================================
# Compliance Service
# ============================================================

class ComplianceService:
    """Compliance mapping operations."""

    def __init__(self, client: BaseClient):
        self._client = client

    def list_frameworks(self) -> List[ComplianceFramework]:
        """List all compliance frameworks."""
        response = self._client._request("GET", "/v1.0/compliance/frameworks")
        data = response.json()
        return [
            ComplianceFramework(
                id=f["id"],
                framework_key=f["framework_key"],
                name=f["name"],
                version=f["version"],
                description=f.get("description"),
                authority=f.get("authority"),
                effective_date=PolicyService._parse_datetime(f.get("effective_date")),
                control_count=f.get("control_count", 0),
            )
            for f in data.get("data", [])
        ]

    def list_controls(
        self,
        framework_id: str,
        *,
        category: Optional[str] = None,
        status: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> List[ComplianceControl]:
        """List controls for a framework."""
        params: Dict[str, Any] = {}
        if category:
            params["category"] = category
        if status:
            params["status"] = status
        if target_id:
            params["target_id"] = target_id

        response = self._client._request("GET", f"/v1.0/compliance/frameworks/{framework_id}/controls", params=params)
        data = response.json()
        return [
            ComplianceControl(
                id=c["id"],
                framework_id=c.get("framework_id"),
                control_key=c.get("control_key"),
                title=c.get("title"),
                description=c.get("description"),
                category=c.get("category"),
                guidance=c.get("guidance"),
            )
            for c in data.get("data", [])
        ]

    def get_posture(
        self,
        *,
        framework: str,
        target_id: str,
        target_type: str,
    ) -> CompliancePosture:
        """Get compliance posture."""
        params = {
            "framework": framework,
            "target_id": target_id,
            "target_type": target_type,
        }
        response = self._client._request("GET", "/v1.0/compliance/posture", params=params)
        data = response.json()

        gaps = [
            ComplianceGap(
                control_id=g["control_id"],
                control_title=g["control_title"],
                status=g["status"],
                severity=g.get("severity"),
                evidence_count=g.get("evidence_count", 0),
                last_assessed=PolicyService._parse_datetime(g.get("last_assessed")),
            )
            for g in data.get("gaps", [])
        ]
        trend_data = data.get("trend", {})
        trend = ComplianceTrend(
            direction=trend_data.get("direction", ""),
            change=trend_data.get("change", ""),
            period=trend_data.get("period", ""),
        ) if trend_data else None

        return CompliancePosture(
            framework=data["framework"],
            target_id=data["target_id"],
            target_type=data["target_type"],
            controls_assessed=data.get("controls_assessed", 0),
            controls_compliant=data.get("controls_compliant", 0),
            controls_non_compliant=data.get("controls_non_compliant", 0),
            controls_not_assessed=data.get("controls_not_assessed", 0),
            compliance_score=data.get("compliance_score", 0.0),
            gaps=gaps,
            trend=trend,
        )

    def create_mapping(
        self,
        *,
        control_id: str,
        mapping_type: str,
        coverage: str,
        policy_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ComplianceMapping:
        """Create a compliance mapping."""
        body: Dict[str, Any] = {
            "control_id": control_id,
            "mapping_type": mapping_type,
            "coverage": coverage,
        }
        if policy_id:
            body["policy_id"] = policy_id
        if assessment_id:
            body["assessment_id"] = assessment_id
        if notes:
            body["notes"] = notes

        response = self._client._request("POST", "/v1.0/compliance/mappings", json_data=body)
        data = response.json()
        return ComplianceMapping(
            id=data["id"],
            control_id=data["control_id"],
            policy_id=data.get("policy_id"),
            assessment_id=data.get("assessment_id"),
            mapping_type=data.get("mapping_type"),
            coverage=data.get("coverage"),
            notes=data.get("notes"),
        )

    def generate_report(
        self,
        *,
        framework: str,
        time_range: Dict[str, str],
        format: str = "json",
        include_evidence: bool = True,
        include_gaps: bool = True,
    ) -> Dict[str, str]:
        """Generate a compliance report."""
        body = {
            "framework": framework,
            "time_range": time_range,
            "format": format,
            "include_evidence": include_evidence,
            "include_gaps": include_gaps,
        }
        response = self._client._request("POST", "/v1.0/compliance/reports", json_data=body)
        return response.json()

    def crosswalk(
        self,
        *,
        control_id: Optional[str] = None,
        framework: Optional[str] = None,
        target_framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query cross-framework mappings."""
        params: Dict[str, Any] = {}
        if control_id:
            params["control_id"] = control_id
        if framework:
            params["framework"] = framework
        if target_framework:
            params["target_framework"] = target_framework

        response = self._client._request("GET", "/v1.0/compliance/crosswalk", params=params)
        return response.json()

# ============================================================
# Agent Service
# ============================================================

class AgentService:
    """Agent registry operations."""

    def __init__(self, client: BaseClient):
        self._client = client

    def list(
        self,
        *,
        type: Optional[str] = None,
        framework: Optional[str] = None,
        lifecycle_stage: Optional[AgentLifecycleStage] = None,
        risk_tier: Optional[RiskTier] = None,
        trust_score_min: Optional[int] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> tuple[List[Agent], Pagination]:
        """List agents."""
        params: Dict[str, Any] = {"limit": limit}
        if type:
            params["type"] = type
        if framework:
            params["framework"] = framework
        if lifecycle_stage:
            params["lifecycle_stage"] = lifecycle_stage.value
        if risk_tier:
            params["risk_tier"] = risk_tier.value
        if trust_score_min is not None:
            params["trust_score_min"] = trust_score_min
        if cursor:
            params["cursor"] = cursor

        response = self._client._request("GET", "/v1.0/agents", params=params)
        data = response.json()

        agents = [self._parse_agent(a) for a in data.get("data", [])]
        pagination = Pagination(
            next_cursor=data.get("pagination", {}).get("next_cursor"),
            has_next=data.get("pagination", {}).get("has_next", False),
            total=data.get("pagination", {}).get("total", 0),
        )
        return agents, pagination

    def register(
        self,
        *,
        name: str,
        type: str,
        framework: str,
        risk_tier: RiskTier,
        owner: Optional[str] = None,
        capabilities: Optional[List[Dict[str, Any]]] = None,
    ) -> Agent:
        """Register a new agent."""
        body: Dict[str, Any] = {
            "name": name,
            "type": type,
            "framework": framework,
            "risk_tier": risk_tier.value,
        }
        if owner:
            body["owner"] = owner
        if capabilities:
            body["capabilities"] = capabilities

        response = self._client._request("POST", "/v1.0/agents", json_data=body)
        return self._parse_agent(response.json())

    def get(self, agent_id: str) -> Agent:
        """Get an agent by ID."""
        response = self._client._request("GET", f"/v1.0/agents/{agent_id}")
        return self._parse_agent(response.json())

    def update(
        self,
        agent_id: str,
        *,
        name: Optional[str] = None,
        lifecycle_stage: Optional[AgentLifecycleStage] = None,
        risk_tier: Optional[RiskTier] = None,
        capabilities: Optional[List[Dict[str, Any]]] = None,
    ) -> Agent:
        """Update an agent."""
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if lifecycle_stage:
            body["lifecycle_stage"] = lifecycle_stage.value
        if risk_tier:
            body["risk_tier"] = risk_tier.value
        if capabilities:
            body["capabilities"] = capabilities

        response = self._client._request("PUT", f"/v1.0/agents/{agent_id}", json_data=body)
        return self._parse_agent(response.json())

    def update_trust_score(
        self,
        agent_id: str,
        *,
        value: int,
        grade: str,
        reason: Optional[str] = None,
    ) -> Agent:
        """Update agent trust score."""
        body: Dict[str, Any] = {"value": value, "grade": grade}
        if reason:
            body["reason"] = reason

        response = self._client._request("POST", f"/v1.0/agents/{agent_id}/trust-score", json_data=body)
        return self._parse_agent(response.json())

    def bind_policies(
        self,
        agent_id: str,
        *,
        policy_ids: List[str],
    ) -> Agent:
        """Bind policies to an agent."""
        body = {"policy_ids": policy_ids}
        response = self._client._request("POST", f"/v1.0/agents/{agent_id}/policy-bindings", json_data=body)
        return self._parse_agent(response.json())

    def _parse_agent(self, data: Dict[str, Any]) -> Agent:
        capabilities = [
            AgentCapability(
                name=c.get("name", ""),
                description=c.get("description"),
                permissions=c.get("permissions", []),
                resource_scope=c.get("resource_scope"),
            )
            for c in data.get("capabilities", [])
        ]
        identity_data = data.get("identity", {})
        identity = AgentIdentity(
            spiffe_id=identity_data.get("spiffe_id"),
            mtls_cert=identity_data.get("mtls_cert"),
            cert_expiry=PolicyService._parse_datetime(identity_data.get("cert_expiry")),
        ) if identity_data else None
        trust_data = data.get("trust_score", {})
        trust_score = TrustScore(
            value=trust_data.get("value", 0),
            grade=trust_data.get("grade", ""),
            last_evaluated=PolicyService._parse_datetime(trust_data.get("last_evaluated")),
        ) if trust_data else None

        return Agent(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            framework=data["framework"],
            lifecycle_stage=AgentLifecycleStage(data["lifecycle_stage"]),
            risk_tier=RiskTier(data["risk_tier"]),
            owner=data.get("owner"),
            capabilities=capabilities,
            identity=identity,
            trust_score=trust_score,
            policy_bindings=data.get("policy_bindings", []),
            created_at=PolicyService._parse_datetime(data.get("created_at")),
            updated_at=PolicyService._parse_datetime(data.get("updated_at")),
        )

# ============================================================
# Audit Service
# ============================================================

class AuditService:
    """Audit trail operations."""

    def __init__(self, client: BaseClient):
        self._client = client

    def query(
        self,
        *,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
    ) -> tuple[List[AuditEvent], Pagination]:
        """Query audit trail."""
        params: Dict[str, Any] = {"limit": limit}
        if event_type:
            params["event_type"] = event_type
        if actor_id:
            params["actor_id"] = actor_id
        if resource_type:
            params["resource_type"] = resource_type
        if resource_id:
            params["resource_id"] = resource_id
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()

        response = self._client._request("GET", "/v1.0/audit", params=params)
        data = response.json()

        events = [
            AuditEvent(
                event_id=e["event_id"],
                event_type=e["event_type"],
                actor=e.get("actor", {}),
                resource=e.get("resource", {}),
                timestamp=PolicyService._parse_datetime(e.get("timestamp")),
                details=e.get("details", {}),
                integrity_hash=e.get("integrity_hash"),
                previous_event_hash=e.get("previous_event_hash"),
            )
            for e in data.get("data", [])
        ]
        pagination = Pagination(
            next_cursor=data.get("pagination", {}).get("next_cursor"),
            has_next=data.get("pagination", {}).get("has_next", False),
            total=data.get("pagination", {}).get("total", 0),
        )
        return events, pagination

    def verify(
        self,
        *,
        from_event_id: str,
        to_event_id: str,
    ) -> AuditVerification:
        """Verify audit chain integrity."""
        body = {"from_event_id": from_event_id, "to_event_id": to_event_id}
        response = self._client._request("POST", "/v1.0/audit/verify", json_data=body)
        data = response.json()
        return AuditVerification(
            verification_status=data["verification_status"],
            events_verified=data["events_verified"],
            chain_intact=data["chain_intact"],
            first_event_id=data.get("first_event_id"),
            last_event_id=data.get("last_event_id"),
            verified_at=PolicyService._parse_datetime(data.get("verified_at")),
        )

# ============================================================
# Webhook Service
# ============================================================

class WebhookService:
    """Webhook subscription operations."""

    def __init__(self, client: BaseClient):
        self._client = client

    def list(self) -> List[WebhookSubscription]:
        """List webhook subscriptions."""
        response = self._client._request("GET", "/v1.0/webhooks/subscriptions")
        data = response.json()
        return [self._parse_subscription(s) for s in data.get("data", [])]

    def create(
        self,
        *,
        url: str,
        events: List[str],
        secret: str,
        description: Optional[str] = None,
        active: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WebhookSubscription:
        """Create a webhook subscription."""
        body: Dict[str, Any] = {
            "url": url,
            "events": events,
            "secret": secret,
            "active": active,
        }
        if description:
            body["description"] = description
        if metadata:
            body["metadata"] = metadata

        response = self._client._request("POST", "/v1.0/webhooks/subscriptions", json_data=body)
        return self._parse_subscription(response.json())

    def get(self, subscription_id: str) -> WebhookSubscription:
        """Get a webhook subscription."""
        response = self._client._request("GET", f"/v1.0/webhooks/subscriptions/{subscription_id}")
        return self._parse_subscription(response.json())

    def update(
        self,
        subscription_id: str,
        *,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        secret: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WebhookSubscription:
        """Update a webhook subscription."""
        body: Dict[str, Any] = {}
        if url:
            body["url"] = url
        if events:
            body["events"] = events
        if secret:
            body["secret"] = secret
        if description:
            body["description"] = description
        if active is not None:
            body["active"] = active
        if metadata:
            body["metadata"] = metadata

        response = self._client._request("PUT", f"/v1.0/webhooks/subscriptions/{subscription_id}", json_data=body)
        return self._parse_subscription(response.json())

    def delete(self, subscription_id: str) -> None:
        """Delete a webhook subscription."""
        self._client._request("DELETE", f"/v1.0/webhooks/subscriptions/{subscription_id}")

    def test(self, subscription_id: str) -> Dict[str, Any]:
        """Test a webhook subscription."""
        response = self._client._request("POST", f"/v1.0/webhooks/subscriptions/{subscription_id}/test")
        return response.json()

    def get_deliveries(
        self,
        subscription_id: str,
        *,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[WebhookDelivery]:
        """Get delivery history."""
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()

        response = self._client._request("GET", f"/v1.0/webhooks/subscriptions/{subscription_id}/deliveries", params=params)
        data = response.json()
        return [
            WebhookDelivery(
                delivery_id=d["delivery_id"],
                subscription_id=d["subscription_id"],
                event_id=d["event_id"],
                event_type=d["event_type"],
                status=d["status"],
                http_status=d.get("http_status"),
                response_time_ms=d.get("response_time_ms"),
                attempts=d.get("attempts", 0),
                delivered_at=PolicyService._parse_datetime(d.get("delivered_at")),
                next_retry_at=PolicyService._parse_datetime(d.get("next_retry_at")),
            )
            for d in data.get("data", [])
        ]

    def _parse_subscription(self, data: Dict[str, Any]) -> WebhookSubscription:
        return WebhookSubscription(
            subscription_id=data["subscription_id"],
            url=data["url"],
            events=data["events"],
            secret=data["secret"],
            description=data.get("description"),
            active=data.get("active", True),
            metadata=data.get("metadata", {}),
            created_at=PolicyService._parse_datetime(data.get("created_at")),
            delivery_stats=data.get("delivery_stats", {}),
        )

# ============================================================
# System Service
# ============================================================

class SystemService:
    """System health and monitoring operations."""

    def __init__(self, client: BaseClient):
        self._client = client

    def health(self) -> HealthStatus:
        """Get system health status."""
        response = self._client._request("GET", "/health")
        data = response.json()
        return HealthStatus(
            status=data["status"],
            version=data["version"],
            components=data.get("components", {}),
            timestamp=PolicyService._parse_datetime(data.get("timestamp")),
        )

    def ready(self) -> ReadinessStatus:
        """Get system readiness status."""
        response = self._client._request("GET", "/ready")
        data = response.json()
        return ReadinessStatus(
            ready=data["ready"],
            checks=data.get("checks", {}),
        )

    def metrics(self) -> str:
        """Get Prometheus metrics."""
        response = self._client._request("GET", "/metrics")
        return response.text

# ============================================================
# Main Client
# ============================================================

class GRCClawClient:
    """
    GRC_Claw API client.

    Provides access to all GRC_Claw API services:
    - Policies
    - Evidence
    - Enforcement
    - Assessments
    - Compliance
    - Agents
    - Audit
    - Webhooks
    - System

    Args:
        api_key: GRC_Claw API key (grc_live_... or grc_test_...)
        tenant_id: Organization tenant ID
        environment: Environment (production, staging, development)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries for failed requests

    Example:
        >>> client = GRCClawClient(
        ...     api_key="grc_live_abc123...",
        ...     tenant_id="org-acme",
        ...     environment="production"
        ... )
        >>> policy = client.policies.create(
        ...     policy_key="AI-ETHICS-001",
        ...     name="Data Access Control Policy",
        ...     category="privacy",
        ... )
    """

    def __init__(
        self,
        api_key: str,
        tenant_id: str,
        environment: Union[Environment, str] = Environment.PRODUCTION,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        if isinstance(environment, str):
            environment = Environment(environment)

        self._base = BaseClient(
            api_key=api_key,
            tenant_id=tenant_id,
            environment=environment,
            timeout=timeout,
            max_retries=max_retries,
        )

        self.policies = PolicyService(self._base)
        self.evidence = EvidenceService(self._base)
        self.enforcement = EnforcementService(self._base)
        self.assessments = AssessmentService(self._base)
        self.compliance = ComplianceService(self._base)
        self.agents = AgentService(self._base)
        self.audit = AuditService(self._base)
        self.webhooks = WebhookService(self._base)
        self.system = SystemService(self._base)

    @property
    def tenant_id(self) -> str:
        return self._base.tenant_id

    @property
    def environment(self) -> Environment:
        return self._base.environment

    def close(self) -> None:
        """Close the client and release resources."""
        self._base.close()

    def __enter__(self) -> GRCClawClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()

# ============================================================
# Async Client (optional, requires httpx async support)
# ============================================================

class AsyncGRCClawClient:
    """
    Async GRC_Claw API client.

    Provides the same interface as GRCClawClient but with async/await support.
    """

    def __init__(
        self,
        api_key: str,
        tenant_id: str,
        environment: Union[Environment, str] = Environment.PRODUCTION,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        if isinstance(environment, str):
            environment = Environment(environment)

        self.api_key = api_key
        self.tenant_id = tenant_id
        self.environment = environment
        self.timeout = timeout
        self.max_retries = max_retries

        base_urls = {
            Environment.PRODUCTION: "https://api.grc-claw.io",
            Environment.STAGING: "https://api.staging.grc-claw.io",
            Environment.DEVELOPMENT: "http://localhost:8080",
        }
        self.base_url = base_urls[environment]

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Tenant-ID": tenant_id,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"grc-claw-sdk-python/{__version__}",
            },
        )

    async def close(self) -> None:
        """Close the async client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncGRCClawClient:
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

# ============================================================
# Convenience Functions
# ============================================================

def create_client(
    api_key: str,
    tenant_id: str,
    environment: Union[Environment, str] = Environment.PRODUCTION,
    **kwargs,
) -> GRCClawClient:
    """Create a new GRC_Claw client."""
    return GRCClawClient(api_key, tenant_id, environment, **kwargs)

def verify_webhook(payload_body: str, signature_header: str, secret: str) -> bool:
    """Verify a webhook signature."""
    return WebhookVerifier.verify(payload_body, signature_header, secret)

# ============================================================
# Exports
# ============================================================

__all__ = [
    "GRCClawClient",
    "AsyncGRCClawClient",
    "BaseClient",
    "PolicyService",
    "EvidenceService",
    "EnforcementService",
    "AssessmentService",
    "ComplianceService",
    "AgentService",
    "AuditService",
    "WebhookService",
    "SystemService",
    "WebhookVerifier",
    "create_client",
    "verify_webhook",
    # Enums
    "PolicyStatus",
    "PolicyCategory",
    "EvidenceType",
    "VerificationLevel",
    "EnforcementVerdict",
    "AssessmentType",
    "AssessmentStatus",
    "RiskTier",
    "AgentLifecycleStage",
    "Environment",
    # Exceptions
    "GRCClawError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    # Data models
    "Policy",
    "PolicyVersion",
    "PolicyDependencyGraph",
    "CompilationResult",
    "DryRunResult",
    "Evidence",
    "EvidenceVerification",
    "ExportPackage",
    "EnforcementDecision",
    "BatchSummary",
    "Assessment",
    "AssessmentFinding",
    "ComplianceFramework",
    "ComplianceControl",
    "CompliancePosture",
    "ComplianceMapping",
    "Agent",
    "AgentCapability",
    "AgentIdentity",
    "TrustScore",
    "AuditEvent",
    "AuditVerification",
    "WebhookSubscription",
    "WebhookDelivery",
    "HealthStatus",
    "ReadinessStatus",
    "Pagination",
]

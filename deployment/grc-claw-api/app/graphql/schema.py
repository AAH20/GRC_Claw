"""GRC_Claw GraphQL schema using Strawberry."""

from datetime import datetime
from typing import Annotated, Any, Generic, Optional, TypeVar
from uuid import uuid4

import strawberry
from strawberry.types import Info

T = TypeVar("T")


# ============================================================
# Scalars
# ============================================================

@strawberry.scalar(serialization_alias="DateTime")
class DateTimeScalar:
    """DateTime scalar."""

    @staticmethod
    def serialize(value: datetime) -> str:
        return value.isoformat()

    @staticmethod
    def parse_value(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


@strawberry.scalar(serialization_alias="JSON")
class JSONScalar:
    """JSON scalar."""

    @staticmethod
    def serialize(value: Any) -> Any:
        return value

    @staticmethod
    def parse_value(value: Any) -> Any:
        return value


# ============================================================
# Enums
# ============================================================

@strawberry.enum
class PolicyStatus:
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@strawberry.enum
class PolicyCategory:
    ETHICS = "ethics"
    SAFETY = "safety"
    PRIVACY = "privacy"
    FAIRNESS = "fairness"


@strawberry.enum
class EvidenceType:
    ARTIFACT = "artifact"
    OBSERVATION = "observation"
    INTERVIEW = "interview"
    ANALYSIS = "analysis"
    LOG = "log"


@strawberry.enum
class VerificationLevel:
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


@strawberry.enum
class EnforcementVerdict:
    ALLOW = "ALLOW"
    ALLOW_WITH_REDACTION = "ALLOW_WITH_REDACTION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"


@strawberry.enum
class AssessmentType:
    RISK = "risk"
    COMPLIANCE = "compliance"
    MATURITY = "maturity"
    READINESS = "readiness"


@strawberry.enum
class AssessmentStatus:
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@strawberry.enum
class ComplianceStatus:
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_ASSESSED = "not_assessed"
    EXEMPT = "exempt"


@strawberry.enum
class AgentLifecycleStage:
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"
    QUARANTINED = "quarantined"


@strawberry.enum
class RiskTier:
    PROHIBITED = "prohibited"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


# ============================================================
# Types
# ============================================================

@strawberry.type
class PageInfo:
    """Pagination page info."""

    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None
    total_count: int = 0


@strawberry.type
class User:
    """User type."""

    id: strawberry.ID
    name: str
    email: str
    roles: list[str]


@strawberry.type
class Policy:
    """Policy type."""

    id: strawberry.ID
    policy_key: str
    name: str
    description: Optional[str] = None
    category: PolicyCategory
    status: PolicyStatus
    version: str
    framework_tags: list[str]
    effective_date: Optional[DateTimeScalar] = None
    expiry_date: Optional[DateTimeScalar] = None
    owner: Optional[User] = None
    agent_bindings: list["Agent"]
    cedar_policy: Optional[str] = None
    rego_policy: Optional[str] = None
    metadata: Optional[JSONScalar] = None
    compliance_mappings: list["ComplianceMapping"]
    dependencies: list["Policy"]
    dependents: list["Policy"]
    versions: list["PolicyVersion"]
    created_at: DateTimeScalar
    updated_at: DateTimeScalar
    created_by: Optional[User] = None
    updated_by: Optional[User] = None


@strawberry.type
class PolicyVersion:
    """Policy version type."""

    version: str
    status: str
    change_summary: Optional[str] = None
    created_at: DateTimeScalar
    created_by: Optional[User] = None


@strawberry.type
class EvidenceSource:
    """Evidence source type."""

    type: str
    system: str
    collection_method: str


@strawberry.type
class EvidenceContent:
    """Evidence content type."""

    format: str
    data: str
    hash: Optional[str] = None


@strawberry.type
class EvidenceContext:
    """Evidence context type."""

    environment: str
    region: Optional[str] = None
    timestamp: DateTimeScalar
    metadata: Optional[JSONScalar] = None


@strawberry.type
class ValidationStatus:
    """Validation status type."""

    status: str
    validated_by: Optional[User] = None
    validated_at: Optional[DateTimeScalar] = None
    confidence_score: float = 0.0


@strawberry.type
class CustodyEvent:
    """Chain of custody event type."""

    action: str
    actor: str
    timestamp: DateTimeScalar
    hash: str


@strawberry.type
class Evidence:
    """Evidence type."""

    id: strawberry.ID
    policy: Optional[Policy] = None
    assessment: Optional["Assessment"] = None
    source: EvidenceSource
    evidence_type: EvidenceType
    content: EvidenceContent
    context: EvidenceContext
    validation: ValidationStatus
    verification_level: VerificationLevel
    chain_of_custody: list[CustodyEvent]
    retention_class: str = "standard"
    created_at: DateTimeScalar
    expires_at: Optional[DateTimeScalar] = None


@strawberry.type
class EnforcementDecision:
    """Enforcement decision type."""

    id: strawberry.ID
    verdict: EnforcementVerdict
    policy: Policy
    policy_version: str
    agent: "Agent"
    action: str
    resource: str
    context: Optional[JSONScalar] = None
    evidence_hash: Optional[str] = None
    timestamp: DateTimeScalar
    ttl: int = 300
    signature: Optional[str] = None
    matched_rules: list[str]
    evaluation_time_ms: float = 0.0


@strawberry.type
class AssessmentFinding:
    """Assessment finding type."""

    id: strawberry.ID
    finding_key: str
    title: str
    description: Optional[str] = None
    severity: str
    category: Optional[str] = None
    status: str
    policy: Optional[Policy] = None
    evidence: list[Evidence]
    remediation: Optional[str] = None
    remediated_by: Optional[User] = None
    remediated_at: Optional[DateTimeScalar] = None
    due_date: Optional[DateTimeScalar] = None
    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class Assessment:
    """Assessment type."""

    id: strawberry.ID
    assessment_key: str
    title: str
    description: Optional[str] = None
    assessment_type: AssessmentType
    target_id: str
    target_type: str
    status: AssessmentStatus
    methodology: Optional[str] = None
    score: Optional[float] = None
    risk_level: Optional[str] = None
    started_at: Optional[DateTimeScalar] = None
    completed_at: Optional[DateTimeScalar] = None
    next_assessment_at: Optional[DateTimeScalar] = None
    lead_assessor: User
    findings: list[AssessmentFinding]
    evidence: list[Evidence]
    metadata: Optional[JSONScalar] = None
    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class ComplianceFramework:
    """Compliance framework type."""

    id: strawberry.ID
    framework_key: str
    name: str
    version: str
    description: Optional[str] = None
    authority: Optional[str] = None
    effective_date: Optional[DateTimeScalar] = None
    controls: list["ComplianceControl"]
    control_count: int = 0
    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class ComplianceControl:
    """Compliance control type."""

    id: strawberry.ID
    framework: ComplianceFramework
    control_key: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    guidance: Optional[str] = None
    mappings: list["ComplianceMapping"]
    status: ComplianceStatus
    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class ComplianceMapping:
    """Compliance mapping type."""

    id: strawberry.ID
    control: ComplianceControl
    policy: Optional[Policy] = None
    assessment: Optional[Assessment] = None
    mapping_type: str
    coverage: str
    notes: Optional[str] = None
    mapped_by: User
    mapped_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class ComplianceGap:
    """Compliance gap type."""

    control: ComplianceControl
    status: ComplianceStatus
    severity: str
    evidence_count: int = 0
    last_assessed: Optional[DateTimeScalar] = None


@strawberry.type
class ComplianceTrend:
    """Compliance trend type."""

    direction: str
    change: str
    period: str


@strawberry.type
class CompliancePosture:
    """Compliance posture type."""

    framework: ComplianceFramework
    target_id: str
    target_type: str
    controls_assessed: int = 0
    controls_compliant: int = 0
    controls_non_compliant: int = 0
    controls_not_assessed: int = 0
    compliance_score: float = 0.0
    gaps: list[ComplianceGap]
    trend: Optional[ComplianceTrend] = None


@strawberry.type
class AgentCapability:
    """Agent capability type."""

    name: str
    description: Optional[str] = None
    permissions: list[str]
    resource_scope: Optional[str] = None


@strawberry.type
class AgentIdentity:
    """Agent identity type."""

    spiffe_id: Optional[str] = None
    mtls_cert: Optional[str] = None
    cert_expiry: Optional[DateTimeScalar] = None


@strawberry.type
class TrustScore:
    """Trust score type."""

    value: int
    grade: str
    last_evaluated: Optional[DateTimeScalar] = None


@strawberry.type
class Agent:
    """Agent type."""

    id: strawberry.ID
    name: str
    type: str
    framework: str
    owner: User
    lifecycle_stage: AgentLifecycleStage
    risk_tier: RiskTier
    capabilities: list[AgentCapability]
    identity: Optional[AgentIdentity] = None
    trust_score: Optional[TrustScore] = None
    policy_bindings: list[Policy]
    created_at: DateTimeScalar
    updated_at: DateTimeScalar


@strawberry.type
class Actor:
    """Audit actor type."""

    type: str
    id: str
    name: Optional[str] = None


@strawberry.type
class Resource:
    """Audit resource type."""

    type: str
    id: str
    name: Optional[str] = None


@strawberry.type
class AuditEvent:
    """Audit event type."""

    id: strawberry.ID
    event_type: str
    actor: Actor
    resource: Resource
    timestamp: DateTimeScalar
    details: Optional[JSONScalar] = None
    integrity_hash: Optional[str] = None
    previous_event_hash: Optional[str] = None


# ============================================================
# Input Types
# ============================================================

@strawberry.input
class PolicyInput:
    """Create policy input."""

    policy_key: str
    name: str
    description: Optional[str] = None
    category: PolicyCategory
    framework_tags: list[str]
    cedar_policy: Optional[str] = None
    metadata: Optional[JSONScalar] = None


@strawberry.input
class PolicyUpdateInput:
    """Update policy input."""

    name: Optional[str] = None
    description: Optional[str] = None
    cedar_policy: Optional[str] = None
    metadata: Optional[JSONScalar] = None


@strawberry.input
class PolicyFilter:
    """Policy filter input."""

    status: Optional[PolicyStatus] = None
    category: Optional[PolicyCategory] = None
    framework: Optional[str] = None
    agent_id: Optional[strawberry.ID] = None


@strawberry.input
class EvidenceInput:
    """Submit evidence input."""

    policy_id: Optional[strawberry.ID] = None
    assessment_id: Optional[strawberry.ID] = None
    source: "EvidenceSourceInput"
    evidence_type: EvidenceType
    content: "EvidenceContentInput"
    context: "EvidenceContextInput"
    control_mapping: Optional["ControlMappingInput"] = None


@strawberry.input
class EvidenceSourceInput:
    """Evidence source input."""

    type: str
    system: str
    collection_method: str


@strawberry.input
class EvidenceContentInput:
    """Evidence content input."""

    format: str
    data: str


@strawberry.input
class EvidenceContextInput:
    """Evidence context input."""

    environment: str
    region: Optional[str] = None
    metadata: Optional[JSONScalar] = None


@strawberry.input
class ControlMappingInput:
    """Control mapping input."""

    control_id: str
    framework: str
    control_title: Optional[str] = None
    control_family: Optional[str] = None


@strawberry.input
class AssessmentInput:
    """Create assessment input."""

    assessment_key: str
    title: str
    description: Optional[str] = None
    assessment_type: AssessmentType
    target_id: str
    target_type: str
    methodology: Optional[str] = None
    lead_assessor: strawberry.ID
    metadata: Optional[JSONScalar] = None


@strawberry.input
class FindingInput:
    """Create finding input."""

    finding_key: str
    title: str
    description: Optional[str] = None
    severity: str
    category: Optional[str] = None
    policy_id: Optional[strawberry.ID] = None
    evidence_ids: list[strawberry.ID]
    remediation: Optional[str] = None
    due_date: Optional[DateTimeScalar] = None


@strawberry.input
class AgentInput:
    """Register agent input."""

    name: str
    type: str
    framework: str
    owner: strawberry.ID
    risk_tier: RiskTier
    capabilities: list["AgentCapabilityInput"]


@strawberry.input
class AgentCapabilityInput:
    """Agent capability input."""

    name: str
    description: Optional[str] = None
    permissions: list[str]
    resource_scope: Optional[str] = None


@strawberry.input
class ComplianceMappingInput:
    """Create compliance mapping input."""

    control_id: strawberry.ID
    policy_id: Optional[strawberry.ID] = None
    assessment_id: Optional[strawberry.ID] = None
    mapping_type: str
    coverage: str
    notes: Optional[str] = None


@strawberry.input
class DecisionInput:
    """Enforcement decision input."""

    agent_id: strawberry.ID
    action: str
    resource: str
    context: Optional[JSONScalar] = None
    policy_ids: list[strawberry.ID]
    include_evidence: bool = True


@strawberry.input
class EvidenceFilter:
    """Evidence filter input."""

    policy_id: Optional[strawberry.ID] = None
    assessment_id: Optional[strawberry.ID] = None
    evidence_type: Optional[EvidenceType] = None
    framework: Optional[str] = None
    control_id: Optional[str] = None
    verification_level: Optional[VerificationLevel] = None
    environment: Optional[str] = None
    date_from: Optional[DateTimeScalar] = None
    date_to: Optional[DateTimeScalar] = None
    query: Optional[str] = None


@strawberry.input
class AssessmentFilter:
    """Assessment filter input."""

    assessment_type: Optional[AssessmentType] = None
    status: Optional[AssessmentStatus] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    methodology: Optional[str] = None


@strawberry.input
class AgentFilter:
    """Agent filter input."""

    type: Optional[str] = None
    framework: Optional[str] = None
    lifecycle_stage: Optional[AgentLifecycleStage] = None
    risk_tier: Optional[RiskTier] = None
    trust_score_min: Optional[int] = None


@strawberry.input
class AuditFilter:
    """Audit filter input."""

    event_type: Optional[str] = None
    actor_id: Optional[strawberry.ID] = None
    resource_type: Optional[str] = None
    resource_id: Optional[strawberry.ID] = None
    date_from: Optional[DateTimeScalar] = None
    date_to: Optional[DateTimeScalar] = None


# ============================================================
# Connections (Relay-style pagination)
# ============================================================

@strawberry.type
class PolicyConnection:
    """Policy connection type."""

    edges: list["PolicyEdge"]
    page_info: PageInfo


@strawberry.type
class PolicyEdge:
    """Policy edge type."""

    node: Policy
    cursor: str


@strawberry.type
class EvidenceConnection:
    """Evidence connection type."""

    edges: list["EvidenceEdge"]
    page_info: PageInfo


@strawberry.type
class EvidenceEdge:
    """Evidence edge type."""

    node: Evidence
    cursor: str


@strawberry.type
class AssessmentConnection:
    """Assessment connection type."""

    edges: list["AssessmentEdge"]
    page_info: PageInfo


@strawberry.type
class AssessmentEdge:
    """Assessment edge type."""

    node: Assessment
    cursor: str


@strawberry.type
class AgentConnection:
    """Agent connection type."""

    edges: list["AgentEdge"]
    page_info: PageInfo


@strawberry.type
class AgentEdge:
    """Agent edge type."""

    node: Agent
    cursor: str


@strawberry.type
class AuditConnection:
    """Audit connection type."""

    edges: list["AuditEdge"]
    page_info: PageInfo


@strawberry.type
class AuditEdge:
    """Audit edge type."""

    node: AuditEvent
    cursor: str


# ============================================================
# Queries
# ============================================================

@strawberry.type
class Query:
    """GraphQL Query type."""

    @strawberry.field
    def policy(self, id: strawberry.ID) -> Optional[Policy]:
        """Get a policy by ID."""
        # In production, this would query the database
        return None

    @strawberry.field
    def policies(
        self,
        filter: Optional[PolicyFilter] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> PolicyConnection:
        """List policies with pagination."""
        return PolicyConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                total_count=0,
            ),
        )

    @strawberry.field
    def evidence(self, id: strawberry.ID) -> Optional[Evidence]:
        """Get evidence by ID."""
        return None

    @strawberry.field
    def evidences(
        self,
        filter: Optional[EvidenceFilter] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> EvidenceConnection:
        """List evidence with pagination."""
        return EvidenceConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                total_count=0,
            ),
        )

    @strawberry.field
    def enforcement_decision(self, id: strawberry.ID) -> Optional[EnforcementDecision]:
        """Get enforcement decision by ID."""
        return None

    @strawberry.field
    def enforcement_decisions(
        self,
        agent_id: Optional[strawberry.ID] = None,
        policy_id: Optional[strawberry.ID] = None,
        verdict: Optional[EnforcementVerdict] = None,
        date_from: Optional[DateTimeScalar] = None,
        date_to: Optional[DateTimeScalar] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
    ) -> list[EnforcementDecision]:
        """List enforcement decisions."""
        return []

    @strawberry.field
    def assessment(self, id: strawberry.ID) -> Optional[Assessment]:
        """Get assessment by ID."""
        return None

    @strawberry.field
    def assessments(
        self,
        filter: Optional[AssessmentFilter] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> AssessmentConnection:
        """List assessments with pagination."""
        return AssessmentConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                total_count=0,
            ),
        )

    @strawberry.field
    def compliance_framework(self, id: strawberry.ID) -> Optional[ComplianceFramework]:
        """Get compliance framework by ID."""
        return None

    @strawberry.field
    def compliance_frameworks(self) -> list[ComplianceFramework]:
        """List all compliance frameworks."""
        return []

    @strawberry.field
    def compliance_posture(
        self,
        framework_id: strawberry.ID,
        target_id: str,
        target_type: str,
    ) -> CompliancePosture:
        """Get compliance posture."""
        return CompliancePosture(
            framework=ComplianceFramework(
                id=strawberry.ID("fw-001"),
                framework_key="NIST-800-53",
                name="NIST SP 800-53 Rev 5",
                version="5",
                controls=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            target_id=target_id,
            target_type=target_type,
        )

    @strawberry.field
    def compliance_crosswalk(self, control_id: strawberry.ID) -> JSONScalar:
        """Get cross-framework control mapping."""
        return {}

    @strawberry.field
    def agent(self, id: strawberry.ID) -> Optional[Agent]:
        """Get agent by ID."""
        return None

    @strawberry.field
    def agents(
        self,
        filter: Optional[AgentFilter] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> AgentConnection:
        """List agents with pagination."""
        return AgentConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                total_count=0,
            ),
        )

    @strawberry.field
    def audit_event(self, id: strawberry.ID) -> Optional[AuditEvent]:
        """Get audit event by ID."""
        return None

    @strawberry.field
    def audit_events(
        self,
        filter: Optional[AuditFilter] = None,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> AuditConnection:
        """List audit events with pagination."""
        return AuditConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                total_count=0,
            ),
        )

    @strawberry.field
    def me(self) -> User:
        """Get current user."""
        return User(
            id=strawberry.ID("user-001"),
            name="Current User",
            email="user@example.com",
            roles=["admin"],
        )


# ============================================================
# Mutations
# ============================================================

@strawberry.type
class Mutation:
    """GraphQL Mutation type."""

    @strawberry.mutation
    def create_policy(self, input: PolicyInput) -> Policy:
        """Create a new policy."""
        now = datetime.now()
        return Policy(
            id=strawberry.ID(str(uuid4())),
            policy_key=input.policy_key,
            name=input.name,
            description=input.description,
            category=input.category,
            status=PolicyStatus.DRAFT,
            version="1.0.0",
            framework_tags=input.framework_tags,
            agent_bindings=[],
            cedar_policy=input.cedar_policy,
            metadata=input.metadata,
            compliance_mappings=[],
            dependencies=[],
            dependents=[],
            versions=[],
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def update_policy(self, id: strawberry.ID, input: PolicyUpdateInput) -> Policy:
        """Update a policy."""
        now = datetime.now()
        return Policy(
            id=id,
            policy_key="updated-key",
            name=input.name or "Updated Policy",
            description=input.description,
            category=PolicyCategory.SAFETY,
            status=PolicyStatus.DRAFT,
            version="1.1.0",
            framework_tags=[],
            agent_bindings=[],
            cedar_policy=input.cedar_policy,
            metadata=input.metadata,
            compliance_mappings=[],
            dependencies=[],
            dependents=[],
            versions=[],
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def delete_policy(self, id: strawberry.ID, force: Optional[bool] = False) -> bool:
        """Delete a policy."""
        return True

    @strawberry.mutation
    def compile_policy(self, id: strawberry.ID) -> JSONScalar:
        """Compile policy to Rego."""
        return {"status": "success", "rego_policy": "package grc.agent..."}

    @strawberry.mutation
    def dry_run_policy(self, id: strawberry.ID, test_inputs: list[JSONScalar]) -> JSONScalar:
        """Dry-run policy against test inputs."""
        return {"results": [], "summary": {"total": 0, "allowed": 0, "denied": 0}}

    @strawberry.mutation
    def activate_policy(self, id: strawberry.ID) -> Policy:
        """Activate a policy."""
        now = datetime.now()
        return Policy(
            id=id,
            policy_key="policy-key",
            name="Policy",
            category=PolicyCategory.SAFETY,
            status=PolicyStatus.ACTIVE,
            version="1.0.0",
            framework_tags=[],
            agent_bindings=[],
            compliance_mappings=[],
            dependencies=[],
            dependents=[],
            versions=[],
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def deprecate_policy(self, id: strawberry.ID) -> Policy:
        """Deprecate a policy."""
        now = datetime.now()
        return Policy(
            id=id,
            policy_key="policy-key",
            name="Policy",
            category=PolicyCategory.SAFETY,
            status=PolicyStatus.DEPRECATED,
            version="1.0.0",
            framework_tags=[],
            agent_bindings=[],
            compliance_mappings=[],
            dependencies=[],
            dependents=[],
            versions=[],
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def submit_evidence(self, input: EvidenceInput) -> Evidence:
        """Submit evidence."""
        now = datetime.now()
        return Evidence(
            id=strawberry.ID(str(uuid4())),
            source=EvidenceSource(
                type=input.source.type,
                system=input.source.system,
                collection_method=input.source.collection_method,
            ),
            evidence_type=input.evidence_type,
            content=EvidenceContent(
                format=input.content.format,
                data=input.content.data,
            ),
            context=EvidenceContext(
                environment=input.context.environment,
                region=input.context.region,
                timestamp=now,
                metadata=input.context.metadata,
            ),
            validation=ValidationStatus(status="pending"),
            verification_level=VerificationLevel.L0,
            chain_of_custody=[],
            created_at=now,
        )

    @strawberry.mutation
    def verify_evidence(self, id: strawberry.ID) -> JSONScalar:
        """Verify evidence integrity."""
        return {"status": "verified", "verification_level": "L2"}

    @strawberry.mutation
    def export_evidence_package(
        self,
        framework: str,
        time_range: JSONScalar,
        format: str,
        include_chain_of_custody: bool,
    ) -> JSONScalar:
        """Export evidence package."""
        return {"package_id": "pkg-001", "status": "processing"}

    @strawberry.mutation
    def request_decision(self, input: DecisionInput) -> EnforcementDecision:
        """Request enforcement decision."""
        now = datetime.now()
        return EnforcementDecision(
            id=strawberry.ID(str(uuid4())),
            verdict=EnforcementVerdict.ALLOW,
            policy=Policy(
                id=strawberry.ID("pol-001"),
                policy_key="AI-ETHICS-001",
                name="Data Access Control Policy",
                category=PolicyCategory.PRIVACY,
                status=PolicyStatus.ACTIVE,
                version="1.0.0",
                framework_tags=[],
                agent_bindings=[],
                compliance_mappings=[],
                dependencies=[],
                dependents=[],
                versions=[],
                created_at=now,
                updated_at=now,
            ),
            policy_version="1.0.0",
            agent=Agent(
                id=input.agent_id,
                name="Agent",
                type="agent",
                framework="custom",
                owner=User(id=strawberry.ID("user-001"), name="User", email="", roles=[]),
                lifecycle_stage=AgentLifecycleStage.ACTIVE,
                risk_tier=RiskTier.LIMITED,
                capabilities=[],
                policy_bindings=[],
                created_at=now,
                updated_at=now,
            ),
            action=input.action,
            resource=input.resource,
            context=input.context,
            timestamp=now,
            matched_rules=["allow_read_public"],
        )

    @strawberry.mutation
    def request_batch_decision(self, decisions: list[DecisionInput]) -> list[EnforcementDecision]:
        """Request batch enforcement decisions."""
        return [self.request_decision(d) for d in decisions]

    @strawberry.mutation
    def create_assessment(self, input: AssessmentInput) -> Assessment:
        """Create assessment."""
        now = datetime.now()
        return Assessment(
            id=strawberry.ID(str(uuid4())),
            assessment_key=input.assessment_key,
            title=input.title,
            description=input.description,
            assessment_type=input.assessment_type,
            target_id=input.target_id,
            target_type=input.target_type,
            status=AssessmentStatus.PLANNED,
            methodology=input.methodology,
            lead_assessor=User(id=input.lead_assessor, name="Assessor", email="", roles=[]),
            findings=[],
            evidence=[],
            metadata=input.metadata,
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def update_assessment(self, id: strawberry.ID, input: AssessmentInput) -> Assessment:
        """Update assessment."""
        now = datetime.now()
        return Assessment(
            id=id,
            assessment_key=input.assessment_key,
            title=input.title,
            description=input.description,
            assessment_type=input.assessment_type,
            target_id=input.target_id,
            target_type=input.target_type,
            status=AssessmentStatus.IN_PROGRESS,
            methodology=input.methodology,
            lead_assessor=User(id=input.lead_assessor, name="Assessor", email="", roles=[]),
            findings=[],
            evidence=[],
            metadata=input.metadata,
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def add_finding(self, assessment_id: strawberry.ID, input: FindingInput) -> AssessmentFinding:
        """Add finding to assessment."""
        now = datetime.now()
        return AssessmentFinding(
            id=strawberry.ID(str(uuid4())),
            finding_key=input.finding_key,
            title=input.title,
            description=input.description,
            severity=input.severity,
            category=input.category,
            status="open",
            evidence=[],
            remediation=input.remediation,
            due_date=input.due_date,
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def update_finding(self, id: strawberry.ID, input: FindingInput) -> AssessmentFinding:
        """Update finding."""
        now = datetime.now()
        return AssessmentFinding(
            id=id,
            finding_key=input.finding_key,
            title=input.title,
            description=input.description,
            severity=input.severity,
            category=input.category,
            status="open",
            evidence=[],
            remediation=input.remediation,
            due_date=input.due_date,
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def generate_assessment_report(self, id: strawberry.ID, format: str) -> JSONScalar:
        """Generate assessment report."""
        return {"report_id": "rpt-001", "status": "processing", "format": format}

    @strawberry.mutation
    def create_compliance_mapping(self, input: ComplianceMappingInput) -> ComplianceMapping:
        """Create compliance mapping."""
        now = datetime.now()
        return ComplianceMapping(
            id=strawberry.ID(str(uuid4())),
            control=ComplianceControl(
                id=input.control_id,
                framework=ComplianceFramework(
                    id=strawberry.ID("fw-001"),
                    framework_key="NIST-800-53",
                    name="NIST SP 800-53 Rev 5",
                    version="5",
                    controls=[],
                    created_at=now,
                    updated_at=now,
                ),
                control_key="AC-2",
                title="Account Management",
                status=ComplianceStatus.COMPLIANT,
                mappings=[],
                created_at=now,
                updated_at=now,
            ),
            mapping_type=input.mapping_type,
            coverage=input.coverage,
            notes=input.notes,
            mapped_by=User(id=strawberry.ID("user-001"), name="User", email="", roles=[]),
            mapped_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def delete_compliance_mapping(self, id: strawberry.ID) -> bool:
        """Delete compliance mapping."""
        return True

    @strawberry.mutation
    def generate_compliance_report(
        self,
        framework: str,
        time_range: JSONScalar,
        format: str,
    ) -> JSONScalar:
        """Generate compliance report."""
        return {"report_id": "rpt-001", "status": "processing"}

    @strawberry.mutation
    def register_agent(self, input: AgentInput) -> Agent:
        """Register agent."""
        now = datetime.now()
        return Agent(
            id=strawberry.ID(str(uuid4())),
            name=input.name,
            type=input.type,
            framework=input.framework,
            owner=User(id=input.owner, name="Owner", email="", roles=[]),
            lifecycle_stage=AgentLifecycleStage.PROPOSED,
            risk_tier=input.risk_tier,
            capabilities=[
                AgentCapability(
                    name=cap.name,
                    description=cap.description,
                    permissions=cap.permissions,
                    resource_scope=cap.resource_scope,
                )
                for cap in input.capabilities
            ],
            policy_bindings=[],
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def update_agent(self, id: strawberry.ID, input: AgentInput) -> Agent:
        """Update agent."""
        now = datetime.now()
        return Agent(
            id=id,
            name=input.name,
            type=input.type,
            framework=input.framework,
            owner=User(id=input.owner, name="Owner", email="", roles=[]),
            lifecycle_stage=AgentLifecycleStage.ACTIVE,
            risk_tier=input.risk_tier,
            capabilities=[
                AgentCapability(
                    name=cap.name,
                    description=cap.description,
                    permissions=cap.permissions,
                    resource_scope=cap.resource_scope,
                )
                for cap in input.capabilities
            ],
            policy_bindings=[],
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def delete_agent(self, id: strawberry.ID) -> bool:
        """Delete agent."""
        return True

    @strawberry.mutation
    def update_agent_trust_score(
        self,
        agent_id: strawberry.ID,
        value: int,
        grade: str,
        reason: str,
    ) -> Agent:
        """Update agent trust score."""
        now = datetime.now()
        return Agent(
            id=agent_id,
            name="Agent",
            type="agent",
            framework="custom",
            owner=User(id=strawberry.ID("user-001"), name="User", email="", roles=[]),
            lifecycle_stage=AgentLifecycleStage.ACTIVE,
            risk_tier=RiskTier.LIMITED,
            capabilities=[],
            trust_score=TrustScore(value=value, grade=grade, last_evaluated=now),
            policy_bindings=[],
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def bind_policy_to_agent(
        self,
        agent_id: strawberry.ID,
        policy_ids: list[strawberry.ID],
    ) -> Agent:
        """Bind policies to agent."""
        now = datetime.now()
        return Agent(
            id=agent_id,
            name="Agent",
            type="agent",
            framework="custom",
            owner=User(id=strawberry.ID("user-001"), name="User", email="", roles=[]),
            lifecycle_stage=AgentLifecycleStage.ACTIVE,
            risk_tier=RiskTier.LIMITED,
            capabilities=[],
            policy_bindings=[],
            created_at=now,
            updated_at=now,
        )

    @strawberry.mutation
    def unbind_policy_from_agent(
        self,
        agent_id: strawberry.ID,
        policy_ids: list[strawberry.ID],
    ) -> Agent:
        """Unbind policies from agent."""
        now = datetime.now()
        return Agent(
            id=agent_id,
            name="Agent",
            type="agent",
            framework="custom",
            owner=User(id=strawberry.ID("user-001"), name="User", email="", roles=[]),
            lifecycle_stage=AgentLifecycleStage.ACTIVE,
            risk_tier=RiskTier.LIMITED,
            capabilities=[],
            policy_bindings=[],
            created_at=now,
            updated_at=now,
        )


# ============================================================
# Subscriptions
# ============================================================

@strawberry.type
class Subscription:
    """GraphQL Subscription type."""

    @strawberry.subscription
    async def enforcement_decisions(self, agent_id: strawberry.ID) -> EnforcementDecision:
        """Subscribe to enforcement decisions for an agent."""
        # In production, this would use a message broker (Redis Pub/Sub, Kafka)
        import asyncio

        while True:
            await asyncio.sleep(5)
            now = datetime.now()
            yield EnforcementDecision(
                id=strawberry.ID(str(uuid4())),
                verdict=EnforcementVerdict.ALLOW,
                policy=Policy(
                    id=strawberry.ID("pol-001"),
                    policy_key="AI-ETHICS-001",
                    name="Data Access Control Policy",
                    category=PolicyCategory.PRIVACY,
                    status=PolicyStatus.ACTIVE,
                    version="1.0.0",
                    framework_tags=[],
                    agent_bindings=[],
                    compliance_mappings=[],
                    dependencies=[],
                    dependents=[],
                    versions=[],
                    created_at=now,
                    updated_at=now,
                ),
                policy_version="1.0.0",
                agent=Agent(
                    id=agent_id,
                    name="Agent",
                    type="agent",
                    framework="custom",
                    owner=User(id=strawberry.ID("user-001"), name="User", email="", roles=[]),
                    lifecycle_stage=AgentLifecycleStage.ACTIVE,
                    risk_tier=RiskTier.LIMITED,
                    capabilities=[],
                    policy_bindings=[],
                    created_at=now,
                    updated_at=now,
                ),
                action="read",
                resource="s3://data/public/dataset.csv",
                timestamp=now,
                matched_rules=["allow_read_public"],
            )

    @strawberry.subscription
    async def evidence_collected(self, policy_id: Optional[strawberry.ID] = None) -> Evidence:
        """Subscribe to evidence collection events."""
        import asyncio

        while True:
            await asyncio.sleep(10)
            now = datetime.now()
            yield Evidence(
                id=strawberry.ID(str(uuid4())),
                source=EvidenceSource(type="scan", system="aws-config", collection_method="api-query"),
                evidence_type=EvidenceType.ARTIFACT,
                content=EvidenceContent(format="json", data="{}"),
                context=EvidenceContext(environment="prod", timestamp=now),
                validation=ValidationStatus(status="pending"),
                verification_level=VerificationLevel.L0,
                chain_of_custody=[],
                created_at=now,
            )

    @strawberry.subscription
    async def policy_changed(self, tenant_id: strawberry.ID) -> Policy:
        """Subscribe to policy changes."""
        import asyncio

        while True:
            await asyncio.sleep(15)
            now = datetime.now()
            yield Policy(
                id=strawberry.ID(str(uuid4())),
                policy_key="AI-ETHICS-001",
                name="Data Access Control Policy",
                category=PolicyCategory.PRIVACY,
                status=PolicyStatus.ACTIVE,
                version="1.0.0",
                framework_tags=[],
                agent_bindings=[],
                compliance_mappings=[],
                dependencies=[],
                dependents=[],
                versions=[],
                created_at=now,
                updated_at=now,
            )

    @strawberry.subscription
    async def compliance_posture_changed(
        self,
        framework_id: strawberry.ID,
        target_id: strawberry.ID,
    ) -> CompliancePosture:
        """Subscribe to compliance posture changes."""
        import asyncio

        while True:
            await asyncio.sleep(30)
            now = datetime.now()
            yield CompliancePosture(
                framework=ComplianceFramework(
                    id=framework_id,
                    framework_key="NIST-800-53",
                    name="NIST SP 800-53 Rev 5",
                    version="5",
                    controls=[],
                    created_at=now,
                    updated_at=now,
                ),
                target_id=str(target_id),
                target_type="organization",
            )

    @strawberry.subscription
    async def agent_trust_score_changed(self, agent_id: strawberry.ID) -> Agent:
        """Subscribe to agent trust score changes."""
        import asyncio

        while True:
            await asyncio.sleep(20)
            now = datetime.now()
            yield Agent(
                id=agent_id,
                name="Agent",
                type="agent",
                framework="custom",
                owner=User(id=strawberry.ID("user-001"), name="User", email="", roles=[]),
                lifecycle_stage=AgentLifecycleStage.ACTIVE,
                risk_tier=RiskTier.LIMITED,
                capabilities=[],
                trust_score=TrustScore(value=85, grade="B", last_evaluated=now),
                policy_bindings=[],
                created_at=now,
                updated_at=now,
            )

    @strawberry.subscription
    async def audit_event_created(self) -> AuditEvent:
        """Subscribe to audit events."""
        import asyncio

        while True:
            await asyncio.sleep(5)
            now = datetime.now()
            yield AuditEvent(
                id=strawberry.ID(str(uuid4())),
                event_type="policy.created",
                actor=Actor(type="user", id="user-001", name="User"),
                resource=Resource(type="policy", id="pol-001", name="Policy"),
                timestamp=now,
            )


# ============================================================
# Schema
# ============================================================

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)

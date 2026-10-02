"""
Shared fixtures for GRC_Claw cross-domain integration tests.

Covers all three domains:
  - Marketing (45 projects)
  - Recruitment (10 projects)
  - UGC (10 projects)
  - Gated Communities (10 projects)
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Domain model helpers
# ---------------------------------------------------------------------------


@dataclass
class FakeResume:
    """Simulates output from the resume-parser service."""

    candidate_id: str
    name: str
    email: str
    skills: List[str] = field(default_factory=list)
    experience_years: float = 0.0
    education: List[Dict[str, Any]] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class FakeJobRequirement:
    """Simulates a job posting consumed by candidate-matcher."""

    job_id: str
    title: str
    required_skills: List[str] = field(default_factory=list)
    min_experience: float = 0.0
    preferred_skills: List[str] = field(default_factory=list)


@dataclass
class FakeMatchResult:
    """Output of candidate-matcher."""

    candidate_id: str
    job_id: str
    score: float
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)


@dataclass
class FakeContentItem:
    """A UGC piece (post, comment, review, etc.)."""

    content_id: str
    author_id: str
    body: str
    content_type: str = "post"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FakeModerationDecision:
    """Output of content-moderation-pipeline."""

    content_id: str
    action: str  # 'approve' | 'reject' | 'flag_for_review'
    reasons: List[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class FakeCommunityMember:
    """A gated-community member."""

    member_id: str
    user_id: str
    tier: str = "free"
    verified: bool = False
    roles: List[str] = field(default_factory=list)


@dataclass
class FakeTier:
    """A subscription/access tier."""

    tier_id: str
    name: str
    level: int
    permissions: List[str] = field(default_factory=list)


@dataclass
class FakeAccessDecision:
    """Output of access-control."""

    member_id: str
    resource: str
    granted: bool
    reason: str = ""


@dataclass
class FakeBiasReport:
    """Output of bias-detector."""

    entity_id: str
    entity_type: str
    bias_score: float
    flags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service stubs (simulate real FastAPI endpoints)
# ---------------------------------------------------------------------------


class ResumeParserStub:
    """Stub for resume-parser service."""

    def __init__(self) -> None:
        self.parsed: Dict[str, FakeResume] = {}
        self.call_count = 0

    async def parse(self, raw_text: str, candidate_id: Optional[str] = None) -> FakeResume:
        self.call_count += 1
        cid = candidate_id or str(uuid.uuid4())
        resume = FakeResume(
            candidate_id=cid,
            name="Test Candidate",
            email=f"{cid[:8]}@example.com",
            skills=["Python", "FastAPI", "SQL"],
            experience_years=3.5,
            education=[{"degree": "BS CS", "school": "Test University"}],
            raw_text=raw_text,
        )
        self.parsed[cid] = resume
        return resume


class CandidateMatcherStub:
    """Stub for candidate-matcher service."""

    def __init__(self) -> None:
        self.matches: List[FakeMatchResult] = []
        self.call_count = 0

    async def match(self, resume: FakeResume, job: FakeJobRequirement) -> FakeMatchResult:
        self.call_count += 1
        matched = [s for s in resume.skills if s in job.required_skills]
        missing = [s for s in job.required_skills if s not in resume.skills]
        score = len(matched) / max(len(job.required_skills), 1)
        if resume.experience_years < job.min_experience:
            score *= 0.5
        result = FakeMatchResult(
            candidate_id=resume.candidate_id,
            job_id=job.job_id,
            score=round(score, 2),
            matched_skills=matched,
            missing_skills=missing,
        )
        self.matches.append(result)
        return result


class ContentModerationPipelineStub:
    """Stub for content-moderation-pipeline service."""

    def __init__(self) -> None:
        self.decisions: List[FakeModerationDecision] = []
        self.call_count = 0
        self._flag_keywords = {"spam", "hate", "violence", "scam"}

    async def moderate(self, content: FakeContentItem) -> FakeModerationDecision:
        self.call_count += 1
        body_lower = content.body.lower()
        flagged = [kw for kw in self._flag_keywords if kw in body_lower]
        if flagged:
            decision = FakeModerationDecision(
                content_id=content.content_id,
                action="flag_for_review",
                reasons=flagged,
                confidence=0.85,
            )
        else:
            decision = FakeModerationDecision(
                content_id=content.content_id,
                action="approve",
                reasons=[],
                confidence=0.99,
            )
        self.decisions.append(decision)
        return decision


class ContentDiscoveryStub:
    """Stub for content-discovery service."""

    def __init__(self) -> None:
        self.items: Dict[str, FakeContentItem] = {}
        self.call_count = 0

    async def index(self, content: FakeContentItem) -> None:
        self.items[content.content_id] = content

    async def search(self, query: str, limit: int = 10) -> List[FakeContentItem]:
        self.call_count += 1
        q = query.lower()
        results = [
            item for item in self.items.values()
            if q in item.body.lower() or q in item.content_type.lower()
        ]
        return results[:limit]


class TierManagementStub:
    """Stub for tier-management service."""

    def __init__(self) -> None:
        self.tiers: Dict[str, FakeTier] = {}
        self.member_tiers: Dict[str, str] = {}
        self.call_count = 0

    async def create_tier(self, name: str, level: int, permissions: List[str]) -> FakeTier:
        self.call_count += 1
        tier = FakeTier(
            tier_id=str(uuid.uuid4()),
            name=name,
            level=level,
            permissions=permissions,
        )
        self.tiers[tier.tier_id] = tier
        return tier

    async def assign_tier(self, member_id: str, tier_id: str) -> None:
        self.call_count += 1
        self.member_tiers[member_id] = tier_id

    async def get_tier(self, member_id: str) -> Optional[FakeTier]:
        tier_id = self.member_tiers.get(member_id)
        return self.tiers.get(tier_id) if tier_id else None


class ModerationQueueStub:
    """Stub for moderation-queue service."""

    def __init__(self) -> None:
        self.queue: List[FakeModerationDecision] = []
        self.call_count = 0

    async def enqueue(self, decision: FakeModerationDecision) -> None:
        self.call_count += 1
        self.queue.append(decision)

    async def dequeue(self) -> Optional[FakeModerationDecision]:
        self.call_count += 1
        return self.queue.pop(0) if self.queue else None

    async def size(self) -> int:
        return len(self.queue)


class MemberVerificationStub:
    """Stub for member-verification service."""

    def __init__(self) -> None:
        self.verified: Dict[str, bool] = {}
        self.call_count = 0

    async def verify(self, member_id: str, method: str = "email") -> bool:
        self.call_count += 1
        self.verified[member_id] = True
        return True

    async def is_verified(self, member_id: str) -> bool:
        return self.verified.get(member_id, False)


class AccessControlStub:
    """Stub for access-control service."""

    def __init__(self) -> None:
        self.decisions: List[FakeAccessDecision] = []
        self.call_count = 0

    async def check_access(
        self, member: FakeCommunityMember, resource: str, required_permission: str
    ) -> FakeAccessDecision:
        self.call_count += 1
        tier = await self._get_tier(member)
        granted = (
            member.verified
            and tier is not None
            and required_permission in tier.permissions
        )
        decision = FakeAccessDecision(
            member_id=member.member_id,
            resource=resource,
            granted=granted,
            reason="" if granted else "insufficient_permissions_or_unverified",
        )
        self.decisions.append(decision)
        return decision

    async def _get_tier(self, member: FakeCommunityMember) -> Optional[FakeTier]:
        # In real impl this calls tier-management; stub returns a default
        return FakeTier(
            tier_id="default",
            name=member.tier,
            level=1,
            permissions=["read", "write"] if member.tier != "free" else ["read"],
        )


class BiasDetectorStub:
    """Stub for bias-detector service."""

    def __init__(self) -> None:
        self.reports: List[FakeBiasReport] = []
        self.call_count = 0

    async def analyze(self, entity_id: str, entity_type: str, text: str) -> FakeBiasReport:
        self.call_count += 1
        flags: List[str] = []
        text_lower = text.lower()
        bias_terms = {"always", "never", "obviously", "clearly", "everyone knows"}
        for term in bias_terms:
            if term in text_lower:
                flags.append(f"loaded_language:{term}")
        score = min(len(flags) * 0.2, 1.0)
        report = FakeBiasReport(
            entity_id=entity_id,
            entity_type=entity_type,
            bias_score=round(score, 2),
            flags=flags,
        )
        self.reports.append(report)
        return report


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def resume_parser() -> AsyncGenerator[ResumeParserStub, None]:
    yield ResumeParserStub()


@pytest_asyncio.fixture
async def candidate_matcher() -> AsyncGenerator[CandidateMatcherStub, None]:
    yield CandidateMatcherStub()


@pytest_asyncio.fixture
async def content_moderation() -> AsyncGenerator[ContentModerationPipelineStub, None]:
    yield ContentModerationPipelineStub()


@pytest_asyncio.fixture
async def content_discovery() -> AsyncGenerator[ContentDiscoveryStub, None]:
    yield ContentDiscoveryStub()


@pytest_asyncio.fixture
async def tier_management() -> AsyncGenerator[TierManagementStub, None]:
    yield TierManagementStub()


@pytest_asyncio.fixture
async def moderation_queue() -> AsyncGenerator[ModerationQueueStub, None]:
    yield ModerationQueueStub()


@pytest_asyncio.fixture
async def member_verification() -> AsyncGenerator[MemberVerificationStub, None]:
    yield MemberVerificationStub()


@pytest_asyncio.fixture
async def access_control() -> AsyncGenerator[AccessControlStub, None]:
    yield AccessControlStub()


@pytest_asyncio.fixture
async def bias_detector() -> AsyncGenerator[BiasDetectorStub, None]:
    yield BiasDetectorStub()


@pytest.fixture
def sample_job() -> FakeJobRequirement:
    return FakeJobRequirement(
        job_id="job-001",
        title="Senior Python Engineer",
        required_skills=["Python", "FastAPI", "SQL"],
        min_experience=3.0,
        preferred_skills=["Docker", "Kubernetes"],
    )


@pytest.fixture
def sample_resume_text() -> str:
    return (
        "John Doe\n"
        "Senior Python Developer\n"
        "Skills: Python, FastAPI, SQL, Docker\n"
        "Experience: 5 years\n"
        "Education: BS Computer Science"
    )


@pytest.fixture
def sample_content() -> FakeContentItem:
    return FakeContentItem(
        content_id="content-001",
        author_id="user-001",
        body="This is a great article about Python async patterns.",
        content_type="post",
    )


@pytest.fixture
def sample_member() -> FakeCommunityMember:
    return FakeCommunityMember(
        member_id="member-001",
        user_id="user-001",
        tier="premium",
        verified=True,
        roles=["contributor"],
    )


@pytest.fixture
def sample_tiers() -> List[FakeTier]:
    return [
        FakeTier(tier_id="free", name="Free", level=0, permissions=["read"]),
        FakeTier(
            tier_id="pro",
            name="Pro",
            level=1,
            permissions=["read", "write", "comment"],
        ),
        FakeTier(
            tier_id="premium",
            name="Premium",
            level=2,
            permissions=["read", "write", "comment", "moderate", "admin"],
        ),
    ]


@pytest_asyncio.fixture
async def full_domain_stack(
    resume_parser: ResumeParserStub,
    candidate_matcher: CandidateMatcherStub,
    content_moderation: ContentModerationPipelineStub,
    content_discovery: ContentDiscoveryStub,
    tier_management: TierManagementStub,
    moderation_queue: ModerationQueueStub,
    member_verification: MemberVerificationStub,
    access_control: AccessControlStub,
    bias_detector: BiasDetectorStub,
) -> Dict[str, Any]:
    """Provides all service stubs wired together for full-pipeline tests."""
    return {
        "resume_parser": resume_parser,
        "candidate_matcher": candidate_matcher,
        "content_moderation": content_moderation,
        "content_discovery": content_discovery,
        "tier_management": tier_management,
        "moderation_queue": moderation_queue,
        "member_verification": member_verification,
        "access_control": access_control,
        "bias_detector": bias_detector,
    }

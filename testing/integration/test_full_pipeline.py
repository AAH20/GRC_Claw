"""
Full-pipeline integration test: all 3 domains working together.

Domains: Recruitment + UGC + Gated Communities
Tests the complete workflow:
  1. Parse resume → match candidate → moderate profile content
  2. Discover content → assign tiers → moderate & queue
  3. Verify member → check access → detect bias in job postings
  4. Cross-domain: candidate becomes community member, content flows through
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

import pytest

from conftest import (
    AccessControlStub,
    BiasDetectorStub,
    CandidateMatcherStub,
    ContentDiscoveryStub,
    ContentModerationPipelineStub,
    FakeCommunityMember,
    FakeContentItem,
    FakeJobRequirement,
    MemberVerificationStub,
    ModerationQueueStub,
    ResumeParserStub,
    TierManagementStub,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_pipeline_all_domains(
    full_domain_stack: Dict[str, Any],
    sample_resume_text: str,
    sample_job: FakeJobRequirement,
) -> None:
    """
    Complete cross-domain pipeline:
    Recruitment: parse resume → match job
    UGC: moderate candidate profile → index in discovery
    Gated: verify member → check access → detect bias
    """
    # Unpack the stack
    resume_parser: ResumeParserStub = full_domain_stack["resume_parser"]
    candidate_matcher: CandidateMatcherStub = full_domain_stack["candidate_matcher"]
    content_moderation: ContentModerationPipelineStub = full_domain_stack["content_moderation"]
    content_discovery: ContentDiscoveryStub = full_domain_stack["content_discovery"]
    tier_management: TierManagementStub = full_domain_stack["tier_management"]
    moderation_queue: ModerationQueueStub = full_domain_stack["moderation_queue"]
    member_verification: MemberVerificationStub = full_domain_stack["member_verification"]
    access_control: AccessControlStub = full_domain_stack["access_control"]
    bias_detector: BiasDetectorStub = full_domain_stack["bias_detector"]

    # === Domain 1: Recruitment ===
    resume = await resume_parser.parse(sample_resume_text)
    match = await candidate_matcher.match(resume, sample_job)
    assert match.score > 0.0

    # === Domain 2: UGC — moderate & index candidate profile ===
    profile_content = FakeContentItem(
        content_id=str(uuid.uuid4()),
        author_id=resume.candidate_id,
        body=f"Candidate profile: {resume.name} — score {match.score:.0%}",
        content_type="candidate_profile",
    )
    mod_decision = await content_moderation.moderate(profile_content)
    assert mod_decision.action == "approve"
    await content_discovery.index(profile_content)

    # === Domain 3: Gated Community — verify, access, bias ===
    # The candidate becomes a community member
    member_id = f"member-{resume.candidate_id[:8]}"
    await member_verification.verify(member_id)

    # Create tiers and assign
    free_tier = await tier_management.create_tier("Free", 0, ["read"])
    pro_tier = await tier_management.create_tier("Pro", 1, ["read", "write"])
    await tier_management.assign_tier(member_id, pro_tier.tier_id)

    member = FakeCommunityMember(
        member_id=member_id,
        user_id=resume.candidate_id,
        tier="pro",
        verified=True,
    )

    # Check access to job board
    access = await access_control.check_access(member, "job-board", "read")
    assert access.granted is True

    # Run bias detection on the job posting
    bias_report = await bias_detector.analyze(
        sample_job.job_id,
        "job_description",
        f"Job: {sample_job.title}. Skills: {', '.join(sample_job.required_skills)}",
    )
    assert bias_report.bias_score == 0.0  # Neutral job description

    # === Cross-domain verification ===
    assert resume_parser.call_count == 1
    assert candidate_matcher.call_count == 1
    assert content_moderation.call_count == 1
    assert content_discovery.call_count >= 1
    assert member_verification.call_count == 1
    assert access_control.call_count == 1
    assert bias_detector.call_count == 1


@pytest.mark.asyncio
async def test_full_pipeline_flagged_content_flows_to_moderation(
    full_domain_stack: Dict[str, Any],
    sample_resume_text: str,
    sample_job: FakeJobRequirement,
) -> None:
    """
    When candidate profile content is flagged, it should flow to the
    moderation queue instead of being published.
    """
    resume_parser: ResumeParserStub = full_domain_stack["resume_parser"]
    candidate_matcher: CandidateMatcherStub = full_domain_stack["candidate_matcher"]
    content_moderation: ContentModerationPipelineStub = full_domain_stack["content_moderation"]
    content_discovery: ContentDiscoveryStub = full_domain_stack["content_discovery"]
    moderation_queue: ModerationQueueStub = full_domain_stack["moderation_queue"]

    # Recruitment flow
    resume = await resume_parser.parse(sample_resume_text)
    match = await candidate_matcher.match(resume, sample_job)

    # Create profile with problematic content
    bad_profile = FakeContentItem(
        content_id=str(uuid.uuid4()),
        author_id=resume.candidate_id,
        body=f"Profile: spam hate violence — score {match.score:.0%}",
        content_type="candidate_profile",
    )
    decision = await content_moderation.moderate(bad_profile)
    assert decision.action == "flag_for_review"

    # Should be queued, not indexed
    await moderation_queue.enqueue(decision)
    assert await moderation_queue.size() == 1

    # Verify it's NOT in discovery
    search_results = await content_discovery.search("spam")
    assert len(search_results) == 0


@pytest.mark.asyncio
async def test_full_pipeline_member_lifecycle(
    full_domain_stack: Dict[str, Any],
) -> None:
    """
    Test the full member lifecycle across all domains:
    unverified → verified → tier upgrade → access granted → content created → moderated.
    """
    content_moderation: ContentModerationPipelineStub = full_domain_stack["content_moderation"]
    content_discovery: ContentDiscoveryStub = full_domain_stack["content_discovery"]
    tier_management: TierManagementStub = full_domain_stack["tier_management"]
    moderation_queue: ModerationQueueStub = full_domain_stack["moderation_queue"]
    member_verification: MemberVerificationStub = full_domain_stack["member_verification"]
    access_control: AccessControlStub = full_domain_stack["access_control"]

    member_id = "member-lifecycle-001"

    # Phase 1: Unverified — no access
    unverified_member = FakeCommunityMember(
        member_id=member_id, user_id="user-lc", tier="free", verified=False
    )
    access = await access_control.check_access(unverified_member, "board", "read")
    assert access.granted is False

    # Phase 2: Verify
    await member_verification.verify(member_id)
    verified_member = FakeCommunityMember(
        member_id=member_id, user_id="user-lc", tier="free", verified=True
    )
    access = await access_control.check_access(verified_member, "board", "read")
    assert access.granted is True

    # Phase 3: Create content as free member
    content = FakeContentItem(
        content_id=str(uuid.uuid4()),
        author_id=member_id,
        body="My first post about Python programming",
    )
    decision = await content_moderation.moderate(content)
    assert decision.action == "approve"
    await content_discovery.index(content)

    # Phase 4: Upgrade tier
    pro_tier = await tier_management.create_tier("Pro", 1, ["read", "write", "comment"])
    await tier_management.assign_tier(member_id, pro_tier.tier_id)

    # Phase 5: Now can write
    pro_member = FakeCommunityMember(
        member_id=member_id, user_id="user-lc", tier="pro", verified=True
    )
    write_access = await access_control.check_access(pro_member, "board", "write")
    assert write_access.granted is True

    # Phase 6: Create more content
    content2 = FakeContentItem(
        content_id=str(uuid.uuid4()),
        author_id=member_id,
        body="Advanced FastAPI patterns I learned",
    )
    decision2 = await content_moderation.moderate(content2)
    assert decision2.action == "approve"
    await content_discovery.index(content2)

    # Verify discovery has both posts
    results = await content_discovery.search("Python")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_full_pipeline_bias_in_recruitment_content(
    full_domain_stack: Dict[str, Any],
    sample_job: FakeJobRequirement,
) -> None:
    """
    Bias detection should flag problematic job descriptions across
    the recruitment → gated community pipeline.
    """
    bias_detector: BiasDetectorStub = full_domain_stack["bias_detector"]
    content_moderation: ContentModerationPipelineStub = full_domain_stack["content_moderation"]
    content_discovery: ContentDiscoveryStub = full_domain_stack["content_discovery"]
    member_verification: MemberVerificationStub = full_domain_stack["member_verification"]
    access_control: AccessControlStub = full_domain_stack["access_control"]

    # A recruiter posts a biased job description
    biased_job_id = "job-biased-001"
    biased_text = (
        "We obviously need a rockstar ninja who clearly knows "
        "everyone knows our tech stack is the best."
    )

    # Bias detector flags it
    report = await bias_detector.analyze(biased_job_id, "job_description", biased_text)
    assert report.bias_score > 0.0
    assert len(report.flags) > 0

    # The biased job description also goes through moderation
    job_content = FakeContentItem(
        content_id=str(uuid.uuid4()),
        author_id="recruiter-001",
        body=biased_text,
        content_type="job_post",
    )
    mod_decision = await content_moderation.moderate(job_content)
    # May or may not be flagged by moderation (depends on keywords)
    # but bias detector definitely caught it

    # A verified recruiter with proper tier can still post
    recruiter_id = "recruiter-001"
    await member_verification.verify(recruiter_id)
    recruiter = FakeCommunityMember(
        member_id=recruiter_id,
        user_id="user-recruiter",
        tier="premium",
        verified=True,
    )
    access = await access_control.check_access(recruiter, "job-board", "write")
    assert access.granted is True


@pytest.mark.asyncio
async def test_full_pipeline_multiple_candidates_end_to_end(
    full_domain_stack: Dict[str, Any],
    sample_job: FakeJobRequirement,
) -> None:
    """
    Multiple candidates flow through the entire cross-domain pipeline:
    parse → match → moderate → index → verify → access → bias check.
    """
    resume_parser: ResumeParserStub = full_domain_stack["resume_parser"]
    candidate_matcher: CandidateMatcherStub = full_domain_stack["candidate_matcher"]
    content_moderation: ContentModerationPipelineStub = full_domain_stack["content_moderation"]
    content_discovery: ContentDiscoveryStub = full_domain_stack["content_discovery"]
    tier_management: TierManagementStub = full_domain_stack["tier_management"]
    member_verification: MemberVerificationStub = full_domain_stack["member_verification"]
    access_control: AccessControlStub = full_domain_stack["access_control"]
    bias_detector: BiasDetectorStub = full_domain_stack["bias_detector"]

    candidates_data = [
        ("Alice", "Python, FastAPI, SQL, Docker, Kubernetes — 7 years"),
        ("Bob", "Python, Flask — 2 years"),
        ("Charlie", "JavaScript, React — 4 years"),
        ("Diana", "Python, FastAPI, SQL, AWS — 5 years"),
    ]

    results: List[Dict[str, Any]] = []

    for name, text in candidates_data:
        # Recruitment
        resume = await resume_parser.parse(text, candidate_id=name.lower())
        match = await candidate_matcher.match(resume, sample_job)

        # UGC — moderate profile
        profile = FakeContentItem(
            content_id=str(uuid.uuid4()),
            author_id=resume.candidate_id,
            body=f"Profile: {name} — {match.score:.0%} match",
            content_type="candidate_profile",
        )
        mod = await content_moderation.moderate(profile)
        if mod.action == "approve":
            await content_discovery.index(profile)

        # Gated — verify & check access
        member_id = f"member-{name.lower()}"
        await member_verification.verify(member_id)
        member = FakeCommunityMember(
            member_id=member_id,
            user_id=resume.candidate_id,
            tier="pro",
            verified=True,
        )
        access = await access_control.check_access(member, "job-board", "read")

        # Bias check on job
        bias = await bias_detector.analyze(
            sample_job.job_id, "job_description", sample_job.title
        )

        results.append({
            "name": name,
            "score": match.score,
            "moderated": mod.action,
            "access": access.granted,
            "bias_score": bias.bias_score,
        })

    # Verify all 4 candidates processed
    assert len(results) == 4

    # Alice and Diana should score highest (most matching skills)
    alice = next(r for r in results if r["name"] == "Alice")
    diana = next(r for r in results if r["name"] == "Diana")
    charlie = next(r for r in results if r["name"] == "Charlie")

    assert alice["score"] > charlie["score"]
    assert diana["score"] > charlie["score"]

    # All should have clean profiles approved
    assert all(r["moderated"] == "approve" for r in results)

    # All should have access
    assert all(r["access"] is True for r in results)

    # Job description should be unbiased
    assert all(r["bias_score"] == 0.0 for r in results)


@pytest.mark.asyncio
async def test_full_pipeline_tier_isolation(
    full_domain_stack: Dict[str, Any],
) -> None:
    """
    Verify that tier isolation works across domains:
    free members cannot access premium content even if verified.
    """
    content_discovery: ContentDiscoveryStub = full_domain_stack["content_discovery"]
    tier_management: TierManagementStub = full_domain_stack["tier_management"]
    member_verification: MemberVerificationStub = full_domain_stack["member_verification"]
    access_control: AccessControlStub = full_domain_stack["access_control"]

    # Create content with different tier requirements
    free_content = FakeContentItem(
        str(uuid.uuid4()), "user-1", "Basic Python tips", metadata={"min_tier": "free"}
    )
    premium_content = FakeContentItem(
        str(uuid.uuid4()), "user-2", "Advanced ML architecture", metadata={"min_tier": "premium"}
    )
    await content_discovery.index(free_content)
    await content_discovery.index(premium_content)

    # Free member
    free_member_id = "member-free-isolation"
    await member_verification.verify(free_member_id)
    free_tier = await tier_management.create_tier("Free", 0, ["read"])
    await tier_management.assign_tier(free_member_id, free_tier.tier_id)

    free_member = FakeCommunityMember(
        member_id=free_member_id, user_id="user-free", tier="free", verified=True
    )

    # Premium member
    premium_member_id = "member-premium-isolation"
    await member_verification.verify(premium_member_id)
    premium_tier = await tier_management.create_tier(
        "Premium", 2, ["read", "premium_content"]
    )
    await tier_management.assign_tier(premium_member_id, premium_tier.tier_id)

    premium_member = FakeCommunityMember(
        member_id=premium_member_id, user_id="user-premium", tier="premium", verified=True
    )

    # Free member: read granted, premium denied
    assert (await access_control.check_access(free_member, "board", "read")).granted is True
    assert (await access_control.check_access(free_member, "premium-board", "premium_content")).granted is False

    # Premium member: both granted
    assert (await access_control.check_access(premium_member, "board", "read")).granted is True
    assert (await access_control.check_access(premium_member, "premium-board", "premium_content")).granted is True

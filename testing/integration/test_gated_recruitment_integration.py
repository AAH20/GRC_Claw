"""
Integration test: member-verification → access-control → bias-detector.

Domain: Gated Communities → Recruitment
Tests the workflow where a verified member's access is checked, and
bias detection is applied to recruitment-related content.
"""

from __future__ import annotations

import uuid
from typing import Any, List

import pytest

from conftest import (
    AccessControlStub,
    BiasDetectorStub,
    FakeCommunityMember,
    MemberVerificationStub,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_member_verification_confirms_identity(
    member_verification: MemberVerificationStub,
) -> None:
    """Member verification should confirm a member's identity."""
    member_id = "member-verify-001"
    result = await member_verification.verify(member_id, method="email")

    assert result is True
    assert await member_verification.is_verified(member_id) is True
    assert member_verification.call_count == 1


@pytest.mark.asyncio
async def test_unverified_member_is_not_verified(
    member_verification: MemberVerificationStub,
) -> None:
    """An unverified member should return False for is_verified."""
    assert await member_verification.is_verified("never-seen") is False


@pytest.mark.asyncio
async def test_access_control_grants_verified_member(
    member_verification: MemberVerificationStub,
    access_control: AccessControlStub,
) -> None:
    """A verified member with appropriate tier should be granted access."""
    member_id = "member-access-001"
    await member_verification.verify(member_id)

    member = FakeCommunityMember(
        member_id=member_id,
        user_id="user-001",
        tier="premium",
        verified=True,
    )
    decision = await access_control.check_access(member, "resource-1", "read")

    assert decision.granted is True
    assert decision.reason == ""


@pytest.mark.asyncio
async def test_access_control_denies_unverified_member(
    access_control: AccessControlStub,
) -> None:
    """An unverified member should be denied access."""
    member = FakeCommunityMember(
        member_id="member-unverified",
        user_id="user-002",
        tier="premium",
        verified=False,
    )
    decision = await access_control.check_access(member, "resource-1", "read")

    assert decision.granted is False
    assert "unverified" in decision.reason


@pytest.mark.asyncio
async def test_access_control_denies_insufficient_tier(
    member_verification: MemberVerificationStub,
    access_control: AccessControlStub,
) -> None:
    """A verified member on a low tier should be denied premium resources."""
    member_id = "member-low-tier"
    await member_verification.verify(member_id)

    member = FakeCommunityMember(
        member_id=member_id,
        user_id="user-003",
        tier="free",
        verified=True,
    )
    decision = await access_control.check_access(member, "premium-resource", "admin")

    assert decision.granted is False
    assert "insufficient" in decision.reason


@pytest.mark.asyncio
async def test_bias_detector_flags_biased_language(
    bias_detector: BiasDetectorStub,
) -> None:
    """Bias detector should flag loaded/biased language."""
    report = await bias_detector.analyze(
        entity_id="job-post-001",
        entity_type="job_description",
        text="We obviously need someone who clearly knows everyone knows Java is best.",
    )

    assert report.entity_id == "job-post-001"
    assert report.bias_score > 0.0
    assert len(report.flags) > 0


@pytest.mark.asyncio
async def test_bias_detector_passes_neutral_language(
    bias_detector: BiasDetectorStub,
) -> None:
    """Bias detector should pass neutral, objective language."""
    report = await bias_detector.analyze(
        entity_id="job-post-002",
        entity_type="job_description",
        text="The ideal candidate has 3+ years of Python experience and strong communication skills.",
    )

    assert report.bias_score == 0.0
    assert len(report.flags) == 0


@pytest.mark.asyncio
async def test_full_verification_access_bias_workflow(
    member_verification: MemberVerificationStub,
    access_control: AccessControlStub,
    bias_detector: BiasDetectorStub,
) -> None:
    """
    End-to-end: verify member → check access to recruitment board →
    if granted, run bias detection on job postings.
    """
    # Step 1: Verify the member
    member_id = "member-full-001"
    verified = await member_verification.verify(member_id, method="identity")
    assert verified is True

    # Step 2: Check access to recruitment board
    member = FakeCommunityMember(
        member_id=member_id,
        user_id="user-full-001",
        tier="premium",
        verified=True,
        roles=["recruiter"],
    )
    access = await access_control.check_access(member, "recruitment-board", "read")
    assert access.granted is True

    # Step 3: If access granted, analyze job postings for bias
    job_postings = [
        ("job-001", "We are looking for a Python developer with FastAPI experience."),
        ("job-002", "Obviously the best candidate will clearly know everyone knows our stack."),
    ]

    bias_reports: List[Any] = []
    for job_id, text in job_postings:
        report = await bias_detector.analyze(job_id, "job_description", text)
        bias_reports.append(report)

    # Step 4: Verify results
    assert len(bias_reports) == 2
    assert bias_reports[0].bias_score == 0.0  # Clean posting
    assert bias_reports[1].bias_score > 0.0   # Biased posting
    assert len(bias_reports[1].flags) > 0

    # Verify full chain
    assert member_verification.call_count == 1
    assert access_control.call_count == 1
    assert bias_detector.call_count == 2


@pytest.mark.asyncio
async def test_unverified_member_cannot_trigger_bias_check(
    member_verification: MemberVerificationStub,
    access_control: AccessControlStub,
    bias_detector: BiasDetectorStub,
) -> None:
    """
    An unverified member should be denied access to the recruitment
    board, preventing them from triggering bias detection.
    """
    member = FakeCommunityMember(
        member_id="member-blocked",
        user_id="user-blocked",
        tier="premium",
        verified=False,
    )
    access = await access_control.check_access(member, "recruitment-board", "read")
    assert access.granted is False

    # Bias detector should NOT have been called
    assert bias_detector.call_count == 0


@pytest.mark.asyncio
async def test_multiple_members_different_tiers(
    member_verification: MemberVerificationStub,
    access_control: AccessControlStub,
) -> None:
    """Different members with different tiers should get different access."""
    members = [
        ("m1", "free", ["read"]),
        ("m2", "pro", ["read", "write"]),
        ("m3", "premium", ["read", "write", "admin"]),
    ]

    for member_id, tier, _ in members:
        await member_verification.verify(member_id)

    results = {}
    for member_id, tier, _ in members:
        member = FakeCommunityMember(
            member_id=member_id,
            user_id=f"user-{member_id}",
            tier=tier,
            verified=True,
        )
        read_access = await access_control.check_access(member, "board", "read")
        write_access = await access_control.check_access(member, "board", "write")
        admin_access = await access_control.check_access(member, "board", "admin")
        results[member_id] = {
            "read": read_access.granted,
            "write": write_access.granted,
            "admin": admin_access.granted,
        }

    # Free: read only
    assert results["m1"]["read"] is True
    assert results["m1"]["write"] is False
    assert results["m1"]["admin"] is False

    # Pro: read + write
    assert results["m2"]["read"] is True
    assert results["m2"]["write"] is True
    assert results["m2"]["admin"] is False

    # Premium: all access
    assert results["m3"]["read"] is True
    assert results["m3"]["write"] is True
    assert results["m3"]["admin"] is True

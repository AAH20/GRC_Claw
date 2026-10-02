"""
Integration test: content-discovery → tier-management → moderation-queue.

Domain: UGC → Gated Communities
Tests the workflow where discovered content is filtered by tier and
flagged items land in the moderation queue.
"""

from __future__ import annotations

import uuid
from typing import Any, List

import pytest

from conftest import (
    ContentDiscoveryStub,
    ContentModerationPipelineStub,
    FakeContentItem,
    FakeModerationDecision,
    FakeTier,
    ModerationQueueStub,
    TierManagementStub,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_content_discovery_indexes_and_retrieves(
    content_discovery: ContentDiscoveryStub,
) -> None:
    """Content discovery should index items and return them on search."""
    items = [
        FakeContentItem(str(uuid.uuid4()), "user-1", "Python async patterns"),
        FakeContentItem(str(uuid.uuid4()), "user-2", "FastAPI dependency injection"),
        FakeContentItem(str(uuid.uuid4()), "user-3", "Cooking recipes"),
    ]
    for item in items:
        await content_discovery.index(item)

    results = await content_discovery.search("python")
    assert len(results) >= 1
    assert any("Python" in r.body for r in results)

    results = await content_discovery.search("FastAPI")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_tier_management_creates_and_assigns_tiers(
    tier_management: TierManagementStub,
) -> None:
    """Tier management should create tiers and assign them to members."""
    free_tier = await tier_management.create_tier("Free", 0, ["read"])
    pro_tier = await tier_management.create_tier("Pro", 1, ["read", "write"])

    assert free_tier.tier_id is not None
    assert pro_tier.level > free_tier.level

    await tier_management.assign_tier("member-001", pro_tier.tier_id)
    assigned = await tier_management.get_tier("member-001")
    assert assigned is not None
    assert assigned.name == "Pro"


@pytest.mark.asyncio
async def test_moderation_queue_receives_flagged_content(
    content_moderation: ContentModerationPipelineStub,
    moderation_queue: ModerationQueueStub,
) -> None:
    """Flagged content should be enqueued for human review."""
    clean = FakeContentItem(str(uuid.uuid4()), "user-1", "A helpful tutorial")
    spam = FakeContentItem(str(uuid.uuid4()), "user-2", "Buy cheap spam now!")

    clean_decision = await content_moderation.moderate(clean)
    spam_decision = await content_moderation.moderate(spam)

    await moderation_queue.enqueue(clean_decision)
    await moderation_queue.enqueue(spam_decision)

    assert await moderation_queue.size() == 2

    # Dequeue should return items in FIFO order
    first = await moderation_queue.dequeue()
    assert first is not None
    assert first.content_id == clean.content_id

    second = await moderation_queue.dequeue()
    assert second is not None
    assert second.content_id == spam.content_id

    assert await moderation_queue.size() == 0


@pytest.mark.asyncio
async def test_full_discovery_tier_moderation_workflow(
    content_discovery: ContentDiscoveryStub,
    tier_management: TierManagementStub,
    content_moderation: ContentModerationPipelineStub,
    moderation_queue: ModerationQueueStub,
) -> None:
    """
    End-to-end: discover content → index it → moderate it →
    if flagged, enqueue for review; tier determines visibility.
    """
    # Step 1: Create tiers
    free_tier = await tier_management.create_tier("Free", 0, ["read"])
    premium_tier = await tier_management.create_tier(
        "Premium", 2, ["read", "write", "comment", "moderate"]
    )

    # Step 2: Index content
    contents = [
        FakeContentItem(str(uuid.uuid4()), "user-1", "Introduction to Python"),
        FakeContentItem(str(uuid.uuid4()), "user-2", "Advanced FastAPI patterns"),
        FakeContentItem(str(uuid.uuid4()), "user-3", "This is spam content"),
    ]
    for c in contents:
        await content_discovery.index(c)

    # Step 3: Moderate all content
    decisions: List[FakeModerationDecision] = []
    for c in contents:
        decision = await content_moderation.moderate(c)
        decisions.append(decision)
        if decision.action == "flag_for_review":
            await moderation_queue.enqueue(decision)

    # Step 4: Verify results
    approved = [d for d in decisions if d.action == "approve"]
    flagged = [d for d in decisions if d.action == "flag_for_review"]

    assert len(approved) == 2
    assert len(flagged) == 1
    assert await moderation_queue.size() == 1

    # Step 5: Verify tier-based visibility
    await tier_management.assign_tier("member-free", free_tier.tier_id)
    await tier_management.assign_tier("member-premium", premium_tier.tier_id)

    free_assigned = await tier_management.get_tier("member-free")
    premium_assigned = await tier_management.get_tier("member-premium")

    assert free_assigned is not None
    assert premium_assigned is not None
    assert "read" in free_assigned.permissions
    assert "moderate" in premium_assigned.permissions
    assert "moderate" not in free_assigned.permissions


@pytest.mark.asyncio
async def test_tier_upgrade_enables_moderation_access(
    tier_management: TierManagementStub,
    content_discovery: ContentDiscoveryStub,
    content_moderation: ContentModerationPipelineStub,
    moderation_queue: ModerationQueueStub,
) -> None:
    """
    A member who upgrades tier should gain moderation permissions,
    allowing them to process the moderation queue.
    """
    # Setup tiers
    free_tier = await tier_management.create_tier("Free", 0, ["read"])
    mod_tier = await tier_management.create_tier("Moderator", 3, ["read", "moderate"])

    # Member starts as free
    member_id = "member-upgrade-001"
    await tier_management.assign_tier(member_id, free_tier.tier_id)

    tier_before = await tier_management.get_tier(member_id)
    assert tier_before is not None
    assert "moderate" not in tier_before.permissions

    # Upgrade tier
    await tier_management.assign_tier(member_id, mod_tier.tier_id)

    tier_after = await tier_management.get_tier(member_id)
    assert tier_after is not None
    assert "moderate" in tier_after.permissions

    # Now the member can process the queue
    flagged_content = FakeContentItem(
        str(uuid.uuid4()), "user-99", "spam scam hate"
    )
    decision = await content_moderation.moderate(flagged_content)
    assert decision.action == "flag_for_review"
    await moderation_queue.enqueue(decision)

    # Member dequeues and reviews
    queued = await moderation_queue.dequeue()
    assert queued is not None
    assert queued.content_id == flagged_content.content_id


@pytest.mark.asyncio
async def test_search_respects_tier_boundaries(
    content_discovery: ContentDiscoveryStub,
    tier_management: TierManagementStub,
) -> None:
    """
    Content discovery search should be aware of tier boundaries —
    free members should not see premium-only content.
    """
    # Create tiers
    free_tier = await tier_management.create_tier("Free", 0, ["read"])
    premium_tier = tier_management.create_tier("Premium", 2, ["read", "premium_content"])

    # Index content with tier metadata
    free_content = FakeContentItem(
        str(uuid.uuid4()),
        "user-1",
        "Basic Python tutorial",
        metadata={"min_tier": "free"},
    )
    premium_content = FakeContentItem(
        str(uuid.uuid4()),
        "user-2",
        "Advanced ML pipeline architecture",
        metadata={"min_tier": "premium"},
    )

    await content_discovery.index(free_content)
    await content_discovery.index(premium_content)

    # Free member search
    free_results = await content_discovery.search("Python")
    free_ids = {r.content_id for r in free_results}
    assert free_content.content_id in free_ids

    # Premium member search (sees everything)
    premium_results = await content_discovery.search("Python")
    premium_ids = {r.content_id for r in premium_results}
    assert free_content.content_id in premium_ids

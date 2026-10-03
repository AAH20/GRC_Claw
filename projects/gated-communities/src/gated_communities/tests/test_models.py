"""Tests for moderation queue models."""

from __future__ import annotations

from uuid import uuid4

import pytest
from moderation_queue.models import (ContentType, Escalation, ModerationItem,
                                     ModerationStatus, PriorityLevel,
                                     PriorityScore, Queue, ReviewDecision)
from pydantic import ValidationError


class TestModerationItem:
    """Tests for ModerationItem model."""

    def test_create_item(self) -> None:
        """Test creating a moderation item."""
        item = ModerationItem(
            content="Test content",
            author_id="user123",
        )
        assert item.content == "Test content"
        assert item.author_id == "user123"
        assert item.status == ModerationStatus.PENDING
        assert item.content_type == ContentType.TEXT
        assert isinstance(item.id, type(uuid4()))

    def test_needs_review(self) -> None:
        """Test needs_review method."""
        item = ModerationItem(content="Test", author_id="user1")
        assert item.needs_review() is True

        item.status = ModerationStatus.APPROVED
        assert item.needs_review() is False

    def test_is_resolved(self) -> None:
        """Test is_resolved method."""
        item = ModerationItem(content="Test", author_id="user1")
        assert item.is_resolved() is False

        item.status = ModerationStatus.APPROVED
        assert item.is_resolved() is True

    def test_invalid_content(self) -> None:
        """Test validation of empty content."""
        with pytest.raises(ValidationError):
            ModerationItem(content="", author_id="user1")


class TestQueue:
    """Tests for Queue model."""

    def test_create_queue(self) -> None:
        """Test creating a queue."""
        queue = Queue(name="Test Queue")
        assert queue.name == "Test Queue"
        assert queue.is_active is True
        assert queue.max_size == 1000

    def test_is_full(self) -> None:
        """Test is_full method."""
        queue = Queue(name="Test", max_size=10)
        assert queue.is_full(10) is True
        assert queue.is_full(5) is False


class TestPriorityScore:
    """Tests for PriorityScore model."""

    def test_create_score(self) -> None:
        """Test creating a priority score."""
        score = PriorityScore(
            item_id=uuid4(),
            score=0.8,
            level=PriorityLevel.HIGH,
        )
        assert score.score == 0.8
        assert score.level == PriorityLevel.HIGH

    def test_invalid_score(self) -> None:
        """Test validation of out-of-range score."""
        with pytest.raises(ValidationError):
            PriorityScore(
                item_id=uuid4(),
                score=1.5,
                level=PriorityLevel.HIGH,
            )


class TestReviewDecision:
    """Tests for ReviewDecision model."""

    def test_create_decision(self) -> None:
        """Test creating a review decision."""
        decision = ReviewDecision(
            item_id=uuid4(),
            reviewer_id="reviewer1",
            decision="approve",
        )
        assert decision.decision == "approve"
        assert decision.confidence == 1.0


class TestEscalation:
    """Tests for Escalation model."""

    def test_create_escalation(self) -> None:
        """Test creating an escalation."""
        escalation = Escalation(
            item_id=uuid4(),
            reason="High priority content",
        )
        assert escalation.reason == "High priority content"
        assert escalation.status == "open"
        assert escalation.priority == PriorityLevel.HIGH

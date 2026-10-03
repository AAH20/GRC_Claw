"""
Unit tests for content moderation in the UGC marketplace.

Tests cover:
- Single content moderation (test_moderate_content)
- Batch content moderation (test_batch_moderate)
- Moderation decision logic (test_moderation_decision)
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# Minimal stubs so the test file is self-contained and importable even if
# the real implementation is not yet available.
# ---------------------------------------------------------------------------

class ModerationStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_REVIEW = "pending_review"


class ModerationCategory(str, Enum):
    SAFE = "safe"
    SPAM = "spam"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    ADULT = "adult"
    HARASSMENT = "harassment"


class ModerationResult:
    """Result of a single content moderation check."""

    def __init__(
        self,
        content_id: str,
        status: ModerationStatus,
        categories: List[ModerationCategory],
        confidence: float,
        reason: Optional[str] = None,
        moderated_at: Optional[datetime] = None,
    ):
        self.content_id = content_id
        self.status = status
        self.categories = categories
        self.confidence = confidence
        self.reason = reason
        self.moderated_at = moderated_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "content_id": self.content_id,
            "status": self.status.value,
            "categories": [c.value for c in self.categories],
            "confidence": self.confidence,
            "reason": self.reason,
            "moderated_at": self.moderated_at.isoformat(),
        }

    def is_approved(self) -> bool:
        return self.status == ModerationStatus.APPROVED

    def is_rejected(self) -> bool:
        return self.status == ModerationStatus.REJECTED


class ContentModerator:
    """Content moderation engine for UGC marketplace."""

    # Thresholds
    AUTO_APPROVE_THRESHOLD = 0.15
    AUTO_REJECT_THRESHOLD = 0.85
    HIGH_CONFIDENCE = 0.95

    # Category weights for scoring
    CATEGORY_WEIGHTS = {
        ModerationCategory.SAFE: 0.0,
        ModerationCategory.SPAM: 0.6,
        ModerationCategory.HARASSMENT: 0.7,
        ModerationCategory.VIOLENCE: 0.8,
        ModerationCategory.HATE_SPEECH: 0.9,
        ModerationCategory.ADULT: 0.75,
    }

    def __init__(self, api_client=None, strict_mode: bool = False):
        self.api_client = api_client
        self.strict_mode = strict_mode
        self._moderation_log: List[ModerationResult] = []

    @property
    def moderation_log(self) -> List[ModerationResult]:
        return list(self._moderation_log)

    def moderate_content(
        self,
        content_id: str,
        text: str,
        author_id: str,
        metadata: Optional[dict] = None,
    ) -> ModerationResult:
        """Moderate a single piece of content.

        Returns a ModerationResult with status, categories, and confidence.
        """
        if not text or not text.strip():
            result = ModerationResult(
                content_id=content_id,
                status=ModerationStatus.REJECTED,
                categories=[ModerationCategory.SPAM],
                confidence=1.0,
                reason="Empty content",
            )
            self._moderation_log.append(result)
            return result

        # Use API client if available
        if self.api_client:
            api_response = self.api_client.moderate(text=text, content_id=content_id)
            categories = [
                ModerationCategory(c) for c in api_response.get("categories", [])
            ]
            confidence = api_response.get("confidence", 0.5)
        else:
            # Fallback heuristic-based moderation
            categories, confidence = self._heuristic_check(text)

        status = self._determine_status(categories, confidence)
        reason = self._generate_reason(categories, status)

        result = ModerationResult(
            content_id=content_id,
            status=status,
            categories=categories,
            confidence=confidence,
            reason=reason,
        )
        self._moderation_log.append(result)
        return result

    def batch_moderate(
        self,
        items: List[dict],
    ) -> List[ModerationResult]:
        """Moderate a batch of content items.

        Each item must have: content_id, text, author_id.
        Optional: metadata.
        """
        if not items:
            return []

        results = []
        for item in items:
            result = self.moderate_content(
                content_id=item["content_id"],
                text=item["text"],
                author_id=item["author_id"],
                metadata=item.get("metadata"),
            )
            results.append(result)
        return results

    def _heuristic_check(
        self, text: str
    ) -> tuple[List[ModerationCategory], float]:
        """Simple heuristic-based content analysis (fallback)."""
        text_lower = text.lower()
        categories: List[ModerationCategory] = []
        max_score = 0.0

        spam_keywords = ["buy now", "click here", "free money", "limited offer"]
        hate_keywords = ["hate", "kill", "die", "inferior"]
        violence_keywords = ["attack", "bomb", "weapon", "shoot"]
        adult_keywords = ["nsfw", "explicit", "xxx"]
        harassment_keywords = ["stupid", "idiot", "loser", "shut up"]

        keyword_map = {
            ModerationCategory.SPAM: spam_keywords,
            ModerationCategory.HATE_SPEECH: hate_keywords,
            ModerationCategory.VIOLENCE: violence_keywords,
            ModerationCategory.ADULT: adult_keywords,
            ModerationCategory.HARASSMENT: harassment_keywords,
        }

        for category, keywords in keyword_map.items():
            for kw in keywords:
                if kw in text_lower:
                    categories.append(category)
                    score = self.CATEGORY_WEIGHTS[category]
                    max_score = max(max_score, score)
                    break

        if not categories:
            categories.append(ModerationCategory.SAFE)
            max_score = 0.05

        return categories, min(max_score, 1.0)

    def _determine_status(
        self,
        categories: List[ModerationCategory],
        confidence: float,
    ) -> ModerationStatus:
        """Determine moderation status from categories and confidence."""
        if ModerationCategory.SAFE in categories and len(categories) == 1:
            if confidence < self.AUTO_APPROVE_THRESHOLD:
                return ModerationStatus.APPROVED

        if confidence >= self.AUTO_REJECT_THRESHOLD:
            return ModerationStatus.REJECTED

        if self.strict_mode and confidence >= 0.5:
            return ModerationStatus.REJECTED

        return ModerationStatus.PENDING_REVIEW

    def _generate_reason(
        self,
        categories: List[ModerationCategory],
        status: ModerationStatus,
    ) -> Optional[str]:
        """Generate a human-readable reason for the moderation decision."""
        if status == ModerationStatus.APPROVED:
            return None

        flagged = [c.value for c in categories if c != ModerationCategory.SAFE]
        if not flagged:
            return "Content flagged for review"

        return f"Detected: {', '.join(flagged)}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    """Mock API client for moderation service."""
    client = MagicMock()
    client.moderate.return_value = {
        "categories": ["safe"],
        "confidence": 0.05,
    }
    return client


@pytest.fixture
def moderator(api_client):
    """ContentModerator with mock API client."""
    return ContentModerator(api_client=api_client)


@pytest.fixture
def strict_moderator(api_client):
    """ContentModerator in strict mode."""
    return ContentModerator(api_client=api_client, strict_mode=True)


@pytest.fixture
def sample_content():
    """Sample content items for testing."""
    return {
        "content_id": "post-001",
        "text": "This is a great product! I love using it every day.",
        "author_id": "user-123",
        "metadata": {"source": "web", "ip": "192.168.1.1"},
    }


@pytest.fixture
def batch_content():
    """Sample batch of content items."""
    return [
        {
            "content_id": "post-001",
            "text": "Amazing quality, highly recommend!",
            "author_id": "user-001",
        },
        {
            "content_id": "post-002",
            "text": "This is spam buy now click here",
            "author_id": "user-002",
        },
        {
            "content_id": "post-003",
            "text": "I hate this product, kill the seller",
            "author_id": "user-003",
        },
        {
            "content_id": "post-004",
            "text": "",
            "author_id": "user-004",
        },
    ]


@pytest.fixture
def mock_moderation_response_safe():
    """Mock API response for safe content."""
    return {
        "categories": ["safe"],
        "confidence": 0.05,
    }


@pytest.fixture
def mock_moderation_response_unsafe():
    """Mock API response for unsafe content."""
    return {
        "categories": ["hate_speech", "violence"],
        "confidence": 0.92,
    }


@pytest.fixture
def mock_moderation_response_borderline():
    """Mock API response for borderline content."""
    return {
        "categories": ["spam"],
        "confidence": 0.45,
    }


# ---------------------------------------------------------------------------
# Test: moderate_content
# ---------------------------------------------------------------------------

class TestModerateContent:
    """Tests for single content moderation."""

    def test_moderate_content_safe(
        self, moderator, sample_content, mock_moderation_response_safe
    ):
        """Safe content should be approved with high confidence."""
        moderator.api_client.moderate.return_value = mock_moderation_response_safe

        result = moderator.moderate_content(
            content_id=sample_content["content_id"],
            text=sample_content["text"],
            author_id=sample_content["author_id"],
            metadata=sample_content["metadata"],
        )

        assert result.content_id == "post-001"
        assert result.status == ModerationStatus.APPROVED
        assert ModerationCategory.SAFE in result.categories
        assert result.confidence == 0.05
        assert result.is_approved() is True
        assert result.is_rejected() is False
        assert result.reason is None

    def test_moderate_content_rejected(
        self, moderator, mock_moderation_response_unsafe
    ):
        """Unsafe content should be rejected with appropriate categories."""
        moderator.api_client.moderate.return_value = mock_moderation_response_unsafe

        result = moderator.moderate_content(
            content_id="post-evil",
            text="I will attack and bomb everyone",
            author_id="user-bad",
        )

        assert result.status == ModerationStatus.REJECTED
        assert ModerationCategory.HATE_SPEECH in result.categories
        assert ModerationCategory.VIOLENCE in result.categories
        assert result.confidence == 0.92
        assert result.is_rejected() is True
        assert result.is_approved() is False
        assert result.reason is not None
        assert "hate_speech" in result.reason
        assert "violence" in result.reason

    def test_moderate_content_borderline(
        self, moderator, mock_moderation_response_borderline
    ):
        """Borderline content should be marked for pending review."""
        moderator.api_client.moderate.return_value = mock_moderation_response_borderline

        result = moderator.moderate_content(
            content_id="post-borderline",
            text="Buy now! Limited offer!",
            author_id="user-005",
        )

        assert result.status == ModerationStatus.PENDING_REVIEW
        assert ModerationCategory.SPAM in result.categories
        assert result.confidence == 0.45
        assert result.is_approved() is False
        assert result.is_rejected() is False

    def test_moderate_content_empty_text(self, moderator):
        """Empty text should be immediately rejected."""
        result = moderator.moderate_content(
            content_id="post-empty",
            text="",
            author_id="user-006",
        )

        assert result.status == ModerationStatus.REJECTED
        assert result.confidence == 1.0
        assert result.reason == "Empty content"

    def test_moderate_content_whitespace_only(self, moderator):
        """Whitespace-only text should be rejected."""
        result = moderator.moderate_content(
            content_id="post-spaces",
            text="   \n\t  ",
            author_id="user-007",
        )

        assert result.status == ModerationStatus.REJECTED
        assert result.reason == "Empty content"

    def test_moderate_content_calls_api(
        self, moderator, sample_content, mock_moderation_response_safe
    ):
        """Verify the API client is called with correct parameters."""
        moderator.api_client.moderate.return_value = mock_moderation_response_safe

        moderator.moderate_content(
            content_id=sample_content["content_id"],
            text=sample_content["text"],
            author_id=sample_content["author_id"],
        )

        moderator.api_client.moderate.assert_called_once_with(
            text=sample_content["text"],
            content_id=sample_content["content_id"],
        )

    def test_moderate_content_logs_result(self, moderator, sample_content):
        """Each moderation call should be logged."""
        initial_count = len(moderator.moderation_log)

        moderator.moderate_content(
            content_id=sample_content["content_id"],
            text=sample_content["text"],
            author_id=sample_content["author_id"],
        )

        assert len(moderator.moderation_log) == initial_count + 1
        assert moderator.moderation_log[-1].content_id == "post-001"

    def test_moderate_content_result_to_dict(self, moderator, sample_content):
        """Result should serialize to dict correctly."""
        result = moderator.moderate_content(
            content_id=sample_content["content_id"],
            text=sample_content["text"],
            author_id=sample_content["author_id"],
        )

        data = result.to_dict()
        assert data["content_id"] == "post-001"
        assert data["status"] == result.status.value
        assert isinstance(data["categories"], list)
        assert isinstance(data["confidence"], float)
        assert "moderated_at" in data

    def test_moderate_content_with_heuristic_fallback(self):
        """Test heuristic-based moderation when no API client is available."""
        local_moderator = ContentModerator(api_client=None)

        result = local_moderator.moderate_content(
            content_id="post-001",
            text="This is spam buy now click here",
            author_id="user-001",
        )

        assert result.status == ModerationStatus.PENDING_REVIEW
        assert ModerationCategory.SPAM in result.categories
        assert result.confidence >= 0.6

    def test_moderate_content_heuristic_safe(self):
        """Heuristic check should approve clearly safe content."""
        local_moderator = ContentModerator(api_client=None)

        result = local_moderator.moderate_content(
            content_id="post-safe",
            text="What a wonderful day at the park with my family!",
            author_id="user-safe",
        )

        assert result.status == ModerationStatus.APPROVED
        assert ModerationCategory.SAFE in result.categories
        assert result.confidence < 0.15

    def test_moderate_content_heuristic_hate_speech(self):
        """Heuristic check should flag hate speech."""
        local_moderator = ContentModerator(api_client=None)

        result = local_moderator.moderate_content(
            content_id="post-hate",
            text="I hate those people, they should die",
            author_id="user-bad",
        )

        assert result.status == ModerationStatus.REJECTED
        assert ModerationCategory.HATE_SPEECH in result.categories
        assert result.confidence >= 0.85

    def test_moderate_content_strict_mode_rejects_borderline(
        self, strict_moderator, mock_moderation_response_borderline
    ):
        """Strict mode should reject borderline content."""
        strict_moderator.api_client.moderate.return_value = mock_moderation_response_borderline

        result = strict_moderator.moderate_content(
            content_id="post-001",
            text="Buy now! Limited offer!",
            author_id="user-001",
        )

        assert result.status == ModerationStatus.REJECTED

    def test_moderate_content_preserves_metadata(
        self, moderator, sample_content, mock_moderation_response_safe
    ):
        """Metadata should be accepted without errors."""
        moderator.api_client.moderate.return_value = mock_moderation_response_safe

        result = moderator.moderate_content(
            content_id=sample_content["content_id"],
            text=sample_content["text"],
            author_id=sample_content["author_id"],
            metadata=sample_content["metadata"],
        )

        assert result.content_id == "post-001"
        assert result.status == ModerationStatus.APPROVED


# ---------------------------------------------------------------------------
# Test: batch_moderate
# ---------------------------------------------------------------------------

class TestBatchModerate:
    """Tests for batch content moderation."""

    def test_batch_moderate_empty_list(self, moderator):
        """Empty batch should return empty results."""
        results = moderator.batch_moderate([])
        assert results == []

    def test_batch_moderate_mixed_content(self, moderator, batch_content):
        """Batch moderation should handle mixed content correctly."""
        def mock_api_response(text, content_id):
            if "spam" in text.lower():
                return {"categories": ["spam"], "confidence": 0.65}
            elif "hate" in text.lower() or "kill" in text.lower():
                return {"categories": ["hate_speech"], "confidence": 0.90}
            elif not text.strip():
                return {"categories": ["spam"], "confidence": 1.0}
            else:
                return {"categories": ["safe"], "confidence": 0.05}

        moderator.api_client.moderate.side_effect = mock_api_response

        results = moderator.batch_moderate(batch_content)

        assert len(results) == 4

        # First item: safe
        assert results[0].status == ModerationStatus.APPROVED
        assert results[0].content_id == "post-001"

        # Second item: spam (pending review)
        assert results[1].status == ModerationStatus.PENDING_REVIEW
        assert results[1].content_id == "post-002"

        # Third item: hate speech (rejected)
        assert results[2].status == ModerationStatus.REJECTED
        assert results[2].content_id == "post-003"

        # Fourth item: empty (rejected)
        assert results[3].status == ModerationStatus.REJECTED
        assert results[3].content_id == "post-004"

    def test_batch_moderate_all_safe(self, moderator):
        """Batch with all safe content should approve all."""
        items = [
            {"content_id": f"post-{i}", "text": f"Nice content {i}", "author_id": f"user-{i}"}
            for i in range(5)
        ]

        results = moderator.batch_moderate(items)

        assert len(results) == 5
        for result in results:
            assert result.status == ModerationStatus.APPROVED
            assert result.is_approved() is True

    def test_batch_moderate_all_rejected(self, moderator):
        """Batch with all unsafe content should reject all."""
        items = [
            {"content_id": f"post-{i}", "text": "kill hate attack", "author_id": f"user-{i}"}
            for i in range(3)
        ]

        results = moderator.batch_moderate(items)

        assert len(results) == 3
        for result in results:
            assert result.status == ModerationStatus.REJECTED
            assert result.is_rejected() is True

    def test_batch_moderate_preserves_order(self, moderator, batch_content):
        """Results should be in the same order as input items."""
        def mock_api_response(text, content_id):
            if "spam" in text.lower():
                return {"categories": ["spam"], "confidence": 0.65}
            elif "hate" in text.lower():
                return {"categories": ["hate_speech"], "confidence": 0.90}
            elif not text.strip():
                return {"categories": ["spam"], "confidence": 1.0}
            else:
                return {"categories": ["safe"], "confidence": 0.05}

        moderator.api_client.moderate.side_effect = mock_api_response

        results = moderator.batch_moderate(batch_content)

        input_ids = [item["content_id"] for item in batch_content]
        result_ids = [r.content_id for r in results]
        assert result_ids == input_ids

    def test_batch_moderate_logs_all(self, moderator, batch_content):
        """All batch results should be logged."""
        initial_count = len(moderator.moderation_log)

        moderator.batch_moderate(batch_content)

        assert len(moderator.moderation_log) == initial_count + len(batch_content)

    def test_batch_moderate_calls_api_for_each(self, moderator, batch_content):
        """API should be called once per item in the batch."""
        moderator.batch_moderate(batch_content)

        assert moderator.api_client.moderate.call_count == len(batch_content)

    def test_batch_moderate_with_metadata(self, moderator):
        """Batch items with metadata should be processed correctly."""
        items = [
            {
                "content_id": "post-meta-1",
                "text": "Great content",
                "author_id": "user-1",
                "metadata": {"source": "mobile"},
            },
            {
                "content_id": "post-meta-2",
                "text": "Another post",
                "author_id": "user-2",
                "metadata": {"source": "web"},
            },
        ]

        results = moderator.batch_moderate(items)

        assert len(results) == 2
        assert results[0].content_id == "post-meta-1"
        assert results[1].content_id == "post-meta-2"

    def test_batch_moderate_single_item(self, moderator):
        """Batch with single item should work correctly."""
        items = [
            {"content_id": "post-single", "text": "Hello world", "author_id": "user-1"}
        ]

        results = moderator.batch_moderate(items)

        assert len(results) == 1
        assert results[0].content_id == "post-single"

    def test_batch_moderate_large_batch(self, moderator):
        """Large batch should be processed efficiently."""
        items = [
            {"content_id": f"post-{i}", "text": f"Content {i}", "author_id": f"user-{i}"}
            for i in range(100)
        ]

        results = moderator.batch_moderate(items)

        assert len(results) == 100
        assert moderator.api_client.moderate.call_count == 100


# ---------------------------------------------------------------------------
# Test: moderation_decision
# ---------------------------------------------------------------------------

class TestModerationDecision:
    """Tests for moderation decision logic."""

    def test_decision_safe_content_approved(self, moderator):
        """Safe content with low confidence should be approved."""
        categories = [ModerationCategory.SAFE]
        confidence = 0.05

        status = moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.APPROVED

    def test_decision_high_confidence_rejected(self, moderator):
        """High confidence unsafe content should be rejected."""
        categories = [ModerationCategory.HATE_SPEECH]
        confidence = 0.95

        status = moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.REJECTED

    def test_decision_borderline_pending_review(self, moderator):
        """Borderline content should be marked for review."""
        categories = [ModerationCategory.SPAM]
        confidence = 0.45

        status = moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.PENDING_REVIEW

    def test_decision_auto_approve_threshold(self, moderator):
        """Content below auto-approve threshold should be approved."""
        categories = [ModerationCategory.SAFE]
        confidence = 0.10  # Below AUTO_APPROVE_THRESHOLD (0.15)

        status = moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.APPROVED

    def test_decision_auto_reject_threshold(self, moderator):
        """Content at or above auto-reject threshold should be rejected."""
        categories = [ModerationCategory.VIOLENCE]
        confidence = 0.85  # At AUTO_REJECT_THRESHOLD

        status = moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.REJECTED

    def test_decision_safe_with_other_categories(self, moderator):
        """SAFE mixed with other categories should not auto-approve."""
        categories = [ModerationCategory.SAFE, ModerationCategory.SPAM]
        confidence = 0.10

        status = moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.PENDING_REVIEW

    def test_decision_strict_mode_lowers_threshold(self, strict_moderator):
        """Strict mode should reject content at lower confidence."""
        categories = [ModerationCategory.SPAM]
        confidence = 0.55

        status = strict_moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.REJECTED

    def test_decision_strict_mode_still_approves_safe(self, strict_moderator):
        """Strict mode should still approve clearly safe content."""
        categories = [ModerationCategory.SAFE]
        confidence = 0.05

        status = strict_moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.APPROVED

    def test_decision_multiple_unsafe_categories(self, moderator):
        """Multiple unsafe categories should be rejected."""
        categories = [
            ModerationCategory.HATE_SPEECH,
            ModerationCategory.VIOLENCE,
            ModerationCategory.HARASSMENT,
        ]
        confidence = 0.80

        status = moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.REJECTED

    def test_decision_confidence_boundary_low(self, moderator):
        """Test at exact auto-approve boundary."""
        categories = [ModerationCategory.SAFE]
        confidence = 0.14

        status = moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.APPROVED

    def test_decision_confidence_boundary_high(self, moderator):
        """Test just below auto-reject boundary."""
        categories = [ModerationCategory.SPAM]
        confidence = 0.84

        status = moderator._determine_status(categories, confidence)

        assert status == ModerationStatus.PENDING_REVIEW

    def test_generate_reason_approved(self, moderator):
        """Approved content should have no reason."""
        categories = [ModerationCategory.SAFE]
        status = ModerationStatus.APPROVED

        reason = moderator._generate_reason(categories, status)

        assert reason is None

    def test_generate_reason_rejected(self, moderator):
        """Rejected content should have descriptive reason."""
        categories = [ModerationCategory.HATE_SPEECH, ModerationCategory.VIOLENCE]
        status = ModerationStatus.REJECTED

        reason = moderator._generate_reason(categories, status)

        assert reason is not None
        assert "hate_speech" in reason
        assert "violence" in reason

    def test_generate_reason_pending_review(self, moderator):
        """Pending review content should have a reason."""
        categories = [ModerationCategory.SPAM]
        status = ModerationStatus.PENDING_REVIEW

        reason = moderator._generate_reason(categories, status)

        assert reason is not None
        assert "spam" in reason

    def test_generate_reason_no_flagged_categories(self, moderator):
        """Reason when no specific categories flagged."""
        categories = [ModerationCategory.SAFE]
        status = ModerationStatus.PENDING_REVIEW

        reason = moderator._generate_reason(categories, status)

        assert reason == "Content flagged for review"

    def test_moderation_result_is_approved(self):
        """ModerationResult.is_approved should work correctly."""
        result = ModerationResult(
            content_id="test",
            status=ModerationStatus.APPROVED,
            categories=[ModerationCategory.SAFE],
            confidence=0.05,
        )

        assert result.is_approved() is True
        assert result.is_rejected() is False

    def test_moderation_result_is_rejected(self):
        """ModerationResult.is_rejected should work correctly."""
        result = ModerationResult(
            content_id="test",
            status=ModerationStatus.REJECTED,
            categories=[ModerationCategory.HATE_SPEECH],
            confidence=0.95,
        )

        assert result.is_rejected() is True
        assert result.is_approved() is False

    def test_moderation_result_pending_neither(self):
        """Pending review should be neither approved nor rejected."""
        result = ModerationResult(
            content_id="test",
            status=ModerationStatus.PENDING_REVIEW,
            categories=[ModerationCategory.SPAM],
            confidence=0.45,
        )

        assert result.is_approved() is False
        assert result.is_rejected() is False

    def test_moderation_result_to_dict_serialization(self):
        """ModerationResult.to_dict should produce valid serializable data."""
        result = ModerationResult(
            content_id="post-001",
            status=ModerationStatus.REJECTED,
            categories=[ModerationCategory.VIOLENCE],
            confidence=0.92,
            reason="Detected: violence",
        )

        data = result.to_dict()

        assert data["content_id"] == "post-001"
        assert data["status"] == "rejected"
        assert data["categories"] == ["violence"]
        assert data["confidence"] == 0.92
        assert data["reason"] == "Detected: violence"
        assert "moderated_at" in data

        # Verify JSON serializable
        import json
        json_str = json.dumps(data)
        assert json_str is not None

    def test_moderation_log_isolated(self):
        """Moderation log should return a copy, not the internal list."""
        mod = ContentModerator(api_client=None)

        mod.moderate_content("post-1", "safe text", "user-1")

        log = mod.moderation_log
        log.clear()  # Should not affect internal state

        assert len(mod.moderation_log) == 1

    def test_category_weights_ordering(self):
        """Category weights should reflect severity ordering."""
        assert ContentModerator.CATEGORY_WEIGHTS[ModerationCategory.SAFE] == 0.0
        assert ContentModerator.CATEGORY_WEIGHTS[ModerationCategory.SPAM] < \
               ContentModerator.CATEGORY_WEIGHTS[ModerationCategory.HARASSMENT]
        assert ContentModerator.CATEGORY_WEIGHTS[ModerationCategory.HARASSMENT] < \
               ContentModerator.CATEGORY_WEIGHTS[ModerationCategory.VIOLENCE]
        assert ContentModerator.CATEGORY_WEIGHTS[ModerationCategory.VIOLENCE] < \
               ContentModerator.CATEGORY_WEIGHTS[ModerationCategory.HATE_SPEECH]

    def test_moderation_status_enum_values(self):
        """ModerationStatus enum should have correct values."""
        assert ModerationStatus.APPROVED.value == "approved"
        assert ModerationStatus.REJECTED.value == "rejected"
        assert ModerationStatus.PENDING_REVIEW.value == "pending_review"

    def test_moderation_category_enum_values(self):
        """ModerationCategory enum should have correct values."""
        assert ModerationCategory.SAFE.value == "safe"
        assert ModerationCategory.SPAM.value == "spam"
        assert ModerationCategory.HATE_SPEECH.value == "hate_speech"
        assert ModerationCategory.VIOLENCE.value == "violence"
        assert ModerationCategory.ADULT.value == "adult"
        assert ModerationCategory.HARASSMENT.value == "harassment"

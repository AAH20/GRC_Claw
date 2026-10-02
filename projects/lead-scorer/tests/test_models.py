"""Tests for lead scorer models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lead_scorer.models.scoring import (
    Lead,
    LeadCreate,
    LeadUpdate,
    LeadStatus,
    LeadSource,
    LeadScoreHistory,
    ScoringWeights,
)


class TestLead:
    """Tests for Lead model."""

    def test_create_lead(self) -> None:
        """Test creating a valid lead."""
        lead = Lead(
            id="lead-123",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            company="Example Corp",
        )
        assert lead.id == "lead-123"
        assert lead.email == "test@example.com"
        assert lead.full_name() == "John Doe"
        assert lead.status == LeadStatus.NEW

    def test_lead_email_normalized(self) -> None:
        """Test that email is normalized to lowercase."""
        lead = Lead(id="lead-1", email="Test@EXAMPLE.com")
        assert lead.email == "test@example.com"

    def test_lead_domain_normalized(self) -> None:
        """Test that domain is normalized to lowercase."""
        lead = Lead(id="lead-1", email="test@example.com", domain="EXAMPLE.COM")
        assert lead.domain == "example.com"

    def test_lead_invalid_email(self) -> None:
        """Test that invalid email raises error."""
        with pytest.raises(ValidationError):
            Lead(id="lead-1", email="invalid-email")

    def test_lead_score_update(self) -> None:
        """Test updating lead score."""
        lead = Lead(id="lead-1", email="test@example.com")
        lead.update_score(75.5, "warm")
        assert lead.score == 75.5
        assert lead.grade == "warm"

    def test_lead_score_clamped(self) -> None:
        """Test that score is clamped to 0-100."""
        lead = Lead(id="lead-1", email="test@example.com")
        lead.update_score(150.0, "hot")
        assert lead.score == 100.0
        lead.update_score(-10.0, "cold")
        assert lead.score == 0.0

    def test_lead_is_qualified(self) -> None:
        """Test qualified check."""
        lead = Lead(id="lead-1", email="test@example.com")
        assert not lead.is_qualified()
        lead.status = LeadStatus.QUALIFIED
        assert lead.is_qualified()


class TestLeadCreate:
    """Tests for LeadCreate model."""

    def test_create_valid(self) -> None:
        """Test creating valid lead create request."""
        data = LeadCreate(
            email="new@example.com",
            first_name="Jane",
            company="New Corp",
            source=LeadSource.WEBSITE,
        )
        assert data.email == "new@example.com"
        assert data.source == LeadSource.WEBSITE

    def test_create_invalid_email(self) -> None:
        """Test that invalid email raises error."""
        with pytest.raises(ValidationError):
            LeadCreate(email="not-an-email")


class TestLeadUpdate:
    """Tests for LeadUpdate model."""

    def test_update_partial(self) -> None:
        """Test partial update."""
        data = LeadUpdate(first_name="Updated")
        assert data.first_name == "Updated"
        assert data.last_name is None

    def test_update_status(self) -> None:
        """Test status update."""
        data = LeadUpdate(status=LeadStatus.CONTACTED)
        assert data.status == LeadStatus.CONTACTED


class TestLeadScoreHistory:
    """Tests for LeadScoreHistory model."""

    def test_create_history(self) -> None:
        """Test creating score history entry."""
        history = LeadScoreHistory(
            lead_id="lead-123",
            score=85.0,
            grade="hot",
            scored_at="2024-01-01T00:00:00Z",
            components={"engagement": 0.8},
        )
        assert history.lead_id == "lead-123"
        assert history.score == 85.0
        assert history.grade == "hot"


class TestScoringWeights:
    """Tests for ScoringWeights model."""

    def test_default_weights(self) -> None:
        """Test default weights sum to 1.0."""
        weights = ScoringWeights()
        assert weights.validate_total() is True

    def test_custom_weights(self) -> None:
        """Test custom weights."""
        weights = ScoringWeights(
            firmographic=0.3,
            technographic=0.2,
            engagement=0.2,
            intent=0.2,
            timing=0.1,
        )
        assert weights.validate_total() is True

    def test_invalid_weights(self) -> None:
        """Test that invalid weights fail validation."""
        weights = ScoringWeights(
            firmographic=0.5,
            technographic=0.5,
            engagement=0.5,
            intent=0.5,
            timing=0.5,
        )
        assert weights.validate_total() is False

    def test_weight_out_of_range(self) -> None:
        """Test that weight > 1.0 raises error."""
        with pytest.raises(ValidationError):
            ScoringWeights(firmographic=1.5)

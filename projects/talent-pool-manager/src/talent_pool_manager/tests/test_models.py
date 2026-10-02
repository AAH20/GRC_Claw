"""Tests for Pydantic data models."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from talent_pool_manager.models import (
    CandidateCreate,
    CandidateSkill,
    CandidateStatus,
    CandidateUpdate,
    EngagementCreate,
    EngagementType,
    OutreachCampaignCreate,
    OutreachChannel,
    OutreachTemplateCreate,
    PoolVisibility,
    SegmentCreate,
    SegmentType,
    TalentPoolCreate,
    TalentPoolUpdate,
)


class TestTalentPoolModels:
    """Tests for talent pool models."""

    def test_create_talent_pool(self) -> None:
        """Test creating a valid talent pool."""
        pool = TalentPoolCreate(
            name="Engineering Pool",
            description="Top engineering candidates",
            organization_id=uuid4(),
        )
        assert pool.name == "Engineering Pool"
        assert pool.visibility == PoolVisibility.PRIVATE
        assert pool.auto_refresh is False

    def test_talent_pool_validation_error(self) -> None:
        """Test talent pool validation with invalid data."""
        with pytest.raises(ValidationError):
            TalentPoolCreate(name="", organization_id=uuid4())

    def test_update_talent_pool(self) -> None:
        """Test updating a talent pool."""
        update = TalentPoolUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.description is None


class TestCandidateModels:
    """Tests for candidate models."""

    def test_create_candidate(self) -> None:
        """Test creating a valid candidate."""
        candidate = CandidateCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            pool_id=uuid4(),
        )
        assert candidate.first_name == "John"
        assert candidate.status == CandidateStatus.NEW

    def test_candidate_with_skills(self) -> None:
        """Test candidate with skills."""
        skills = [
            CandidateSkill(name="Python", proficiency="expert", years_experience=5),
            CandidateSkill(name="Go", proficiency="advanced", years_experience=3),
        ]
        candidate = CandidateCreate(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            pool_id=uuid4(),
            skills=skills,
        )
        assert len(candidate.skills) == 2
        assert candidate.skills[0].name == "Python"

    def test_candidate_validation_error(self) -> None:
        """Test candidate validation with invalid email."""
        with pytest.raises(ValidationError):
            CandidateCreate(
                first_name="John",
                last_name="Doe",
                email="invalid-email",
                pool_id=uuid4(),
            )

    def test_update_candidate(self) -> None:
        """Test updating a candidate."""
        update = CandidateUpdate(status=CandidateStatus.CONTACTED)
        assert update.status == CandidateStatus.CONTACTED


class TestSegmentModels:
    """Tests for segment models."""

    def test_create_segment(self) -> None:
        """Test creating a valid segment."""
        segment = SegmentCreate(
            name="Senior Engineers",
            pool_id=uuid4(),
            segment_type=SegmentType.EXPERIENCE_BASED,
        )
        assert segment.name == "Senior Engineers"
        assert segment.segment_type == SegmentType.EXPERIENCE_BASED

    def test_segment_validation_error(self) -> None:
        """Test segment validation with empty name."""
        with pytest.raises(ValidationError):
            SegmentCreate(name="", pool_id=uuid4())


class TestEngagementModels:
    """Tests for engagement models."""

    def test_create_engagement(self) -> None:
        """Test creating a valid engagement."""
        engagement = EngagementCreate(
            engagement_type=EngagementType.EMAIL,
            subject="Test Subject",
            content="Test content",
            candidate_id=uuid4(),
        )
        assert engagement.engagement_type == EngagementType.EMAIL
        assert engagement.channel == OutreachChannel.EMAIL

    def test_engagement_validation_error(self) -> None:
        """Test engagement validation with empty subject."""
        with pytest.raises(ValidationError):
            EngagementCreate(
                engagement_type=EngagementType.EMAIL,
                subject="",
                content="Test content",
                candidate_id=uuid4(),
            )


class TestOutreachModels:
    """Tests for outreach models."""

    def test_create_outreach_template(self) -> None:
        """Test creating a valid outreach template."""
        template = OutreachTemplateCreate(
            name="Test Template",
            subject_template="Hello {{name}}",
            body_template="Hi {{name}}, ...",
        )
        assert template.name == "Test Template"
        assert template.channel == OutreachChannel.EMAIL

    def test_create_outreach_campaign(self) -> None:
        """Test creating a valid outreach campaign."""
        campaign = OutreachCampaignCreate(
            name="Test Campaign",
            template_id=uuid4(),
        )
        assert campaign.name == "Test Campaign"

    def test_outreach_template_validation_error(self) -> None:
        """Test outreach template validation with empty name."""
        with pytest.raises(ValidationError):
            OutreachTemplateCreate(
                name="",
                subject_template="Subject",
                body_template="Body",
            )

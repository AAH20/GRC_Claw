"""Tests for escalation workflow models."""

from __future__ import annotations

from datetime import datetime

import pytest
from escalation_workflow.models.analysis import EscalationAnalysis, EscalationPattern, TrendReport
from escalation_workflow.models.escalation import (
    Escalation,
    EscalationCreate,
    EscalationStatus,
    EscalationUpdate,
)
from escalation_workflow.models.priority import Priority, PriorityAssessment, PriorityLevel
from escalation_workflow.models.resolution import Resolution, ResolutionCreate, ResolutionStatus
from escalation_workflow.models.sla import SLA, SLABreach, SLAStatus


class TestEscalationModel:
    """Tests for Escalation model."""

    def test_create_escalation(self) -> None:
        """Test creating a valid escalation."""
        escalation = Escalation(
            title="Test Escalation",
            description="Test description",
            requester="test_user",
        )
        assert escalation.title == "Test Escalation"
        assert escalation.status == EscalationStatus.PENDING
        assert escalation.priority == "medium"

    def test_escalation_create_schema(self) -> None:
        """Test EscalationCreate schema validation."""
        data = EscalationCreate(
            title="Test",
            description="Test description",
            requester="user",
        )
        assert data.priority == "medium"
        assert data.category == "general"

    def test_escalation_update_schema(self) -> None:
        """Test EscalationUpdate schema."""
        update = EscalationUpdate(priority="high")
        assert update.priority == "high"
        assert update.title is None

    def test_invalid_title_too_long(self) -> None:
        """Test validation fails for overly long title."""
        with pytest.raises(ValueError):
            Escalation(
                title="x" * 501,
                description="Test",
                requester="user",
            )


class TestPriorityModel:
    """Tests for Priority model."""

    def test_create_priority(self) -> None:
        """Test creating a priority configuration."""
        priority = Priority(
            level=PriorityLevel.HIGH,
            name="High",
            sla_minutes=30,
        )
        assert priority.level == PriorityLevel.HIGH
        assert priority.sla_minutes == 30

    def test_priority_assessment(self) -> None:
        """Test priority assessment model."""
        assessment = PriorityAssessment(
            escalation_id="123e4567-e89b-12d3-a456-426614174000",
            assessed_priority=PriorityLevel.CRITICAL,
            confidence=0.95,
            reasoning="Test reasoning",
        )
        assert assessment.confidence == 0.95


class TestSLAModel:
    """Tests for SLA model."""

    def test_create_sla(self) -> None:
        """Test creating an SLA record."""
        now = datetime.utcnow()
        sla = SLA(
            escalation_id="123e4567-e89b-12d3-a456-426614174000",
            priority="high",
            response_time_minutes=30,
            resolution_time_minutes=120,
            response_deadline=now,
            resolution_deadline=now,
        )
        assert sla.status == SLAStatus.ACTIVE
        assert sla.breach_count == 0

    def test_sla_breach(self) -> None:
        """Test SLA breach model."""
        breach = SLABreach(
            sla_id="123e4567-e89b-12d3-a456-426614174000",
            escalation_id="123e4567-e89b-12d3-a456-426614174001",
            minutes_overdue=15.5,
        )
        assert breach.minutes_overdue == 15.5
        assert not breach.acknowledged


class TestResolutionModel:
    """Tests for Resolution model."""

    def test_create_resolution(self) -> None:
        """Test creating a resolution."""
        resolution = Resolution(
            escalation_id="123e4567-e89b-12d3-a456-426614174000",
            title="Test Resolution",
            description="Test description",
        )
        assert resolution.status == ResolutionStatus.PROPOSED
        assert not resolution.automated

    def test_resolution_create_schema(self) -> None:
        """Test ResolutionCreate schema."""
        data = ResolutionCreate(
            escalation_id="123e4567-e89b-12d3-a456-426614174000",
            title="Test",
            description="Test description",
        )
        assert data.resolution_type == "manual"
        assert data.confidence == 0.0


class TestAnalysisModel:
    """Tests for Analysis models."""

    def test_create_analysis(self) -> None:
        """Test creating an analysis."""
        analysis = EscalationAnalysis(
            escalation_id="123e4567-e89b-12d3-a456-426614174000",
            patterns=[EscalationPattern.RECURRING],
            risk_score=0.7,
        )
        assert analysis.risk_score == 0.7
        assert EscalationPattern.RECURRING in analysis.patterns

    def test_trend_report(self) -> None:
        """Test trend report model."""
        now = datetime.utcnow()
        report = TrendReport(
            period_start=now,
            period_end=now,
            total_escalations=10,
            resolved_count=8,
        )
        assert report.total_escalations == 10
        assert report.resolved_count == 8

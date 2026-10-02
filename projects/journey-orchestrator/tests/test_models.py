"""Tests for data models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from journey_orchestrator.models.journey import (
    Journey,
    JourneyCreate,
    JourneyStatus,
    JourneyStep,
    CustomerEvent,
    Segment,
)


class TestJourneyStep:
    """Tests for JourneyStep model."""

    def test_create_step(self) -> None:
        step = JourneyStep(
            step_number=1,
            channel="email",
            action="send_welcome",
            delay_hours=0,
        )
        assert step.step_number == 1
        assert step.channel == "email"
        assert step.exit_conditions == []

    def test_step_with_exit_conditions(self) -> None:
        step = JourneyStep(
            step_number=2,
            channel="push",
            action="notify",
            exit_conditions=["converted", "unsubscribed"],
        )
        assert len(step.exit_conditions) == 2


class TestJourneyCreate:
    """Tests for JourneyCreate model."""

    def test_valid_create(self) -> None:
        create = JourneyCreate(
            business_goal="Increase sales",
            target_audience="Enterprise customers",
            channels=["email", "sms"],
        )
        assert create.business_goal == "Increase sales"
        assert create.channels == ["email", "sms"]

    def test_empty_goal_raises(self) -> None:
        with pytest.raises(ValidationError):
            JourneyCreate(business_goal="", target_audience="Users")

    def test_default_channels(self) -> None:
        create = JourneyCreate(
            business_goal="Test",
            target_audience="Users",
        )
        assert create.channels == ["email"]


class TestJourney:
    """Tests for Journey model."""

    def test_create_journey(self) -> None:
        journey = Journey(
            id="journey_123",
            name="Test Journey",
            business_goal="Test goal",
            target_audience="Test audience",
            channels=["email"],
        )
        assert journey.id == "journey_123"
        assert journey.status == JourneyStatus.DRAFT
        assert isinstance(journey.created_at, datetime)

    def test_journey_status_enum(self) -> None:
        assert JourneyStatus.DRAFT == "draft"
        assert JourneyStatus.ACTIVE == "active"
        assert JourneyStatus.PAUSED == "paused"
        assert JourneyStatus.COMPLETED == "completed"
        assert JourneyStatus.ARCHIVED == "archived"

    def test_journey_with_steps(self) -> None:
        journey = Journey(
            id="j_1",
            name="Test",
            business_goal="Goal",
            target_audience="Audience",
            channels=["email"],
            steps=[
                JourneyStep(step_number=1, channel="email", action="send"),
            ],
        )
        assert len(journey.steps) == 1


class TestCustomerEvent:
    """Tests for CustomerEvent model."""

    def test_create_event(self) -> None:
        event = CustomerEvent(
            id="evt_123",
            customer_id="cust_456",
            event_type="page_view",
            properties={"page": "/home"},
        )
        assert event.id == "evt_123"
        assert event.event_type == "page_view"
        assert event.properties["page"] == "/home"

    def test_event_default_timestamp(self) -> None:
        event = CustomerEvent(
            id="evt_1",
            customer_id="cust_1",
            event_type="test",
        )
        assert isinstance(event.timestamp, datetime)


class TestSegment:
    """Tests for Segment model."""

    def test_create_segment(self) -> None:
        segment = Segment(
            id="seg_123",
            name="High Value",
            criteria={"min_ltv": 1000},
        )
        assert segment.id == "seg_123"
        assert segment.name == "High Value"
        assert segment.customer_count == 0

    def test_segment_with_count(self) -> None:
        segment = Segment(
            id="seg_1",
            name="Test",
            customer_count=500,
        )
        assert segment.customer_count == 500

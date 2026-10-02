"""Planning Agent - Handles event strategy, venue selection, budget, and timeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from event_management.agents.base import AgentContext, BaseAgent


class VenueOption(BaseModel):
    """A venue option for the event."""

    name: str
    address: str
    capacity: int
    cost: float
    amenities: list[str] = Field(default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    score: float = 0.0


class BudgetItem(BaseModel):
    """A single budget line item."""

    category: str
    description: str
    estimated_cost: float
    actual_cost: float | None = None
    priority: str = "medium"  # low, medium, high


class TimelineTask(BaseModel):
    """A task on the event timeline."""

    name: str
    description: str
    start_date: str
    end_date: str
    owner: str
    dependencies: list[str] = Field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed


class PlanningInput(BaseModel):
    """Input for the Planning Agent."""

    event_name: str
    event_type: str  # conference, workshop, meetup, webinar, social
    expected_attendees: int
    date: str
    duration_hours: float
    budget_total: float
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(default_factory=dict)


class PlanningOutput(BaseModel):
    """Output from the Planning Agent."""

    event_strategy: str = ""
    venue_options: list[VenueOption] = Field(default_factory=list)
    recommended_venue: VenueOption | None = None
    budget_breakdown: list[BudgetItem] = Field(default_factory=list)
    timeline: list[TimelineTask] = Field(default_factory=list)
    risk_assessment: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class PlanningAgent(BaseAgent[PlanningInput, PlanningOutput]):
    """Agent responsible for event planning and strategy."""

    @property
    def name(self) -> str:
        return "PlanningAgent"

    async def execute(self, input_data: PlanningInput, context: AgentContext) -> PlanningOutput:
        """Generate a comprehensive event plan.

        Args:
            input_data: The planning requirements and constraints.
            context: Execution context with event and user info.

        Returns:
            A complete event plan with venue, budget, and timeline.
        """
        self.logger.info(
            "generating_event_plan",
            event_name=input_data.event_name,
            event_type=input_data.event_type,
            expected_attendees=input_data.expected_attendees,
        )

        # Generate venue options based on requirements
        venue_options = self._generate_venue_options(input_data)
        recommended_venue = venue_options[0] if venue_options else None

        # Create budget breakdown
        budget_breakdown = self._create_budget_breakdown(input_data)

        # Build timeline
        timeline = self._build_timeline(input_data)

        # Assess risks
        risks = self._assess_risks(input_data)

        # Generate recommendations
        recommendations = self._generate_recommendations(input_data)

        strategy = self._create_strategy_summary(input_data)

        return PlanningOutput(
            event_strategy=strategy,
            venue_options=venue_options,
            recommended_venue=recommended_venue,
            budget_breakdown=budget_breakdown,
            timeline=timeline,
            risk_assessment=risks,
            recommendations=recommendations,
        )

    def _generate_venue_options(self, data: PlanningInput) -> list[VenueOption]:
        """Generate venue options based on event requirements."""
        # In production, this would query venue databases and APIs
        base_cost = data.budget_total * 0.3
        return [
            VenueOption(
                name="Downtown Conference Center",
                address="123 Main St, City Center",
                capacity=max(data.expected_attendees + 50, 200),
                cost=base_cost,
                amenities=["WiFi", "AV Equipment", "Catering Kitchen", "Parking"],
                pros=["Central location", "Full AV support", "On-site catering"],
                cons=["Higher cost", "Limited availability"],
                score=0.85,
            ),
            VenueOption(
                name="Tech Hub Coworking Space",
                address="456 Innovation Blvd",
                capacity=max(data.expected_attendees + 20, 100),
                cost=base_cost * 0.6,
                amenities=["WiFi", "Projectors", "Whiteboards", "Coffee Bar"],
                pros=["Modern tech setup", "Flexible layout", "Affordable"],
                cons=["No on-site catering", "Street parking only"],
                score=0.72,
            ),
            VenueOption(
                name="University Auditorium",
                address="789 Campus Dr",
                capacity=max(data.expected_attendees + 100, 300),
                cost=base_cost * 0.4,
                amenities=["WiFi", "PA System", "Stage", "Seating for 500"],
                pros=["Very affordable", "Large capacity", "Professional setup"],
                cons=["Academic calendar constraints", "Basic amenities"],
                score=0.65,
            ),
        ]

    def _create_budget_breakdown(self, data: PlanningInput) -> list[BudgetItem]:
        """Create a detailed budget breakdown."""
        total = data.budget_total
        return [
            BudgetItem(
                category="Venue",
                description="Venue rental and setup",
                estimated_cost=total * 0.30,
                priority="high",
            ),
            BudgetItem(
                category="Catering",
                description="Food and beverages",
                estimated_cost=total * 0.25,
                priority="high",
            ),
            BudgetItem(
                category="Marketing",
                description="Promotion and advertising",
                estimated_cost=total * 0.15,
                priority="medium",
            ),
            BudgetItem(
                category="AV & Tech",
                description="Audio/visual equipment and tech support",
                estimated_cost=total * 0.10,
                priority="medium",
            ),
            BudgetItem(
                category="Speakers",
                description="Speaker fees and travel",
                estimated_cost=total * 0.10,
                priority="medium",
            ),
            BudgetItem(
                category="Miscellaneous",
                description="Contingency and unexpected costs",
                estimated_cost=total * 0.10,
                priority="low",
            ),
        ]

    def _build_timeline(self, data: PlanningInput) -> list[TimelineTask]:
        """Build an event planning timeline."""
        return [
            TimelineTask(
                name="Venue Booking",
                description="Secure venue and sign contract",
                start_date="T-90 days",
                end_date="T-75 days",
                owner="Event Manager",
                status="pending",
            ),
            TimelineTask(
                name="Speaker Outreach",
                description="Identify and confirm speakers",
                start_date="T-75 days",
                end_date="T-45 days",
                owner="Content Lead",
                dependencies=["Venue Booking"],
                status="pending",
            ),
            TimelineTask(
                name="Marketing Launch",
                description="Begin promotional campaigns",
                start_date="T-45 days",
                end_date="T-1 day",
                owner="Marketing Lead",
                dependencies=["Venue Booking"],
                status="pending",
            ),
            TimelineTask(
                name="Registration Open",
                description="Open attendee registration",
                start_date="T-30 days",
                end_date="T-1 day",
                owner="Event Manager",
                dependencies=["Marketing Launch"],
                status="pending",
            ),
            TimelineTask(
                name="Final Logistics",
                description="Confirm all vendors and logistics",
                start_date="T-7 days",
                end_date="T-1 day",
                owner="Event Manager",
                dependencies=["Speaker Outreach", "Registration Open"],
                status="pending",
            ),
            TimelineTask(
                name="Event Day",
                description="Execute the event",
                start_date="T-0",
                end_date="T-0",
                owner="All Teams",
                dependencies=["Final Logistics"],
                status="pending",
            ),
        ]

    def _assess_risks(self, data: PlanningInput) -> list[str]:
        """Assess potential risks for the event."""
        risks = [
            "Venue availability may be limited for popular dates",
            "Speaker cancellations could affect program quality",
            "Weather may impact attendance for outdoor components",
            "Budget overruns in catering or AV",
        ]
        if data.expected_attendees > 200:
            risks.append("Large crowd requires additional security and safety measures")
        if data.budget_total < 5000:
            risks.append("Limited budget may constrain venue and catering options")
        return risks

    def _generate_recommendations(self, data: PlanningInput) -> list[str]:
        """Generate planning recommendations."""
        recs = [
            "Book venue at least 90 days in advance for best rates",
            "Implement early-bird pricing to drive early registration",
            "Create a detailed run-of-show document for event day",
            "Establish a communication plan for all stakeholders",
        ]
        if data.event_type == "conference":
            recs.append("Consider a mobile app for attendee engagement")
        if data.event_type == "workshop":
            recs.append("Limit attendance to ensure hands-on experience quality")
        return recs

    def _create_strategy_summary(self, data: PlanningInput) -> str:
        """Create a high-level strategy summary."""
        return (
            f"Plan a {data.event_type} event '{data.event_name}' for "
            f"{data.expected_attendees} attendees on {data.date} with a "
            f"budget of ${data.budget_total:,.2f}. Focus on: "
            f"{', '.join(data.goals) if data.goals else 'delivering a great experience'}."
        )

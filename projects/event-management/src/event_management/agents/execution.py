"""Execution Agent - Handles day-of logistics, vendor coordination, and check-in."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from event_management.agents.base import AgentContext, BaseAgent


class VendorTask(BaseModel):
    """A vendor coordination task."""

    vendor_name: str
    vendor_type: str  # catering, av, security, decor, transportation
    task: str
    deadline: str
    status: str = "pending"  # pending, confirmed, in_progress, completed
    contact_info: str = ""
    notes: str = ""


class CheckInStation(BaseModel):
    """An attendee check-in station configuration."""

    station_id: str
    name: str
    location: str
    staff_assigned: list[str] = Field(default_factory=list)
    capacity_per_hour: int = 50
    equipment_needed: list[str] = Field(default_factory=list)


class RunOfShowItem(BaseModel):
    """A single item in the run of show."""

    time: str
    duration_minutes: int
    activity: str
    owner: str
    location: str
    av_needs: list[str] = Field(default_factory=list)
    notes: str = ""


class ExecutionInput(BaseModel):
    """Input for the Execution Agent."""

    event_name: str
    event_date: str
    venue: str
    expected_attendees: int
    staff_count: int
    vendors: list[dict[str, Any]] = Field(default_factory=list)
    schedule: list[dict[str, Any]] = Field(default_factory=list)
    special_requirements: list[str] = Field(default_factory=list)


class ExecutionOutput(BaseModel):
    """Output from the Execution Agent."""

    run_of_show: list[RunOfShowItem] = Field(default_factory=list)
    vendor_tasks: list[VendorTask] = Field(default_factory=list)
    checkin_stations: list[CheckInStation] = Field(default_factory=list)
    staffing_plan: dict[str, Any] = Field(default_factory=dict)
    contingency_plans: list[str] = Field(default_factory=list)
    day_of_timeline: list[dict[str, Any]] = Field(default_factory=list)


class ExecutionAgent(BaseAgent[ExecutionInput, ExecutionOutput]):
    """Agent responsible for event execution and day-of logistics."""

    @property
    def name(self) -> str:
        return "ExecutionAgent"

    async def execute(self, input_data: ExecutionInput, context: AgentContext) -> ExecutionOutput:
        """Generate a comprehensive execution plan.

        Args:
            input_data: The execution requirements and logistics.
            context: Execution context with event and user info.

        Returns:
            A complete execution plan with run of show, vendors, and staffing.
        """
        self.logger.info(
            "generating_execution_plan",
            event_name=input_data.event_name,
            venue=input_data.venue,
            expected_attendees=input_data.expected_attendees,
        )

        run_of_show = self._create_run_of_show(input_data)
        vendor_tasks = self._coordinate_vendors(input_data)
        checkin_stations = self._setup_checkin(input_data)
        staffing_plan = self._create_staffing_plan(input_data)
        contingencies = self._create_contingency_plans(input_data)
        day_of_timeline = self._create_day_of_timeline(input_data)

        return ExecutionOutput(
            run_of_show=run_of_show,
            vendor_tasks=vendor_tasks,
            checkin_stations=checkin_stations,
            staffing_plan=staffing_plan,
            contingency_plans=contingencies,
            day_of_timeline=day_of_timeline,
        )

    def _create_run_of_show(self, data: ExecutionInput) -> list[RunOfShowItem]:
        """Create a detailed run of show for event day."""
        return [
            RunOfShowItem(
                time="07:00",
                duration_minutes=60,
                activity="Venue Setup & Vendor Load-in",
                owner="Event Manager",
                location="Main Hall",
                av_needs=["Power", "WiFi Test"],
                notes="All vendors must be loaded in by 08:00",
            ),
            RunOfShowItem(
                time="08:00",
                duration_minutes=30,
                activity="Staff Briefing & Final Checks",
                owner="Event Manager",
                location="Back Stage",
                av_needs=["PA System"],
                notes="Review emergency procedures and day-of timeline",
            ),
            RunOfShowItem(
                time="08:30",
                duration_minutes=30,
                activity="Check-in Stations Open",
                owner="Check-in Team",
                location="Entrance",
                av_needs=["Laptops", "Printers", "Badge Stock"],
                notes="Begin attendee check-in",
            ),
            RunOfShowItem(
                time="09:00",
                duration_minutes=15,
                activity="Welcome & Opening Remarks",
                owner="MC",
                location="Main Stage",
                av_needs=["Microphone", "Projector", "Slides"],
                notes="Welcome attendees and introduce event",
            ),
            RunOfShowItem(
                time="09:15",
                duration_minutes=45,
                activity="Keynote Presentation",
                owner="Keynote Speaker",
                location="Main Stage",
                av_needs=["Microphone", "Projector", "Clicker", "Laptop"],
                notes="Main keynote address",
            ),
            RunOfShowItem(
                time="10:00",
                duration_minutes=15,
                activity="Networking Break",
                owner="All Staff",
                location="Lobby",
                av_needs=["Background Music"],
                notes="Refreshments available",
            ),
            RunOfShowItem(
                time="10:15",
                duration_minutes=90,
                activity="Breakout Sessions",
                owner="Session Leads",
                location="Breakout Rooms",
                av_needs=["Projectors", "Microphones"],
                notes="Multiple tracks running in parallel",
            ),
            RunOfShowItem(
                time="11:45",
                duration_minutes=60,
                activity="Lunch",
                owner="Catering Team",
                location="Dining Area",
                av_needs=[],
                notes="Buffet style service",
            ),
            RunOfShowItem(
                time="12:45",
                duration_minutes=90,
                activity="Afternoon Workshops",
                owner="Workshop Leads",
                location="Breakout Rooms",
                av_needs=["Projectors", "Whiteboards"],
                notes="Hands-on workshop sessions",
            ),
            RunOfShowItem(
                time="14:15",
                duration_minutes=15,
                activity="Afternoon Break",
                owner="All Staff",
                location="Lobby",
                av_needs=["Background Music"],
                notes="Snacks and beverages",
            ),
            RunOfShowItem(
                time="14:30",
                duration_minutes=60,
                activity="Panel Discussion",
                owner="Moderator",
                location="Main Stage",
                av_needs=["Panel Mics", "Projector"],
                notes="Industry panel Q&A",
            ),
            RunOfShowItem(
                time="15:30",
                duration_minutes=30,
                activity="Closing Remarks & Awards",
                owner="MC",
                location="Main Stage",
                av_needs=["Microphone", "Projector"],
                notes="Thank sponsors and attendees",
            ),
            RunOfShowItem(
                time="16:00",
                duration_minutes=60,
                activity="Networking & Wrap-up",
                owner="All Staff",
                location="Main Hall",
                av_needs=["Background Music"],
                notes="Informal networking",
            ),
            RunOfShowItem(
                time="17:00",
                duration_minutes=60,
                activity="Teardown & Vendor Load-out",
                owner="Event Manager",
                location="Main Hall",
                av_needs=[],
                notes="All vendors out by 18:00",
            ),
        ]

    def _coordinate_vendors(self, data: ExecutionInput) -> list[VendorTask]:
        """Create vendor coordination tasks."""
        return [
            VendorTask(
                vendor_name="Catering Co.",
                vendor_type="catering",
                task="Finalize menu and headcount",
                deadline="T-3 days",
                status="confirmed",
                contact_info="orders@cateringco.com",
                notes="Include vegetarian and gluten-free options",
            ),
            VendorTask(
                vendor_name="AV Solutions",
                vendor_type="av",
                task="Test all AV equipment",
                deadline="T-1 day",
                status="confirmed",
                contact_info="support@avsolutions.com",
                notes="Full sound check and projector test",
            ),
            VendorTask(
                vendor_name="Secure Events",
                vendor_type="security",
                task="Post security staff at all entrances",
                deadline="T-0",
                status="confirmed",
                contact_info="dispatch@secureevents.com",
                notes="4 guards: 2 at main entrance, 1 at VIP, 1 roving",
            ),
            VendorTask(
                vendor_name="Floral Designs",
                vendor_type="decor",
                task="Set up stage and table decorations",
                deadline="T-0 06:00",
                status="confirmed",
                contact_info="events@floraldesigns.com",
                notes="Stage backdrop, registration table, centerpieces",
            ),
        ]

    def _setup_checkin(self, data: ExecutionInput) -> list[CheckInStation]:
        """Set up attendee check-in stations."""
        num_stations = max(2, data.expected_attendees // 100)
        stations = []
        for i in range(num_stations):
            stations.append(
                CheckInStation(
                    station_id=f"CHK-{i + 1:03d}",
                    name=f"Check-in Station {i + 1}",
                    location=f"Entrance Area {i + 1}",
                    staff_assigned=[f"Staff {i * 2 + 1}", f"Staff {i * 2 + 2}"],
                    capacity_per_hour=60,
                    equipment_needed=["Laptop", "Badge Printer", "Scanner", "Badge Stock"],
                )
            )
        # Add VIP station
        stations.append(
            CheckInStation(
                station_id="CHK-VIP",
                name="VIP Check-in",
                location="VIP Lounge Entrance",
                staff_assigned=["VIP Coordinator", "Staff 10"],
                capacity_per_hour=30,
                equipment_needed=["Laptop", "Premium Badge Stock", "Welcome Packets"],
            )
        )
        return stations

    def _create_staffing_plan(self, data: ExecutionInput) -> dict[str, Any]:
        """Create a staffing plan for event day."""
        return {
            "total_staff": data.staff_count,
            "roles": {
                "event_manager": {"count": 1, "responsibilities": "Overall coordination"},
                "registration_desk": {
                    "count": max(2, data.expected_attendees // 100),
                    "responsibilities": "Check-in and badge printing"
                },
                "av_technician": {"count": 2, "responsibilities": "Audio/visual support"},
                "runner": {
                    "count": max(2, data.staff_count // 5),
                    "responsibilities": "General support and errands"
                },
                "volunteer_coordinator": {"count": 1, "responsibilities": "Manage volunteers"},
                "sponsor_liaison": {"count": 1, "responsibilities": "Sponsor support"},
            },
            "shift_schedule": {
                "setup_shift": {"start": "06:00", "end": "10:00", "staff": data.staff_count},
                "main_shift": {"start": "08:00", "end": "18:00", "staff": data.staff_count},
                "teardown_shift": {
                    "start": "16:00",
                    "end": "20:00",
                    "staff": max(3, data.staff_count // 2)
                },
            },
        }

    def _create_contingency_plans(self, data: ExecutionInput) -> list[str]:
        """Create contingency plans for common issues."""
        return [
            "Venue power failure: Backup generator on-site, UPS for critical AV equipment",
            "Speaker no-show: Pre-recorded video backup, moderator prepared to extend Q&A",
            "Overcrowding: Overflow room with live stream, additional seating on standby",
            "Medical emergency: First aid station on-site, AED available, "
            "nearest hospital: 5 min drive",
            "Catering shortage: Backup catering vendor on call, emergency food supply",
            "Check-in system failure: Manual sign-in sheet backup, printed attendee list",
            "Severe weather: Indoor backup plan, communication tree for attendee notification",
        ]

    def _create_day_of_timeline(self, data: ExecutionInput) -> list[dict[str, Any]]:
        """Create a detailed day-of timeline."""
        return [
            {
                "time": "06:00",
                "task": "Venue opens, vendor load-in begins",
                "owner": "Event Manager"
            },
            {"time": "07:00", "task": "AV setup and testing", "owner": "AV Technician"},
            {"time": "07:30", "task": "Registration desk setup", "owner": "Registration Lead"},
            {"time": "08:00", "task": "Staff briefing", "owner": "Event Manager"},
            {"time": "08:30", "task": "Check-in opens", "owner": "Registration Team"},
            {"time": "09:00", "task": "Event begins", "owner": "MC"},
            {"time": "16:00", "task": "Event ends, networking", "owner": "All"},
            {"time": "17:00", "task": "Teardown begins", "owner": "Event Manager"},
            {"time": "18:00", "task": "Venue clear", "owner": "Event Manager"},
        ]

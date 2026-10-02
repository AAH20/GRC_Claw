"""Production Agent.

Manages video production workflows including scheduling, asset management,
shot lists, and production status tracking.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ProductionStatus(StrEnum):
    """Production workflow status."""

    PENDING = "pending"
    PRE_PRODUCTION = "pre_production"
    READY_TO_SHOOT = "ready_to_shoot"
    IN_PRODUCTION = "in_production"
    POST_PRODUCTION = "post_production"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class ShotType(StrEnum):
    """Types of shots in a production."""

    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    OVER_SHOULDER = "over_shoulder"
    B_ROLL = "b_roll"
    AERIAL = "aerial"
    SCREEN_CAPTURE = "screen_capture"


@dataclass
class Shot:
    """A single shot in a production."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    shot_type: ShotType = ShotType.MEDIUM
    description: str = ""
    duration_seconds: float = 5.0
    location: str = ""
    equipment_needed: list[str] = field(default_factory=list)
    notes: str = ""
    completed: bool = False
    takes: int = 0
    best_take: int | None = None


@dataclass
class ProductionAsset:
    """An asset required for production."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    asset_type: str = ""  # video, audio, image, graphic, document
    url: str = ""
    status: str = "pending"  # pending, approved, rejected
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Production:
    """A video production project."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    script_id: str = ""
    status: ProductionStatus = ProductionStatus.PENDING
    shots: list[Shot] = field(default_factory=list)
    assets: list[ProductionAsset] = field(default_factory=list)
    scheduled_date: datetime | None = None
    location: str = ""
    crew: list[str] = field(default_factory=list)
    equipment: list[str] = field(default_factory=list)
    budget: float = 0.0
    actual_cost: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage based on shots."""
        if not self.shots:
            return 0.0
        completed = sum(1 for s in self.shots if s.completed)
        return (completed / len(self.shots)) * 100

    @property
    def total_shot_duration(self) -> float:
        """Calculate total duration of all shots."""
        return sum(s.duration_seconds for s in self.shots)

    @property
    def is_over_budget(self) -> bool:
        """Check if production is over budget."""
        return self.budget > 0 and self.actual_cost > self.budget

    def to_dict(self) -> dict[str, Any]:
        """Convert production to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "script_id": self.script_id,
            "status": self.status.value,
            "completion_percentage": self.completion_percentage,
            "total_shot_duration_seconds": self.total_shot_duration,
            "shot_count": len(self.shots),
            "completed_shots": sum(1 for s in self.shots if s.completed),
            "asset_count": len(self.assets),
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "location": self.location,
            "crew": self.crew,
            "equipment": self.equipment,
            "budget": self.budget,
            "actual_cost": self.actual_cost,
            "is_over_budget": self.is_over_budget,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
            "metadata": self.metadata,
        }


class ProductionError(Exception):
    """Raised when a production operation fails."""

    def __init__(self, message: str, production_id: str | None = None) -> None:
        super().__init__(message)
        self.production_id = production_id


class ProductionAgent:
    """Agent responsible for managing video production workflows.

    Handles production lifecycle from pre-production planning through
    shooting, asset management, and completion tracking.
    """

    def __init__(self, storage_backend: Any | None = None) -> None:
        """Initialize the Production Agent.

        Args:
            storage_backend: Optional storage backend for persistence.
        """
        self._storage = storage_backend
        self._productions: dict[str, Production] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def create_production(
        self,
        title: str,
        script_id: str = "",
        location: str = "",
        scheduled_date: datetime | None = None,
        crew: list[str] | None = None,
        equipment: list[str] | None = None,
        budget: float = 0.0,
        notes: str = "",
    ) -> Production:
        """Create a new production project.

        Args:
            title: Production title.
            script_id: Associated script ID.
            location: Filming location.
            scheduled_date: Scheduled production date.
            crew: List of crew members.
            equipment: Required equipment list.
            budget: Production budget.
            notes: Additional notes.

        Returns:
            The created Production object.

        Raises:
            ProductionError: If creation fails.
        """
        if not title or not title.strip():
            raise ProductionError("Production title is required")

        production = Production(
            title=title,
            script_id=script_id,
            location=location,
            scheduled_date=scheduled_date,
            crew=crew or [],
            equipment=equipment or [],
            budget=budget,
            notes=notes,
        )

        self._productions[production.id] = production
        self._logger.info(
            "Production created",
            extra={"production_id": production.id, "title": title},
        )
        return production

    async def get_production(self, production_id: str) -> Production:
        """Get a production by ID.

        Args:
            production_id: The production ID.

        Returns:
            The Production object.

        Raises:
            ProductionError: If production not found.
        """
        if production_id not in self._productions:
            raise ProductionError(
                f"Production '{production_id}' not found",
                production_id=production_id,
            )
        return self._productions[production_id]

    async def update_status(
        self,
        production_id: str,
        status: ProductionStatus,
    ) -> Production:
        """Update production status.

        Args:
            production_id: The production ID.
            status: New status.

        Returns:
            Updated Production object.

        Raises:
            ProductionError: If production not found or invalid transition.
        """
        production = await self.get_production(production_id)

        # Validate status transition
        valid_transitions = self._get_valid_transitions(production.status)
        if status not in valid_transitions:
            raise ProductionError(
                f"Invalid status transition from {production.status.value} to {status.value}",
                production_id=production_id,
            )

        production.status = status
        production.updated_at = datetime.now(UTC)

        if status == ProductionStatus.COMPLETED:
            production.completed_at = datetime.now(UTC)

        self._logger.info(
            "Production status updated",
            extra={"production_id": production_id, "status": status.value},
        )
        return production

    def _get_valid_transitions(self, current: ProductionStatus) -> list[ProductionStatus]:
        """Get valid status transitions from current status."""
        transitions: dict[ProductionStatus, list[ProductionStatus]] = {
            ProductionStatus.PENDING: [
                ProductionStatus.PRE_PRODUCTION,
                ProductionStatus.ON_HOLD,
                ProductionStatus.CANCELLED,
            ],
            ProductionStatus.PRE_PRODUCTION: [
                ProductionStatus.READY_TO_SHOOT,
                ProductionStatus.ON_HOLD,
                ProductionStatus.CANCELLED,
            ],
            ProductionStatus.READY_TO_SHOOT: [
                ProductionStatus.IN_PRODUCTION,
                ProductionStatus.ON_HOLD,
                ProductionStatus.CANCELLED,
            ],
            ProductionStatus.IN_PRODUCTION: [
                ProductionStatus.POST_PRODUCTION,
                ProductionStatus.ON_HOLD,
                ProductionStatus.CANCELLED,
            ],
            ProductionStatus.POST_PRODUCTION: [
                ProductionStatus.COMPLETED,
                ProductionStatus.ON_HOLD,
            ],
            ProductionStatus.ON_HOLD: [
                ProductionStatus.PRE_PRODUCTION,
                ProductionStatus.READY_TO_SHOOT,
                ProductionStatus.IN_PRODUCTION,
                ProductionStatus.CANCELLED,
            ],
            ProductionStatus.COMPLETED: [],
            ProductionStatus.CANCELLED: [],
        }
        return transitions.get(current, [])

    async def add_shot(
        self,
        production_id: str,
        shot_type: ShotType,
        description: str,
        duration_seconds: float = 5.0,
        location: str = "",
        equipment_needed: list[str] | None = None,
        notes: str = "",
    ) -> Shot:
        """Add a shot to a production.

        Args:
            production_id: The production ID.
            shot_type: Type of shot.
            description: Shot description.
            duration_seconds: Estimated duration.
            location: Shot location.
            equipment_needed: Equipment required for this shot.
            notes: Additional notes.

        Returns:
            The created Shot object.

        Raises:
            ProductionError: If production not found.
        """
        production = await self.get_production(production_id)

        shot = Shot(
            shot_type=shot_type,
            description=description,
            duration_seconds=duration_seconds,
            location=location,
            equipment_needed=equipment_needed or [],
            notes=notes,
        )

        production.shots.append(shot)
        production.updated_at = datetime.now(UTC)

        self._logger.info(
            "Shot added to production",
            extra={"production_id": production_id, "shot_id": shot.id, "type": shot_type.value},
        )
        return shot

    async def mark_shot_complete(
        self,
        production_id: str,
        shot_id: str,
        best_take: int | None = None,
    ) -> Shot:
        """Mark a shot as completed.

        Args:
            production_id: The production ID.
            shot_id: The shot ID.
            best_take: The best take number.

        Returns:
            Updated Shot object.

        Raises:
            ProductionError: If production or shot not found.
        """
        production = await self.get_production(production_id)

        shot = next((s for s in production.shots if s.id == shot_id), None)
        if shot is None:
            raise ProductionError(
                f"Shot '{shot_id}' not found in production '{production_id}'",
                production_id=production_id,
            )

        shot.completed = True
        shot.takes += 1
        shot.best_take = best_take
        production.updated_at = datetime.now(UTC)

        self._logger.info(
            "Shot completed",
            extra={"production_id": production_id, "shot_id": shot_id},
        )
        return shot

    async def add_asset(
        self,
        production_id: str,
        name: str,
        asset_type: str,
        url: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ProductionAsset:
        """Add an asset to a production.

        Args:
            production_id: The production ID.
            name: Asset name.
            asset_type: Type of asset.
            url: Asset URL or path.
            metadata: Additional metadata.

        Returns:
            The created ProductionAsset.

        Raises:
            ProductionError: If production not found.
        """
        production = await self.get_production(production_id)

        asset = ProductionAsset(
            name=name,
            asset_type=asset_type,
            url=url,
            metadata=metadata or {},
        )

        production.assets.append(asset)
        production.updated_at = datetime.now(UTC)

        self._logger.info(
            "Asset added to production",
            extra={"production_id": production_id, "asset_id": asset.id, "name": name},
        )
        return asset

    async def update_budget(
        self,
        production_id: str,
        actual_cost: float,
    ) -> Production:
        """Update actual production cost.

        Args:
            production_id: The production ID.
            actual_cost: The actual cost incurred.

        Returns:
            Updated Production object.

        Raises:
            ProductionError: If production not found.
        """
        production = await self.get_production(production_id)
        production.actual_cost = actual_cost
        production.updated_at = datetime.now(UTC)

        if production.is_over_budget:
            self._logger.warning(
                "Production over budget",
                extra={
                    "production_id": production_id,
                    "budget": production.budget,
                    "actual_cost": actual_cost,
                },
            )

        return production

    async def list_productions(
        self,
        status: ProductionStatus | None = None,
    ) -> list[Production]:
        """List productions, optionally filtered by status.

        Args:
            status: Filter by status.

        Returns:
            List of Production objects.
        """
        productions = list(self._productions.values())
        if status is not None:
            productions = [p for p in productions if p.status == status]
        return sorted(productions, key=lambda p: p.created_at, reverse=True)

    async def generate_shot_list(self, production_id: str) -> list[dict[str, Any]]:
        """Generate a formatted shot list for a production.

        Args:
            production_id: The production ID.

        Returns:
            List of shot dictionaries ready for production use.

        Raises:
            ProductionError: If production not found.
        """
        production = await self.get_production(production_id)
        return [
            {
                "shot_number": i + 1,
                "shot_id": s.id,
                "type": s.shot_type.value,
                "description": s.description,
                "duration_seconds": s.duration_seconds,
                "location": s.location,
                "equipment": s.equipment_needed,
                "completed": s.completed,
                "notes": s.notes,
            }
            for i, s in enumerate(production.shots)
        ]

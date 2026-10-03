"""Interview model for the recruitment platform."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from recruitment_platform.models.base import Base


class Interview(Base):
    """Represents an interview scheduled for a job application."""

    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Duration in minutes"
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="scheduled",
        comment="scheduled, completed, cancelled, no_show",
    )
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    application = relationship("Application", back_populates="interviews")
    interviewer = relationship("User", back_populates="interviews")

    def __repr__(self) -> str:
        return (
            f"<Interview(id={self.id}, application_id={self.application_id}, "
            f"status={self.status}, scheduled_at={self.scheduled_at})>"
        )

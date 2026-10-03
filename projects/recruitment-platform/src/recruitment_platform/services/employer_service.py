"""Employer service for recruitment platform."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from recruitment_platform.models.employer import Employer
from recruitment_platform.schemas.employer import EmployerCreate, EmployerUpdate

logger = logging.getLogger(__name__)


class EmployerNotFoundError(Exception):
    """Raised when an employer is not found."""

    def __init__(self, employer_id: int) -> None:
        self.employer_id = employer_id
        super().__init__(f"Employer with id {employer_id} not found")


class EmployerValidationError(Exception):
    """Raised when employer data fails validation."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EmployerService:
    """Service for managing employers."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_employer(self, data: EmployerCreate) -> Employer:
        """Create a new employer with validation.

        Args:
            data: Employer creation data.

        Returns:
            The created Employer instance.

        Raises:
            EmployerValidationError: If data validation fails.
            SQLAlchemyError: If database operation fails.
        """
        try:
            # Validate required fields
            if not data.name or not data.name.strip():
                raise EmployerValidationError("Employer name is required")

            if not data.email or not data.email.strip():
                raise EmployerValidationError("Employer email is required")

            # Check for duplicate email
            existing = self.db.query(Employer).filter(
                Employer.email == data.email
            ).first()
            if existing:
                raise EmployerValidationError(
                    f"Employer with email {data.email} already exists"
                )

            employer = Employer(
                name=data.name.strip(),
                email=data.email.strip(),
                phone=data.phone,
                website=data.website,
                industry=data.industry,
                size=data.size,
                location=data.location,
                description=data.description,
                is_active=True,
            )

            self.db.add(employer)
            self.db.commit()
            self.db.refresh(employer)

            logger.info(f"Created employer {employer.id}: {employer.name}")
            return employer

        except EmployerValidationError:
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating employer: {e}")
            raise EmployerValidationError("Employer with this data already exists") from e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating employer: {e}")
            raise

    def get_employer(self, employer_id: int) -> Employer:
        """Get an employer by ID.

        Args:
            employer_id: The employer's unique identifier.

        Returns:
            The Employer instance.

        Raises:
            EmployerNotFoundError: If employer is not found.
            SQLAlchemyError: If database operation fails.
        """
        try:
            employer = self.db.query(Employer).filter(
                Employer.id == employer_id
            ).first()

            if not employer:
                raise EmployerNotFoundError(employer_id)

            return employer

        except EmployerNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching employer {employer_id}: {e}")
            raise

    def list_employers(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None,
    ) -> Tuple[List[Employer], int]:
        """List employers with optional filtering and pagination.

        Args:
            filters: Optional filter criteria (e.g., {"industry": "tech", "is_active": True}).
            pagination: Optional pagination params (e.g., {"page": 1, "per_page": 20}).

        Returns:
            Tuple of (list of employers, total count).

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        try:
            query = self.db.query(Employer)

            # Apply filters
            if filters:
                if "name" in filters and filters["name"]:
                    query = query.filter(
                        Employer.name.ilike(f"%{filters['name']}%")
                    )
                if "industry" in filters and filters["industry"]:
                    query = query.filter(Employer.industry == filters["industry"])
                if "location" in filters and filters["location"]:
                    query = query.filter(
                        Employer.location.ilike(f"%{filters['location']}%")
                    )
                if "is_active" in filters and filters["is_active"] is not None:
                    query = query.filter(Employer.is_active == filters["is_active"])
                if "size" in filters and filters["size"]:
                    query = query.filter(Employer.size == filters["size"])

            # Get total count before pagination
            total = query.count()

            # Apply pagination
            if pagination:
                page = pagination.get("page", 1)
                per_page = pagination.get("per_page", 20)
                offset = (page - 1) * per_page
                query = query.offset(offset).limit(per_page)

            employers = query.all()
            return employers, total

        except SQLAlchemyError as e:
            logger.error(f"Database error listing employers: {e}")
            raise

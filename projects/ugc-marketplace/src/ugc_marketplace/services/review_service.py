"""Review service for UGC Marketplace."""

from __future__ import annotations

from typing import Any


class ReviewValidationError(Exception):
    """Raised when review data fails validation."""


class ReviewService:
    """Service for managing content reviews."""

    def __init__(self, db: Any) -> None:
        """Initialize with a database session/connection."""
        self._db = db

    def create_review(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new review with validation.

        Args:
            data: Dictionary containing review fields:
                - content_id (int/str): ID of the content being reviewed
                - user_id (int/str): ID of the user creating the review
                - rating (int/float): Rating value (1-5)
                - comment (str, optional): Review text

        Returns:
            The created review record as a dictionary.

        Raises:
            ReviewValidationError: If required fields are missing or invalid.
        """
        required_fields = ("content_id", "user_id", "rating")
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ReviewValidationError(
                f"Missing required fields: {', '.join(missing)}"
            )

        rating = data["rating"]
        if not isinstance(rating, (int, float)):
            raise ReviewValidationError("Rating must be a number")
        if not 1 <= rating <= 5:
            raise ReviewValidationError("Rating must be between 1 and 5")

        review = {
            "content_id": data["content_id"],
            "user_id": data["user_id"],
            "rating": rating,
            "comment": data.get("comment", ""),
        }

        return self._db.insert("reviews", review)

    def get_reviews(self, content_id: int | str) -> list[dict[str, Any]]:
        """Get all reviews for a specific content item.

        Args:
            content_id: ID of the content to fetch reviews for.

        Returns:
            List of review dictionaries.
        """
        return self._db.query(
            "SELECT * FROM reviews WHERE content_id = ? ORDER BY created_at DESC",
            (content_id,),
        )

    def get_average_rating(self, content_id: int | str) -> float | None:
        """Get the average rating for a specific content item.

        Args:
            content_id: ID of the content to calculate average rating for.

        Returns:
            Average rating as a float, or None if no reviews exist.
        """
        result = self._db.query_one(
            "SELECT AVG(rating) as avg_rating FROM reviews WHERE content_id = ?",
            (content_id,),
        )
        if result is None or result["avg_rating"] is None:
            return None
        return float(result["avg_rating"])

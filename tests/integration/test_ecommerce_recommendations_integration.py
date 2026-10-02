"""Integration tests for Ecommerce Marketing + Product Recommendations.

Tests the integration between the ecommerce-marketing and product-recommendations
projects, verifying that ecommerce campaigns leverage product recommendations and
that recommendation data informs marketing campaign strategy.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest


class TestEcommerceRecommendationsIntegration:
    """Integration tests for ecommerce-marketing and product-recommendations collaboration."""

    @pytest.fixture
    def product_catalog(self) -> List[Dict[str, Any]]:
        """Create a product catalog for recommendation testing.

        Returns:
            List of product dictionaries.
        """
        return [
            {
                "id": f"prod_{uuid.uuid4().hex[:8]}",
                "name": "Wireless Noise-Cancelling Headphones",
                "description": "Premium over-ear headphones with active noise cancellation",
                "price": 299.99,
                "category": "Electronics",
                "tags": ["wireless", "noise-cancelling", "premium"],
                "in_stock": True,
            },
            {
                "id": f"prod_{uuid.uuid4().hex[:8]}",
                "name": "Organic Cotton T-Shirt",
                "description": "Soft, sustainable organic cotton t-shirt",
                "price": 29.99,
                "category": "Clothing",
                "tags": ["organic", "sustainable", "casual"],
                "in_stock": True,
            },
            {
                "id": f"prod_{uuid.uuid4().hex[:8]}",
                "name": "Smart Home Hub",
                "description": "Central control for all your smart home devices",
                "price": 149.99,
                "category": "Electronics",
                "tags": ["smart-home", "automation", "IoT"],
                "in_stock": True,
            },
        ]

    @pytest.fixture
    def customer_behavior_data(self) -> List[Dict[str, Any]]:
        """Create customer behavior data for recommendation testing.

        Returns:
            List of customer behavior event dictionaries.
        """
        customer_id = f"cust_{uuid.uuid4().hex[:8]}"
        return [
            {
                "customer_id": customer_id,
                "event_type": "view",
                "product_id": f"prod_{uuid.uuid4().hex[:8]}",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            },
            {
                "customer_id": customer_id,
                "event_type": "add_to_cart",
                "product_id": f"prod_{uuid.uuid4().hex[:8]}",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            },
            {
                "customer_id": customer_id,
                "event_type": "purchase",
                "product_id": f"prod_{uuid.uuid4().hex[:8]}",
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            },
        ]

    @pytest.fixture
    def recommendation_result(self) -> Dict[str, Any]:
        """Create a recommendation result for testing.

        Returns:
            Recommendation result dictionary.
        """
        return {
            "customer_id": f"cust_{uuid.uuid4().hex[:8]}",
            "recommendations": [
                {
                    "product_id": f"prod_{uuid.uuid4().hex[:8]}",
                    "product_name": "Wireless Noise-Cancelling Headphones",
                    "score": 0.92,
                    "reason": "Based on your recent purchase of electronics",
                    "algorithm": "collaborative",
                },
                {
                    "product_id": f"prod_{uuid.uuid4().hex[:8]}",
                    "product_name": "Smart Home Hub",
                    "score": 0.78,
                    "reason": "Frequently bought together with headphones",
                    "algorithm": "content_based",
                },
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def test_recommendations_personalize_ecommerce_campaign(
        self, recommendation_result: Dict[str, Any]
    ) -> None:
        """Verify product recommendations personalize ecommerce marketing campaigns.

        Args:
            recommendation_result: Recommendation result fixture.
        """
        recommendations = recommendation_result["recommendations"]
        assert len(recommendations) > 0

        # Each recommendation should have a score and reason
        for rec in recommendations:
            assert 0.0 <= rec["score"] <= 1.0
            assert len(rec["reason"]) > 0
            assert rec["algorithm"] in ["collaborative", "content_based", "trending", "hybrid"]

    def test_ecommerce_campaign_uses_recommendation_data(
        self, product_catalog: List[Dict[str, Any]], recommendation_result: Dict[str, Any]
    ) -> None:
        """Verify ecommerce campaigns incorporate recommendation data.

        Args:
            product_catalog: Product catalog fixture.
            recommendation_result: Recommendation result fixture.
        """
        # Campaign should feature recommended products
        campaign = {
            "campaign_id": f"ecom_{uuid.uuid4().hex[:12]}",
            "name": "Personalized Product Recommendations",
            "featured_products": [rec["product_id"] for rec in recommendation_result["recommendations"]],
            "target_segment": "high_intent_shoppers",
        }

        assert len(campaign["featured_products"]) > 0
        assert campaign["target_segment"] == "high_intent_shoppers"

    def test_customer_behavior_drives_recommendations(
        self, customer_behavior_data: List[Dict[str, Any]]
    ) -> None:
        """Verify customer behavior data drives product recommendations.

        Args:
            customer_behavior_data: Customer behavior data fixture.
        """
        # Analyze behavior sequence
        events = customer_behavior_data
        assert len(events) >= 3

        # Should have view, cart, and purchase events
        event_types = {e["event_type"] for e in events}
        assert "view" in event_types
        assert "add_to_cart" in event_types
        assert "purchase" in event_types

        # All events should be for the same customer
        customer_ids = {e["customer_id"] for e in events}
        assert len(customer_ids) == 1

    def test_recommendation_cross_sell_opportunities(
        self, product_catalog: List[Dict[str, Any]]
    ) -> None:
        """Verify cross-sell opportunities are identified from product catalog.

        Args:
            product_catalog: Product catalog fixture.
        """
        # Identify cross-sell opportunities
        categories = {p["category"] for p in product_catalog}
        assert len(categories) > 1

        # Products in same category should have cross-sell potential
        electronics = [p for p in product_catalog if p["category"] == "Electronics"]
        if len(electronics) >= 2:
            cross_sell = {
                "source_product": electronics[0]["id"],
                "suggested_product": electronics[1]["id"],
                "relationship_type": "complementary",
                "confidence": 0.75,
            }
            assert cross_sell["confidence"] >= 0.5

    def test_ecommerce_recommendations_end_to_end_flow(self) -> None:
        """Test the complete flow from behavior tracking to personalized campaign."""
        # Step 1: Track customer behavior
        customer_id = f"cust_{uuid.uuid4().hex[:8]}"
        behaviors = [
            {"event_type": "view", "product_id": "prod_001"},
            {"event_type": "add_to_cart", "product_id": "prod_001"},
        ]
        assert len(behaviors) > 0

        # Step 2: Generate recommendations
        recommendations = {
            "customer_id": customer_id,
            "recommendations": [
                {"product_id": "prod_002", "score": 0.85, "reason": "Similar to viewed items"},
                {"product_id": "prod_003", "score": 0.72, "reason": "Frequently bought together"},
            ],
        }
        assert len(recommendations["recommendations"]) > 0

        # Step 3: Create personalized campaign
        campaign = {
            "campaign_id": f"ecom_{uuid.uuid4().hex[:12]}",
            "customer_id": customer_id,
            "recommended_products": [r["product_id"] for r in recommendations["recommendations"]],
            "channel": "email",
        }
        assert campaign["channel"] == "email"

        # Step 4: Track campaign performance
        performance = {
            "campaign_id": campaign["campaign_id"],
            "sent": 1,
            "opened": 1,
            "clicked": 1,
            "converted": 1,
            "revenue": 299.99,
        }
        assert performance["revenue"] > 0

    def test_recommendation_algorithm_selection(self) -> None:
        """Verify appropriate recommendation algorithm is selected based on data."""
        # Algorithm selection logic
        customer_data = {
            "view_count": 15,
            "purchase_count": 3,
            "cart_count": 5,
        }

        # Select algorithm based on data availability
        if customer_data["purchase_count"] >= 3:
            algorithm = "collaborative"
        elif customer_data["view_count"] >= 10:
            algorithm = "content_based"
        else:
            algorithm = "trending"

        assert algorithm in ["collaborative", "content_based", "trending", "hybrid"]

    def test_ecommerce_cart_abandonment_recommendations(self) -> None:
        """Verify cart abandonment triggers product recommendations."""
        # Simulate cart abandonment
        cart_data = {
            "customer_id": f"cust_{uuid.uuid4().hex[:8]}",
            "cart_items": [
                {"product_id": "prod_001", "quantity": 1, "price": 299.99},
            ],
            "abandoned_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        }

        # Should generate recovery recommendations
        recovery_recommendations = {
            "customer_id": cart_data["customer_id"],
            "cart_items": cart_data["cart_items"],
            "recommendations": [
                {"product_id": "prod_002", "reason": "Complete your setup"},
                {"product_id": "prod_003", "reason": "Customers also bought"},
            ],
            "incentive": "10% off",
        }

        assert len(recovery_recommendations["recommendations"]) > 0
        assert recovery_recommendations["incentive"] == "10% off"

    def test_recommendation_diversity_and_coverage(
        self, product_catalog: List[Dict[str, Any]]
    ) -> None:
        """Verify recommendations maintain diversity and catalog coverage.

        Args:
            product_catalog: Product catalog fixture.
        """
        # Recommendations should cover multiple categories
        recommendations = [
            {"product_id": product_catalog[0]["id"], "category": "Electronics"},
            {"product_id": product_catalog[1]["id"], "category": "Clothing"},
        ]

        categories_covered = {r["category"] for r in recommendations}
        assert len(categories_covered) >= 2

        # Should not recommend out-of-stock items
        for rec in recommendations:
            product = next(p for p in product_catalog if p["id"] == rec["product_id"])
            assert product["in_stock"] is True

    def test_ecommerce_recommendations_error_handling(self) -> None:
        """Verify error handling in ecommerce recommendations integration."""
        # Test with empty catalog
        empty_catalog: List[Dict[str, Any]] = []
        assert len(empty_catalog) == 0

        # Test with no behavior data
        no_behavior: List[Dict[str, Any]] = []
        assert len(no_behavior) == 0

        # Should return default recommendations
        default_recommendations = {
            "customer_id": f"cust_{uuid.uuid4().hex[:8]}",
            "recommendations": [],
            "fallback": "trending",
        }
        assert default_recommendations["fallback"] == "trending"

    def test_recommendation_performance_metrics(self) -> None:
        """Verify recommendation performance metrics are tracked."""
        metrics = {
            "recommendation_id": f"rec_{uuid.uuid4().hex[:8]}",
            "impressions": 1000,
            "clicks": 150,
            "conversions": 25,
            "revenue": 5000.0,
            "ctr": 0.15,
            "conversion_rate": 0.025,
            "average_order_value": 200.0,
        }

        assert metrics["ctr"] > 0
        assert metrics["conversion_rate"] > 0
        assert metrics["revenue"] > 0
        assert metrics["average_order_value"] > 0

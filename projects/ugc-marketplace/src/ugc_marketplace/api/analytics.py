"""
Analytics API endpoints for UGC Marketplace.

Provides marketplace-level and creator-level performance metrics.
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_metrics(
    period: Optional[str] = Query("30d", description="Time period: 7d, 30d, 90d, 12m")
):
    """
    Get marketplace-wide analytics dashboard metrics.
    """
    # Mock data — replace with real aggregation queries
    return {
        "period": period,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "overview": {
            "total_revenue": 284750.00,
            "total_orders": 3241,
            "total_creators": 187,
            "total_buyers": 1204,
            "average_order_value": 87.85,
            "conversion_rate": 3.42,
        },
        "revenue": {
            "current": 284750.00,
            "previous": 241300.00,
            "change_percent": 18.0,
            "breakdown": {
                "product_sales": 198500.00,
                "commission": 56950.00,
                "subscriptions": 29300.00,
            },
        },
        "orders": {
            "current": 3241,
            "previous": 2890,
            "change_percent": 12.1,
            "by_status": {
                "completed": 2890,
                "pending": 187,
                "cancelled": 98,
                "refunded": 66,
            },
        },
        "creators": {
            "total": 187,
            "active": 142,
            "new_this_period": 23,
            "change_percent": 14.3,
        },
        "buyers": {
            "total": 1204,
            "returning": 489,
            "new": 715,
            "change_percent": 9.8,
        },
        "top_categories": [
            {"name": "Digital Art", "revenue": 89400.00, "orders": 892},
            {"name": "Templates", "revenue": 67200.00, "orders": 1105},
            {"name": "Photography", "revenue": 45800.00, "orders": 567},
            {"name": "Video Clips", "revenue": 38900.00, "orders": 312},
            {"name": "Audio", "revenue": 24700.00, "orders": 198},
            {"name": "Writing", "revenue": 18750.00, "orders": 167},
        ],
        "daily_trend": [
            {"date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"), "revenue": 8200 + (i * 137) % 3400, "orders": 89 + (i * 11) % 42}
            for i in range(30, 0, -1)
        ],
    }


@router.get("/creators")
async def get_creator_metrics(
    period: Optional[str] = Query("30d", description="Time period: 7d, 30d, 90d, 12m"),
    sort_by: Optional[str] = Query("revenue", description="Sort field: revenue, orders, rating"),
    limit: Optional[int] = Query(20, ge=1, le=100),
):
    """
    Get creator performance metrics.
    """
    # Mock data — replace with real aggregation queries
    creators = [
        {
            "creator_id": "cr_001",
            "name": "Elena Vasquez",
            "avatar_url": "https://cdn.ugc-marketplace.io/avatars/cr_001.png",
            "total_revenue": 42300.00,
            "total_orders": 312,
            "average_rating": 4.9,
            "total_reviews": 287,
            "products_listed": 18,
            "conversion_rate": 4.8,
            "refund_rate": 1.2,
            "response_time_hours": 2.3,
            "joined_at": "2024-03-15T10:00:00Z",
            "top_category": "Digital Art",
            "revenue_change_percent": 22.5,
        },
        {
            "creator_id": "cr_002",
            "name": "Marcus Chen",
            "avatar_url": "https://cdn.ugc-marketplace.io/avatars/cr_002.png",
            "total_revenue": 38750.00,
            "total_orders": 428,
            "average_rating": 4.8,
            "total_reviews": 391,
            "products_listed": 24,
            "conversion_rate": 5.2,
            "refund_rate": 0.8,
            "response_time_hours": 1.7,
            "joined_at": "2023-11-02T10:00:00Z",
            "top_category": "Templates",
            "revenue_change_percent": 15.3,
        },
        {
            "creator_id": "cr_003",
            "name": "Aisha Patel",
            "avatar_url": "https://cdn.ugc-marketplace.io/avatars/cr_003.png",
            "total_revenue": 31200.00,
            "total_orders": 189,
            "average_rating": 4.9,
            "total_reviews": 172,
            "products_listed": 12,
            "conversion_rate": 3.9,
            "refund_rate": 1.5,
            "response_time_hours": 3.1,
            "joined_at": "2024-06-20T10:00:00Z",
            "top_category": "Photography",
            "revenue_change_percent": 31.7,
        },
        {
            "creator_id": "cr_004",
            "name": "James O'Brien",
            "avatar_url": "https://cdn.ugc-marketplace.io/avatars/cr_004.png",
            "total_revenue": 27800.00,
            "total_orders": 256,
            "average_rating": 4.7,
            "total_reviews": 231,
            "products_listed": 15,
            "conversion_rate": 4.1,
            "refund_rate": 2.1,
            "response_time_hours": 4.5,
            "joined_at": "2024-01-10T10:00:00Z",
            "top_category": "Video Clips",
            "revenue_change_percent": 8.9,
        },
        {
            "creator_id": "cr_005",
            "name": "Sofia Andersson",
            "avatar_url": "https://cdn.ugc-marketplace.io/avatars/cr_005.png",
            "total_revenue": 24500.00,
            "total_orders": 198,
            "average_rating": 4.8,
            "total_reviews": 184,
            "products_listed": 9,
            "conversion_rate": 3.6,
            "refund_rate": 1.0,
            "response_time_hours": 2.8,
            "joined_at": "2024-08-05T10:00:00Z",
            "top_category": "Audio",
            "revenue_change_percent": 19.2,
        },
        {
            "creator_id": "cr_006",
            "name": "David Kim",
            "avatar_url": "https://cdn.ugc-marketplace.io/avatars/cr_006.png",
            "total_revenue": 21300.00,
            "total_orders": 167,
            "average_rating": 4.6,
            "total_reviews": 149,
            "products_listed": 11,
            "conversion_rate": 3.2,
            "refund_rate": 1.8,
            "response_time_hours": 5.2,
            "joined_at": "2024-04-18T10:00:00Z",
            "top_category": "Writing",
            "revenue_change_percent": -3.4,
        },
        {
            "creator_id": "cr_007",
            "name": "Priya Sharma",
            "avatar_url": "https://cdn.ugc-marketplace.io/avatars/cr_007.png",
            "total_revenue": 18900.00,
            "total_orders": 145,
            "average_rating": 4.9,
            "total_reviews": 138,
            "products_listed": 8,
            "conversion_rate": 4.4,
            "refund_rate": 0.6,
            "response_time_hours": 1.9,
            "joined_at": "2024-09-12T10:00:00Z",
            "top_category": "Digital Art",
            "revenue_change_percent": 42.1,
        },
        {
            "creator_id": "cr_008",
            "name": "Lucas Silva",
            "avatar_url": "https://cdn.ugc-marketplace.io/avatars/cr_008.png",
            "total_revenue": 16700.00,
            "total_orders": 132,
            "average_rating": 4.7,
            "total_reviews": 121,
            "products_listed": 7,
            "conversion_rate": 3.8,
            "refund_rate": 1.3,
            "response_time_hours": 3.7,
            "joined_at": "2024-07-22T10:00:00Z",
            "top_category": "Templates",
            "revenue_change_percent": 11.6,
        },
    ]

    # Sort creators
    sort_key = sort_by if sort_by in ("revenue", "orders", "rating") else "revenue"
    sort_map = {"revenue": "total_revenue", "orders": "total_orders", "rating": "average_rating"}
    creators.sort(key=lambda c: c[sort_map[sort_key]], reverse=True)

    return {
        "period": period,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_creators": 187,
        "returned": min(limit, len(creators)),
        "sort_by": sort_key,
        "creators": creators[:limit],
    }

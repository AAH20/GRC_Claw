"""Analytics API endpoints for recruitment metrics and pipeline funnel."""

from fastapi import APIRouter
from typing import Any

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard() -> dict[str, Any]:
    """Return recruitment dashboard metrics."""
    return {
        "total_candidates": 1247,
        "active_jobs": 38,
        "open_positions": 156,
        "interviews_scheduled": 89,
        "offers_extended": 23,
        "offers_accepted": 18,
        "offers_declined": 5,
        "average_time_to_hire_days": 28.4,
        "average_time_to_fill_days": 34.1,
        "offer_acceptance_rate": 0.783,
        "candidate_satisfaction_score": 4.2,
        "hiring_manager_satisfaction": 4.0,
        "top_sources": [
            {"source": "LinkedIn", "count": 412, "conversion_rate": 0.18},
            {"source": "Indeed", "count": 298, "conversion_rate": 0.12},
            {"source": "Referral", "count": 234, "conversion_rate": 0.31},
            {"source": "Company Website", "count": 187, "conversion_rate": 0.09},
            {"source": "Glassdoor", "count": 116, "conversion_rate": 0.07},
        ],
        "hires_by_department": [
            {"department": "Engineering", "hires": 42, "open_roles": 18},
            {"department": "Product", "hires": 18, "open_roles": 7},
            {"department": "Design", "hires": 12, "open_roles": 5},
            {"department": "Marketing", "hires": 15, "open_roles": 6},
            {"department": "Sales", "hires": 22, "open_roles": 9},
            {"department": "Operations", "hires": 8, "open_roles": 3},
        ],
        "monthly_trend": [
            {"month": "2026-05", "applications": 312, "hires": 14},
            {"month": "2026-06", "applications": 358, "hires": 17},
            {"month": "2026-07", "applications": 289, "hires": 12},
            {"month": "2026-08", "applications": 401, "hires": 19},
            {"month": "2026-09", "applications": 376, "hires": 16},
            {"month": "2026-10", "applications": 245, "hires": 11},
        ],
    }


@router.get("/pipeline")
async def get_pipeline() -> dict[str, Any]:
    """Return pipeline funnel metrics."""
    return {
        "stages": [
            {
                "name": "Applied",
                "count": 1247,
                "conversion_rate": 1.0,
                "average_days_in_stage": 0.0,
            },
            {
                "name": "Screening",
                "count": 623,
                "conversion_rate": 0.50,
                "average_days_in_stage": 3.2,
            },
            {
                "name": "Phone Interview",
                "count": 312,
                "conversion_rate": 0.25,
                "average_days_in_stage": 5.1,
            },
            {
                "name": "Technical Interview",
                "count": 187,
                "conversion_rate": 0.15,
                "average_days_in_stage": 7.4,
            },
            {
                "name": "Onsite Interview",
                "count": 94,
                "conversion_rate": 0.075,
                "average_days_in_stage": 10.2,
            },
            {
                "name": "Offer",
                "count": 38,
                "conversion_rate": 0.030,
                "average_days_in_stage": 4.8,
            },
            {
                "name": "Hired",
                "count": 18,
                "conversion_rate": 0.014,
                "average_days_in_stage": 0.0,
            },
        ],
        "overall_conversion_rate": 0.014,
        "drop_off_points": [
            {"from_stage": "Applied", "to_stage": "Screening", "drop_off_count": 624, "drop_off_rate": 0.50},
            {"from_stage": "Screening", "to_stage": "Phone Interview", "drop_off_count": 311, "drop_off_rate": 0.50},
            {"from_stage": "Phone Interview", "to_stage": "Technical Interview", "drop_off_count": 125, "drop_off_rate": 0.40},
            {"from_stage": "Technical Interview", "to_stage": "Onsite Interview", "drop_off_count": 93, "drop_off_rate": 0.50},
            {"from_stage": "Onsite Interview", "to_stage": "Offer", "drop_off_count": 56, "drop_off_rate": 0.60},
            {"from_stage": "Offer", "to_stage": "Hired", "drop_off_count": 20, "drop_off_rate": 0.53},
        ],
        "pipeline_by_job_family": [
            {"job_family": "Engineering", "in_pipeline": 342, "hired": 12, "conversion_rate": 0.035},
            {"job_family": "Product", "in_pipeline": 189, "hired": 5, "conversion_rate": 0.026},
            {"job_family": "Design", "in_pipeline": 98, "hired": 3, "conversion_rate": 0.031},
            {"job_family": "Marketing", "in_pipeline": 156, "hired": 4, "conversion_rate": 0.026},
            {"job_family": "Sales", "in_pipeline": 212, "hired": 8, "conversion_rate": 0.038},
            {"job_family": "Operations", "in_pipeline": 87, "hired": 2, "conversion_rate": 0.023},
        ],
    }

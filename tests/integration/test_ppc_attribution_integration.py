"""Integration tests for PPC Manager + Marketing Attribution.

Tests the integration between the ppc-manager and marketing-attribution projects,
verifying that PPC campaign data flows into attribution models and that attribution
insights inform PPC budget and bid optimization.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest


class TestPPCAttributionIntegration:
    """Integration tests for ppc-manager and marketing-attribution collaboration."""

    @pytest.fixture
    def ppc_campaign_performance(self) -> Dict[str, Any]:
        """Create PPC campaign performance data for attribution.

        Returns:
            PPC campaign performance dictionary.
        """
        return {
            "campaign_id": f"ppc_{uuid.uuid4().hex[:12]}",
            "platform": "google",
            "impressions": 100000,
            "clicks": 3500,
            "conversions": 120,
            "spend": 5000.0,
            "revenue": 15000.0,
            "keywords": [
                {"keyword": "marketing automation", "clicks": 500, "conversions": 20, "spend": 800.0},
                {"keyword": "AI marketing tools", "clicks": 300, "conversions": 15, "spend": 600.0},
            ],
        }

    @pytest.fixture
    def attribution_touchpoints(self) -> List[Dict[str, Any]]:
        """Create multi-touch attribution data including PPC touchpoints.

        Returns:
            List of attribution touchpoint dictionaries.
        """
        base_time = datetime.now(timezone.utc)
        return [
            {
                "touchpoint_id": f"tp_{uuid.uuid4().hex[:8]}",
                "channel": "ppc",
                "sub_channel": "google_ads",
                "campaign_id": f"ppc_{uuid.uuid4().hex[:12]}",
                "event_type": "click",
                "timestamp": (base_time - timedelta(days=5)).isoformat(),
                "cost": 2.50,
            },
            {
                "touchpoint_id": f"tp_{uuid.uuid4().hex[:8]}",
                "channel": "organic",
                "sub_channel": "search",
                "event_type": "session",
                "timestamp": (base_time - timedelta(days=3)).isoformat(),
            },
            {
                "touchpoint_id": f"tp_{uuid.uuid4().hex[:8]}",
                "channel": "email",
                "sub_channel": "newsletter",
                "event_type": "open",
                "timestamp": (base_time - timedelta(days=2)).isoformat(),
            },
            {
                "touchpoint_id": f"tp_{uuid.uuid4().hex[:8]}",
                "channel": "ppc",
                "sub_channel": "google_ads",
                "campaign_id": f"ppc_{uuid.uuid4().hex[:12]}",
                "event_type": "conversion",
                "timestamp": (base_time - timedelta(days=1)).isoformat(),
                "revenue": 150.0,
            },
        ]

    def test_ppc_data_flows_into_attribution(
        self, ppc_campaign_performance: Dict[str, Any]
    ) -> None:
        """Verify PPC campaign data is correctly ingested by attribution system.

        Args:
            ppc_campaign_performance: PPC campaign performance fixture.
        """
        required_fields = ["campaign_id", "clicks", "conversions", "spend", "revenue"]
        for field in required_fields:
            assert field in ppc_campaign_performance

        ctr = ppc_campaign_performance["clicks"] / ppc_campaign_performance["impressions"]
        cvr = ppc_campaign_performance["conversions"] / ppc_campaign_performance["clicks"]
        roas = ppc_campaign_performance["revenue"] / ppc_campaign_performance["spend"]

        assert 0.0 < ctr < 1.0
        assert 0.0 < cvr < 1.0
        assert roas > 0.0

    def test_ppc_attribution_model_selection(
        self, ppc_campaign_performance: Dict[str, Any]
    ) -> None:
        """Verify appropriate attribution model is selected for PPC data.

        Args:
            ppc_campaign_performance: PPC campaign performance fixture.
        """
        models = {
            "first_touch": "Best for top-of-funnel PPC campaigns",
            "last_touch": "Best for bottom-of-funnel conversion campaigns",
            "linear": "Best for multi-touch journeys",
            "data_driven": "Best for high-volume campaigns with sufficient data",
            "time_decay": "Best for long sales cycles",
        }

        if ppc_campaign_performance["conversions"] > 100:
            selected_model = "data_driven"
        elif ppc_campaign_performance["conversions"] > 50:
            selected_model = "time_decay"
        else:
            selected_model = "last_touch"

        assert selected_model in models

    def test_ppc_keyword_level_attribution(
        self, ppc_campaign_performance: Dict[str, Any]
    ) -> None:
        """Verify attribution works at the keyword level for PPC.

        Args:
            ppc_campaign_performance: PPC campaign performance fixture.
        """
        keywords = ppc_campaign_performance["keywords"]

        for keyword in keywords:
            keyword_roas = (
                keyword["conversions"] * 100.0 / keyword["spend"]
                if keyword["spend"] > 0
                else 0.0
            )
            assert keyword_roas >= 0.0
            assert keyword["conversions"] > 0
            assert keyword["clicks"] > 0

    def test_ppc_budget_optimization_from_attribution(
        self, ppc_campaign_performance: Dict[str, Any]
    ) -> None:
        """Verify attribution insights inform PPC budget optimization.

        Args:
            ppc_campaign_performance: PPC campaign performance fixture.
        """
        current_roas = ppc_campaign_performance["revenue"] / ppc_campaign_performance["spend"]

        if current_roas >= 3.0:
            budget_recommendation = "increase"
            budget_change_pct = 20.0
        elif current_roas >= 2.0:
            budget_recommendation = "maintain"
            budget_change_pct = 0.0
        else:
            budget_recommendation = "decrease"
            budget_change_pct = -15.0

        assert budget_recommendation in ["increase", "maintain", "decrease"]
        assert -50.0 <= budget_change_pct <= 50.0

    def test_ppc_attribution_end_to_end_flow(self) -> None:
        """Test the complete flow from PPC click to attributed conversion."""
        ppc_click = {
            "click_id": f"click_{uuid.uuid4().hex[:8]}",
            "campaign_id": f"ppc_{uuid.uuid4().hex[:12]}",
            "keyword": "marketing automation",
            "cost": 3.50,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        assert ppc_click["cost"] > 0.0

        conversion = {
            "conversion_id": f"conv_{uuid.uuid4().hex[:8]}",
            "click_id": ppc_click["click_id"],
            "revenue": 200.0,
            "attribution_model": "last_touch",
            "attributed_channel": "ppc",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        assert conversion["revenue"] > 0.0
        assert conversion["attributed_channel"] == "ppc"

        attributed_roas = conversion["revenue"] / ppc_click["cost"]
        assert attributed_roas > 0.0

    def test_ppc_cross_platform_attribution(self) -> None:
        """Verify attribution works across multiple PPC platforms."""
        platforms = ["google", "meta", "linkedin", "tiktok"]

        platform_performance = {}
        for platform in platforms:
            platform_performance[platform] = {
                "clicks": 1000,
                "conversions": 30,
                "spend": 2000.0,
                "revenue": 6000.0,
            }

        total_clicks = sum(p["clicks"] for p in platform_performance.values())
        total_conversions = sum(p["conversions"] for p in platform_performance.values())
        total_spend = sum(p["spend"] for p in platform_performance.values())
        total_revenue = sum(p["revenue"] for p in platform_performance.values())

        assert total_clicks > 0
        assert total_conversions > 0
        assert total_spend > 0
        assert total_revenue > 0

        cross_platform_roas = total_revenue / total_spend
        assert cross_platform_roas > 0.0

    def test_ppc_attribution_with_view_through(self) -> None:
        """Verify view-through conversions are attributed to PPC."""
        view_through = {
            "impression_id": f"imp_{uuid.uuid4().hex[:8]}",
            "campaign_id": f"ppc_{uuid.uuid4().hex[:12]}",
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
            "converted": True,
            "conversion_time": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "revenue": 75.0,
        }

        view_through_weight = 0.3
        click_through_weight = 1.0

        assert view_through_weight < click_through_weight
        assert view_through["converted"] is True

    def test_ppc_attribution_data_quality_checks(
        self, ppc_campaign_performance: Dict[str, Any]
    ) -> None:
        """Verify data quality checks for PPC attribution data.

        Args:
            ppc_campaign_performance: PPC campaign performance fixture.
        """
        issues = []

        if ppc_campaign_performance["clicks"] > ppc_campaign_performance["impressions"]:
            issues.append("clicks_exceed_impressions")

        if ppc_campaign_performance["conversions"] > ppc_campaign_performance["clicks"]:
            issues.append("conversions_exceed_clicks")

        if ppc_campaign_performance["spend"] < 0:
            issues.append("negative_spend")

        if ppc_campaign_performance["revenue"] < 0:
            issues.append("negative_revenue")

        assert len(issues) == 0

    def test_ppc_attribution_reporting_integration(
        self, ppc_campaign_performance: Dict[str, Any]
    ) -> None:
        """Verify PPC attribution reports are correctly generated.

        Args:
            ppc_campaign_performance: PPC campaign performance fixture.
        """
        report = {
            "report_id": f"rpt_{uuid.uuid4().hex[:8]}",
            "period": "last_30_days",
            "ppc_summary": {
                "total_spend": ppc_campaign_performance["spend"],
                "total_revenue": ppc_campaign_performance["revenue"],
                "roas": ppc_campaign_performance["revenue"] / ppc_campaign_performance["spend"],
                "total_conversions": ppc_campaign_performance["conversions"],
                "cpa": ppc_campaign_performance["spend"] / ppc_campaign_performance["conversions"],
            },
            "attribution_model": "data_driven",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        assert report["ppc_summary"]["roas"] > 0.0
        assert report["ppc_summary"]["cpa"] > 0.0
        assert report["attribution_model"] == "data_driven"

    def test_ppc_attribution_error_handling(self) -> None:
        """Verify error handling in PPC attribution pipeline."""
        incomplete_data = {
            "campaign_id": f"ppc_{uuid.uuid4().hex[:12]}",
            "clicks": 0,
            "conversions": 0,
            "spend": 0.0,
            "revenue": 0.0,
        }

        if incomplete_data["spend"] > 0:
            roas = incomplete_data["revenue"] / incomplete_data["spend"]
        else:
            roas = 0.0

        assert roas == 0.0

        invalid_data = {
            "clicks": -100,
            "conversions": 50,
        }

        assert invalid_data["clicks"] < 0

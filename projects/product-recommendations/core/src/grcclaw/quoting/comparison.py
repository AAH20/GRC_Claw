"""
Quote Comparison Tool — compare multiple quotes side by side.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from .models import Quote, OrganizationProfile, DeploymentModel, SupportLevel, PricingTier
from .quote_calculator import QuoteCalculator


@dataclass
class ComparisonRow:
    """Single row in a comparison table."""

    label: str
    values: list[str] = field(default_factory=list)
    highlight: bool = False  # highlight this row (e.g., total cost)


@dataclass
class ComparisonResult:
    """Complete comparison result."""

    quotes: list[Quote] = field(default_factory=list)
    rows: list[ComparisonRow] = field(default_factory=list)
    winner_index: int = -1  # index of best value quote (-1 if N/A)
    savings_vs_highest: float = 0.0


class QuoteComparison:
    """
    Compare multiple quotes side by side.
    
    Useful for comparing different deployment models, support levels,
    or pricing tiers for the same organization.
    """

    def __init__(self, quotes: Optional[list[Quote]] = None):
        self.quotes = quotes or []

    def add_quote(self, quote: Quote):
        """Add a quote to the comparison."""
        self.quotes.append(quote)

    def compare(self) -> ComparisonResult:
        """Generate side-by-side comparison."""
        if len(self.quotes) < 2:
            raise ValueError("Need at least 2 quotes to compare")

        result = ComparisonResult(quotes=self.quotes)

        # Organization info
        result.rows.append(ComparisonRow(
            label="Organization",
            values=[q.organization.name for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Industry",
            values=[q.organization.industry.title() for q in self.quotes],
        ))

        # Scale
        result.rows.append(ComparisonRow(
            label="Agents",
            values=[f"{q.organization.agents:,}" for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Models",
            values=[f"{q.organization.models:,}" for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Policies",
            values=[f"{q.organization.policies:,}" for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Evidence (GB)",
            values=[f"{q.organization.evidence_volume_gb:,.0f}" for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Frameworks",
            values=[str(len(q.organization.frameworks)) for q in self.quotes],
        ))

        # Configuration
        result.rows.append(ComparisonRow(
            label="Deployment",
            values=[q.organization.deployment_model.value.replace("_", " ").title() for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Support",
            values=[q.organization.support_level.value.title() for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Pricing Tier",
            values=[q.organization.pricing_tier.value.title() for q in self.quotes],
        ))

        # Pricing
        result.rows.append(ComparisonRow(
            label="Subtotal",
            values=[f"${q.subtotal:,.0f}" for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Volume Discount",
            values=[f"{q.volume_discount_pct:.0f}%" for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Support Multiplier",
            values=[f"{q.support_multiplier:.2f}x" for q in self.quotes],
        ))
        result.rows.append(ComparisonRow(
            label="Deployment Multiplier",
            values=[f"{q.deployment_multiplier:.2f}x" for q in self.quotes],
        ))

        # Totals
        result.rows.append(ComparisonRow(
            label="Annual Cost",
            values=[f"${q.annual_cost:,.0f}" for q in self.quotes],
            highlight=True,
        ))
        result.rows.append(ComparisonRow(
            label="Monthly Cost",
            values=[f"${q.monthly_cost:,.0f}" for q in self.quotes],
            highlight=True,
        ))

        # Per-unit costs
        for q in self.quotes:
            if q.organization.agents > 0:
                pass  # computed below

        per_agent = [f"${q.annual_cost / q.organization.agents:,.0f}" if q.organization.agents > 0 else "N/A" for q in self.quotes]
        result.rows.append(ComparisonRow(
            label="Cost per Agent",
            values=per_agent,
        ))

        per_policy = [f"${q.annual_cost / q.organization.policies:,.0f}" if q.organization.policies > 0 else "N/A" for q in self.quotes]
        result.rows.append(ComparisonRow(
            label="Cost per Policy",
            values=per_policy,
        ))

        # Find winner (lowest annual cost)
        costs = [q.annual_cost for q in self.quotes]
        result.winner_index = costs.index(min(costs))
        result.savings_vs_highest = max(costs) - min(costs)

        return result

    def to_html(self) -> str:
        """Generate HTML comparison table."""
        result = self.compare()

        header_cells = "".join(
            f'<th>{q.organization.name}<br><small>{q.organization.deployment_model.value.replace("_", " ").title()} / {q.organization.support_level.value.title()}</small></th>'
            for q in self.quotes
        )

        body_rows = ""
        for row in result.rows:
            cells = "".join(f"<td>{v}</td>" for v in row.values)
            highlight = ' class="highlight"' if row.highlight else ""
            winner_marker = ""
            if row.label in ("Annual Cost", "Monthly Cost"):
                for i, v in enumerate(row.values):
                    if i == result.winner_index:
                        row.values[i] = f"⭐ {v}"
                cells = "".join(f"<td>{v}</td>" for v in row.values)
            body_rows += f"<tr{highlight}><th>{row.label}</th>{cells}</tr>"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GRC_Claw Quote Comparison</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1a1a2e; background: #f8f9fa; padding: 2rem; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 2rem; }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .content {{ padding: 2rem; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f8f9fa; font-weight: 600; font-size: 0.85rem; }}
        td {{ font-variant-numeric: tabular-nums; }}
        tr.highlight {{ background: #e7f3ff; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        tr.highlight:hover {{ background: #d4e9ff; }}
        .savings {{ margin-top: 1.5rem; padding: 1rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745; }}
        .savings strong {{ color: #155724; }}
        .footer {{ padding: 1rem 2rem; background: #f8f9fa; text-align: center; font-size: 0.8rem; color: #6c757d; }}
        @media print {{ body {{ background: white; padding: 0; }} .container {{ box-shadow: none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GRC_Claw Quote Comparison</h1>
            <p>Side-by-side comparison of {len(self.quotes)} quotes</p>
        </div>
        <div class="content">
            <table>
                <thead>
                    <tr>
                        <th>Attribute</th>
                        {header_cells}
                    </tr>
                </thead>
                <tbody>
                    {body_rows}
                </tbody>
            </table>
            <div class="savings">
                <strong>💡 Savings Opportunity:</strong>
                Choosing the most cost-effective option saves
                <strong>${result.savings_vs_highest:,.0f}/year</strong>
                compared to the most expensive option.
            </div>
        </div>
        <div class="footer">
            <p>GRC_Claw — Governance, Risk & Compliance AI Agents</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def to_text(self) -> str:
        """Generate plain text comparison."""
        result = self.compare()

        # Calculate column widths
        label_width = max(len(row.label) for row in result.rows) + 2
        value_widths = [0] * len(self.quotes)
        for row in result.rows:
            for i, v in enumerate(row.values):
                value_widths[i] = max(value_widths[i], len(v))

        lines = [
            "════════════════════════════════════════════════════════════",
            "              GRC_Claw QUOTE COMPARISON",
            "════════════════════════════════════════════════════════════",
            "",
        ]

        # Header
        header = f"{'Attribute':<{label_width}}"
        for i, q in enumerate(self.quotes):
            header += f" │ {q.organization.name[:value_widths[i]]:>{value_widths[i]}}"
        lines.append(header)
        lines.append("─" * len(header))

        # Rows
        for row in result.rows:
            line = f"{row.label:<{label_width}}"
            for i, v in enumerate(row.values):
                line += f" │ {v:>{value_widths[i]}}"
            if row.highlight:
                line += " ◀"
            lines.append(line)

        lines.extend([
            "",
            f"💡 Savings vs highest: ${result.savings_vs_highest:,.0f}/year",
            "════════════════════════════════════════════════════════════",
        ])

        return "\n".join(lines)

    def to_json(self) -> str:
        """Generate JSON comparison."""
        import json
        result = self.compare()
        data = {
            "quotes": [
                {
                    "quote_id": q.quote_id,
                    "organization": q.organization.name,
                    "deployment": q.organization.deployment_model.value,
                    "support": q.organization.support_level.value,
                    "tier": q.organization.pricing_tier.value,
                    "annual_cost": q.annual_cost,
                    "monthly_cost": q.monthly_cost,
                    "cost_per_agent": q.annual_cost / q.organization.agents if q.organization.agents > 0 else 0,
                }
                for q in self.quotes
            ],
            "comparison": {
                row.label: row.values for row in result.rows
            },
            "winner_index": result.winner_index,
            "savings_vs_highest": result.savings_vs_highest,
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def compare_deployment_models(
        profile: OrganizationProfile,
        calculator: Optional[QuoteCalculator] = None,
    ) -> "QuoteComparison":
        """Compare all deployment models for a given profile."""
        calc = calculator or QuoteCalculator()
        comparison = QuoteComparison()

        for model in DeploymentModel:
            p = OrganizationProfile(
                name=profile.name,
                industry=profile.industry,
                agents=profile.agents,
                models=profile.models,
                policies=profile.policies,
                evidence_volume_gb=profile.evidence_volume_gb,
                frameworks=profile.frameworks,
                deployment_model=model,
                support_level=profile.support_level,
                pricing_tier=profile.pricing_tier,
            )
            quote = calc.calculate(p)
            comparison.add_quote(quote)

        return comparison

    @staticmethod
    def compare_support_levels(
        profile: OrganizationProfile,
        calculator: Optional[QuoteCalculator] = None,
    ) -> "QuoteComparison":
        """Compare all support levels for a given profile."""
        calc = calculator or QuoteCalculator()
        comparison = QuoteComparison()

        for level in SupportLevel:
            p = OrganizationProfile(
                name=profile.name,
                industry=profile.industry,
                agents=profile.agents,
                models=profile.models,
                policies=profile.policies,
                evidence_volume_gb=profile.evidence_volume_gb,
                frameworks=profile.frameworks,
                deployment_model=profile.deployment_model,
                support_level=level,
                pricing_tier=profile.pricing_tier,
            )
            quote = calc.calculate(p)
            comparison.add_quote(quote)

        return comparison

    @staticmethod
    def compare_pricing_tiers(
        profile: OrganizationProfile,
        calculator: Optional[QuoteCalculator] = None,
    ) -> "QuoteComparison":
        """Compare all pricing tiers for a given profile."""
        calc = calculator or QuoteCalculator()
        comparison = QuoteComparison()

        for tier in PricingTier:
            p = OrganizationProfile(
                name=profile.name,
                industry=profile.industry,
                agents=profile.agents,
                models=profile.models,
                policies=profile.policies,
                evidence_volume_gb=profile.evidence_volume_gb,
                frameworks=profile.frameworks,
                deployment_model=profile.deployment_model,
                support_level=profile.support_level,
                pricing_tier=tier,
            )
            quote = calc.calculate(p)
            comparison.add_quote(quote)

        return comparison

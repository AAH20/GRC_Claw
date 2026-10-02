"""
Quote Generator — outputs quotes in PDF, HTML, and JSON formats.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union
from .models import Quote, OrganizationProfile
from .pricing_engine import PricingEngine


class QuoteGenerator:
    """
    Generate quotes in multiple output formats:
    - JSON (machine-readable)
    - HTML (web-viewable, printable)
    - Markdown (documentation-friendly)
    - Plain text (email-friendly)
    """

    def __init__(self, quote: Quote):
        self.quote = quote

    def to_json(self, indent: int = 2) -> str:
        """Generate JSON representation of the quote."""
        data = {
            "quote_id": self.quote.quote_id,
            "created_at": self.quote.created_at,
            "valid_until": self.quote.valid_until,
            "organization": {
                "name": self.quote.organization.name,
                "industry": self.quote.organization.industry,
                "agents": self.quote.organization.agents,
                "models": self.quote.organization.models,
                "policies": self.quote.organization.policies,
                "evidence_volume_gb": self.quote.organization.evidence_volume_gb,
                "frameworks": self.quote.organization.frameworks,
                "deployment_model": self.quote.organization.deployment_model.value,
                "support_level": self.quote.organization.support_level.value,
                "pricing_tier": self.quote.organization.pricing_tier.value,
            },
            "line_items": [
                {
                    "description": li.description,
                    "quantity": li.quantity,
                    "unit_price": li.unit_price,
                    "unit": li.unit,
                    "category": li.category,
                    "subtotal": li.subtotal,
                    "discount_pct": li.discount_pct,
                    "discount_amount": li.discount_amount,
                    "total": li.total,
                }
                for li in self.quote.line_items
            ],
            "summary": {
                "subtotal": self.quote.subtotal,
                "volume_discount_pct": self.quote.volume_discount_pct,
                "volume_discount_amount": self.quote.volume_discount_amount,
                "support_multiplier": self.quote.support_multiplier,
                "deployment_multiplier": self.quote.deployment_multiplier,
                "total_before_tax": self.quote.total_before_tax,
                "tax_rate": self.quote.tax_rate,
                "tax_amount": self.quote.tax_amount,
                "total": self.quote.total,
                "annual_cost": self.quote.annual_cost,
                "monthly_cost": self.quote.monthly_cost,
            },
            "assumptions": self.quote.assumptions,
            "notes": self.quote.notes,
        }
        return json.dumps(data, indent=indent)

    def to_html(self) -> str:
        """Generate a professional HTML quote document."""
        q = self.quote
        org = q.organization

        line_items_html = ""
        for li in q.line_items:
            line_items_html += f"""
            <tr>
                <td>{li.description}</td>
                <td class="num">{li.quantity:,.0f}</td>
                <td class="num">${li.unit_price:,.2f}</td>
                <td class="num">${li.subtotal:,.2f}</td>
            </tr>"""

        frameworks_str = ", ".join(org.frameworks) if org.frameworks else "None"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GRC_Claw Quote — {org.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1a1a2e; background: #f8f9fa; padding: 2rem; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 2rem; }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .header .subtitle {{ opacity: 0.8; font-size: 0.9rem; }}
        .content {{ padding: 2rem; }}
        .org-info {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; }}
        .org-info dt {{ font-weight: 600; color: #495057; font-size: 0.85rem; }}
        .org-info dd {{ margin: 0; color: #1a1a2e; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; }}
        th {{ background: #1a1a2e; color: white; padding: 0.75rem; text-align: left; font-size: 0.85rem; }}
        td {{ padding: 0.75rem; border-bottom: 1px solid #dee2e6; }}
        td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
        tr:hover {{ background: #f8f9fa; }}
        .totals {{ margin-top: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; }}
        .totals .row {{ display: flex; justify-content: space-between; padding: 0.25rem 0; }}
        .totals .row.grand {{ font-size: 1.2rem; font-weight: 700; border-top: 2px solid #1a1a2e; margin-top: 0.5rem; padding-top: 0.75rem; }}
        .assumptions {{ margin-top: 1.5rem; padding: 1rem; background: #e7f3ff; border-radius: 8px; border-left: 4px solid #0066cc; }}
        .assumptions h3 {{ margin-bottom: 0.5rem; color: #0066cc; }}
        .assumptions ul {{ margin-left: 1.25rem; }}
        .footer {{ padding: 1rem 2rem; background: #f8f9fa; text-align: center; font-size: 0.8rem; color: #6c757d; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }}
        .badge-primary {{ background: #0066cc; color: white; }}
        .badge-success {{ background: #28a745; color: white; }}
        @media print {{ body {{ background: white; padding: 0; }} .container {{ box-shadow: none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GRC_Claw</h1>
            <p class="subtitle">Custom Quote for {org.name}</p>
            <p class="subtitle">Quote ID: {q.quote_id} | Generated: {q.created_at[:10]}</p>
        </div>
        <div class="content">
            <dl class="org-info">
                <div><dt>Industry</dt><dd>{org.industry.title()}</dd></div>
                <div><dt>Deployment</dt><dd>{org.deployment_model.value.replace('_', ' ').title()}</dd></div>
                <div><dt>Support Level</dt><dd>{org.support_level.value.title()}</dd></div>
                <div><dt>Pricing Tier</dt><dd>{org.pricing_tier.value.title()}</dd></div>
                <div><dt>Agents</dt><dd>{org.agents:,}</dd></div>
                <div><dt>Models</dt><dd>{org.models:,}</dd></div>
                <div><dt>Policies</dt><dd>{org.policies:,}</dd></div>
                <div><dt>Evidence Volume</dt><dd>{org.evidence_volume_gb:,.0f} GB</dd></div>
                <div><dt>Frameworks</dt><dd>{frameworks_str}</dd></div>
            </dl>

            <h2>Line Items</h2>
            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th class="num">Qty</th>
                        <th class="num">Unit Price</th>
                        <th class="num">Total</th>
                    </tr>
                </thead>
                <tbody>{line_items_html}
                </tbody>
            </table>

            <div class="totals">
                <div class="row"><span>Subtotal</span><span>${q.subtotal:,.2f}</span></div>
                <div class="row"><span>Volume Discount ({q.volume_discount_pct:.0f}%)</span><span>-${q.volume_discount_amount:,.2f}</span></div>
                <div class="row"><span>Support Multiplier</span><span>{q.support_multiplier:.2f}x</span></div>
                <div class="row"><span>Deployment Multiplier</span><span>{q.deployment_multiplier:.2f}x</span></div>
                <div class="row"><span>Tax ({q.tax_rate:.0f}%)</span><span>${q.tax_amount:,.2f}</span></div>
                <div class="row grand"><span>Total Annual Cost</span><span>${q.total:,.2f}</span></div>
                <div class="row"><span>Monthly Equivalent</span><span>${q.monthly_cost:,.2f}</span></div>
            </div>

            <div class="assumptions">
                <h3>Assumptions</h3>
                <ul>
                    {''.join(f'<li>{a}</li>' for a in q.assumptions)}
                </ul>
            </div>
        </div>
        <div class="footer">
            <p>GRC_Claw — Governance, Risk & Compliance AI Agents</p>
            <p>This quote is valid for 30 days from the date of generation.</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def to_markdown(self) -> str:
        """Generate Markdown representation of the quote."""
        q = self.quote
        org = q.organization

        lines = [
            f"# GRC_Claw Quote — {org.name}",
            "",
            f"**Quote ID:** {q.quote_id}  ",
            f"**Generated:** {q.created_at[:10]}  ",
            f"**Valid Until:** {q.valid_until or '30 days from generation'}",
            "",
            "## Organization Profile",
            "",
            f"| Attribute | Value |",
            f"|-----------|-------|",
            f"| Industry | {org.industry.title()} |",
            f"| Deployment | {org.deployment_model.value.replace('_', ' ').title()} |",
            f"| Support Level | {org.support_level.value.title()} |",
            f"| Pricing Tier | {org.pricing_tier.value.title()} |",
            f"| Agents | {org.agents:,} |",
            f"| Models | {org.models:,} |",
            f"| Policies | {org.policies:,} |",
            f"| Evidence Volume | {org.evidence_volume_gb:,.0f} GB |",
            f"| Frameworks | {', '.join(org.frameworks) if org.frameworks else 'None'} |",
            "",
            "## Line Items",
            "",
            "| Description | Qty | Unit Price | Total |",
            "|-------------|-----|------------|-------|",
        ]

        for li in q.line_items:
            lines.append(f"| {li.description} | {li.quantity:,.0f} | ${li.unit_price:,.2f} | ${li.total:,.2f} |")

        lines.extend([
            "",
            "## Summary",
            "",
            f"| Item | Amount |",
            f"|------|--------|",
            f"| Subtotal | ${q.subtotal:,.2f} |",
            f"| Volume Discount ({q.volume_discount_pct:.0f}%) | -${q.volume_discount_amount:,.2f} |",
            f"| Support Multiplier | {q.support_multiplier:.2f}x |",
            f"| Deployment Multiplier | {q.deployment_multiplier:.2f}x |",
            f"| Tax ({q.tax_rate:.0f}%) | ${q.tax_amount:,.2f} |",
            f"| **Total Annual Cost** | **${q.total:,.2f}** |",
            f"| Monthly Equivalent | ${q.monthly_cost:,.2f} |",
            "",
            "## Assumptions",
            "",
        ])

        for a in q.assumptions:
            lines.append(f"- {a}")

        lines.extend([
            "",
            "---",
            "*GRC_Claw — Governance, Risk & Compliance AI Agents*",
        ])

        return "\n".join(lines)

    def to_text(self) -> str:
        """Generate plain text representation of the quote."""
        q = self.quote
        org = q.organization

        lines = [
            "════════════════════════════════════════════════════════════",
            "                    GRC_Claw QUOTE",
            "════════════════════════════════════════════════════════════",
            "",
            f"  Quote ID:    {q.quote_id}",
            f"  Generated:   {q.created_at[:10]}",
            f"  Valid Until: {q.valid_until or '30 days from generation'}",
            "",
            "────────────────────────────────────────────────────────────",
            "  ORGANIZATION",
            "────────────────────────────────────────────────────────────",
            f"  Name:        {org.name}",
            f"  Industry:    {org.industry.title()}",
            f"  Deployment:  {org.deployment_model.value.replace('_', ' ').title()}",
            f"  Support:     {org.support_level.value.title()}",
            f"  Tier:        {org.pricing_tier.value.title()}",
            "",
            "────────────────────────────────────────────────────────────",
            "  LINE ITEMS",
            "────────────────────────────────────────────────────────────",
        ]

        for li in q.line_items:
            lines.append(f"  {li.description}")
            lines.append(f"    {li.quantity:,.0f} x ${li.unit_price:,.2f} = ${li.total:,.2f}")

        lines.extend([
            "",
            "────────────────────────────────────────────────────────────",
            "  SUMMARY",
            "────────────────────────────────────────────────────────────",
            f"  Subtotal:            ${q.subtotal:>12,.2f}",
            f"  Volume Discount:     -${q.volume_discount_amount:>11,.2f} ({q.volume_discount_pct:.0f}%)",
            f"  Support Multiplier:  {q.support_multiplier:>12.2f}x",
            f"  Deployment Mult.:    {q.deployment_multiplier:>12.2f}x",
            f"  Tax ({q.tax_rate:.0f}%):          ${q.tax_amount:>12,.2f}",
            "                              ────────────",
            f"  TOTAL ANNUAL:        ${q.total:>12,.2f}",
            f"  Monthly:             ${q.monthly_cost:>12,.2f}",
            "",
            "────────────────────────────────────────────────────────────",
            "  ASSUMPTIONS",
            "────────────────────────────────────────────────────────────",
        ])

        for a in q.assumptions:
            lines.append(f"  • {a}")

        lines.extend([
            "",
            "════════════════════════════════════════════════════════════",
            "  GRC_Claw — Governance, Risk & Compliance AI Agents",
            "════════════════════════════════════════════════════════════",
        ])

        return "\n".join(lines)

    def save(self, filepath: Union[str, Path], format: str = "html") -> Path:
        """Save quote to file in specified format."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            content = self.to_json()
            filepath = filepath.with_suffix(".json")
        elif format == "html":
            content = self.to_html()
            filepath = filepath.with_suffix(".html")
        elif format == "markdown" or format == "md":
            content = self.to_markdown()
            filepath = filepath.with_suffix(".md")
        elif format == "text" or format == "txt":
            content = self.to_text()
            filepath = filepath.with_suffix(".txt")
        else:
            raise ValueError(f"Unsupported format: {format}")

        filepath.write_text(content, encoding="utf-8")
        return filepath

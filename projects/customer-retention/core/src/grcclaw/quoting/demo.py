"""
Demo script for the GRC_Claw Quote Engine.

Run this to see the quote engine in action with sample data.
"""

from grcclaw.quoting import (
    DeploymentModel,
    OrganizationProfile,
    PricingTier,
    QuoteCalculator,
    QuoteComparison,
    QuoteGenerator,
    ROICalculator,
    SupportLevel,
    UnitEconomicsDashboard,
)


def main():
    print("=" * 70)
    print("  GRC_Claw Quote Engine Demo")
    print("=" * 70)
    print()

    # ── Create sample organization profile ─────────────────────────────
    profile = OrganizationProfile(
        name="Acme Healthcare Corp",
        industry="healthcare",
        agents=50,
        models=3,
        policies=120,
        evidence_volume_gb=2000,
        frameworks=["HIPAA", "SOC2", "ISO27001", "GDPR"],
        deployment_model=DeploymentModel.CLOUD_SAAS,
        support_level=SupportLevel.PREMIUM,
        pricing_tier=PricingTier.GROWTH,
        risk_exposure_score=8.0,
        compliance_maturity=4.0,
        annual_revenue_millions=500.0,
        existing_tooling_cost_annual=350_000,
        incident_history_count=12,
        avg_incident_cost=200_000,
        audit_findings_annual=25,
        avg_audit_remediation_cost=30_000,
        data_breach_probability_annual=0.20,
        avg_data_breach_cost=5_000_000,
        regulatory_fine_exposure_annual=500_000,
    )

    # ── Generate Quote ─────────────────────────────────────────────────
    calculator = QuoteCalculator()
    quote = calculator.calculate(profile)

    print(f"Quote ID: {quote.quote_id}")
    print(f"Organization: {profile.name}")
    print(f"Annual Cost: ${quote.annual_cost:,.0f}")
    print(f"Monthly Cost: ${quote.monthly_cost:,.0f}")
    print()

    # ── Unit Economics ─────────────────────────────────────────────────
    ue_dashboard = UnitEconomicsDashboard(quote, profile)
    print(ue_dashboard.summary())
    print()

    # ── ROI Analysis ───────────────────────────────────────────────────
    roi_calc = ROICalculator()
    roi = roi_calc.calculate(
        profile,
        quote,
        implementation_cost=25_000,
        training_cost=10_000,
    )
    print(roi_calc.generate_executive_summary(roi))
    print()

    # ── Quote Comparison ───────────────────────────────────────────────
    print("=" * 70)
    print("  Deployment Model Comparison")
    print("=" * 70)
    comparison = QuoteComparison.compare_deployment_models(profile, calculator)
    print(comparison.to_text())
    print()

    # ── Export Quote ───────────────────────────────────────────────────
    generator = QuoteGenerator(quote)

    import os
    output_dir = os.path.expanduser("~/GRC_Claw/quotes_output")
    os.makedirs(output_dir, exist_ok=True)

    json_path = generator.save(f"{output_dir}/quote_{quote.quote_id}", format="json")
    html_path = generator.save(f"{output_dir}/quote_{quote.quote_id}", format="html")
    md_path = generator.save(f"{output_dir}/quote_{quote.quote_id}", format="markdown")
    txt_path = generator.save(f"{output_dir}/quote_{quote.quote_id}", format="text")

    print("Quote exported to:")
    print(f"  JSON:     {json_path}")
    print(f"  HTML:     {html_path}")
    print(f"  Markdown: {md_path}")
    print(f"  Text:     {txt_path}")

    # ── Comparison HTML ────────────────────────────────────────────────
    comp_html = comparison.to_html()
    comp_path = f"{output_dir}/comparison_{quote.quote_id}.html"
    with open(comp_path, "w") as f:
        f.write(comp_html)
    print(f"  Comparison: {comp_path}")

    print()
    print("=" * 70)
    print("  Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

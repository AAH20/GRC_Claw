"""Quote generation commands for GRC_Claw CLI."""
import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from grc_claw_cli.utils.output import print_json, print_table, print_success, print_error, print_warning, print_info
from grc_claw_cli.utils.config import Config


DEPLOYMENT_MODELS = ["cloud_saas", "private_cloud", "on_premises", "hybrid"]
SUPPORT_LEVELS = ["standard", "premium", "enterprise"]
PRICING_TIERS = ["startup", "growth", "enterprise"]


# Base pricing (per unit, monthly)
BASE_PRICING = {
    "agent": {"startup": 50, "growth": 75, "enterprise": 150},
    "model": {"startup": 30, "growth": 50, "enterprise": 100},
    "policy": {"startup": 10, "growth": 15, "enterprise": 25},
    "evidence_gb": {"startup": 0.50, "growth": 0.35, "enterprise": 0.25},
}

SUPPORT_MULTIPLIER = {"standard": 1.0, "premium": 1.5, "enterprise": 2.5}
DEPLOYMENT_MULTIPLIER = {"cloud_saas": 1.0, "private_cloud": 1.3, "on_premises": 1.5, "hybrid": 1.4}

FRAMEWORK_COSTS = {
    "iso27001": 5000, "nist-csf": 4000, "soc2": 8000, "iso42001": 6000,
    "eu-ai-act": 7000, "dora": 9000, "hipaa": 7500, "pci-dss": 10000,
    "gdpr": 5500, "fedramp": 15000, "cmmc": 12000,
}


def generate_quote(org_name, industry, agents, models, policies, evidence_gb,
                   frameworks=None, deployment_model="cloud_saas", support_level="standard",
                   pricing_tier="growth", risk_exposure=5, compliance_maturity=5):
    """Generate a custom GRC_Claw quote."""
    frameworks = frameworks or []
    quote_id = str(uuid.uuid4())[:8].upper()
    timestamp = datetime.now(timezone.utc).isoformat()

    line_items = []

    # Agent licensing
    agent_price = BASE_PRICING["agent"][pricing_tier]
    line_items.append({
        "description": f"AI Agent Licensing ({pricing_tier} tier)",
        "quantity": agents, "unit_price": agent_price, "unit": "agent/month",
        "category": "licensing", "subtotal": agents * agent_price,
        "discount_pct": 0, "discount_amount": 0, "total": agents * agent_price,
    })

    # Model licensing
    model_price = BASE_PRICING["model"][pricing_tier]
    line_items.append({
        "description": f"AI Model Licensing ({pricing_tier} tier)",
        "quantity": models, "unit_price": model_price, "unit": "model/month",
        "category": "licensing", "subtotal": models * model_price,
        "discount_pct": 0, "discount_amount": 0, "total": models * model_price,
    })

    # Policy management
    policy_price = BASE_PRICING["policy"][pricing_tier]
    line_items.append({
        "description": f"Policy Management ({pricing_tier} tier)",
        "quantity": policies, "unit_price": policy_price, "unit": "policy/month",
        "category": "licensing", "subtotal": policies * policy_price,
        "discount_pct": 0, "discount_amount": 0, "total": policies * policy_price,
    })

    # Evidence storage
    evidence_price = BASE_PRICING["evidence_gb"][pricing_tier]
    line_items.append({
        "description": f"Evidence Storage ({evidence_gb} GB)",
        "quantity": evidence_gb, "unit_price": evidence_price, "unit": "GB/month",
        "category": "storage", "subtotal": evidence_gb * evidence_price,
        "discount_pct": 0, "discount_amount": 0, "total": evidence_gb * evidence_price,
    })

    # Framework packs
    for fw in frameworks:
        cost = FRAMEWORK_COSTS.get(fw, 5000)
        line_items.append({
            "description": f"Framework Pack: {fw}",
            "quantity": 1, "unit_price": cost, "unit": "one-time",
            "category": "framework", "subtotal": cost,
            "discount_pct": 0, "discount_amount": 0, "total": cost,
        })

    # Calculate subtotal
    subtotal = sum(li["total"] for li in line_items)

    # Volume discount
    volume_discount_pct = 0
    if agents >= 100:
        volume_discount_pct = 15
    elif agents >= 50:
        volume_discount_pct = 10
    elif agents >= 20:
        volume_discount_pct = 5
    volume_discount = subtotal * (volume_discount_pct / 100)

    # Apply multipliers
    support_mult = SUPPORT_MULTIPLIER.get(support_level, 1.0)
    deploy_mult = DEPLOYMENT_MULTIPLIER.get(deployment_model, 1.0)
    total_before_tax = (subtotal - volume_discount) * support_mult * deploy_mult

    # Risk adjustment
    risk_adjustment = 1 + (risk_exposure - 5) * 0.02
    total_before_tax *= risk_adjustment

    # Compliance maturity discount
    maturity_discount = 1 - (compliance_maturity - 5) * 0.01
    total_before_tax *= maturity_discount

    annual_cost = total_before_tax
    monthly_cost = annual_cost / 12

    quote = {
        "quote_id": quote_id,
        "created_at": timestamp,
        "valid_until": (datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)).isoformat(),
        "organization": {
            "name": org_name, "industry": industry,
            "agents": agents, "models": models, "policies": policies,
            "evidence_volume_gb": evidence_gb, "frameworks": frameworks,
            "deployment_model": deployment_model, "support_level": support_level,
            "pricing_tier": pricing_tier,
        },
        "line_items": line_items,
        "subtotal": round(subtotal, 2),
        "volume_discount_pct": volume_discount_pct,
        "volume_discount_amount": round(volume_discount, 2),
        "support_multiplier": support_mult,
        "deployment_multiplier": deploy_mult,
        "total_before_tax": round(total_before_tax, 2),
        "annual_cost": round(annual_cost, 2),
        "monthly_cost": round(monthly_cost, 2),
        "notes": [
            f"Risk exposure adjustment: {risk_exposure}/10",
            f"Compliance maturity adjustment: {compliance_maturity}/10",
        ],
        "assumptions": [
            "Pricing valid for 12 months",
            "Volume discounts applied at agent tier thresholds",
            "Support and deployment multipliers applied to subtotal",
        ],
    }
    return quote


def register(subparsers):
    """Register quote subcommands."""
    parser = subparsers.add_parser("quote", help="Quote generation commands")
    quote_sub = parser.add_subparsers(dest="quote_command", help="Quote operations")

    # quote generate
    gen_p = quote_sub.add_parser("generate", help="Generate a custom quote")
    gen_p.add_argument("--org-name", required=True, help="Organization name")
    gen_p.add_argument("--industry", required=True, help="Industry")
    gen_p.add_argument("--agents", type=int, required=True, help="Number of agents")
    gen_p.add_argument("--models", type=int, required=True, help="Number of models")
    gen_p.add_argument("--policies", type=int, required=True, help="Number of policies")
    gen_p.add_argument("--evidence-gb", type=float, required=True, help="Evidence volume in GB")
    gen_p.add_argument("--frameworks", nargs="*", default=[], help="Framework packs")
    gen_p.add_argument("--deployment", default="cloud_saas", choices=DEPLOYMENT_MODELS, help="Deployment model")
    gen_p.add_argument("--support", default="standard", choices=SUPPORT_LEVELS, help="Support level")
    gen_p.add_argument("--tier", default="growth", choices=PRICING_TIER, help="Pricing tier")
    gen_p.add_argument("--risk-exposure", type=float, default=5, help="Risk exposure 1-10")
    gen_p.add_argument("--compliance-maturity", type=float, default=5, help="Compliance maturity 1-10")
    gen_p.add_argument("--output", help="Output file path")
    gen_p.add_argument("--json", action="store_true", help="Output as JSON")

    # quote compare
    compare_p = quote_sub.add_parser("compare", help="Compare quotes across tiers")
    compare_p.add_argument("--org-name", required=True, help="Organization name")
    compare_p.add_argument("--industry", required=True, help="Industry")
    compare_p.add_argument("--agents", type=int, required=True, help="Number of agents")
    compare_p.add_argument("--models", type=int, required=True, help="Number of models")
    compare_p.add_argument("--policies", type=int, required=True, help="Number of policies")
    compare_p.add_argument("--evidence-gb", type=float, required=True, help="Evidence volume in GB")
    compare_p.add_argument("--frameworks", nargs="*", default=[], help="Framework packs")
    compare_p.add_argument("--json", action="store_true", help="Output as JSON")


def handle(args, config: Config):
    """Handle quote commands."""
    cmd = args.quote_command

    if cmd == "generate":
        quote = generate_quote(
            org_name=args.org_name, industry=args.industry,
            agents=args.agents, models=args.models, policies=args.policies,
            evidence_gb=args.evidence_gb, frameworks=args.frameworks,
            deployment_model=args.deployment, support_level=args.support,
            pricing_tier=args.tier, risk_exposure=args.risk_exposure,
            compliance_maturity=args.compliance_maturity,
        )
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(quote, f, indent=2, default=str)
            print_success(f"Quote written to {args.output}")
        elif args.json:
            print_json(quote)
        else:
            print_info(f"Quote: {quote['quote_id']}")
            print(f"  Organization: {quote['organization']['name']}")
            print(f"  Industry: {quote['organization']['industry']}")
            print(f"  Tier: {quote['organization']['pricing_tier']}")
            print(f"\n  Line Items:")
            for li in quote["line_items"]:
                print(f"    {li['description']}: {li['quantity']} x ${li['unit_price']:,.2f} = ${li['total']:,.2f}")
            print(f"\n  Subtotal: ${quote['subtotal']:,.2f}")
            if quote["volume_discount_amount"] > 0:
                print(f"  Volume Discount ({quote['volume_discount_pct']}%): -${quote['volume_discount_amount']:,.2f}")
            print(f"  Support Multiplier: {quote['support_multiplier']}x")
            print(f"  Deployment Multiplier: {quote['deployment_multiplier']}x")
            print(f"\n  Annual Cost: ${quote['annual_cost']:,.2f}")
            print(f"  Monthly Cost: ${quote['monthly_cost']:,.2f}")
        return 0

    elif cmd == "compare":
        tiers = {}
        for tier in PRICING_TIER:
            quote = generate_quote(
                org_name=args.org_name, industry=args.industry,
                agents=args.agents, models=args.models, policies=args.policies,
                evidence_gb=args.evidence_gb, frameworks=args.frameworks,
                pricing_tier=tier,
            )
            tiers[tier] = {
                "annual_cost": quote["annual_cost"],
                "monthly_cost": quote["monthly_cost"],
                "subtotal": quote["subtotal"],
            }
        if args.json:
            print_json(tiers)
        else:
            print_info("Quote Comparison by Pricing Tier")
            rows = [[t, f"${v['annual_cost']:,.0f}", f"${v['monthly_cost']:,.0f}", f"${v['subtotal']:,.0f}"] for t, v in tiers.items()]
            print_table(["Tier", "Annual", "Monthly", "Subtotal"], rows)
        return 0

    else:
        print_error("No quote subcommand specified. Use: grc quote <generate|compare>")
        return 1

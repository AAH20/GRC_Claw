"""
CLI for running database seeders.

Usage:
    python -m database.seeders.cli --help
    python -m database.seeders.cli seed --entity tiers --count 10
    python -m database.seeders.cli seed --all
    python -m database.seeders.cli validate
    python -m database.seeders.cli benchmark
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# Ensure src/ is on the path
_src = str(Path(__file__).resolve().parents[3] / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from database.seeders.seeders import (
    seed_tiers, seed_tier_evaluations, seed_upgrade_requests,
    seed_access_policies, seed_benefits, seed_tier_analytics,
    seed_governance_policies, seed_rules, seed_rule_enforcement_results,
    seed_disputes, seed_dispute_resolutions, seed_governance_actions,
    seed_governance_health_scores, seed_governance_analytics,
    seed_governance_summaries, seed_escalations, seed_resolutions,
    seed_slas, seed_sla_breaches, seed_priorities,
    seed_priority_assessments, seed_escalation_analyses,
    seed_trend_reports, seed_permissions, seed_roles,
    seed_access_requests, seed_access_results, seed_access_audits,
    seed_access_recommendations, seed_reputation_scores, seed_badges,
    seed_trust_tiers, seed_reputation_history, seed_reputation_explanations,
    seed_compliance_policies, seed_violations, seed_audit_reports,
    seed_compliance_scores, seed_compliance_reports, seed_remediation_actions,
    seed_identity_data, seed_document_data, seed_verification_requests,
    seed_verification_results, seed_trust_scores, seed_fraud_reports,
    seed_document_verification_results, seed_verification_explanations,
    seed_moderation_items, seed_queues, seed_priority_scores,
    seed_review_decisions, seed_moderation_escalations, seed_queue_metrics,
    seed_moderation_analytics, seed_trends, seed_moderator_performance,
    seed_policy_effectiveness, seed_moderation_predictions,
    seed_analytics_summaries, seed_engagement_metrics, seed_toxicity_reports,
    seed_growth_analyses, seed_churn_predictions, seed_health_scores,
    seed_health_explanations, seed_all,
)


# Entity name to seeder function mapping
SEEDER_MAP: dict[str, Any] = {
    # Tier Management
    "tiers": seed_tiers,
    "tier_evaluations": seed_tier_evaluations,
    "upgrade_requests": seed_upgrade_requests,
    "access_policies": seed_access_policies,
    "benefits": seed_benefits,
    "tier_analytics": seed_tier_analytics,
    # Community Governance
    "governance_policies": seed_governance_policies,
    "rules": seed_rules,
    "rule_enforcement_results": seed_rule_enforcement_results,
    "disputes": seed_disputes,
    "dispute_resolutions": seed_dispute_resolutions,
    "governance_actions": seed_governance_actions,
    "governance_health_scores": seed_governance_health_scores,
    "governance_analytics": seed_governance_analytics,
    "governance_summaries": seed_governance_summaries,
    # Escalation Workflow
    "escalations": seed_escalations,
    "resolutions": seed_resolutions,
    "slas": seed_slas,
    "sla_breaches": seed_sla_breaches,
    "priorities": seed_priorities,
    "priority_assessments": seed_priority_assessments,
    "escalation_analyses": seed_escalation_analyses,
    "trend_reports": seed_trend_reports,
    # Access Control
    "permissions": seed_permissions,
    "roles": seed_roles,
    "access_requests": seed_access_requests,
    "access_results": seed_access_results,
    "access_audits": seed_access_audits,
    "access_recommendations": seed_access_recommendations,
    # Reputation System
    "reputation_scores": seed_reputation_scores,
    "badges": seed_badges,
    "trust_tiers": seed_trust_tiers,
    "reputation_history": seed_reputation_history,
    "reputation_explanations": seed_reputation_explanations,
    # Compliance Monitor
    "compliance_policies": seed_compliance_policies,
    "violations": seed_violations,
    "audit_reports": seed_audit_reports,
    "compliance_scores": seed_compliance_scores,
    "compliance_reports": seed_compliance_reports,
    "remediation_actions": seed_remediation_actions,
    # Member Verification
    "identity_data": seed_identity_data,
    "document_data": seed_document_data,
    "verification_requests": seed_verification_requests,
    "verification_results": seed_verification_results,
    "trust_scores": seed_trust_scores,
    "fraud_reports": seed_fraud_reports,
    "document_verification_results": seed_document_verification_results,
    "verification_explanations": seed_verification_explanations,
    # Moderation Queue
    "moderation_items": seed_moderation_items,
    "queues": seed_queues,
    "priority_scores": seed_priority_scores,
    "review_decisions": seed_review_decisions,
    "moderation_escalations": seed_moderation_escalations,
    "queue_metrics": seed_queue_metrics,
    # Moderation Analytics
    "moderation_analytics": seed_moderation_analytics,
    "trends": seed_trends,
    "moderator_performance": seed_moderator_performance,
    "policy_effectiveness": seed_policy_effectiveness,
    "moderation_predictions": seed_moderation_predictions,
    "analytics_summaries": seed_analytics_summaries,
    # Community Health Scorer
    "engagement_metrics": seed_engagement_metrics,
    "toxicity_reports": seed_toxicity_reports,
    "growth_analyses": seed_growth_analyses,
    "churn_predictions": seed_churn_predictions,
    "health_scores": seed_health_scores,
    "health_explanations": seed_health_explanations,
}


def cmd_seed(args: argparse.Namespace) -> None:
    """Run a specific seeder or all seeders."""
    if args.entity:
        entity = args.entity
        if entity not in SEEDER_MAP:
            print(f"Error: Unknown entity '{entity}'", file=sys.stderr)
            print(f"Available entities: {', '.join(sorted(SEEDER_MAP.keys()))}", file=sys.stderr)
            sys.exit(1)

        seeder_func = SEEDER_MAP[entity]
        count = args.count or 10

        print(f"Seeding {count} {entity}...")
        start = time.perf_counter()
        result = seeder_func(count=count)
        elapsed = time.perf_counter() - start

        print(f"Seeded {len(result)} {entity} in {elapsed:.4f}s")
        if args.output:
            # Output as JSON
            output_data = [item.model_dump() if hasattr(item, 'model_dump') else item.dict() for item in result]
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"Output written to {args.output}")
    else:
        # Seed all
        print("Seeding all entities...")
        start = time.perf_counter()
        data = seed_all()
        elapsed = time.perf_counter() - start

        total = sum(len(v) for v in data.values())
        print(f"Seeded {total} records across {len(data)} entity types in {elapsed:.4f}s:")
        for name, records in data.items():
            print(f"  {name}: {len(records)}")


def cmd_validate(args: argparse.Namespace) -> None:
    """Run validation suite."""
    from database.seeders.validation import run_all_validations

    print("Running validation suite...")
    results = run_all_validations()

    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    # Factory validation
    fv = results["factory_validation"]
    print(f"\n1. Factory Validation: {fv['passed']} passed, {fv['failed']} failed")
    if fv["errors"]:
        for err in fv["errors"]:
            print(f"   FAIL: {err['factory']}: {err['error']}")

    # Edge cases
    ec = results["edge_cases"]
    print(f"\n2. Edge Cases:")
    for name, result in ec.items():
        status = result.get("status", "unknown")
        if status == "passed":
            print(f"   PASS: {name}: {result.get('example', '')}")
        elif status == "expected_failure":
            print(f"   EXPECTED FAIL: {name}: {result.get('error', '')[:80]}")
        else:
            print(f"   FAIL: {name}: {result.get('error', '')}")

    # Performance benchmarks
    pb = results["performance_benchmarks"]
    print(f"\n3. Performance Benchmarks:")
    for name, bench in pb.items():
        print(f"   {name}: {bench['count']} records in {bench['elapsed_seconds']}s ({bench['records_per_second']} rec/s)")

    # Data consistency
    dc = results["data_consistency"]
    print(f"\n4. Data Consistency:")
    for name, check in dc.items():
        status = check.get("status", "unknown")
        if status == "passed":
            print(f"   PASS: {name}: {check.get('detail', '')}")
        elif status == "warning":
            print(f"   WARN: {name}: missing={check.get('missing', [])}, extra={check.get('extra', [])}")
        else:
            print(f"   FAIL: {name}: {check.get('error', '')}")

    # Bulk insert
    bi = results["bulk_insert_optimization"]
    print(f"\n5. Bulk Insert Optimization:")
    print(f"   INSERT: {bi['insert_simulation']['records_per_second']} rec/s")
    print(f"   COPY: {bi['copy_simulation']['records_per_second']} rec/s")
    print(f"   Speedup: {bi['speedup']}x")

    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nFull results written to {args.output}")


def cmd_benchmark(args: argparse.Namespace) -> None:
    """Run performance benchmarks."""
    from database.seeders.validation import benchmark_seeders

    print("Running performance benchmarks...")
    results = benchmark_seeders()

    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARKS")
    print("=" *  60)
    for name, bench in results.items():
        print(f"{name:30s} {bench['count']:6d} records  {bench['elapsed_seconds']:8.4f}s  {bench['records_per_second']:10.2f} rec/s")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults written to {args.output}")


def cmd_list(args: argparse.Namespace) -> None:
    """List all available seeders."""
    print("Available seeders:")
    print("-" * 40)

    # Group by service
    services = {
        "Tier Management": ["tiers", "tier_evaluations", "upgrade_requests", "access_policies", "benefits", "tier_analytics"],
        "Community Governance": ["governance_policies", "rules", "rule_enforcement_results", "disputes", "dispute_resolutions", "governance_actions", "governance_health_scores", "governance_analytics", "governance_summaries"],
        "Escalation Workflow": ["escalations", "resolutions", "slas", "sla_breaches", "priorities", "priority_assessments", "escalation_analyses", "trend_reports"],
        "Access Control": ["permissions", "roles", "access_requests", "access_results", "access_audits", "access_recommendations"],
        "Reputation System": ["reputation_scores", "badges", "trust_tiers", "reputation_history", "reputation_explanations"],
        "Compliance Monitor": ["compliance_policies", "violations", "audit_reports", "compliance_scores", "compliance_reports", "remediation_actions"],
        "Member Verification": ["identity_data", "document_data", "verification_requests", "verification_results", "trust_scores", "fraud_reports", "document_verification_results", "verification_explanations"],
        "Moderation Queue": ["moderation_items", "queues", "priority_scores", "review_decisions", "moderation_escalations", "queue_metrics"],
        "Moderation Analytics": ["moderation_analytics", "trends", "moderator_performance", "policy_effectiveness", "moderation_predictions", "analytics_summaries"],
        "Community Health Scorer": ["engagement_metrics", "toxicity_reports", "growth_analyses", "churn_predictions", "health_scores", "health_explanations"],
    }

    for service, entities in services.items():
        print(f"\n{service}:")
        for entity in entities:
            print(f"  - {entity}")

    print(f"\nTotal: {len(SEEDER_MAP)} seeders")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database seeder CLI for gated-communities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # seed command
    seed_parser = subparsers.add_parser("seed", help="Run seeders")
    seed_parser.add_argument("--entity", "-e", help="Entity to seed (e.g., tiers, escalations)")
    seed_parser.add_argument("--count", "-c", type=int, default=10, help="Number of records to seed")
    seed_parser.add_argument("--output", "-o", help="Output file (JSON)")
    seed_parser.add_argument("--all", "-a", action="store_true", help="Seed all entities")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Run validation suite")
    validate_parser.add_argument("--output", "-o", help="Output file (JSON)")

    # benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run performance benchmarks")
    benchmark_parser.add_argument("--output", "-o", help="Output file (JSON)")

    # list command
    list_parser = subparsers.add_parser("list", help="List available seeders")

    args = parser.parse_args()

    if args.command == "seed":
        if args.all:
            args.entity = None
        cmd_seed(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

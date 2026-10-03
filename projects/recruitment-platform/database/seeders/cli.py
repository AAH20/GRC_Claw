"""Enhanced CLI for running database seeders with validation, benchmarks, and edge cases."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from database.seeders.benchmarks import run_all_benchmarks, run_seeder_benchmarks
from database.seeders.bulk_insert import run_optimized_full_seed
from database.seeders.edge_cases import seed_edge_cases
from database.seeders.seeders import (
    create_session,
    run_full_seed,
    seed_applications,
    seed_candidates,
    seed_companies,
    seed_education,
    seed_experience,
    seed_interviews,
    seed_jobs,
    seed_notes,
    seed_skills,
    seed_talent_pools,
    seed_users,
)
from database.seeders.validators import run_full_validation

logger = logging.getLogger(__name__)

SEEDER_MAP = {
    "skills": seed_skills,
    "users": seed_users,
    "companies": seed_companies,
    "jobs": seed_jobs,
    "candidates": seed_candidates,
    "applications": seed_applications,
    "interviews": seed_interviews,
    "notes": seed_notes,
    "talent_pools": seed_talent_pools,
    "education": seed_education,
    "experience": seed_experience,
}


def cmd_seed(args: argparse.Namespace) -> int:
    """Run seeders."""
    session = create_session(args.database_url)

    try:
        if args.entity:
            if args.entity not in SEEDER_MAP:
                print(
                    f"Unknown entity: {args.entity}. Available: {', '.join(SEEDER_MAP.keys())}"
                )
                return 1
            seeder_func = SEEDER_MAP[args.entity]
            count = args.count or 10
            result = seeder_func(session, count)
            print(f"Seeded {len(result) if result else count} {args.entity}")
        else:
            run_full_seed(args.database_url, args.scale)
            print(f"Full seed completed at '{args.scale}' scale")
        return 0
    except Exception as e:
        logger.error("Seed failed: %s", e)
        return 1
    finally:
        session.close()


def cmd_validate(args: argparse.Namespace) -> int:
    """Run validation checks."""
    print("Running factory validations...")
    report = run_full_validation(args.database_url)
    print(report.summary())

    if args.output:
        with open(args.output, "w") as f:
            f.write(report.summary())
        print(f"Report saved to {args.output}")

    return 0 if report.failed == 0 else 1


def cmd_benchmark(args: argparse.Namespace) -> int:
    """Run performance benchmarks."""
    print("Running seeder benchmarks...")
    reports = run_all_benchmarks(args.database_url, args.scale)

    for name, report in reports.items():
        print(f"\n{name}:")
        print(report.summary())

    if args.output:
        output = {}
        for name, report in reports.items():
            output[name] = {
                "results": [
                    {
                        "name": r.name,
                        "duration_seconds": r.duration_seconds,
                        "records_created": r.records_created,
                        "records_per_second": r.records_per_second,
                        "scale": r.scale,
                    }
                    for r in report.results
                ],
                "total_duration": report.total_duration,
                "total_records": report.total_records,
            }
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Benchmark results saved to {args.output}")

    return 0


def cmd_edge_cases(args: argparse.Namespace) -> int:
    """Seed edge case data."""
    session = create_session(args.database_url)

    try:
        count = args.count or 5
        results = seed_edge_cases(session, count)
        total = sum(len(v) for v in results.values())
        print(f"Seeded {total} edge case records:")
        for entity, objects in results.items():
            print(f"  {entity}: {len(objects)}")
        return 0
    except Exception as e:
        logger.error("Edge case seeding failed: %s", e)
        return 1
    finally:
        session.close()


def cmd_optimized_seed(args: argparse.Namespace) -> int:
    """Run optimized bulk insert seed."""
    print("Running optimized seed with bulk inserts...")
    results = run_optimized_full_seed(args.database_url, args.scale, args.batch_size)
    total = sum(results.values())
    print(f"Optimized seed completed: {total} total records")
    for name, count in results.items():
        print(f"  {name}: {count}")
    return 0


def cmd_full_pipeline(args: argparse.Namespace) -> int:
    """Run full pipeline: seed, validate, benchmark."""
    print("=" * 70)
    print("FULL SEEDER PIPELINE")
    print("=" * 70)

    # Step 1: Seed
    print("\n[1/3] Seeding database...")
    session = create_session(args.database_url)
    try:
        run_full_seed(args.database_url, args.scale)
        print("  Seed completed")
    except Exception as e:
        logger.error("  Seed failed: %s", e)
        return 1
    finally:
        session.close()

    # Step 2: Validate
    print("\n[2/3] Running validations...")
    report = run_full_validation(args.database_url)
    print(report.summary())

    # Step 3: Benchmark
    print("\n[3/3] Running benchmarks...")
    bench_report = run_seeder_benchmarks(args.database_url, args.scale)
    print(bench_report.summary())

    if args.output:
        with open(args.output, "w") as f:
            f.write("VALIDATION REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(report.summary())
            f.write("\n\nBENCHMARK REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(bench_report.summary())
        print(f"\nFull report saved to {args.output}")

    return 0 if report.failed == 0 else 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced database seeder CLI for recruitment platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full seed
  python -m database.seeders.cli seed

  # Seed specific entity
  python -m database.seeders.cli seed --entity candidates --count 50

  # Run validation
  python -m database.seeders.cli validate

  # Run benchmarks
  python -m database.seeders.cli benchmark --scale large

  # Seed edge cases
  python -m database.seeders.cli edge-cases --count 10

  # Run optimized bulk insert seed
  python -m database.seeders.cli optimized-seed --batch-size 500

  # Run full pipeline
  python -m database.seeders.cli full-pipeline --scale medium
        """,
    )

    parser.add_argument(
        "--database-url",
        default="sqlite:///./recruitment.db",
        help="SQLAlchemy database URL",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Seed command
    seed_parser = subparsers.add_parser("seed", help="Run seeders")
    seed_parser.add_argument(
        "--scale",
        choices=["small", "medium", "large"],
        default="medium",
        help="Seed scale factor",
    )
    seed_parser.add_argument(
        "--entity",
        choices=list(SEEDER_MAP.keys()),
        help="Seed specific entity only",
    )
    seed_parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of records (for single entity seeding)",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Run validation checks")
    validate_parser.add_argument(
        "--output",
        help="Save report to file",
    )

    # Benchmark command
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="Run performance benchmarks"
    )
    benchmark_parser.add_argument(
        "--scale",
        choices=["small", "medium", "large"],
        default="medium",
        help="Seed scale factor",
    )
    benchmark_parser.add_argument(
        "--output",
        help="Save results to JSON file",
    )

    # Edge cases command
    edge_parser = subparsers.add_parser("edge-cases", help="Seed edge case data")
    edge_parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of edge case records per entity type",
    )

    # Optimized seed command
    opt_parser = subparsers.add_parser(
        "optimized-seed", help="Run optimized bulk insert seed"
    )
    opt_parser.add_argument(
        "--scale",
        choices=["small", "medium", "large"],
        default="medium",
        help="Seed scale factor",
    )
    opt_parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for bulk inserts",
    )

    # Full pipeline command
    pipeline_parser = subparsers.add_parser(
        "full-pipeline", help="Run full pipeline: seed, validate, benchmark"
    )
    pipeline_parser.add_argument(
        "--scale",
        choices=["small", "medium", "large"],
        default="medium",
        help="Seed scale factor",
    )
    pipeline_parser.add_argument(
        "--output",
        help="Save report to file",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "seed": cmd_seed,
        "validate": cmd_validate,
        "benchmark": cmd_benchmark,
        "edge-cases": cmd_edge_cases,
        "optimized-seed": cmd_optimized_seed,
        "full-pipeline": cmd_full_pipeline,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Command-line interface for UGC Marketplace database seeders."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ugc_marketplace.database.seeders.models import Base
from ugc_marketplace.database.seeders.seeders import seed_all

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def create_session(database_url: str):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def cmd_seed(args: argparse.Namespace) -> int:
    setup_logging(args.verbose)
    session, engine = create_session(args.database_url)
    try:
        results = seed_all(
            session,
            num_creators=args.creators,
            num_content_per_creator=args.content_per_creator,
            num_listings_per_content=args.listings_per_content,
            num_transactions_per_listing=args.transactions_per_listing,
            num_licenses_per_transaction=args.licenses_per_transaction,
            num_moderation_actions=args.moderation_actions,
            num_quality_scores_per_content=args.quality_scores_per_content,
            num_fraud_reports=args.fraud_reports,
            num_analytics_events=args.analytics_events,
            num_audit_logs=args.audit_logs,
        )
        print("\n" + "=" * 60)
        print("SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 60)
        for key, items in results.items():
            print(f"  {key}: {len(items)} records")
        print("=" * 60)
        return 0
    except Exception as e:
        logger.error("Seeding failed: %s", e)
        session.rollback()
        return 1
    finally:
        session.close()
        engine.dispose()


def cmd_validate(args: argparse.Namespace) -> int:
    setup_logging(args.verbose)
    session, engine = create_session(args.database_url)
    try:
        from ugc_marketplace.database.seeders.validation import run_validation

        report = run_validation(session)
        print("\n" + "=" * 60)
        print("VALIDATION REPORT")
        print("=" * 60)
        print(f"Total checks: {report.total}")
        print(f"Passed: {report.passed}")
        print(f"Failed: {report.failed}")
        print("-" * 60)
        for result in report.results:
            status = "PASS" if result.passed else "FAIL"
            print(f"  [{status}] {result.name}")
            if not result.passed:
                print(f"         {result.message}")
        print("=" * 60)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
            print(f"Report saved to: {args.output}")
        return 0 if report.failed == 0 else 1
    except Exception as e:
        logger.error("Validation failed: %s", e)
        return 1
    finally:
        session.close()
        engine.dispose()


def cmd_edge_cases(args: argparse.Namespace) -> int:
    setup_logging(args.verbose)
    session, engine = create_session(args.database_url)
    try:
        from ugc_marketplace.database.seeders.edge_cases import seed_edge_cases

        results = seed_edge_cases(session)
        print("\n" + "=" * 60)
        print("EDGE CASE DATA SEEDED")
        print("=" * 60)
        for key, items in results.items():
            print(f"  {key}: {len(items)} records")
        print("=" * 60)
        return 0
    except Exception as e:
        logger.error("Edge case seeding failed: %s", e)
        session.rollback()
        return 1
    finally:
        session.close()
        engine.dispose()


def cmd_benchmark(args: argparse.Namespace) -> int:
    setup_logging(args.verbose)
    session, engine = create_session(args.database_url)
    try:
        from ugc_marketplace.database.seeders.benchmarks import run_benchmarks

        report = run_benchmarks(session)
        print("\n" + "=" * 60)
        print("BENCHMARK REPORT")
        print("=" * 60)
        print(f"Total benchmarks: {len(report.results)}")
        print(f"Total duration: {report.total_duration:.4f}s")
        print("-" * 60)
        for result in report.results:
            print(f"  {result.name}:")
            print(f"    Duration: {result.duration_seconds:.4f}s")
            print(f"    Records: {result.records_processed}")
            print(f"    Throughput: {result.records_per_second:.2f} rec/s")
        print("=" * 60)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
            print(f"Report saved to: {args.output}")
        return 0
    except Exception as e:
        logger.error("Benchmark failed: %s", e)
        return 1
    finally:
        session.close()
        engine.dispose()


def cmd_consistency(args: argparse.Namespace) -> int:
    setup_logging(args.verbose)
    session, engine = create_session(args.database_url)
    try:
        from ugc_marketplace.database.seeders.consistency import \
            run_consistency_checks

        report = run_consistency_checks(session)
        print("\n" + "=" * 60)
        print("CONSISTENCY CHECK REPORT")
        print("=" * 60)
        print(f"Total checks: {report.total}")
        print(f"Passed: {report.passed}")
        print(f"Failed: {report.failed}")
        print(f"Total violations: {report.total_violations}")
        print("-" * 60)
        for result in report.results:
            status = "PASS" if result.passed else "FAIL"
            print(f"  [{status}] {result.name}")
            if not result.passed:
                print(f"         {result.message} (violations: {result.violations})")
        print("=" * 60)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
            print(f"Report saved to: {args.output}")
        return 0 if report.failed == 0 else 1
    except Exception as e:
        logger.error("Consistency check failed: %s", e)
        return 1
    finally:
        session.close()
        engine.dispose()


def cmd_bulk_insert(args: argparse.Namespace) -> int:
    setup_logging(args.verbose)
    session, engine = create_session(args.database_url)
    try:
        from ugc_marketplace.database.seeders.bulk_insert import \
            bulk_insert_all
        from ugc_marketplace.database.seeders.factories import (
            ActiveListingFactory, CommercialLicenseFactory,
            CompletedTransactionFactory, CreatorFactory,
            PublishedContentFactory)
        from ugc_marketplace.database.seeders.models import (AnalyticsEvent,
                                                             AuditLog)

        print("Generating test data...")
        creators = [CreatorFactory() for _ in range(args.count)]
        content_items = []
        for creator in creators[: args.count // 10]:
            for _ in range(5):
                content_items.append(PublishedContentFactory(creator=creator))
        listings = []
        for content in content_items:
            listings.append(
                ActiveListingFactory(content=content, creator=content.creator)
            )
        transactions = []
        for listing in listings:
            for _ in range(3):
                buyer = creators[(hash(listing.id) + 1) % len(creators)]
                seller = listing.creator
                if buyer.id != seller.id:
                    transactions.append(
                        CompletedTransactionFactory(
                            listing=listing, buyer=buyer, seller=seller
                        )
                    )
        licenses = []
        for txn in transactions:
            licenses.append(CommercialLicenseFactory(transaction=txn))
        analytics_events = [AnalyticsEvent() for _ in range(args.count * 10)]
        audit_logs = [AuditLog() for _ in range(args.count * 2)]

        print("Bulk inserting via COPY...")
        counts = bulk_insert_all(
            session,
            creators,
            content_items,
            listings,
            transactions,
            licenses,
            analytics_events,
            audit_logs,
        )
        print("\n" + "=" * 60)
        print("BULK INSERT COMPLETED")
        print("=" * 60)
        for key, count in counts.items():
            print(f"  {key}: {count} records")
        print("=" * 60)
        return 0
    except Exception as e:
        logger.error("Bulk insert failed: %s", e)
        session.rollback()
        return 1
    finally:
        session.close()
        engine.dispose()


def cmd_report(args: argparse.Namespace) -> int:
    setup_logging(args.verbose)
    session, engine = create_session(args.database_url)
    try:
        from ugc_marketplace.database.seeders.benchmarks import run_benchmarks
        from ugc_marketplace.database.seeders.consistency import \
            run_consistency_checks
        from ugc_marketplace.database.seeders.validation import run_validation

        print("\n" + "=" * 60)
        print("GENERATING COMPREHENSIVE REPORT")
        print("=" * 60)
        print("\n[1/3] Running validation checks...")
        validation_report = run_validation(session)
        print("[2/3] Running consistency checks...")
        consistency_report = run_consistency_checks(session)
        print("[3/3] Running benchmarks...")
        benchmark_report = run_benchmarks(session)

        report = {
            "validation": validation_report.to_dict(),
            "consistency": consistency_report.to_dict(),
            "benchmarks": benchmark_report.to_dict(),
        }
        print("\n" + "=" * 60)
        print("COMPREHENSIVE REPORT SUMMARY")
        print("=" * 60)
        print(
            f"Validation: {validation_report.passed}/{validation_report.total} passed"
        )
        print(
            f"Consistency: {consistency_report.passed}/{consistency_report.total} passed"
        )
        print(f"Benchmarks: {len(benchmark_report.results)} completed")
        print("=" * 60)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Report saved to: {args.output}")
        return 0
    except Exception as e:
        logger.error("Report generation failed: %s", e)
        return 1
    finally:
        session.close()
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="UGC Marketplace Database Seeder CLI")
    parser.add_argument(
        "--database-url",
        default="postgresql://postgres:postgres@localhost:5432/ugc_marketplace",
        help="Database connection URL",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    seed_parser = subparsers.add_parser("seed", help="Seed the database")
    seed_parser.add_argument("--creators", type=int, default=50)
    seed_parser.add_argument("--content-per-creator", type=int, default=5)
    seed_parser.add_argument("--listings-per-content", type=int, default=2)
    seed_parser.add_argument("--transactions-per-listing", type=int, default=3)
    seed_parser.add_argument("--licenses-per-transaction", type=int, default=1)
    seed_parser.add_argument("--moderation-actions", type=int, default=100)
    seed_parser.add_argument("--quality-scores-per-content", type=int, default=1)
    seed_parser.add_argument("--fraud-reports", type=int, default=50)
    seed_parser.add_argument("--analytics-events", type=int, default=1000)
    seed_parser.add_argument("--audit-logs", type=int, default=200)
    seed_parser.add_argument("--drop-all", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="Validate factories")
    validate_parser.add_argument("--output", "-o", help="Output file for report")

    subparsers.add_parser("edge-cases", help="Seed edge case data")

    benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmarks")
    benchmark_parser.add_argument("--output", "-o", help="Output file for report")

    consistency_parser = subparsers.add_parser(
        "consistency", help="Run consistency checks"
    )
    consistency_parser.add_argument("--output", "-o", help="Output file for report")

    bulk_parser = subparsers.add_parser("bulk-insert", help="Run bulk insert")
    bulk_parser.add_argument("--count", type=int, default=100)

    report_parser = subparsers.add_parser(
        "report", help="Generate comprehensive report"
    )
    report_parser.add_argument("--output", "-o", default="seeder_report.json")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "seed": cmd_seed,
        "validate": cmd_validate,
        "edge-cases": cmd_edge_cases,
        "benchmark": cmd_benchmark,
        "consistency": cmd_consistency,
        "bulk-insert": cmd_bulk_insert,
        "report": cmd_report,
    }
    handler = commands.get(args.command)
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

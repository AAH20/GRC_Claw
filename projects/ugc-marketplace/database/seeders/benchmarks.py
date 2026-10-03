"""Performance benchmarks for UGC Marketplace database seeders.

This module measures seeder execution time, throughput, and compares
different insertion strategies (INSERT vs COPY).
"""

from __future__ import annotations

import io
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from ugc_marketplace.database.seeders.factories import (
    CreatorFactory, PublishedContentFactory)
from ugc_marketplace.database.seeders.models import AnalyticsEvent, Transaction
from ugc_marketplace.database.seeders.seeders import seed_all

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    name: str
    duration_seconds: float
    records_processed: int
    records_per_second: float
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "duration_seconds": round(self.duration_seconds, 4),
            "records_processed": self.records_processed,
            "records_per_second": round(self.records_per_second, 2),
            "details": self.details,
        }


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""

    results: list[BenchmarkResult] = field(default_factory=list)

    def add(self, result: BenchmarkResult) -> None:
        self.results.append(result)

    @property
    def total_duration(self) -> float:
        return sum(r.duration_seconds for r in self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total_benchmarks": len(self.results),
                "total_duration_seconds": round(self.total_duration, 4),
            },
            "results": [r.to_dict() for r in self.results],
        }


class SeederBenchmark:
    """Benchmark suite for database seeders."""

    def __init__(self, session: Session):
        self.session = session
        self.report = BenchmarkReport()

    def run_all(self) -> BenchmarkReport:
        """Run all benchmarks."""
        self.benchmark_seed_all()
        self.benchmark_individual_seeders()
        self.benchmark_insert_vs_copy()
        self.benchmark_batch_sizes()
        self.benchmark_factory_creation()
        return self.report

    def _benchmark(self, name: str, func: Callable, count: int, **details) -> Any:
        """Run a single benchmark."""
        logger.info("Running benchmark: %s", name)
        start = time.perf_counter()
        result = func()
        duration = time.perf_counter() - start

        records_per_second = count / duration if duration > 0 else 0

        benchmark_result = BenchmarkResult(
            name=name,
            duration_seconds=duration,
            records_processed=count,
            records_per_second=records_per_second,
            details=details,
        )
        self.report.add(benchmark_result)
        logger.info(
            "Benchmark %s: %.4fs for %d records (%.2f rec/s)",
            name,
            duration,
            count,
            records_per_second,
        )
        return result

    def benchmark_seed_all(self) -> None:
        """Benchmark the main seed_all function."""
        configs = [
            ("seed_all_10_creators", 10, 5, 2, 3),
            ("seed_all_50_creators", 50, 5, 2, 3),
            ("seed_all_100_creators", 100, 5, 2, 3),
        ]

        for name, creators, content_per, listings_per, txns_per in configs:
            total_records = (
                creators
                + creators * content_per
                + creators * content_per * listings_per
                + creators * content_per * listings_per * txns_per
            )

            def run_seed():
                return seed_all(
                    self.session,
                    num_creators=creators,
                    num_content_per_creator=content_per,
                    num_listings_per_content=listings_per,
                    num_transactions_per_listing=txns_per,
                    num_licenses_per_transaction=1,
                    num_moderation_actions=creators * 2,
                    num_quality_scores_per_content=1,
                    num_fraud_reports=creators,
                    num_analytics_events=creators * 20,
                    num_audit_logs=creators * 4,
                )

            self._benchmark(
                name,
                run_seed,
                total_records,
                creators=creators,
                content_per_creator=content_per,
                listings_per_content=listings_per,
                transactions_per_listing=txns_per,
            )

    def benchmark_individual_seeders(self) -> None:
        """Benchmark individual seeder functions."""
        from ugc_marketplace.database.seeders.seeders import (
            seed_analytics_events, seed_audit_logs, seed_content,
            seed_creators)

        # Benchmark seed_creators
        for count in [10, 50, 100, 500]:
            self._benchmark(
                f"seed_creators_{count}",
                lambda c=count: seed_creators(self.session, count),
                count,
                seeder="seed_creators",
            )

        # Benchmark seed_content
        creators = seed_creators(self.session, 50)
        for per_creator in [1, 5, 10]:
            count = 50 * per_creator
            self._benchmark(
                f"seed_content_{per_creator}_per_creator",
                lambda p=per_creator: seed_content(
                    self.session, creators, per_creator=p
                ),
                count,
                seeder="seed_content",
                per_creator=per_creator,
            )

        # Benchmark seed_analytics_events
        for count in [100, 500, 1000, 5000]:
            self._benchmark(
                f"seed_analytics_events_{count}",
                lambda c=count: seed_analytics_events(
                    self.session, creators, [], [], count=c
                ),
                count,
                seeder="seed_analytics_events",
            )

        # Benchmark seed_audit_logs
        for count in [100, 500, 1000]:
            self._benchmark(
                f"seed_audit_logs_{count}",
                lambda c=count: seed_audit_logs(self.session, creators, count=c),
                count,
                seeder="seed_audit_logs",
            )

    def benchmark_insert_vs_copy(self) -> None:
        """Compare INSERT vs COPY performance for bulk data loading."""
        # Generate test data
        creators = [CreatorFactory() for _ in range(1000)]
        self.session.add_all(creators)
        self.session.flush()

        content_items = []
        for creator in creators[:100]:
            for _ in range(5):
                content_items.append(PublishedContentFactory(creator=creator))
        self.session.add_all(content_items)
        self.session.flush()

        # Benchmark INSERT for transactions
        def insert_transactions():
            transactions = []
            for i in range(1000):
                listing_id = content_items[i % len(content_items)].id
                buyer_id = creators[(i + 1) % len(creators)].id
                seller_id = creators[i % len(creators)].id
                if buyer_id == seller_id:
                    buyer_id = creators[(i + 2) % len(creators)].id
                transactions.append(
                    Transaction(
                        id=uuid4(),
                        listing_id=listing_id,
                        buyer_id=buyer_id,
                        seller_id=seller_id,
                        amount=49.99,
                        currency="USD",
                        platform_fee=4.99,
                        seller_earnings=45.00,
                        payment_method="stripe",
                        payment_status="completed",
                        metadata_={},
                    )
                )
            self.session.add_all(transactions)
            self.session.flush()
            return transactions

        self._benchmark(
            "insert_transactions_1000",
            insert_transactions,
            1000,
            method="INSERT",
        )

        # Benchmark COPY for transactions using raw SQL
        def copy_transactions():
            # Build CSV data
            buffer = io.StringIO()
            for i in range(1000):
                listing_id = content_items[i % len(content_items)].id
                buyer_id = creators[(i + 1) % len(creators)].id
                seller_id = creators[i % len(creators)].id
                if buyer_id == seller_id:
                    buyer_id = creators[(i + 2) % len(creators)].id
                buffer.write(
                    f"{uuid4()},{listing_id},{buyer_id},{seller_id},"
                    f"49.99,USD,4.99,45.00,stripe,completed,{{}}\n"
                )
            buffer.seek(0)

            # Use COPY via raw connection
            raw_conn = self.session.connection().connection
            with raw_conn.cursor() as cursor:
                cursor.copy_from(
                    buffer,
                    "transactions",
                    columns=[
                        "id",
                        "listing_id",
                        "buyer_id",
                        "seller_id",
                        "amount",
                        "currency",
                        "platform_fee",
                        "seller_earnings",
                        "payment_method",
                        "payment_status",
                        "metadata",
                    ],
                    null="",
                )
            self.session.flush()

        self._benchmark(
            "copy_transactions_1000",
            copy_transactions,
            1000,
            method="COPY",
        )

        # Benchmark COPY for analytics events (larger dataset)
        def copy_analytics_events():
            buffer = io.StringIO()
            for i in range(5000):
                user_id = creators[i % len(creators)].id if i % 3 != 0 else ""
                content_id = (
                    content_items[i % len(content_items)].id if i % 2 == 0 else ""
                )
                listing_id = (
                    content_items[i % len(content_items)].id if i % 3 == 0 else ""
                )
                buffer.write(
                    f"{uuid4()},page_view,{user_id},{content_id},{listing_id},"
                    f"{uuid4()},192.168.1.1,Mozilla/5.0,,"
                    f'{{"page": "/test", "duration": 100}}\n'
                )
            buffer.seek(0)

            raw_conn = self.session.connection().connection
            with raw_conn.cursor() as cursor:
                cursor.copy_from(
                    buffer,
                    "analytics_events",
                    columns=[
                        "id",
                        "event_type",
                        "user_id",
                        "content_id",
                        "listing_id",
                        "session_id",
                        "ip_address",
                        "user_agent",
                        "referrer",
                        "event_data",
                    ],
                    null="",
                )
            self.session.flush()

        self._benchmark(
            "copy_analytics_events_5000",
            copy_analytics_events,
            5000,
            method="COPY",
        )

        # Benchmark INSERT for analytics events (for comparison)
        def insert_analytics_events():
            events = []
            for i in range(5000):
                user_id = creators[i % len(creators)].id if i % 3 != 0 else None
                content_id = (
                    content_items[i % len(content_items)].id if i % 2 == 0 else None
                )
                listing_id = (
                    content_items[i % len(content_items)].id if i % 3 == 0 else None
                )
                events.append(
                    AnalyticsEvent(
                        id=uuid4(),
                        event_type="page_view",
                        user_id=user_id,
                        content_id=content_id,
                        listing_id=listing_id,
                        session_id=uuid4(),
                        ip_address="192.168.1.1",
                        user_agent="Mozilla/5.0",
                        referrer=None,
                        event_data={"page": "/test", "duration": 100},
                    )
                )
            self.session.add_all(events)
            self.session.flush()

        self._benchmark(
            "insert_analytics_events_5000",
            insert_analytics_events,
            5000,
            method="INSERT",
        )

    def benchmark_batch_sizes(self) -> None:
        """Benchmark different batch sizes for bulk operations."""
        batch_sizes = [100, 500, 1000, 5000]

        for batch_size in batch_sizes:

            def create_batch(size=batch_size):
                creators = [CreatorFactory() for _ in range(size)]
                self.session.add_all(creators)
                self.session.flush()
                return creators

            self._benchmark(
                f"batch_insert_creators_{batch_size}",
                create_batch,
                batch_size,
                batch_size=batch_size,
            )

    def benchmark_factory_creation(self) -> None:
        """Benchmark factory object creation (without DB insertion)."""
        for count in [100, 500, 1000]:

            def create_factories(c=count):
                return [CreatorFactory() for _ in range(c)]

            self._benchmark(
                f"factory_create_creators_{count}",
                create_factories,
                count,
                operation="factory_creation_only",
            )


def run_benchmarks(session: Session) -> BenchmarkReport:
    """Run all benchmarks and return the report.

    Args:
        session: SQLAlchemy session.

    Returns:
        BenchmarkReport with all results.
    """
    benchmark = SeederBenchmark(session)
    return benchmark.run_all()

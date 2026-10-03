"""Performance benchmarks for database seeders."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from database.seeders.factories import configure_session
from database.seeders.models import Base
from database.seeders.seeders import (
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

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    name: str
    duration_seconds: float
    records_created: int
    records_per_second: float
    scale: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    """Aggregate benchmark report."""

    results: list[BenchmarkResult] = field(default_factory=list)

    def add(self, result: BenchmarkResult) -> None:
        self.results.append(result)

    @property
    def total_duration(self) -> float:
        return sum(r.duration_seconds for r in self.results)

    @property
    def total_records(self) -> int:
        return sum(r.records_created for r in self.results)

    def summary(self) -> str:
        lines = [
            "=" * 80,
            "SEEDER PERFORMANCE BENCHMARK REPORT",
            "=" * 80,
            f"Total benchmarks: {len(self.results)}",
            f"Total records created: {self.total_records}",
            f"Total duration: {self.total_duration:.3f}s",
            (
                f"Overall throughput: {self.total_records / self.total_duration:.1f} records/s"
                if self.total_duration > 0
                else "N/A"
            ),
            "-" * 80,
            f"{'Benchmark':<30} {'Duration':>10} {'Records':>10} {'Rec/s':>10} {'Scale':>10}",
            "-" * 80,
        ]
        for r in self.results:
            lines.append(
                f"{r.name:<30} {r.duration_seconds:>9.3f}s {r.records_created:>10} "
                f"{r.records_per_second:>9.1f} {r.scale:>10}"
            )
        lines.append("=" * 80)
        return "\n".join(lines)


def _measure_seeder(
    session: Session,
    seeder_func: Callable,
    count: int,
    name: str,
    scale: str = "",
) -> BenchmarkResult:
    """Measure execution time of a seeder function."""
    start = time.perf_counter()
    try:
        result = seeder_func(session, count)
        records_created = len(result) if result else count
    except Exception as e:
        logger.error("Benchmark %s failed: %s", name, e)
        records_created = 0
    duration = time.perf_counter() - start

    return BenchmarkResult(
        name=name,
        duration_seconds=duration,
        records_created=records_created,
        records_per_second=records_created / duration if duration > 0 else 0,
        scale=scale,
    )


def run_seeder_benchmarks(database_url: str, scale: str = "medium") -> BenchmarkReport:
    """Run performance benchmarks for all seeders.

    Args:
        database_url: SQLAlchemy database URL.
        scale: Seed scale - 'small', 'medium', or 'large'.

    Returns:
        BenchmarkReport with all results.
    """
    scale_factors = {
        "small": 0.2,
        "medium": 0.5,
        "large": 1.0,
    }
    factor = scale_factors.get(scale, 0.5)

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    configure_session(session)

    report = BenchmarkReport()

    try:
        # Benchmark each seeder individually
        benchmarks = [
            (seed_skills, 50, "seed_skills"),
            (seed_users, 20, "seed_users"),
            (seed_companies, 10, "seed_companies"),
            (seed_jobs, 30, "seed_jobs"),
            (seed_candidates, 100, "seed_candidates"),
            (seed_applications, 200, "seed_applications"),
            (seed_interviews, 150, "seed_interviews"),
            (seed_notes, 80, "seed_notes"),
            (seed_talent_pools, 10, "seed_talent_pools"),
            (seed_education, 150, "seed_education"),
            (seed_experience, 200, "seed_experience"),
        ]

        for seeder_func, base_count, name in benchmarks:
            count = max(1, int(base_count * factor))
            result = _measure_seeder(session, seeder_func, count, name, scale)
            report.add(result)
            logger.info(
                "Benchmark %s: %.3fs for %d records",
                name,
                result.duration_seconds,
                result.records_created,
            )

        # Benchmark full seed
        from database.seeders.seeders import run_full_seed

        start = time.perf_counter()
        try:
            run_full_seed(database_url, scale)
            full_duration = time.perf_counter() - start
            # Count total records
            total = 0
            for table in Base.metadata.sorted_tables:
                count = session.execute(
                    text(f"SELECT COUNT(*) FROM {table.name}")
                ).scalar()
                total += count or 0
            report.add(
                BenchmarkResult(
                    name="full_seed",
                    duration_seconds=full_duration,
                    records_created=total,
                    records_per_second=(
                        total / full_duration if full_duration > 0 else 0
                    ),
                    scale=scale,
                )
            )
        except Exception as e:
            logger.error("Full seed benchmark failed: %s", e)

    finally:
        session.close()

    return report


def run_bulk_insert_benchmark(
    database_url: str, batch_sizes: list[int] | None = None
) -> BenchmarkReport:
    """Benchmark bulk insert vs individual insert performance.

    Args:
        database_url: SQLAlchemy database URL.
        batch_sizes: List of batch sizes to test.

    Returns:
        BenchmarkReport comparing insert strategies.
    """
    if batch_sizes is None:
        batch_sizes = [10, 50, 100, 500, 1000]

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    configure_session(session)

    report = BenchmarkReport()

    try:
        from database.seeders.factories import UserFactory

        for batch_size in batch_sizes:
            # Clear users table
            session.execute(text("DELETE FROM users"))
            session.commit()

            # Benchmark individual inserts
            start = time.perf_counter()
            for _ in range(batch_size):
                user = UserFactory()
                session.add(user)
            session.commit()
            individual_duration = time.perf_counter() - start

            report.add(
                BenchmarkResult(
                    name=f"individual_insert_{batch_size}",
                    duration_seconds=individual_duration,
                    records_created=batch_size,
                    records_per_second=(
                        batch_size / individual_duration
                        if individual_duration > 0
                        else 0
                    ),
                    details={"batch_size": batch_size, "strategy": "individual"},
                )
            )

            # Clear users table
            session.execute(text("DELETE FROM users"))
            session.commit()

            # Benchmark bulk insert
            start = time.perf_counter()
            users = [UserFactory() for _ in range(batch_size)]
            session.bulk_save_objects(users)
            session.commit()
            bulk_duration = time.perf_counter() - start

            report.add(
                BenchmarkResult(
                    name=f"bulk_insert_{batch_size}",
                    duration_seconds=bulk_duration,
                    records_created=batch_size,
                    records_per_second=(
                        batch_size / bulk_duration if bulk_duration > 0 else 0
                    ),
                    details={"batch_size": batch_size, "strategy": "bulk"},
                )
            )

    finally:
        session.close()

    return report


def run_all_benchmarks(
    database_url: str, scale: str = "medium"
) -> dict[str, BenchmarkReport]:
    """Run all benchmark suites.

    Args:
        database_url: SQLAlchemy database URL.
        scale: Seed scale.

    Returns:
        Dictionary mapping benchmark suite names to reports.
    """
    return {
        "seeder_benchmarks": run_seeder_benchmarks(database_url, scale),
        "bulk_insert_benchmarks": run_bulk_insert_benchmark(database_url),
    }

"""Bulk insert optimization using COPY for PostgreSQL and bulk operations for other databases."""

from __future__ import annotations

import io
import logging
from collections.abc import Sequence
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _is_postgresql(engine) -> bool:
    """Check if the engine is PostgreSQL."""
    return engine.dialect.name == "postgresql"


def _table_to_csv(table, objects: Sequence[Any]) -> str:
    """Convert a list of ORM objects to CSV string for COPY."""
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    # Get column names from the table
    columns = [col.name for col in table.columns]

    for obj in objects:
        row = []
        for col_name in columns:
            value = getattr(obj, col_name, None)
            if value is None:
                row.append("")
            else:
                row.append(str(value))
        writer.writerow(row)

    return output.getvalue()


def bulk_insert_postgresql(
    session: Session, table_name: str, objects: Sequence[Any]
) -> int:
    """Use PostgreSQL COPY for bulk insert.

    Args:
        session: Database session.
        table_name: Name of the table to insert into.
        objects: List of ORM objects to insert.

    Returns:
        Number of rows inserted.
    """
    if not objects:
        return 0

    engine = session.get_bind()
    if not _is_postgresql(engine):
        raise ValueError("COPY is only supported for PostgreSQL")

    # Get the table object
    from database.seeders.models import Base

    table = Base.metadata.tables.get(table_name)
    if table is None:
        raise ValueError(f"Table {table_name} not found")

    # Convert to CSV
    csv_data = _table_to_csv(table, objects)

    # Use COPY
    raw_connection = engine.raw_connection()
    try:
        cursor = raw_connection.cursor()
        columns = [col.name for col in table.columns]
        col_list = ", ".join(columns)
        copy_sql = f"COPY {table_name} ({col_list}) FROM STDIN WITH (FORMAT csv)"
        cursor.copy_expert(copy_sql, io.StringIO(csv_data))
        raw_connection.commit()
        return len(objects)
    finally:
        raw_connection.close()


def bulk_insert_sqlalchemy(
    session: Session, objects: Sequence[Any], batch_size: int = 1000
) -> int:
    """Use SQLAlchemy bulk_save_objects for bulk insert.

    Args:
        session: Database session.
        objects: List of ORM objects to insert.
        batch_size: Number of objects per batch.

    Returns:
        Number of rows inserted.
    """
    if not objects:
        return 0

    total = 0
    for i in range(0, len(objects), batch_size):
        batch = objects[i : i + batch_size]
        session.bulk_save_objects(batch)
        session.commit()
        total += len(batch)

    return total


def bulk_insert(
    session: Session,
    objects: Sequence[Any],
    table_name: str | None = None,
    batch_size: int = 1000,
) -> int:
    """Bulk insert objects using the best available strategy.

    Uses COPY for PostgreSQL, bulk_save_objects for other databases.

    Args:
        session: Database session.
        objects: List of ORM objects to insert.
        table_name: Name of the table (required for PostgreSQL COPY).
        batch_size: Number of objects per batch for non-PostgreSQL.

    Returns:
        Number of rows inserted.
    """
    if not objects:
        return 0

    engine = session.get_bind()

    if _is_postgresql(engine) and table_name:
        try:
            return bulk_insert_postgresql(session, table_name, objects)
        except Exception as e:
            logger.warning("COPY failed, falling back to bulk_save_objects: %s", e)

    return bulk_insert_sqlalchemy(session, objects, batch_size)


def optimized_seed_users(session: Session, count: int, batch_size: int = 1000) -> int:
    """Optimized user seeding with bulk insert."""
    from database.seeders.factories import UserFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        users = [UserFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, users, "users", batch_size)
        total += inserted

    return total


def optimized_seed_skills(session: Session, count: int, batch_size: int = 1000) -> int:
    """Optimized skill seeding with bulk insert."""
    from database.seeders.factories import SkillFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        skills = [SkillFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, skills, "skills", batch_size)
        total += inserted

    return total


def optimized_seed_companies(
    session: Session, count: int, batch_size: int = 1000
) -> int:
    """Optimized company seeding with bulk insert."""
    from database.seeders.factories import CompanyFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        companies = [CompanyFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, companies, "companies", batch_size)
        total += inserted

    return total


def optimized_seed_jobs(session: Session, count: int, batch_size: int = 1000) -> int:
    """Optimized job seeding with bulk insert."""
    from database.seeders.factories import JobFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        jobs = [JobFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, jobs, "jobs", batch_size)
        total += inserted

    return total


def optimized_seed_candidates(
    session: Session, count: int, batch_size: int = 1000
) -> int:
    """Optimized candidate seeding with bulk insert."""
    from database.seeders.factories import CandidateFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        candidates = [CandidateFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, candidates, "candidates", batch_size)
        total += inserted

    return total


def optimized_seed_applications(
    session: Session, count: int, batch_size: int = 1000
) -> int:
    """Optimized application seeding with bulk insert."""
    from database.seeders.factories import ApplicationFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        applications = [ApplicationFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, applications, "applications", batch_size)
        total += inserted

    return total


def optimized_seed_interviews(
    session: Session, count: int, batch_size: int = 1000
) -> int:
    """Optimized interview seeding with bulk insert."""
    from database.seeders.factories import InterviewFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        interviews = [InterviewFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, interviews, "interviews", batch_size)
        total += inserted

    return total


def optimized_seed_notes(session: Session, count: int, batch_size: int = 1000) -> int:
    """Optimized note seeding with bulk insert."""
    from database.seeders.factories import NoteFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        notes = [NoteFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, notes, "notes", batch_size)
        total += inserted

    return total


def optimized_seed_talent_pools(
    session: Session, count: int, batch_size: int = 1000
) -> int:
    """Optimized talent pool seeding with bulk insert."""
    from database.seeders.factories import TalentPoolFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        pools = [TalentPoolFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, pools, "talent_pools", batch_size)
        total += inserted

    return total


def optimized_seed_education(
    session: Session, count: int, batch_size: int = 1000
) -> int:
    """Optimized education seeding with bulk insert."""
    from database.seeders.factories import EducationFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        education = [EducationFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, education, "education", batch_size)
        total += inserted

    return total


def optimized_seed_experience(
    session: Session, count: int, batch_size: int = 1000
) -> int:
    """Optimized experience seeding with bulk insert."""
    from database.seeders.factories import ExperienceFactory

    total = 0
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        experience = [ExperienceFactory() for _ in range(batch_count)]
        inserted = bulk_insert(session, experience, "experience", batch_size)
        total += inserted

    return total


def run_optimized_full_seed(
    database_url: str, scale: str = "medium", batch_size: int = 1000
) -> dict[str, int]:
    """Run full database seed with optimized bulk inserts.

    Args:
        database_url: SQLAlchemy database URL.
        scale: Seed scale - 'small', 'medium', or 'large'.
        batch_size: Number of records per batch.

    Returns:
        Dictionary mapping seeder names to record counts.
    """
    scale_factors = {
        "small": 0.2,
        "medium": 0.5,
        "large": 1.0,
    }
    factor = scale_factors.get(scale, 0.5)

    engine = create_engine(database_url)
    from database.seeders.models import Base

    Base.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker

    session_local = sessionmaker(bind=engine)
    session = session_local()

    from database.seeders.factories import configure_session

    configure_session(session)

    results = {}

    try:
        seeders = [
            ("skills", optimized_seed_skills, 50),
            ("users", optimized_seed_users, 20),
            ("companies", optimized_seed_companies, 10),
            ("jobs", optimized_seed_jobs, 30),
            ("candidates", optimized_seed_candidates, 100),
            ("applications", optimized_seed_applications, 200),
            ("interviews", optimized_seed_interviews, 150),
            ("notes", optimized_seed_notes, 80),
            ("talent_pools", optimized_seed_talent_pools, 10),
            ("education", optimized_seed_education, 150),
            ("experience", optimized_seed_experience, 200),
        ]

        for name, seeder_func, base_count in seeders:
            count = max(1, int(base_count * factor))
            try:
                inserted = seeder_func(session, count, batch_size)
                results[name] = inserted
                logger.info("Optimized seed %s: %d records", name, inserted)
            except Exception as e:
                logger.error("Optimized seed %s failed: %s", name, e)
                results[name] = 0

    finally:
        session.close()

    return results

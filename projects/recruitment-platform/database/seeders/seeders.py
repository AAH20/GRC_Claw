"""Seeder scripts for generating test data."""
from __future__ import annotations

import argparse
import logging
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.seeders.factories import (
    ApplicationFactory,
    CandidateFactory,
    CompanyFactory,
    EducationFactory,
    ExperienceFactory,
    InterviewFactory,
    JobFactory,
    NoteFactory,
    SkillFactory,
    TalentPoolFactory,
    UserFactory,
)
from database.seeders.models import Base

logger = logging.getLogger(__name__)


def create_session(database_url: str) -> Session:
    """Create a database session and configure factories.

    Args:
        database_url: SQLAlchemy database URL.

    Returns:
        Configured session.
    """
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    # Configure all factories to use this session
    from database.seeders.factories import configure_session
    configure_session(session)
    return session


def seed_skills(session: Session, count: int = 50) -> list[Any]:
    """Seed skills.

    Args:
        session: Database session.
        count: Number of skills to create.

    Returns:
        List of created skills.
    """
    skills = [SkillFactory() for _ in range(count)]
    session.add_all(skills)
    session.commit()
    logger.info("Created %d skills", count)
    return skills


def seed_users(session: Session, count: int = 20) -> list[Any]:
    """Seed users.

    Args:
        session: Database session.
        count: Number of users to create.

    Returns:
        List of created users.
    """
    users = [UserFactory() for _ in range(count)]
    session.add_all(users)
    session.commit()
    logger.info("Created %d users", count)
    return users


def seed_companies(session: Session, count: int = 10) -> list[Any]:
    """Seed companies.

    Args:
        session: Database session.
        count: Number of companies to create.

    Returns:
        List of created companies.
    """
    companies = [CompanyFactory() for _ in range(count)]
    session.add_all(companies)
    session.commit()
    logger.info("Created %d companies", count)
    return companies


def seed_jobs(session: Session, count: int = 30) -> list[Any]:
    """Seed jobs.

    Args:
        session: Database session.
        count: Number of jobs to create.

    Returns:
        List of created jobs.
    """
    jobs = [JobFactory() for _ in range(count)]
    session.add_all(jobs)
    session.commit()
    logger.info("Created %d jobs", count)
    return jobs


def seed_candidates(session: Session, count: int = 100) -> list[Any]:
    """Seed candidates.

    Args:
        session: Database session.
        count: Number of candidates to create.

    Returns:
        List of created candidates.
    """
    candidates = [CandidateFactory() for _ in range(count)]
    session.add_all(candidates)
    session.commit()
    logger.info("Created %d candidates", count)
    return candidates


def seed_applications(session: Session, count: int = 200) -> list[Any]:
    """Seed applications.

    Args:
        session: Database session.
        count: Number of applications to create.

    Returns:
        List of created applications.
    """
    applications = [ApplicationFactory() for _ in range(count)]
    session.add_all(applications)
    session.commit()
    logger.info("Created %d applications", count)
    return applications


def seed_interviews(session: Session, count: int = 150) -> list[Any]:
    """Seed interviews.

    Args:
        session: Database session.
        count: Number of interviews to create.

    Returns:
        List of created interviews.
    """
    interviews = [InterviewFactory() for _ in range(count)]
    session.add_all(interviews)
    session.commit()
    logger.info("Created %d interviews", count)
    return interviews


def seed_notes(session: Session, count: int = 80) -> list[Any]:
    """Seed notes.

    Args:
        session: Database session.
        count: Number of notes to create.

    Returns:
        List of created notes.
    """
    notes = [NoteFactory() for _ in range(count)]
    session.add_all(notes)
    session.commit()
    logger.info("Created %d notes", count)
    return notes


def seed_talent_pools(session: Session, count: int = 10) -> list[Any]:
    """Seed talent pools.

    Args:
        session: Database session.
        count: Number of talent pools to create.

    Returns:
        List of created talent pools.
    """
    pools = [TalentPoolFactory() for _ in range(count)]
    session.add_all(pools)
    session.commit()
    logger.info("Created %d talent pools", count)
    return pools


def seed_education(session: Session, count: int = 150) -> list[Any]:
    """Seed education entries.

    Args:
        session: Database session.
        count: Number of education entries to create.

    Returns:
        List of created education entries.
    """
    education = [EducationFactory() for _ in range(count)]
    session.add_all(education)
    session.commit()
    logger.info("Created %d education entries", count)
    return education


def seed_experience(session: Session, count: int = 200) -> list[Any]:
    """Seed experience entries.

    Args:
        session: Database session.
        count: Number of experience entries to create.

    Returns:
        List of created experience entries.
    """
    experience = [ExperienceFactory() for _ in range(count)]
    session.add_all(experience)
    session.commit()
    logger.info("Created %d experience entries", count)
    return experience


def run_full_seed(database_url: str, scale: str = "medium") -> None:
    """Run full database seed.

    Args:
        database_url: SQLAlchemy database URL.
        scale: Seed scale - 'small', 'medium', or 'large'.
    """
    scale_factors = {
        "small": 0.2,
        "medium": 0.5,
        "large": 1.0,
    }
    factor = scale_factors.get(scale, 0.5)

    session = create_session(database_url)

    try:
        seed_skills(session, int(50 * factor))
        seed_users(session, int(20 * factor))
        seed_companies(session, int(10 * factor))
        seed_jobs(session, int(30 * factor))
        seed_candidates(session, int(100 * factor))
        seed_applications(session, int(200 * factor))
        seed_interviews(session, int(150 * factor))
        seed_notes(session, int(80 * factor))
        seed_talent_pools(session, int(10 * factor))
        seed_education(session, int(150 * factor))
        seed_experience(session, int(200 * factor))

        logger.info("Full seed completed at '%s' scale", scale)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    """CLI entry point for seeders."""
    parser = argparse.ArgumentParser(description="Database seeders for recruitment platform")
    parser.add_argument(
        "--database-url",
        default="sqlite:///./recruitment.db",
        help="SQLAlchemy database URL",
    )
    parser.add_argument(
        "--scale",
        choices=["small", "medium", "large"],
        default="medium",
        help="Seed scale factor",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    run_full_seed(args.database_url, args.scale)


if __name__ == "__main__":
    main()

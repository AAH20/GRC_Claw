"""Pytest fixtures for database testing."""

from __future__ import annotations

from collections.abc import Generator

import pytest
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
    configure_session,
)
from database.seeders.models import Base


@pytest.fixture(scope="session")
def db_engine():
    """Create a test database engine.

    Yields:
        SQLAlchemy engine for an in-memory SQLite database.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test.

    Args:
        db_engine: Session-scoped database engine.

    Yields:
        SQLAlchemy session with automatic rollback.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    # Configure all factories to use this session
    configure_session(session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def skill(db_session: Session):
    """Create a single skill.

    Args:
        db_session: Database session.

    Returns:
        Created Skill instance.
    """
    skill = SkillFactory()
    db_session.add(skill)
    db_session.commit()
    return skill


@pytest.fixture
def user(db_session: Session):
    """Create a single user.

    Args:
        db_session: Database session.

    Returns:
        Created User instance.
    """
    user = UserFactory()
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def company(db_session: Session):
    """Create a single company.

    Args:
        db_session: Database session.

    Returns:
        Created Company instance.
    """
    company = CompanyFactory()
    db_session.add(company)
    db_session.commit()
    return company


@pytest.fixture
def job(db_session: Session, company):
    """Create a single job.

    Args:
        db_session: Database session.
        company: Company fixture.

    Returns:
        Created Job instance.
    """
    job = JobFactory(company=company)
    db_session.add(job)
    db_session.commit()
    return job


@pytest.fixture
def candidate(db_session: Session):
    """Create a single candidate.

    Args:
        db_session: Database session.

    Returns:
        Created Candidate instance.
    """
    candidate = CandidateFactory()
    db_session.add(candidate)
    db_session.commit()
    return candidate


@pytest.fixture
def application(db_session: Session, candidate, job):
    """Create a single application.

    Args:
        db_session: Database session.
        candidate: Candidate fixture.
        job: Job fixture.

    Returns:
        Created Application instance.
    """
    application = ApplicationFactory(candidate=candidate, job=job)
    db_session.add(application)
    db_session.commit()
    return application


@pytest.fixture
def interview(db_session: Session, application, user):
    """Create a single interview.

    Args:
        db_session: Database session.
        application: Application fixture.
        user: User fixture.

    Returns:
        Created Interview instance.
    """
    interview = InterviewFactory(application=application, interviewer_id=user.id)
    db_session.add(interview)
    db_session.commit()
    return interview


@pytest.fixture
def education(db_session: Session, candidate):
    """Create a single education entry.

    Args:
        db_session: Database session.
        candidate: Candidate fixture.

    Returns:
        Created Education instance.
    """
    education = EducationFactory(candidate=candidate)
    db_session.add(education)
    db_session.commit()
    return education


@pytest.fixture
def experience(db_session: Session, candidate):
    """Create a single experience entry.

    Args:
        db_session: Database session.
        candidate: Candidate fixture.

    Returns:
        Created Experience instance.
    """
    experience = ExperienceFactory(candidate=candidate)
    db_session.add(experience)
    db_session.commit()
    return experience


@pytest.fixture
def note(db_session: Session, candidate, user):
    """Create a single note.

    Args:
        db_session: Database session.
        candidate: Candidate fixture.
        user: User fixture.

    Returns:
        Created Note instance.
    """
    note = NoteFactory(candidate_id=candidate.id, author_id=user.id)
    db_session.add(note)
    db_session.commit()
    return note


@pytest.fixture
def talent_pool(db_session: Session, user):
    """Create a single talent pool.

    Args:
        db_session: Database session.
        user: User fixture.

    Returns:
        Created TalentPool instance.
    """
    pool = TalentPoolFactory(created_by=user.id)
    db_session.add(pool)
    db_session.commit()
    return pool


@pytest.fixture
def skills_batch(db_session: Session, count: int = 10):
    """Create a batch of skills.

    Args:
        db_session: Database session.
        count: Number of skills to create.

    Returns:
        List of created Skill instances.
    """
    skills = [SkillFactory() for _ in range(count)]
    db_session.add_all(skills)
    db_session.commit()
    return skills


@pytest.fixture
def candidates_batch(db_session: Session, count: int = 20):
    """Create a batch of candidates.

    Args:
        db_session: Database session.
        count: Number of candidates to create.

    Returns:
        List of created Candidate instances.
    """
    candidates = [CandidateFactory() for _ in range(count)]
    db_session.add_all(candidates)
    db_session.commit()
    return candidates


@pytest.fixture
def jobs_batch(db_session: Session, count: int = 10):
    """Create a batch of jobs.

    Args:
        db_session: Database session.
        count: Number of jobs to create.

    Returns:
        List of created Job instances.
    """
    jobs = [JobFactory() for _ in range(count)]
    db_session.add_all(jobs)
    db_session.commit()
    return jobs

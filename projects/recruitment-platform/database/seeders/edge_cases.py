"""Edge case factories for testing boundary conditions, null values, and unicode."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

import factory
from faker import Faker

from database.seeders.factories import BaseFactory, CandidateFactory, UserFactory, configure_session
from database.seeders.models import (
    Application,
    Candidate,
    Company,
    Education,
    Experience,
    Interview,
    Job,
    Note,
    Skill,
    TalentPool,
    User,
)

fake = Faker()


class EdgeCaseUserFactory(BaseFactory):
    """Factory producing edge case User data."""

    class Meta:
        model = User

    email = factory.LazyAttribute(
        lambda _: f"edge_{random.randint(10000, 99999)}@test.com"
    )
    name = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "",  # empty string
                "A",  # single char
                "X" * 255,  # max length
                "José García Márquez",  # unicode
                "中村太郎",  # CJK
                "Иван Петров",  # Cyrillic
                "O'Brien-Smith",  # special chars
                "  spaces  ",  # leading/trailing spaces
            ]
        )
    )
    role = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "recruiter",
                "hiring_manager",
                "admin",
                "",
                "unknown",
                "SUPER_ADMIN",
                None,
            ]
        )
    )
    created_at = factory.LazyAttribute(
        lambda _: random.choice(
            [
                datetime(1970, 1, 1),  # epoch
                datetime(2038, 1, 19),  # near 32-bit limit
                datetime.utcnow(),
                None,
            ]
        )
    )


class EdgeCaseCompanyFactory(BaseFactory):
    """Factory producing edge case Company data."""

    class Meta:
        model = Company

    name = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "",
                "A",
                "X" * 255,
                "Müller & Söhne GmbH",  # unicode
                "北京科技有限公司",  # CJK
                "ООО Технологии",  # Cyrillic
                "Company <script>alert('xss')</script>",  # XSS attempt
                "  padded  ",
            ]
        )
    )
    industry = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "A",
                "X" * 100,
                "Technology",
                "Healthcare",
                "Unknown Industry",
            ]
        )
    )
    size = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "1-10",
                "5000+",
                "unknown",
            ]
        )
    )
    location = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 255,
                "Zürich, Switzerland",
                "東京, 日本",
            ]
        )
    )
    website = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "not-a-url",
                "http://",
                "https://x.com",
                "javascript:alert(1)",
            ]
        )
    )


class EdgeCaseJobFactory(BaseFactory):
    """Factory producing edge case Job data."""

    class Meta:
        model = Job

    title = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "",
                "A",
                "X" * 255,
                "Senior 工程师 (Engineer)",  # unicode
                "Разработчик ПО",  # Cyrillic
            ]
        )
    )
    description = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 10000,
                "Multi\nline\ndescription\twith\ttabs",
                "Description with <b>HTML</b> & entities",
            ]
        )
    )
    company = factory.SubFactory("database.seeders.factories.CompanyFactory")
    location = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 255,
                "Remote",
                "New York, NY",
            ]
        )
    )
    salary_min = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                0,
                -1,
                1,
                999999999.99,
                float("inf"),
                float("-inf"),
            ]
        )
    )
    salary_max = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                0,
                1,
                999999999.99,
                float("inf"),
            ]
        )
    )
    employment_type = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "full-time",
                "part-time",
                "contract",
                "internship",
                "freelance",
                "unknown",
            ]
        )
    )
    status = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "open",
                "closed",
                "draft",
                "on_hold",
                "archived",
                "unknown",
            ]
        )
    )
    posted_at = factory.LazyAttribute(
        lambda _: random.choice(
            [
                datetime(1970, 1, 1),
                datetime(2038, 1, 19),
                datetime.utcnow(),
                None,
            ]
        )
    )
    closes_at = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                datetime(1970, 1, 1),
                datetime(2038, 1, 19),
                datetime.utcnow() + timedelta(days=30),
            ]
        )
    )


class EdgeCaseCandidateFactory(BaseFactory):
    """Factory producing edge case Candidate data."""

    class Meta:
        model = Candidate

    email = factory.LazyAttribute(
        lambda _: f"edge_{random.randint(10000, 99999)}@test.com"
    )
    name = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "",
                "A",
                "X" * 255,
                "张伟",
                "John O'Brien",
                "María José Fernández",
                "田中 太郎",
                "Петр Иванов",
            ]
        )
    )
    phone = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "123",
                "+1-555-123-4567",
                "not-a-phone",
                "X" * 50,
            ]
        )
    )
    location = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 255,
                "San Francisco, CA",
            ]
        )
    )
    linkedin_url = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "not-a-url",
                "https://linkedin.com/in/test",
            ]
        )
    )
    resume_text = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 50000,
                "Resume with\nnewlines\tand\ttabs",
            ]
        )
    )
    years_experience = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                0,
                -1,
                0.5,
                50,
                100,
                float("inf"),
            ]
        )
    )
    current_title = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 255,
                "Software Engineer",
            ]
        )
    )
    created_at = factory.LazyAttribute(
        lambda _: random.choice(
            [
                datetime(1970, 1, 1),
                datetime(2038, 1, 19),
                datetime.utcnow(),
                None,
            ]
        )
    )


class EdgeCaseApplicationFactory(BaseFactory):
    """Factory producing edge case Application data."""

    class Meta:
        model = Application

    candidate = factory.SubFactory("database.seeders.factories.CandidateFactory")
    job = factory.SubFactory("database.seeders.factories.JobFactory")
    status = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "applied",
                "screening",
                "interview",
                "offer",
                "hired",
                "rejected",
                "withdrawn",
                "unknown",
            ]
        )
    )
    match_score = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                0.0,
                1.0,
                -0.01,
                1.01,
                0.5,
                float("inf"),
                float("-inf"),
            ]
        )
    )
    applied_at = factory.LazyAttribute(
        lambda _: random.choice(
            [
                datetime(1970, 1, 1),
                datetime(2038, 1, 19),
                datetime.utcnow(),
                None,
            ]
        )
    )


class EdgeCaseInterviewFactory(BaseFactory):
    """Factory producing edge case Interview data."""

    class Meta:
        model = Interview

    application = factory.SubFactory("database.seeders.factories.ApplicationFactory")
    interviewer_id = factory.LazyAttribute(lambda _: UserFactory().id)
    scheduled_at = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                datetime(1970, 1, 1),
                datetime(2038, 1, 19),
                datetime.utcnow() + timedelta(hours=1),
            ]
        )
    )
    duration_minutes = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                0,
                1,
                30,
                45,
                60,
                90,
                120,
                480,
                1440,
                -30,
            ]
        )
    )
    interview_type = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "phone_screen",
                "technical",
                "behavioral",
                "panel",
                "final",
                "unknown",
            ]
        )
    )
    status = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "scheduled",
                "completed",
                "cancelled",
                "no_show",
                "rescheduled",
            ]
        )
    )
    feedback = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 10000,
                "Feedback with\nnewlines\tand\ttabs",
            ]
        )
    )
    rating = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                0,
                1,
                3,
                5,
                6,
                10,
                -1,
            ]
        )
    )


class EdgeCaseSkillFactory(BaseFactory):
    """Factory producing edge case Skill data."""

    class Meta:
        model = Skill

    name = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "",
                "A",
                "X" * 100,
                "C++",
                "C#",
                "Node.js",
                "Objective-C",
                "机器学习",
                "データベース",
            ]
        )
    )
    category = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "programming",
                "framework",
                "database",
                "cloud",
                "devops",
                "design",
                "management",
                "soft_skill",
                "unknown",
            ]
        )
    )


class EdgeCaseEducationFactory(BaseFactory):
    """Factory producing edge case Education data."""

    class Meta:
        model = Education

    candidate = factory.SubFactory("database.seeders.factories.CandidateFactory")
    institution = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 255,
                "MIT",
                "東京大学",
            ]
        )
    )
    degree = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "Bachelor of Science",
                "Master of Science",
                "PhD",
                "Associate Degree",
                "Unknown Degree",
            ]
        )
    )
    field_of_study = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "Computer Science",
                "Computer Science",
                "未知の分野",
            ]
        )
    )
    start_year = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                1900,
                2000,
                2020,
                2024,
                2030,
            ]
        )
    )
    end_year = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                1900,
                2004,
                2024,
                2030,
            ]
        )
    )
    gpa = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                0.0,
                2.5,
                4.0,
                5.0,
                -1.0,
            ]
        )
    )


class EdgeCaseExperienceFactory(BaseFactory):
    """Factory producing edge case Experience data."""

    class Meta:
        model = Experience

    candidate = factory.SubFactory("database.seeders.factories.CandidateFactory")
    company = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 255,
                "Google",
                "Microsoft",
            ]
        )
    )
    title = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 255,
                "Software Engineer",
            ]
        )
    )
    description = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 10000,
            ]
        )
    )
    start_date = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                datetime(1970, 1, 1),
                datetime(2020, 1, 1),
            ]
        )
    )
    end_date = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                datetime(2019, 1, 1),
                datetime(2024, 1, 1),
            ]
        )
    )
    is_current = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                True,
                False,
            ]
        )
    )


class EdgeCaseNoteFactory(BaseFactory):
    """Factory producing edge case Note data."""

    class Meta:
        model = Note

    candidate_id = factory.LazyAttribute(lambda _: CandidateFactory().id)
    author_id = factory.LazyAttribute(lambda _: UserFactory().id)
    content = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 10000,
                "Note with\nnewlines\tand\ttabs",
                "Note with <b>HTML</b> & entities",
            ]
        )
    )
    created_at = factory.LazyAttribute(
        lambda _: random.choice(
            [
                datetime(1970, 1, 1),
                datetime(2038, 1, 19),
                datetime.utcnow(),
                None,
            ]
        )
    )


class EdgeCaseTalentPoolFactory(BaseFactory):
    """Factory producing edge case TalentPool data."""

    class Meta:
        model = TalentPool

    name = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "",
                "A",
                "X" * 255,
                "Senior Engineers 2024",
                "Top Talent — 最高の人材",
            ]
        )
    )
    description = factory.LazyAttribute(
        lambda _: random.choice(
            [
                None,
                "",
                "X" * 10000,
            ]
        )
    )
    created_by = factory.LazyAttribute(lambda _: UserFactory().id)
    created_at = factory.LazyAttribute(
        lambda _: random.choice(
            [
                datetime(1970, 1, 1),
                datetime(2038, 1, 19),
                datetime.utcnow(),
                None,
            ]
        )
    )


def seed_edge_cases(session, count_per_type: int = 5) -> dict[str, list[Any]]:
    """Seed edge case data for all entity types.

    Args:
        session: Database session.
        count_per_type: Number of edge case records per entity type.

    Returns:
        Dictionary mapping entity type names to lists of created objects.
    """
    configure_session(session)
    results: dict[str, list[Any]] = {}

    edge_factories = {
        "users": EdgeCaseUserFactory,
        "companies": EdgeCaseCompanyFactory,
        "jobs": EdgeCaseJobFactory,
        "candidates": EdgeCaseCandidateFactory,
        "applications": EdgeCaseApplicationFactory,
        "interviews": EdgeCaseInterviewFactory,
        "skills": EdgeCaseSkillFactory,
        "education": EdgeCaseEducationFactory,
        "experience": EdgeCaseExperienceFactory,
        "notes": EdgeCaseNoteFactory,
        "talent_pools": EdgeCaseTalentPoolFactory,
    }

    for entity_name, factory_class in edge_factories.items():
        objects = []
        for _ in range(count_per_type):
            try:
                obj = factory_class()
                session.add(obj)
                objects.append(obj)
            except Exception:
                # Some edge cases may fail validation — that's expected
                session.rollback()
                continue
        session.commit()
        results[entity_name] = objects

    return results

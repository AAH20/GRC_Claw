"""factory_boy factories for all recruitment platform models."""

from __future__ import annotations

import random
from datetime import datetime

import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

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


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration.

    The session is set at runtime by seeders.py or conftest.py via
    ``configure_session()``.
    """

    class Meta:
        abstract = True
        sqlalchemy_session = None


def configure_session(session) -> None:
    """Set the database session for all factories.

    Args:
        session: SQLAlchemy session to use for object creation.
    """
    for factory_class in BaseFactory.__subclasses__():
        factory_class._meta.sqlalchemy_session = session


class UserFactory(BaseFactory):
    """Factory for User model."""

    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    name = factory.LazyAttribute(lambda _: fake.name())
    role = factory.LazyAttribute(
        lambda _: random.choice(["recruiter", "hiring_manager", "admin"])
    )
    created_at = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-2y", end_date="now")
    )
    updated_at = factory.LazyAttribute(lambda _: datetime.utcnow())


class CompanyFactory(BaseFactory):
    """Factory for Company model."""

    class Meta:
        model = Company

    name = factory.LazyAttribute(lambda _: fake.company())
    industry = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "Technology",
                "Healthcare",
                "Finance",
                "Education",
                "Manufacturing",
                "Retail",
                "Consulting",
                "Media",
            ]
        )
    )
    size = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "1-10",
                "11-50",
                "51-200",
                "201-500",
                "501-1000",
                "1001-5000",
                "5000+",
            ]
        )
    )
    location = factory.LazyAttribute(lambda _: fake.city())
    website = factory.LazyAttribute(lambda _: fake.url())
    created_at = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-3y", end_date="now")
    )


class SkillFactory(BaseFactory):
    """Factory for Skill model."""

    class Meta:
        model = Skill

    name = factory.LazyAttribute(lambda _: fake.unique.word().capitalize())
    category = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "programming",
                "framework",
                "database",
                "cloud",
                "devops",
                "design",
                "management",
                "soft_skill",
            ]
        )
    )


class JobFactory(BaseFactory):
    """Factory for Job model."""

    class Meta:
        model = Job

    title = factory.LazyAttribute(lambda _: fake.job())
    description = factory.LazyAttribute(lambda _: fake.paragraph(nb_sentences=5))
    company = factory.SubFactory(CompanyFactory)
    location = factory.LazyAttribute(lambda _: fake.city())
    salary_min = factory.LazyAttribute(lambda _: random.randint(50000, 120000))
    salary_max = factory.LazyAttribute(lambda _: random.randint(120000, 250000))
    employment_type = factory.LazyAttribute(
        lambda _: random.choice(["full-time", "part-time", "contract", "internship"])
    )
    status = factory.LazyAttribute(
        lambda _: random.choice(["open", "closed", "draft", "on_hold"])
    )
    posted_at = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-6m", end_date="now")
    )
    closes_at = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="now", end_date="+3m")
    )

    @factory.post_generation
    def skills(obj, create, extracted, **kwargs):  # noqa: N805
        """Add skills to the job."""
        if not create:
            return
        if extracted:
            for skill in extracted:
                obj.skills.append(skill)
        else:
            for _ in range(random.randint(2, 6)):
                obj.skills.append(SkillFactory())


class CandidateFactory(BaseFactory):
    """Factory for Candidate model."""

    class Meta:
        model = Candidate

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    name = factory.LazyAttribute(lambda _: fake.name())
    phone = factory.LazyAttribute(lambda _: fake.phone_number())
    location = factory.LazyAttribute(lambda _: fake.city())
    linkedin_url = factory.LazyAttribute(
        lambda _: f"https://linkedin.com/in/{fake.user_name()}"
    )
    resume_text = factory.LazyAttribute(lambda _: fake.paragraph(nb_sentences=10))
    years_experience = factory.LazyAttribute(lambda _: random.uniform(0, 20))
    current_title = factory.LazyAttribute(lambda _: fake.job())
    created_at = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-2y", end_date="now")
    )

    @factory.post_generation
    def skills(obj, create, extracted, **kwargs):  # noqa: N805
        """Add skills to the candidate."""
        if not create:
            return
        if extracted:
            for skill in extracted:
                obj.skills.append(skill)
        else:
            for _ in range(random.randint(3, 10)):
                obj.skills.append(SkillFactory())

    @factory.post_generation
    def education(obj, create, extracted, **kwargs):  # noqa: N805
        """Add education entries to the candidate."""
        if not create:
            return
        if extracted:
            for edu in extracted:
                obj.education.append(edu)
        else:
            for _ in range(random.randint(1, 3)):
                obj.education.append(EducationFactory(candidate=obj))

    @factory.post_generation
    def experience(obj, create, extracted, **kwargs):  # noqa: N805
        """Add experience entries to the candidate."""
        if not create:
            return
        if extracted:
            for exp in extracted:
                obj.experience.append(exp)
        else:
            for _ in range(random.randint(1, 4)):
                obj.experience.append(ExperienceFactory(candidate=obj))


class EducationFactory(BaseFactory):
    """Factory for Education model."""

    class Meta:
        model = Education

    candidate = factory.SubFactory(CandidateFactory)
    institution = factory.LazyAttribute(lambda _: fake.company())
    degree = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "Bachelor of Science",
                "Master of Science",
                "Bachelor of Arts",
                "Master of Arts",
                "PhD",
                "Associate Degree",
            ]
        )
    )
    field_of_study = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "Computer Science",
                "Business Administration",
                "Engineering",
                "Mathematics",
                "Physics",
                "Economics",
                "Psychology",
            ]
        )
    )
    start_year = factory.LazyAttribute(lambda _: random.randint(2000, 2020))
    end_year = factory.LazyAttribute(lambda _: random.randint(2004, 2024))
    gpa = factory.LazyAttribute(lambda _: round(random.uniform(2.5, 4.0), 2))


class ExperienceFactory(BaseFactory):
    """Factory for Experience model."""

    class Meta:
        model = Experience

    candidate = factory.SubFactory(CandidateFactory)
    company = factory.LazyAttribute(lambda _: fake.company())
    title = factory.LazyAttribute(lambda _: fake.job())
    description = factory.LazyAttribute(lambda _: fake.paragraph(nb_sentences=3))
    start_date = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-10y", end_date="now")
    )
    end_date = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-5y", end_date="now")
    )
    is_current = factory.LazyAttribute(lambda _: random.choice([True, False]))


class ApplicationFactory(BaseFactory):
    """Factory for Application model."""

    class Meta:
        model = Application

    candidate = factory.SubFactory(CandidateFactory)
    job = factory.SubFactory(JobFactory)
    status = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "applied",
                "screening",
                "interview",
                "offer",
                "hired",
                "rejected",
            ]
        )
    )
    match_score = factory.LazyAttribute(lambda _: round(random.uniform(0.0, 1.0), 2))
    applied_at = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-3m", end_date="now")
    )


class InterviewFactory(BaseFactory):
    """Factory for Interview model."""

    class Meta:
        model = Interview

    application = factory.SubFactory(ApplicationFactory)
    interviewer_id = factory.LazyAttribute(lambda _: UserFactory().id)
    scheduled_at = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="now", end_date="+2w")
    )
    duration_minutes = factory.LazyAttribute(
        lambda _: random.choice([30, 45, 60, 90, 120])
    )
    interview_type = factory.LazyAttribute(
        lambda _: random.choice(
            [
                "phone_screen",
                "technical",
                "behavioral",
                "panel",
                "final",
            ]
        )
    )
    status = factory.LazyAttribute(
        lambda _: random.choice(["scheduled", "completed", "cancelled", "no_show"])
    )
    feedback = factory.LazyAttribute(lambda _: fake.paragraph(nb_sentences=3))
    rating = factory.LazyAttribute(lambda _: random.randint(1, 5))


class NoteFactory(BaseFactory):
    """Factory for Note model."""

    class Meta:
        model = Note

    candidate_id = factory.LazyAttribute(lambda _: CandidateFactory().id)
    author_id = factory.LazyAttribute(lambda _: UserFactory().id)
    content = factory.LazyAttribute(lambda _: fake.paragraph(nb_sentences=2))
    created_at = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-1y", end_date="now")
    )


class TalentPoolFactory(BaseFactory):
    """Factory for TalentPool model."""

    class Meta:
        model = TalentPool

    name = factory.LazyAttribute(lambda _: fake.bs().title())
    description = factory.LazyAttribute(lambda _: fake.paragraph(nb_sentences=2))
    created_by = factory.LazyAttribute(lambda _: UserFactory().id)
    created_at = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-1y", end_date="now")
    )

    @factory.post_generation
    def members(obj, create, extracted, **kwargs):  # noqa: N805
        """Add members to the talent pool."""
        if not create:
            return
        if extracted:
            for member in extracted:
                obj.members.append(member)
        else:
            for _ in range(random.randint(5, 20)):
                obj.members.append(CandidateFactory())

"""SQLAlchemy models for the recruitment platform database."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Association tables
candidate_skills = Table(
    "candidate_skills",
    Base.metadata,
    Column("candidate_id", Integer, ForeignKey("candidates.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
    Column("proficiency", String(20)),
    Column("years_experience", Float),
)

job_skills = Table(
    "job_skills",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("jobs.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
    Column("required", Boolean, default=True),
    Column("min_proficiency", String(20)),
)

talent_pool_members = Table(
    "talent_pool_members",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("talent_pools.id"), primary_key=True),
    Column("candidate_id", Integer, ForeignKey("candidates.id"), primary_key=True),
    Column("added_at", DateTime, default=datetime.utcnow),
    Column("notes", Text),
)


class User(Base):
    """Platform user (recruiter, hiring manager, admin)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="recruiter")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Company(Base):
    """Company/organization posting jobs."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(100))
    size = Column(String(50))
    location = Column(String(255))
    website = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class Job(Base):
    """Job posting."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    location = Column(String(255))
    salary_min = Column(Float)
    salary_max = Column(Float)
    employment_type = Column(String(50), default="full-time")
    status = Column(String(50), default="open")
    posted_at = Column(DateTime, default=datetime.utcnow)
    closes_at = Column(DateTime)

    company = relationship("Company", back_populates="jobs")
    skills = relationship("Skill", secondary=job_skills, back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    """Job candidate."""

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50))
    location = Column(String(255))
    linkedin_url = Column(String(255))
    resume_text = Column(Text)
    years_experience = Column(Float)
    current_title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("Skill", secondary=candidate_skills, back_populates="candidates")
    education = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    experience = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    talent_pools = relationship(
        "TalentPool", secondary=talent_pool_members, back_populates="members"
    )


class Application(Base):
    """Job application linking a candidate to a job."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(String(50), default="applied")
    match_score = Column(Float)
    applied_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")


class Interview(Base):
    """Interview scheduled for an application."""

    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    interviewer_id = Column(Integer, ForeignKey("users.id"))
    scheduled_at = Column(DateTime)
    duration_minutes = Column(Integer, default=60)
    interview_type = Column(String(50), default="phone_screen")
    status = Column(String(50), default="scheduled")
    feedback = Column(Text)
    rating = Column(Integer)

    application = relationship("Application", back_populates="interviews")


class Skill(Base):
    """Skill that candidates have and jobs require."""

    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50))

    candidates = relationship("Candidate", secondary=candidate_skills, back_populates="skills")
    jobs = relationship("Job", secondary=job_skills, back_populates="skills")


class Education(Base):
    """Candidate education entry."""

    __tablename__ = "education"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    institution = Column(String(255))
    degree = Column(String(255))
    field_of_study = Column(String(255))
    start_year = Column(Integer)
    end_year = Column(Integer)
    gpa = Column(Float)

    candidate = relationship("Candidate", back_populates="education")


class Experience(Base):
    """Candidate work experience entry."""

    __tablename__ = "experience"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    company = Column(String(255))
    title = Column(String(255))
    description = Column(Text)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_current = Column(Boolean, default=False)

    candidate = relationship("Candidate", back_populates="experience")


class Note(Base):
    """Note about a candidate."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class TalentPool(Base):
    """Curated pool of candidates."""

    __tablename__ = "talent_pools"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship(
        "Candidate", secondary=talent_pool_members, back_populates="talent_pools"
    )

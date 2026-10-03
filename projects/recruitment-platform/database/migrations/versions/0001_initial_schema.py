"""Initial schema for recruitment platform

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-03 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # Create enum types
    application_status = sa.Enum(
        "draft",
        "submitted",
        "screening",
        "interview",
        "assessment",
        "offer",
        "hired",
        "rejected",
        "withdrawn",
        name="application_status",
    )
    interview_status = sa.Enum(
        "scheduled",
        "confirmed",
        "in_progress",
        "completed",
        "cancelled",
        "no_show",
        "rescheduled",
        name="interview_status",
    )
    interview_type = sa.Enum(
        "phone_screen",
        "video",
        "onsite",
        "technical",
        "behavioral",
        "panel",
        name="interview_type",
    )
    assessment_status = sa.Enum(
        "pending",
        "in_progress",
        "submitted",
        "evaluated",
        "expired",
        name="assessment_status",
    )
    assessment_type = sa.Enum(
        "coding",
        "personality",
        "cognitive",
        "technical_quiz",
        "case_study",
        "take_home",
        name="assessment_type",
    )
    talent_pool_type = sa.Enum(
        "active", "passive", "alumni", "referred", "custom", name="talent_pool_type"
    )
    employment_type = sa.Enum(
        "full_time",
        "part_time",
        "contract",
        "internship",
        "freelance",
        name="employment_type",
    )
    experience_type = sa.Enum(
        "full_time",
        "part_time",
        "contract",
        "internship",
        "freelance",
        "volunteer",
        name="experience_type",
    )
    education_level = sa.Enum(
        "high_school",
        "associate",
        "bachelor",
        "master",
        "doctorate",
        "postdoc",
        "certificate",
        "bootcamp",
        name="education_level",
    )
    event_type = sa.Enum(
        "page_view",
        "job_view",
        "job_apply_start",
        "job_apply_complete",
        "candidate_signup",
        "candidate_login",
        "search_query",
        "filter_applied",
        "email_open",
        "email_click",
        "interview_scheduled",
        "interview_completed",
        "assessment_started",
        "assessment_completed",
        "offer_extended",
        "offer_accepted",
        "offer_declined",
        name="event_type",
    )
    audit_action = sa.Enum(
        "INSERT",
        "UPDATE",
        "DELETE",
        "TRUNCATE",
        "LOGIN",
        "LOGOUT",
        "EXPORT",
        name="audit_action",
    )

    # Enum types are created automatically by SQLAlchemy when used in create_table

    # employers
    op.create_table(
        "employers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("website", sa.String(500)),
        sa.Column("industry", sa.String(100)),
        sa.Column("company_size", sa.String(50)),
        sa.Column("founded_year", sa.Integer),
        sa.Column("logo_url", sa.String(1000)),
        sa.Column("headquarters", postgresql.JSONB, server_default="{}"),
        sa.Column("social_links", postgresql.JSONB, server_default="{}"),
        sa.Column("settings", postgresql.JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("search_vector", postgresql.TSVECTOR),
    )
    op.create_index(
        "idx_employers_name",
        "employers",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_index("idx_employers_slug", "employers", ["slug"])
    op.create_index("idx_employers_industry", "employers", ["industry"])
    op.create_index(
        "idx_employers_is_active",
        "employers",
        ["is_active"],
        postgresql_where=sa.text("is_active = TRUE"),
    )
    op.create_index(
        "idx_employers_search", "employers", ["search_vector"], postgresql_using="gin"
    )
    op.create_index(
        "idx_employers_headquarters",
        "employers",
        ["headquarters"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_employers_social_links",
        "employers",
        ["social_links"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_employers_settings", "employers", ["settings"], postgresql_using="gin"
    )

    # recruiters
    op.create_table(
        "recruiters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "employer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("title", sa.String(150)),
        sa.Column("department", sa.String(100)),
        sa.Column("phone", sa.String(50)),
        sa.Column("avatar_url", sa.String(1000)),
        sa.Column("bio", sa.Text),
        sa.Column("specialties", postgresql.JSONB, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("search_vector", postgresql.TSVECTOR),
    )
    op.create_index("idx_recruiters_employer_id", "recruiters", ["employer_id"])
    op.create_index("idx_recruiters_email", "recruiters", ["email"])
    op.create_index("idx_recruiters_user_id", "recruiters", ["user_id"])
    op.create_index(
        "idx_recruiters_is_active",
        "recruiters",
        ["is_active"],
        postgresql_where=sa.text("is_active = TRUE"),
    )
    op.create_index(
        "idx_recruiters_search", "recruiters", ["search_vector"], postgresql_using="gin"
    )
    op.create_index(
        "idx_recruiters_specialties",
        "recruiters",
        ["specialties"],
        postgresql_using="gin",
    )

    # candidates
    op.create_table(
        "candidates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(50)),
        sa.Column("date_of_birth", sa.Date),
        sa.Column("gender", sa.String(50)),
        sa.Column("nationality", sa.String(100)),
        sa.Column("current_title", sa.String(200)),
        sa.Column("current_company", sa.String(200)),
        sa.Column("current_location", sa.String(200)),
        sa.Column("address", postgresql.JSONB, server_default="{}"),
        sa.Column("social_profiles", postgresql.JSONB, server_default="{}"),
        sa.Column("resume_url", sa.String(1000)),
        sa.Column("resume_text", sa.Text),
        sa.Column("cover_letter", sa.Text),
        sa.Column("portfolio_url", sa.String(1000)),
        sa.Column("linkedin_url", sa.String(1000)),
        sa.Column("github_url", sa.String(1000)),
        sa.Column("website_url", sa.String(1000)),
        sa.Column("preferred_location", sa.String(200)),
        sa.Column("preferred_salary", postgresql.JSONB, server_default="{}"),
        sa.Column("notice_period_days", sa.Integer),
        sa.Column("years_experience", sa.Numeric(4, 1)),
        sa.Column("summary", sa.Text),
        sa.Column("languages", postgresql.JSONB, server_default="[]"),
        sa.Column("certifications", postgresql.JSONB, server_default="[]"),
        sa.Column("preferences", postgresql.JSONB, server_default="{}"),
        sa.Column("source", sa.String(100)),
        sa.Column("referral_code", sa.String(100)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "is_anonymous", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "email_verified", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "phone_verified", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column("profile_completeness", sa.Integer, server_default="0"),
        sa.Column("last_active_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("search_vector", postgresql.TSVECTOR),
    )
    op.create_index("idx_candidates_email", "candidates", ["email"])
    op.create_index(
        "idx_candidates_current_title",
        "candidates",
        ["current_title"],
        postgresql_using="gin",
        postgresql_ops={"current_title": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_candidates_current_company",
        "candidates",
        ["current_company"],
        postgresql_using="gin",
        postgresql_ops={"current_company": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_candidates_current_location",
        "candidates",
        ["current_location"],
        postgresql_using="gin",
        postgresql_ops={"current_location": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_candidates_is_active",
        "candidates",
        ["is_active"],
        postgresql_where=sa.text("is_active = TRUE"),
    )
    op.create_index("idx_candidates_source", "candidates", ["source"])
    op.create_index(
        "idx_candidates_created_at",
        "candidates",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_candidates_last_active_at",
        "candidates",
        ["last_active_at"],
        postgresql_using="btree",
        postgresql_ops={"last_active_at": "DESC"},
    )
    op.create_index(
        "idx_candidates_search", "candidates", ["search_vector"], postgresql_using="gin"
    )
    op.create_index(
        "idx_candidates_address", "candidates", ["address"], postgresql_using="gin"
    )
    op.create_index(
        "idx_candidates_social_profiles",
        "candidates",
        ["social_profiles"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_candidates_preferred_salary",
        "candidates",
        ["preferred_salary"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_candidates_languages", "candidates", ["languages"], postgresql_using="gin"
    )
    op.create_index(
        "idx_candidates_certifications",
        "candidates",
        ["certifications"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_candidates_preferences",
        "candidates",
        ["preferences"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_candidates_years_experience", "candidates", ["years_experience"]
    )

    # jobs
    op.create_table(
        "jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "employer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "posted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("slug", sa.String(350), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("responsibilities", sa.Text),
        sa.Column("requirements", sa.Text),
        sa.Column("nice_to_have", sa.Text),
        sa.Column(
            "employment_type",
            employment_type,
            nullable=False,
            server_default="full_time",
        ),
        sa.Column("experience_level", sa.String(50)),
        sa.Column("department", sa.String(100)),
        sa.Column(
            "location_type", sa.String(50), nullable=False, server_default="onsite"
        ),
        sa.Column("location", postgresql.JSONB, server_default="{}"),
        sa.Column("salary_range", postgresql.JSONB, server_default="{}"),
        sa.Column("benefits", postgresql.JSONB, server_default="[]"),
        sa.Column("skills_required", postgresql.JSONB, server_default="[]"),
        sa.Column("skills_preferred", postgresql.JSONB, server_default="[]"),
        sa.Column("application_url", sa.String(1000)),
        sa.Column("application_email", sa.String(255)),
        sa.Column("openings", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_remote", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_urgent", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("views_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("applications_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("closed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("search_vector", postgresql.TSVECTOR),
    )
    op.create_index("idx_jobs_employer_id", "jobs", ["employer_id"])
    op.create_index("idx_jobs_posted_by", "jobs", ["posted_by"])
    op.create_index("idx_jobs_slug", "jobs", ["slug"])
    op.create_index(
        "idx_jobs_title",
        "jobs",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_index("idx_jobs_department", "jobs", ["department"])
    op.create_index("idx_jobs_employment_type", "jobs", ["employment_type"])
    op.create_index("idx_jobs_experience_level", "jobs", ["experience_level"])
    op.create_index(
        "idx_jobs_is_active",
        "jobs",
        ["is_active"],
        postgresql_where=sa.text("is_active = TRUE"),
    )
    op.create_index(
        "idx_jobs_is_featured",
        "jobs",
        ["is_featured"],
        postgresql_where=sa.text("is_featured = TRUE"),
    )
    op.create_index(
        "idx_jobs_is_remote",
        "jobs",
        ["is_remote"],
        postgresql_where=sa.text("is_remote = TRUE"),
    )
    op.create_index(
        "idx_jobs_published_at",
        "jobs",
        ["published_at"],
        postgresql_using="btree",
        postgresql_ops={"published_at": "DESC"},
    )
    op.create_index("idx_jobs_expires_at", "jobs", ["expires_at"])
    op.create_index(
        "idx_jobs_created_at",
        "jobs",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_jobs_views_count",
        "jobs",
        ["views_count"],
        postgresql_using="btree",
        postgresql_ops={"views_count": "DESC"},
    )
    op.create_index(
        "idx_jobs_applications_count",
        "jobs",
        ["applications_count"],
        postgresql_using="btree",
        postgresql_ops={"applications_count": "DESC"},
    )
    op.create_index(
        "idx_jobs_search", "jobs", ["search_vector"], postgresql_using="gin"
    )
    op.create_index("idx_jobs_location", "jobs", ["location"], postgresql_using="gin")
    op.create_index(
        "idx_jobs_salary_range", "jobs", ["salary_range"], postgresql_using="gin"
    )
    op.create_index("idx_jobs_benefits", "jobs", ["benefits"], postgresql_using="gin")
    op.create_index(
        "idx_jobs_skills_required", "jobs", ["skills_required"], postgresql_using="gin"
    )
    op.create_index(
        "idx_jobs_skills_preferred",
        "jobs",
        ["skills_preferred"],
        postgresql_using="gin",
    )

    # applications
    op.create_table(
        "applications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "status", application_status, nullable=False, server_default="submitted"
        ),
        sa.Column("status_history", postgresql.JSONB, server_default="[]"),
        sa.Column("cover_letter", sa.Text),
        sa.Column("custom_answers", postgresql.JSONB, server_default="{}"),
        sa.Column("source", sa.String(100)),
        sa.Column("referral_code", sa.String(100)),
        sa.Column(
            "rating", sa.Integer, sa.CheckConstraint("rating >= 1 AND rating <= 5")
        ),
        sa.Column("internal_notes", sa.Text),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("rejection_category", sa.String(100)),
        sa.Column("offer_details", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "applied_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("decided_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("candidate_id", "job_id"),
    )
    op.create_index("idx_applications_candidate_id", "applications", ["candidate_id"])
    op.create_index("idx_applications_job_id", "applications", ["job_id"])
    op.create_index("idx_applications_recruiter_id", "applications", ["recruiter_id"])
    op.create_index("idx_applications_status", "applications", ["status"])
    op.create_index(
        "idx_applications_applied_at",
        "applications",
        ["applied_at"],
        postgresql_using="btree",
        postgresql_ops={"applied_at": "DESC"},
    )
    op.create_index(
        "idx_applications_reviewed_at",
        "applications",
        ["reviewed_at"],
        postgresql_using="btree",
        postgresql_ops={"reviewed_at": "DESC"},
    )
    op.create_index(
        "idx_applications_decided_at",
        "applications",
        ["decided_at"],
        postgresql_using="btree",
        postgresql_ops={"decided_at": "DESC"},
    )
    op.create_index("idx_applications_source", "applications", ["source"])
    op.create_index("idx_applications_rating", "applications", ["rating"])
    op.create_index(
        "idx_applications_status_history",
        "applications",
        ["status_history"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_applications_custom_answers",
        "applications",
        ["custom_answers"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_applications_offer_details",
        "applications",
        ["offer_details"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_applications_candidate_job", "applications", ["candidate_id", "job_id"]
    )
    op.create_index("idx_applications_job_status", "applications", ["job_id", "status"])

    # interviews
    op.create_table(
        "interviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "interviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("interview_type", interview_type, nullable=False),
        sa.Column(
            "status", interview_status, nullable=False, server_default="scheduled"
        ),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("location", sa.String(500)),
        sa.Column("meeting_url", sa.String(1000)),
        sa.Column("meeting_id", sa.String(255)),
        sa.Column("feedback", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "overall_rating",
            sa.Integer,
            sa.CheckConstraint("overall_rating >= 1 AND overall_rating <= 5"),
        ),
        sa.Column("recommendation", sa.String(50)),
        sa.Column("notes", sa.Text),
        sa.Column("candidate_notes", sa.Text),
        sa.Column("no_show_reason", sa.Text),
        sa.Column(
            "rescheduled_from",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interviews.id", ondelete="SET NULL"),
        ),
        sa.Column("reminder_sent_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_interviews_application_id", "interviews", ["application_id"])
    op.create_index("idx_interviews_interviewer_id", "interviews", ["interviewer_id"])
    op.create_index("idx_interviews_status", "interviews", ["status"])
    op.create_index("idx_interviews_scheduled_at", "interviews", ["scheduled_at"])
    op.create_index("idx_interviews_interview_type", "interviews", ["interview_type"])
    op.create_index("idx_interviews_overall_rating", "interviews", ["overall_rating"])
    op.create_index(
        "idx_interviews_feedback", "interviews", ["feedback"], postgresql_using="gin"
    )
    op.create_index(
        "idx_interviews_application_scheduled",
        "interviews",
        ["application_id", "scheduled_at"],
        postgresql_using="btree",
        postgresql_ops={"scheduled_at": "DESC"},
    )

    # assessments
    op.create_table(
        "assessments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assessment_type", assessment_type, nullable=False),
        sa.Column(
            "status", assessment_status, nullable=False, server_default="pending"
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("instructions", sa.Text),
        sa.Column("duration_minutes", sa.Integer),
        sa.Column("max_score", sa.Numeric(6, 2)),
        sa.Column("passing_score", sa.Numeric(6, 2)),
        sa.Column("questions", postgresql.JSONB, server_default="[]"),
        sa.Column("candidate_answers", postgresql.JSONB, server_default="{}"),
        sa.Column("score", sa.Numeric(6, 2)),
        sa.Column("score_details", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "evaluator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
        ),
        sa.Column("evaluation_notes", sa.Text),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("evaluated_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("due_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_assessments_application_id", "assessments", ["application_id"])
    op.create_index(
        "idx_assessments_assessment_type", "assessments", ["assessment_type"]
    )
    op.create_index("idx_assessments_status", "assessments", ["status"])
    op.create_index("idx_assessments_evaluator_id", "assessments", ["evaluator_id"])
    op.create_index("idx_assessments_due_at", "assessments", ["due_at"])
    op.create_index(
        "idx_assessments_submitted_at",
        "assessments",
        ["submitted_at"],
        postgresql_using="btree",
        postgresql_ops={"submitted_at": "DESC"},
    )
    op.create_index(
        "idx_assessments_evaluated_at",
        "assessments",
        ["evaluated_at"],
        postgresql_using="btree",
        postgresql_ops={"evaluated_at": "DESC"},
    )
    op.create_index(
        "idx_assessments_questions",
        "assessments",
        ["questions"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_assessments_candidate_answers",
        "assessments",
        ["candidate_answers"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_assessments_score_details",
        "assessments",
        ["score_details"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_assessments_application_type",
        "assessments",
        ["application_id", "assessment_type"],
    )

    # skills
    op.create_table(
        "skills",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("slug", sa.String(150), nullable=False, unique=True),
        sa.Column("category", sa.String(100)),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("description", sa.Text),
        sa.Column("aliases", postgresql.JSONB, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_skills_name",
        "skills",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_index("idx_skills_slug", "skills", ["slug"])
    op.create_index("idx_skills_category", "skills", ["category"])
    op.create_index("idx_skills_subcategory", "skills", ["subcategory"])
    op.create_index(
        "idx_skills_is_active",
        "skills",
        ["is_active"],
        postgresql_where=sa.text("is_active = TRUE"),
    )
    op.create_index("idx_skills_aliases", "skills", ["aliases"], postgresql_using="gin")

    # experiences
    op.create_table(
        "experiences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("company_logo_url", sa.String(1000)),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column(
            "employment_type",
            experience_type,
            nullable=False,
            server_default="full_time",
        ),
        sa.Column("department", sa.String(100)),
        sa.Column("location", sa.String(200)),
        sa.Column("is_remote", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text),
        sa.Column("achievements", postgresql.JSONB, server_default="[]"),
        sa.Column("skills_used", postgresql.JSONB, server_default="[]"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_experiences_candidate_id", "experiences", ["candidate_id"])
    op.create_index(
        "idx_experiences_company_name",
        "experiences",
        ["company_name"],
        postgresql_using="gin",
        postgresql_ops={"company_name": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_experiences_title",
        "experiences",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_experiences_employment_type", "experiences", ["employment_type"]
    )
    op.create_index(
        "idx_experiences_start_date",
        "experiences",
        ["start_date"],
        postgresql_using="btree",
        postgresql_ops={"start_date": "DESC"},
    )
    op.create_index(
        "idx_experiences_end_date",
        "experiences",
        ["end_date"],
        postgresql_using="btree",
        postgresql_ops={"end_date": "DESC"},
    )
    op.create_index(
        "idx_experiences_is_current",
        "experiences",
        ["is_current"],
        postgresql_where=sa.text("is_current = TRUE"),
    )
    op.create_index(
        "idx_experiences_achievements",
        "experiences",
        ["achievements"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_experiences_skills_used",
        "experiences",
        ["skills_used"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_experiences_candidate_current",
        "experiences",
        ["candidate_id", "is_current"],
    )

    # education
    op.create_table(
        "education",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("institution_name", sa.String(300), nullable=False),
        sa.Column("institution_logo_url", sa.String(1000)),
        sa.Column("degree", sa.String(200), nullable=False),
        sa.Column("field_of_study", sa.String(200)),
        sa.Column("education_level", education_level, nullable=False),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "gpa", sa.Numeric(3, 2), sa.CheckConstraint("gpa >= 0.00 AND gpa <= 4.00")
        ),
        sa.Column(
            "max_gpa",
            sa.Numeric(3, 2),
            sa.CheckConstraint("max_gpa >= 0.00 AND max_gpa <= 4.00"),
        ),
        sa.Column("honors", sa.String(200)),
        sa.Column("activities", sa.Text),
        sa.Column("coursework", postgresql.JSONB, server_default="[]"),
        sa.Column("description", sa.Text),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_education_candidate_id", "education", ["candidate_id"])
    op.create_index(
        "idx_education_institution_name",
        "education",
        ["institution_name"],
        postgresql_using="gin",
        postgresql_ops={"institution_name": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_education_degree",
        "education",
        ["degree"],
        postgresql_using="gin",
        postgresql_ops={"degree": "gin_trgm_ops"},
    )
    op.create_index(
        "idx_education_field_of_study",
        "education",
        ["field_of_study"],
        postgresql_using="gin",
        postgresql_ops={"field_of_study": "gin_trgm_ops"},
    )
    op.create_index("idx_education_education_level", "education", ["education_level"])
    op.create_index(
        "idx_education_start_date",
        "education",
        ["start_date"],
        postgresql_using="btree",
        postgresql_ops={"start_date": "DESC"},
    )
    op.create_index(
        "idx_education_end_date",
        "education",
        ["end_date"],
        postgresql_using="btree",
        postgresql_ops={"end_date": "DESC"},
    )
    op.create_index(
        "idx_education_is_current",
        "education",
        ["is_current"],
        postgresql_where=sa.text("is_current = TRUE"),
    )
    op.create_index(
        "idx_education_coursework", "education", ["coursework"], postgresql_using="gin"
    )
    op.create_index(
        "idx_education_candidate_level",
        "education",
        ["candidate_id", "education_level"],
    )

    # talent_pools
    op.create_table(
        "talent_pools",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "employer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "pool_type", talent_pool_type, nullable=False, server_default="custom"
        ),
        sa.Column("criteria", postgresql.JSONB, server_default="{}"),
        sa.Column("member_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("idx_talent_pools_employer_id", "talent_pools", ["employer_id"])
    op.create_index("idx_talent_pools_created_by", "talent_pools", ["created_by"])
    op.create_index("idx_talent_pools_pool_type", "talent_pools", ["pool_type"])
    op.create_index(
        "idx_talent_pools_is_active",
        "talent_pools",
        ["is_active"],
        postgresql_where=sa.text("is_active = TRUE"),
    )
    op.create_index(
        "idx_talent_pools_criteria",
        "talent_pools",
        ["criteria"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_talent_pools_name",
        "talent_pools",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )

    # talent_pool_members
    op.create_table(
        "talent_pool_members",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "talent_pool_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("talent_pools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "added_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("talent_pool_id", "candidate_id"),
    )
    op.create_index(
        "idx_talent_pool_members_pool_id", "talent_pool_members", ["talent_pool_id"]
    )
    op.create_index(
        "idx_talent_pool_members_candidate_id", "talent_pool_members", ["candidate_id"]
    )
    op.create_index(
        "idx_talent_pool_members_added_by", "talent_pool_members", ["added_by"]
    )
    op.create_index(
        "idx_talent_pool_members_created_at",
        "talent_pool_members",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )

    # candidate_skills
    op.create_table(
        "candidate_skills",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "proficiency_level",
            sa.Integer,
            sa.CheckConstraint("proficiency_level >= 1 AND proficiency_level <= 5"),
            nullable=False,
            server_default="1",
        ),
        sa.Column("years_experience", sa.Numeric(4, 1)),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "verified_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
        ),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("candidate_id", "skill_id"),
    )
    op.create_index(
        "idx_candidate_skills_candidate_id", "candidate_skills", ["candidate_id"]
    )
    op.create_index("idx_candidate_skills_skill_id", "candidate_skills", ["skill_id"])
    op.create_index(
        "idx_candidate_skills_proficiency", "candidate_skills", ["proficiency_level"]
    )
    op.create_index(
        "idx_candidate_skills_is_primary",
        "candidate_skills",
        ["is_primary"],
        postgresql_where=sa.text("is_primary = TRUE"),
    )
    op.create_index(
        "idx_candidate_skills_verified_by", "candidate_skills", ["verified_by"]
    )

    # analytics_events (partitioned)
    op.create_table(
        "analytics_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("event_name", sa.String(200), nullable=False),
        sa.Column("session_id", sa.String(255)),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "employer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employers.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "interview_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interviews.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessments.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
        ),
        sa.Column("ip_address", postgresql.INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("referrer", sa.String(1000)),
        sa.Column("url", sa.String(2000)),
        sa.Column("page_title", sa.String(500)),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("properties", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id", "created_at"),
        postgresql_partition_by="RANGE (created_at)",
    )
    op.create_index(
        "idx_analytics_events_event_type", "analytics_events", ["event_type"]
    )
    op.create_index(
        "idx_analytics_events_event_name", "analytics_events", ["event_name"]
    )
    op.create_index(
        "idx_analytics_events_session_id", "analytics_events", ["session_id"]
    )
    op.create_index("idx_analytics_events_user_id", "analytics_events", ["user_id"])
    op.create_index(
        "idx_analytics_events_candidate_id", "analytics_events", ["candidate_id"]
    )
    op.create_index(
        "idx_analytics_events_employer_id", "analytics_events", ["employer_id"]
    )
    op.create_index("idx_analytics_events_job_id", "analytics_events", ["job_id"])
    op.create_index(
        "idx_analytics_events_application_id", "analytics_events", ["application_id"]
    )
    op.create_index(
        "idx_analytics_events_created_at",
        "analytics_events",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_analytics_events_metadata",
        "analytics_events",
        ["metadata"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_analytics_events_properties",
        "analytics_events",
        ["properties"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_analytics_events_event_type_created",
        "analytics_events",
        ["event_type", "created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_analytics_events_user_created",
        "analytics_events",
        ["user_id", "created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )

    # audit_log
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("table_name", sa.String(100), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("old_values", postgresql.JSONB),
        sa.Column("new_values", postgresql.JSONB),
        sa.Column("changed_fields", postgresql.JSONB),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("performed_by_type", sa.String(50)),
        sa.Column("ip_address", postgresql.INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("session_id", sa.String(255)),
        sa.Column("reason", sa.Text),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_audit_log_table_name", "audit_log", ["table_name"])
    op.create_index("idx_audit_log_record_id", "audit_log", ["record_id"])
    op.create_index("idx_audit_log_action", "audit_log", ["action"])
    op.create_index("idx_audit_log_performed_by", "audit_log", ["performed_by"])
    op.create_index(
        "idx_audit_log_created_at",
        "audit_log",
        ["created_at"],
        postgresql_using="btree",
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "idx_audit_log_table_record", "audit_log", ["table_name", "record_id"]
    )
    op.create_index(
        "idx_audit_log_old_values", "audit_log", ["old_values"], postgresql_using="gin"
    )
    op.create_index(
        "idx_audit_log_new_values", "audit_log", ["new_values"], postgresql_using="gin"
    )
    op.create_index(
        "idx_audit_log_changed_fields",
        "audit_log",
        ["changed_fields"],
        postgresql_using="gin",
    )

    # Create views
    op.execute("""
        CREATE VIEW v_active_jobs AS
        SELECT
            j.*,
            e.name AS employer_name,
            e.slug AS employer_slug,
            e.logo_url AS employer_logo_url,
            e.website AS employer_website
        FROM jobs j
        JOIN employers e ON j.employer_id = e.id
        WHERE j.is_active = TRUE
            AND j.deleted_at IS NULL
            AND (j.expires_at IS NULL OR j.expires_at > NOW())
    """)

    op.execute("""
        CREATE VIEW v_candidate_applications AS
        SELECT
            a.*,
            c.first_name AS candidate_first_name,
            c.last_name AS candidate_last_name,
            c.email AS candidate_email,
            j.title AS job_title,
            j.slug AS job_slug,
            e.name AS employer_name,
            e.slug AS employer_slug
        FROM applications a
        JOIN candidates c ON a.candidate_id = c.id
        JOIN jobs j ON a.job_id = j.id
        JOIN employers e ON j.employer_id = e.id
        WHERE a.deleted_at IS NULL
    """)

    op.execute("""
        CREATE VIEW v_recruiter_pipeline AS
        SELECT
            r.id AS recruiter_id,
            r.first_name || ' ' || r.last_name AS recruiter_name,
            r.email AS recruiter_email,
            e.name AS employer_name,
            COUNT(DISTINCT a.id) AS total_applications,
            COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'submitted') AS new_applications,
            COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'interview') AS in_interview,
            COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'offer') AS in_offer,
            COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'hired') AS hired,
            COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'rejected') AS rejected,
            COUNT(DISTINCT i.id) AS total_interviews,
            COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'scheduled') AS upcoming_interviews
        FROM recruiters r
        JOIN employers e ON r.employer_id = e.id
        LEFT JOIN applications a ON a.recruiter_id = r.id AND a.deleted_at IS NULL
        LEFT JOIN interviews i ON i.application_id = a.id AND i.deleted_at IS NULL
        WHERE r.is_active = TRUE
        GROUP BY r.id, r.first_name, r.last_name, r.email, e.name
    """)


def downgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS v_recruiter_pipeline")
    op.execute("DROP VIEW IF EXISTS v_candidate_applications")
    op.execute("DROP VIEW IF EXISTS v_active_jobs")

    # Drop tables in reverse order
    op.drop_table('audit_log')
    op.execute("DROP TABLE IF EXISTS analytics_events_default")
    op.drop_table('analytics_events')
    op.drop_table("candidate_skills")
    op.drop_table("talent_pool_members")
    op.drop_table("talent_pools")
    op.drop_table("education")
    op.drop_table("experiences")
    op.drop_table("skills")
    op.drop_table("assessments")
    op.drop_table("interviews")
    op.drop_table("applications")
    op.drop_table("jobs")
    op.drop_table("candidates")
    op.drop_table("recruiters")
    op.drop_table("employers")

    # Drop enum types
    for enum_name in [
        "audit_action",
        "event_type",
        "education_level",
        "experience_type",
        "employment_type",
        "talent_pool_type",
        "assessment_type",
        "assessment_status",
        "interview_type",
        "interview_status",
        "application_status",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

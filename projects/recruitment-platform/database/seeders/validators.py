"""Factory validation and data consistency checks for recruitment platform seeders."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

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

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Aggregate validation report."""

    results: list[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)

    def add(self, result: ValidationResult) -> None:
        self.results.append(result)

    def summary(self) -> str:
        lines = [
            "=" * 70,
            "SEEDER VALIDATION REPORT",
            "=" * 70,
            f"Total checks: {self.total}  |  Passed: {self.passed}  |  Failed: {self.failed}",
            "-" * 70,
        ]
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"  [{status}] {r.name}: {r.message}")
        lines.append("=" * 70)
        return "\n".join(lines)


def validate_user_factory(session: Session) -> list[ValidationResult]:
    """Validate UserFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        user = UserFactory()
        session.add(user)
        session.commit()

        results.append(
            ValidationResult(
                name="user_email_present",
                passed=bool(user.email),
                message=f"Email: {user.email}",
            )
        )
        results.append(
            ValidationResult(
                name="user_name_present",
                passed=bool(user.name),
                message=f"Name: {user.name}",
            )
        )
        results.append(
            ValidationResult(
                name="user_role_valid",
                passed=user.role in ("recruiter", "hiring_manager", "admin"),
                message=f"Role: {user.role}",
            )
        )
        results.append(
            ValidationResult(
                name="user_created_at_set",
                passed=user.created_at is not None,
                message=f"Created: {user.created_at}",
            )
        )
        results.append(
            ValidationResult(
                name="user_id_assigned",
                passed=user.id is not None,
                message=f"ID: {user.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="user_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_company_factory(session: Session) -> list[ValidationResult]:
    """Validate CompanyFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        company = CompanyFactory()
        session.add(company)
        session.commit()

        results.append(
            ValidationResult(
                name="company_name_present",
                passed=bool(company.name),
                message=f"Name: {company.name}",
            )
        )
        results.append(
            ValidationResult(
                name="company_industry_valid",
                passed=company.industry
                in (
                    "Technology",
                    "Healthcare",
                    "Finance",
                    "Education",
                    "Manufacturing",
                    "Retail",
                    "Consulting",
                    "Media",
                ),
                message=f"Industry: {company.industry}",
            )
        )
        results.append(
            ValidationResult(
                name="company_size_valid",
                passed=company.size
                in (
                    "1-10",
                    "11-50",
                    "51-200",
                    "201-500",
                    "501-1000",
                    "1001-5000",
                    "5000+",
                ),
                message=f"Size: {company.size}",
            )
        )
        results.append(
            ValidationResult(
                name="company_id_assigned",
                passed=company.id is not None,
                message=f"ID: {company.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="company_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_job_factory(session: Session) -> list[ValidationResult]:
    """Validate JobFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        job = JobFactory()
        session.add(job)
        session.commit()

        results.append(
            ValidationResult(
                name="job_title_present",
                passed=bool(job.title),
                message=f"Title: {job.title}",
            )
        )
        results.append(
            ValidationResult(
                name="job_company_fk_valid",
                passed=job.company_id is not None,
                message=f"Company ID: {job.company_id}",
            )
        )
        results.append(
            ValidationResult(
                name="job_salary_range_valid",
                passed=job.salary_min is not None
                and job.salary_max is not None
                and job.salary_min <= job.salary_max,
                message=f"Salary: {job.salary_min} - {job.salary_max}",
            )
        )
        results.append(
            ValidationResult(
                name="job_employment_type_valid",
                passed=job.employment_type
                in ("full-time", "part-time", "contract", "internship"),
                message=f"Type: {job.employment_type}",
            )
        )
        results.append(
            ValidationResult(
                name="job_status_valid",
                passed=job.status in ("open", "closed", "draft", "on_hold"),
                message=f"Status: {job.status}",
            )
        )
        results.append(
            ValidationResult(
                name="job_has_skills",
                passed=len(job.skills) > 0,
                message=f"Skills count: {len(job.skills)}",
            )
        )
        results.append(
            ValidationResult(
                name="job_id_assigned",
                passed=job.id is not None,
                message=f"ID: {job.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="job_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_candidate_factory(session: Session) -> list[ValidationResult]:
    """Validate CandidateFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        candidate = CandidateFactory()
        session.add(candidate)
        session.commit()

        results.append(
            ValidationResult(
                name="candidate_email_present",
                passed=bool(candidate.email),
                message=f"Email: {candidate.email}",
            )
        )
        results.append(
            ValidationResult(
                name="candidate_name_present",
                passed=bool(candidate.name),
                message=f"Name: {candidate.name}",
            )
        )
        results.append(
            ValidationResult(
                name="candidate_years_exp_valid",
                passed=candidate.years_experience is not None
                and 0 <= candidate.years_experience <= 50,
                message=f"Years: {candidate.years_experience}",
            )
        )
        results.append(
            ValidationResult(
                name="candidate_has_skills",
                passed=len(candidate.skills) > 0,
                message=f"Skills count: {len(candidate.skills)}",
            )
        )
        results.append(
            ValidationResult(
                name="candidate_has_education",
                passed=len(candidate.education) > 0,
                message=f"Education entries: {len(candidate.education)}",
            )
        )
        results.append(
            ValidationResult(
                name="candidate_has_experience",
                passed=len(candidate.experience) > 0,
                message=f"Experience entries: {len(candidate.experience)}",
            )
        )
        results.append(
            ValidationResult(
                name="candidate_id_assigned",
                passed=candidate.id is not None,
                message=f"ID: {candidate.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="candidate_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_application_factory(session: Session) -> list[ValidationResult]:
    """Validate ApplicationFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        application = ApplicationFactory()
        session.add(application)
        session.commit()

        results.append(
            ValidationResult(
                name="application_candidate_fk_valid",
                passed=application.candidate_id is not None,
                message=f"Candidate ID: {application.candidate_id}",
            )
        )
        results.append(
            ValidationResult(
                name="application_job_fk_valid",
                passed=application.job_id is not None,
                message=f"Job ID: {application.job_id}",
            )
        )
        results.append(
            ValidationResult(
                name="application_status_valid",
                passed=application.status
                in (
                    "applied",
                    "screening",
                    "interview",
                    "offer",
                    "hired",
                    "rejected",
                ),
                message=f"Status: {application.status}",
            )
        )
        results.append(
            ValidationResult(
                name="application_match_score_valid",
                passed=application.match_score is not None
                and 0.0 <= application.match_score <= 1.0,
                message=f"Match score: {application.match_score}",
            )
        )
        results.append(
            ValidationResult(
                name="application_id_assigned",
                passed=application.id is not None,
                message=f"ID: {application.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="application_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_interview_factory(session: Session) -> list[ValidationResult]:
    """Validate InterviewFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        interview = InterviewFactory()
        session.add(interview)
        session.commit()

        results.append(
            ValidationResult(
                name="interview_application_fk_valid",
                passed=interview.application_id is not None,
                message=f"Application ID: {interview.application_id}",
            )
        )
        results.append(
            ValidationResult(
                name="interview_interviewer_fk_valid",
                passed=interview.interviewer_id is not None,
                message=f"Interviewer ID: {interview.interviewer_id}",
            )
        )
        results.append(
            ValidationResult(
                name="interview_type_valid",
                passed=interview.interview_type
                in (
                    "phone_screen",
                    "technical",
                    "behavioral",
                    "panel",
                    "final",
                ),
                message=f"Type: {interview.interview_type}",
            )
        )
        results.append(
            ValidationResult(
                name="interview_status_valid",
                passed=interview.status
                in ("scheduled", "completed", "cancelled", "no_show"),
                message=f"Status: {interview.status}",
            )
        )
        results.append(
            ValidationResult(
                name="interview_duration_valid",
                passed=interview.duration_minutes is not None
                and interview.duration_minutes > 0,
                message=f"Duration: {interview.duration_minutes} min",
            )
        )
        results.append(
            ValidationResult(
                name="interview_rating_valid",
                passed=interview.rating is None or 1 <= interview.rating <= 5,
                message=f"Rating: {interview.rating}",
            )
        )
        results.append(
            ValidationResult(
                name="interview_id_assigned",
                passed=interview.id is not None,
                message=f"ID: {interview.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="interview_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_skill_factory(session: Session) -> list[ValidationResult]:
    """Validate SkillFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        skill = SkillFactory()
        session.add(skill)
        session.commit()

        results.append(
            ValidationResult(
                name="skill_name_present",
                passed=bool(skill.name),
                message=f"Name: {skill.name}",
            )
        )
        results.append(
            ValidationResult(
                name="skill_category_valid",
                passed=skill.category
                in (
                    "programming",
                    "framework",
                    "database",
                    "cloud",
                    "devops",
                    "design",
                    "management",
                    "soft_skill",
                ),
                message=f"Category: {skill.category}",
            )
        )
        results.append(
            ValidationResult(
                name="skill_id_assigned",
                passed=skill.id is not None,
                message=f"ID: {skill.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="skill_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_education_factory(session: Session) -> list[ValidationResult]:
    """Validate EducationFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        education = EducationFactory()
        session.add(education)
        session.commit()

        results.append(
            ValidationResult(
                name="education_candidate_fk_valid",
                passed=education.candidate_id is not None,
                message=f"Candidate ID: {education.candidate_id}",
            )
        )
        results.append(
            ValidationResult(
                name="education_institution_present",
                passed=bool(education.institution),
                message=f"Institution: {education.institution}",
            )
        )
        results.append(
            ValidationResult(
                name="education_degree_valid",
                passed=education.degree
                in (
                    "Bachelor of Science",
                    "Master of Science",
                    "Bachelor of Arts",
                    "Master of Arts",
                    "PhD",
                    "Associate Degree",
                ),
                message=f"Degree: {education.degree}",
            )
        )
        results.append(
            ValidationResult(
                name="education_years_valid",
                passed=education.start_year is not None
                and education.end_year is not None
                and education.start_year <= education.end_year,
                message=f"Years: {education.start_year} - {education.end_year}",
            )
        )
        results.append(
            ValidationResult(
                name="education_gpa_valid",
                passed=education.gpa is not None and 0.0 <= education.gpa <= 4.0,
                message=f"GPA: {education.gpa}",
            )
        )
        results.append(
            ValidationResult(
                name="education_id_assigned",
                passed=education.id is not None,
                message=f"ID: {education.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="education_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_experience_factory(session: Session) -> list[ValidationResult]:
    """Validate ExperienceFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        experience = ExperienceFactory()
        session.add(experience)
        session.commit()

        results.append(
            ValidationResult(
                name="experience_candidate_fk_valid",
                passed=experience.candidate_id is not None,
                message=f"Candidate ID: {experience.candidate_id}",
            )
        )
        results.append(
            ValidationResult(
                name="experience_company_present",
                passed=bool(experience.company),
                message=f"Company: {experience.company}",
            )
        )
        results.append(
            ValidationResult(
                name="experience_title_present",
                passed=bool(experience.title),
                message=f"Title: {experience.title}",
            )
        )
        results.append(
            ValidationResult(
                name="experience_dates_valid",
                passed=experience.start_date is not None
                and experience.end_date is not None
                and experience.start_date <= experience.end_date,
                message=f"Dates: {experience.start_date} - {experience.end_date}",
            )
        )
        results.append(
            ValidationResult(
                name="experience_id_assigned",
                passed=experience.id is not None,
                message=f"ID: {experience.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="experience_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_note_factory(session: Session) -> list[ValidationResult]:
    """Validate NoteFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        note = NoteFactory()
        session.add(note)
        session.commit()

        results.append(
            ValidationResult(
                name="note_candidate_fk_valid",
                passed=note.candidate_id is not None,
                message=f"Candidate ID: {note.candidate_id}",
            )
        )
        results.append(
            ValidationResult(
                name="note_author_fk_valid",
                passed=note.author_id is not None,
                message=f"Author ID: {note.author_id}",
            )
        )
        results.append(
            ValidationResult(
                name="note_content_present",
                passed=bool(note.content),
                message=f"Content length: {len(note.content)}",
            )
        )
        results.append(
            ValidationResult(
                name="note_id_assigned",
                passed=note.id is not None,
                message=f"ID: {note.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="note_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def validate_talent_pool_factory(session: Session) -> list[ValidationResult]:
    """Validate TalentPoolFactory produces valid data."""
    results = []
    configure_session(session)

    try:
        pool = TalentPoolFactory()
        session.add(pool)
        session.commit()

        results.append(
            ValidationResult(
                name="talent_pool_name_present",
                passed=bool(pool.name),
                message=f"Name: {pool.name}",
            )
        )
        results.append(
            ValidationResult(
                name="talent_pool_created_by_fk_valid",
                passed=pool.created_by is not None,
                message=f"Created by: {pool.created_by}",
            )
        )
        results.append(
            ValidationResult(
                name="talent_pool_has_members",
                passed=len(pool.members) > 0,
                message=f"Members count: {len(pool.members)}",
            )
        )
        results.append(
            ValidationResult(
                name="talent_pool_id_assigned",
                passed=pool.id is not None,
                message=f"ID: {pool.id}",
            )
        )
    except Exception as e:
        results.append(
            ValidationResult(
                name="talent_pool_factory",
                passed=False,
                message=f"Exception: {e}",
            )
        )

    return results


def run_all_factory_validations(session: Session) -> ValidationReport:
    """Run all factory validations and return a report."""
    report = ValidationReport()

    validators = [
        validate_user_factory,
        validate_company_factory,
        validate_job_factory,
        validate_candidate_factory,
        validate_application_factory,
        validate_interview_factory,
        validate_skill_factory,
        validate_education_factory,
        validate_experience_factory,
        validate_note_factory,
        validate_talent_pool_factory,
    ]

    for validator in validators:
        try:
            results = validator(session)
            for r in results:
                report.add(r)
        except Exception as e:
            report.add(
                ValidationResult(
                    name=validator.__name__,
                    passed=False,
                    message=f"Validator crashed: {e}",
                )
            )

    return report


def check_foreign_key_consistency(session: Session) -> ValidationReport:
    """Verify all foreign key relationships are consistent."""
    report = ValidationReport()

    fk_checks = [
        (
            "jobs -> companies",
            "SELECT COUNT(*) FROM jobs WHERE company_id NOT IN (SELECT id FROM companies)",
        ),
        (
            "applications -> candidates",
            "SELECT COUNT(*) FROM applications WHERE candidate_id NOT IN (SELECT id FROM candidates)",
        ),
        (
            "applications -> jobs",
            "SELECT COUNT(*) FROM applications WHERE job_id NOT IN (SELECT id FROM jobs)",
        ),
        (
            "interviews -> applications",
            "SELECT COUNT(*) FROM interviews WHERE application_id NOT IN (SELECT id FROM applications)",
        ),
        (
            "interviews -> users",
            "SELECT COUNT(*) FROM interviews WHERE interviewer_id NOT IN (SELECT id FROM users)",
        ),
        (
            "education -> candidates",
            "SELECT COUNT(*) FROM education WHERE candidate_id NOT IN (SELECT id FROM candidates)",
        ),
        (
            "experience -> candidates",
            "SELECT COUNT(*) FROM experience WHERE candidate_id NOT IN (SELECT id FROM candidates)",
        ),
        (
            "notes -> candidates",
            "SELECT COUNT(*) FROM notes WHERE candidate_id NOT IN (SELECT id FROM candidates)",
        ),
        (
            "notes -> users",
            "SELECT COUNT(*) FROM notes WHERE author_id NOT IN (SELECT id FROM users)",
        ),
        (
            "talent_pools -> users",
            "SELECT COUNT(*) FROM talent_pools WHERE created_by NOT IN (SELECT id FROM users)",
        ),
        (
            "candidate_skills -> candidates",
            "SELECT COUNT(*) FROM candidate_skills WHERE candidate_id NOT IN (SELECT id FROM candidates)",
        ),
        (
            "candidate_skills -> skills",
            "SELECT COUNT(*) FROM candidate_skills WHERE skill_id NOT IN (SELECT id FROM skills)",
        ),
        (
            "job_skills -> jobs",
            "SELECT COUNT(*) FROM job_skills WHERE job_id NOT IN (SELECT id FROM jobs)",
        ),
        (
            "job_skills -> skills",
            "SELECT COUNT(*) FROM job_skills WHERE skill_id NOT IN (SELECT id FROM skills)",
        ),
        (
            "talent_pool_members -> talent_pools",
            "SELECT COUNT(*) FROM talent_pool_members WHERE pool_id NOT IN (SELECT id FROM talent_pools)",
        ),
        (
            "talent_pool_members -> candidates",
            "SELECT COUNT(*) FROM talent_pool_members WHERE candidate_id NOT IN (SELECT id FROM candidates)",
        ),
    ]

    for name, query in fk_checks:
        try:
            orphan_count = session.execute(text(query)).scalar()
            passed = orphan_count == 0
            report.add(
                ValidationResult(
                    name=f"fk_{name.replace(' ', '_').replace('->', 'to')}",
                    passed=passed,
                    message=f"Orphans: {orphan_count}",
                    details={"query": query, "orphan_count": orphan_count},
                )
            )
        except Exception as e:
            report.add(
                ValidationResult(
                    name=f"fk_{name.replace(' ', '_').replace('->', 'to')}",
                    passed=False,
                    message=f"Check failed: {e}",
                )
            )

    return report


def check_data_quality(session: Session) -> ValidationReport:
    """Run data quality checks on seeded data."""
    report = ValidationReport()

    quality_checks = [
        ("users_email_unique", "SELECT COUNT(*) - COUNT(DISTINCT email) FROM users", 0),
        (
            "candidates_email_unique",
            "SELECT COUNT(*) - COUNT(DISTINCT email) FROM candidates",
            0,
        ),
        ("skills_name_unique", "SELECT COUNT(*) - COUNT(DISTINCT name) FROM skills", 0),
        (
            "applications_valid_score",
            "SELECT COUNT(*) FROM applications WHERE match_score < 0 OR match_score > 1",
            0,
        ),
        (
            "interviews_valid_rating",
            "SELECT COUNT(*) FROM interviews WHERE rating IS NOT NULL AND (rating < 1 OR rating > 5)",
            0,
        ),
        (
            "education_valid_gpa",
            "SELECT COUNT(*) FROM education WHERE gpa IS NOT NULL AND (gpa < 0 OR gpa > 4.0)",
            0,
        ),
        (
            "education_valid_years",
            "SELECT COUNT(*) FROM education WHERE start_year > end_year",
            0,
        ),
        (
            "experience_valid_dates",
            "SELECT COUNT(*) FROM experience WHERE start_date > end_date",
            0,
        ),
        (
            "jobs_valid_salary",
            "SELECT COUNT(*) FROM jobs WHERE salary_min > salary_max",
            0,
        ),
        (
            "candidates_valid_experience",
            "SELECT COUNT(*) FROM candidates WHERE years_experience < 0 OR years_experience > 50",
            0,
        ),
    ]

    for name, query, expected in quality_checks:
        try:
            actual = session.execute(text(query)).scalar()
            passed = actual == expected
            report.add(
                ValidationResult(
                    name=name,
                    passed=passed,
                    message=f"Expected {expected}, got {actual}",
                    details={"query": query, "expected": expected, "actual": actual},
                )
            )
        except Exception as e:
            report.add(
                ValidationResult(
                    name=name,
                    passed=False,
                    message=f"Check failed: {e}",
                )
            )

    return report


def run_full_validation(database_url: str) -> ValidationReport:
    """Run complete validation suite against a database."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(database_url)
    session_local = sessionmaker(bind=engine)
    session = session_local()

    try:
        report = ValidationReport()

        # Factory validations
        factory_report = run_all_factory_validations(session)
        report.results.extend(factory_report.results)

        # FK consistency
        fk_report = check_foreign_key_consistency(session)
        report.results.extend(fk_report.results)

        # Data quality
        quality_report = check_data_quality(session)
        report.results.extend(quality_report.results)

        return report
    finally:
        session.close()

"""Resume Parser Agent for recruitment-platform.

Extracts structured candidate data from resume files and scores
candidate-job fit using keyword matching and experience heuristics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ExperienceEntry:
    """A single work-experience entry parsed from a resume."""

    title: str
    company: str
    start_year: int
    end_year: int | None  # None means "Present"
    description: str = ""

    @property
    def duration_years(self) -> float:
        end = self.end_year if self.end_year is not None else 2026
        return max(0.0, float(end - self.start_year))


@dataclass
class EducationEntry:
    """A single education entry parsed from a resume."""

    degree: str
    institution: str
    graduation_year: int | None = None


@dataclass
class ResumeData:
    """Structured representation of a parsed resume."""

    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] = field(default_factory=list)
    experience: list[ExperienceEntry] = field(default_factory=list)
    education: list[EducationEntry] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class JobRequirements:
    """Requirements for a job posting used to score a candidate."""

    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    min_years_experience: float = 0.0
    required_degree: str = ""  # e.g. "Bachelor", "Master", "PhD"
    keywords: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mock resume database (keyed by file name)
# ---------------------------------------------------------------------------

_MOCK_RESUMES: dict[str, dict[str, Any]] = {
    "alice_chen_resume.pdf": {
        "name": "Alice Chen",
        "email": "alice.chen@email.com",
        "phone": "+1-415-555-0101",
        "skills": [
            "Python", "Machine Learning", "TensorFlow", "SQL",
            "AWS", "Docker", "Kubernetes", "Data Pipelines",
        ],
        "experience": [
            {
                "title": "Senior ML Engineer",
                "company": "TechCorp AI",
                "start_year": 2020,
                "end_year": None,
                "description": "Led ML platform serving 10M+ predictions/day.",
            },
            {
                "title": "Data Scientist",
                "company": "DataDriven Inc",
                "start_year": 2017,
                "end_year": 2020,
                "description": "Built recommendation engines and A/B testing frameworks.",
            },
        ],
        "education": [
            {
                "degree": "Master of Science in Computer Science",
                "institution": "Stanford University",
                "graduation_year": 2017,
            }
        ],
    },
    "bob_martinez_resume.pdf": {
        "name": "Bob Martinez",
        "email": "bob.martinez@email.com",
        "phone": "+1-206-555-0202",
        "skills": [
            "Java", "Spring Boot", "Microservices", "PostgreSQL",
            "Redis", "Kafka", "CI/CD", "Terraform",
        ],
        "experience": [
            {
                "title": "Backend Engineer",
                "company": "CloudScale Systems",
                "start_year": 2019,
                "end_year": None,
                "description": "Designed event-driven microservices on AWS.",
            },
            {
                "title": "Software Developer",
                "company": "WebWorks Agency",
                "start_year": 2016,
                "end_year": 2019,
                "description": "Full-stack development for enterprise clients.",
            },
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Software Engineering",
                "institution": "University of Washington",
                "graduation_year": 2016,
            }
        ],
    },
    "carol_williams_resume.pdf": {
        "name": "Carol Williams",
        "email": "carol.williams@email.com",
        "phone": "+1-312-555-0303",
        "skills": [
            "Product Management", "Agile", "Scrum", "Jira",
            "User Research", "A/B Testing", "SQL", "Roadmapping",
        ],
        "experience": [
            {
                "title": "Senior Product Manager",
                "company": "InnovateCo",
                "start_year": 2018,
                "end_year": None,
                "description": "Managed B2B SaaS product line with $20M ARR.",
            },
            {
                "title": "Associate Product Manager",
                "company": "StartupXYZ",
                "start_year": 2015,
                "end_year": 2018,
                "description": "Launched 3 features that increased retention by 15%.",
            },
        ],
        "education": [
            {
                "degree": "Master of Business Administration",
                "institution": "Northwestern University",
                "graduation_year": 2015,
            }
        ],
    },
    "david_kim_resume.pdf": {
        "name": "David Kim",
        "email": "david.kim@email.com",
        "phone": "+1-646-555-0404",
        "skills": [
            "React", "TypeScript", "Node.js", "GraphQL",
            "Next.js", "Tailwind CSS", "Figma", "Accessibility",
        ],
        "experience": [
            {
                "title": "Frontend Engineer",
                "company": "DesignFirst Studio",
                "start_year": 2021,
                "end_year": None,
                "description": "Built accessible design systems used by 50+ engineers.",
            },
            {
                "title": "UI Developer",
                "company": "PixelPerfect Agency",
                "start_year": 2019,
                "end_year": 2021,
                "description": "Delivered 20+ client websites with 99+ Lighthouse scores.",
            },
        ],
        "education": [
            {
                "degree": "Bachelor of Arts in Web Design",
                "institution": "RISD",
                "graduation_year": 2019,
            }
        ],
    },
}


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")

# Common section headers in resumes
_SECTION_HEADERS = {
    "experience": r"(?:work\s+)?experience|employment\s+history|professional\s+background",
    "education": r"education|academic\s+background|qualifications",
    "skills": r"skills|technical\s+skills|core\s+competencies|technologies",
}


def _extract_name(text: str) -> str:
    """Heuristic: first non-empty line that looks like a person's name."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that are clearly not names
        if _EMAIL_RE.search(line) or _PHONE_RE.search(line):
            continue
        if len(line.split()) <= 4 and line.replace(" ", "").isalpha():
            return line.title()
    return ""


def _extract_email(text: str) -> str:
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    match = _PHONE_RE.search(text)
    return match.group(0) if match else ""


def _extract_skills(text: str) -> list[str]:
    """Extract skills from a skills section or scan for known tech keywords."""
    known_skills = {
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
        "react", "angular", "vue", "svelte", "next.js", "node.js", "express",
        "django", "flask", "fastapi", "spring boot", "rails",
        "tensorflow", "pytorch", "scikit-keras", "machine learning", "deep learning",
        "nlp", "computer vision", "data science", "data engineering",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "ci/cd", "jenkins", "github actions", "gitlab ci",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "kafka", "rabbitmq", "spark", "hadoop", "airflow", "dbt",
        "agile", "scrum", "kanban", "jira", "confluence",
        "product management", "roadmapping", "user research", "a/b testing",
        "figma", "sketch", "adobe xd", "accessibility", "tailwind css",
        "graphql", "rest api", "microservices", "serverless",
    }

    text_lower = text.lower()
    found: list[str] = []
    for skill in known_skills:
        if skill in text_lower:
            # Title-case single words, keep multi-word as-is
            found.append(skill.title() if " " not in skill else skill)
    return sorted(set(found))


def _extract_experience(text: str) -> list[ExperienceEntry]:
    """Parse experience entries using year-range heuristics."""
    entries: list[ExperienceEntry] = []
    year_range_re = re.compile(
        r"(\d{4})\s*[-\s*(?:present|current|now|\d{4})", re.IGNORECASE
    )

    lines = text.splitlines()
    current_entry: dict[str, Any] | None = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        year_match = year_range_re.search(line)
        if year_match:
            # Flush previous entry
            if current_entry:
                entries.append(ExperienceEntry(**current_entry))

            start_year = int(year_match.group(1))
            end_year: int | None = None
            end_match = re.search(r"-\s*(\d{4})", line, re.IGNORECASE)
            if end_match:
                end_year = int(end_match.group(1))

            # Try to extract title/company from the same or previous line
            title = line[: year_match.start()].strip(" -|")
            company = ""
            if "|" in title:
                parts = title.split("|", 1)
                title = parts[0].strip()
                company = parts[1].strip()
            elif "," in title:
                parts = title.split(",", 1)
                title = parts[0].strip()
                company = parts[1].strip()

            current_entry = {
                "title": title or "Unknown Role",
                "company": company or "Unknown Company",
                "start_year": start_year,
                "end_year": end_year,
                "description": "",
            }
        elif current_entry is not None:
            # Accumulate description lines
            if current_entry["description"]:
                current_entry["description"] += " " + line
            else:
                current_entry["description"] = line

    # Flush last entry
    if current_entry:
        entries.append(ExperienceEntry(**current_entry))

    return entries


def _extract_education(text: str) -> list[EducationEntry]:
    """Parse education entries using degree keywords and year patterns."""
    entries: list[EducationEntry] = []
    degree_keywords = [
        "ph.d", "phd", "master", "bachelor", "mba", "m.s.", "b.s.",
        "m.sc", "b.sc", "b.a.", "m.a.", "b.tech", "m.tech",
    ]

    lines = text.splitlines()
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in degree_keywords):
            year_match = re.search(r"(\d{4})", line)
            grad_year = int(year_match.group(1)) if year_match else None

            # Try to split degree and institution
            degree = line.strip()
            institution = ""
            if "," in line:
                parts = line.split(",", 1)
                degree = parts[0].strip()
                institution = parts[1].strip()
            elif " - " in line:
                parts = line.split(" - ", 1)
                degree = parts[0].strip()
                institution = parts[1].strip()

            entries.append(
                EducationEntry(
                    degree=degree,
                    institution=institution,
                    graduation_year=grad_year,
                )
            )

    return entries


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_resume(file_path: str | Path) -> ResumeData:
    """Parse a resume file and extract structured candidate data.

    Supports PDF, DOCX, and plain-text files. Falls back to mock data
    when the file cannot be read or is not found.

    Args:
        file_path: Path to the resume file.

    Returns:
        ResumeData with extracted name, email, phone, skills,
        experience, and education.
    """
    path = Path(file_path)
    raw_text = ""

    # Attempt to read the file
    if path.exists():
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            raw_text = _read_pdf(path)
        elif suffix in (".docx", ".doc"):
            raw_text = _read_docx(path)
        elif suffix in (".txt", ".md"):
            raw_text = path.read_text(encoding="utf-8", errors="ignore")

    # Fall back to mock data if file unreadable or not found
    if not raw_text.strip():
        mock_key = path.name
        if mock_key in _MOCK_RESUMES:
            return _resume_from_mock(_MOCK_RESUMES[mock_key])
        # Generic fallback: try to parse whatever text we have
        if not raw_text.strip():
            return ResumeData()

    # Extract structured fields from raw text
    name = _extract_name(raw_text)
    email = _extract_email(raw_text)
    phone = _extract_phone(raw_text)
    skills = _extract_skills(raw_text)
    experience = _extract_experience(raw_text)
    education = _extract_education(raw_text)

    return ResumeData(
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        experience=experience,
        education=education,
        raw_text=raw_text,
    )


def score_resume(
    resume_data: ResumeData,
    job_requirements: JobRequirements,
) -> float:
    """Score a candidate's resume against job requirements.

    Returns a match score between 0.0 and 100.0 based on:
    - Required skills match (40% weight)
    - Preferred skills match (15% weight)
    - Years of experience vs. minimum (25% weight)
    - Education level match (10% weight)
    - Keyword overlap in experience descriptions (10% weight)

    Args:
        resume_data: Parsed resume data from parse_resume().
        job_requirements: Job requirements to score against.

    Returns:
        Float score from 0.0 to 100.0.
    """
    if not job_requirements.required_skills and not job_requirements.preferred_skills:
        return 0.0

    total_score = 0.0

    # --- Required skills (40%) ---
    if job_requirements.required_skills:
        resume_skills_lower = {s.lower() for s in resume_data.skills}
        required_lower = {s.lower() for s in job_requirements.required_skills}
        matched_required = resume_skills_lower & required_lower
        required_ratio = len(matched_required) / len(required_lower)
        total_score += required_ratio * 40.0

    # --- Preferred skills (15%) ---
    if job_requirements.preferred_skills:
        resume_skills_lower = {s.lower() for s in resume_data.skills}
        preferred_lower = {s.lower() for s in job_requirements.preferred_skills}
        matched_preferred = resume_skills_lower & preferred_lower
        preferred_ratio = len(matched_preferred) / len(preferred_lower)
        total_score += preferred_ratio * 15.0

    # --- Experience duration (25%) ---
    total_years = sum(exp.duration_years for exp in resume_data.experience)
    if job_requirements.min_years_experience > 0:
        if total_years >= job_requirements.min_years_experience:
            total_score += 25.0
        else:
            ratio = total_years / job_requirements.min_years_experience
            total_score += ratio * 25.0
    elif total_years > 0:
        total_score += 25.0  # No minimum specified, give credit for having experience

    # --- Education (10%) ---
    if job_requirements.required_degree:
        degree_levels = {"phd": 4, "ph.d": 4, "master": 3, "mba": 3, "bachelor": 2}
        required_level = 0
        for kw, level in degree_levels.items():
            if kw in job_requirements.required_degree.lower():
                required_level = level
                break

        candidate_level = 0
        for edu in resume_data.education:
            for kw, level in degree_levels.items():
                if kw in edu.degree.lower():
                    candidate_level = max(candidate_level, level)
                    break

        if candidate_level >= required_level:
            total_score += 10.0
        elif candidate_level > 0:
            total_score += 5.0
    elif resume_data.education:
        total_score += 10.0

    # --- Keyword overlap in experience descriptions (10%) ---
    if job_requirements.keywords:
        exp_text = " ".join(
            f"{exp.title} {exp.description}" for exp in resume_data.experience
        ).lower()
        keyword_matches = sum(
            1 for kw in job_requirements.keywords if kw.lower() in exp_text
        )
        keyword_ratio = keyword_matches / len(job_requirements.keywords)
        total_score += keyword_ratio * 10.0

    return round(min(total_score, 100.0), 2)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_pdf(path: Path) -> str:
    """Extract text from a PDF file using PyPDF2 or pdfplumber."""
    try:
        import pdfplumber  # type: ignore

        text_parts: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        pass

    try:
        import PyPDF2  # type: ignore

        text_parts: list[str] = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        return ""


def _read_docx(path: Path) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        import docx  # type: ignore

        doc = docx.Document(str(path))
        return "\n".join(para.text for para in doc.paragraphs)
    except ImportError:
        return ""


def _resume_from_mock(mock: dict[str, Any]) -> ResumeData:
    """Build ResumeData from a mock dictionary."""
    experience = [
        ExperienceEntry(**exp) for exp in mock.get("experience", [])
    ]
    education = [
        EducationEntry(**edu) for edu in mock.get("education", [])
    ]
    return ResumeData(
        name=mock.get("name", ""),
        email=mock.get("email", ""),
        phone=mock.get("phone", ""),
        skills=mock.get("skills", []),
        experience=experience,
        education=education,
    )

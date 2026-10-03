# Database Seeders

Test data generation for the recruitment platform using factory_boy and Faker.

## Files

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy ORM models for all entities |
| `factories.py` | factory_boy factories for each model |
| `seeders.py` | CLI seeder scripts with configurable scale |
| `conftest.py` | Pytest fixtures for database testing |

## Models

- **User** — recruiters, hiring managers, admins
- **Company** — organizations posting jobs
- **Job** — job postings with salary, location, status
- **Candidate** — job candidates with resume, experience
- **Application** — links candidates to jobs with status and match score
- **Interview** — scheduled interviews with feedback and ratings
- **Skill** — skills that candidates have and jobs require
- **Education** — candidate education history
- **Experience** — candidate work experience
- **Note** — recruiter notes on candidates
- **TalentPool** — curated candidate collections

## Quick Start

### Install dependencies

```bash
pip install factory_boy faker sqlalchemy
```

### Run seeders

```bash
# Medium scale (default)
python -m database.seeders.seeders

# Small scale
python -m database.seeders.seeders --scale small

# Large scale
python -m database.seeders.seeders --scale large

# Custom database
python -m database.seeders.seeders --database-url postgresql://user:pass@localhost/recruitment

# Verbose output
python -m database.seeders.seeders --verbose
```

### Use in tests

```python
def test_candidate_creation(db_session, candidate):
    assert candidate.id is not None
    assert candidate.email is not None

def test_job_with_skills(db_session, job):
    assert len(job.skills) > 0

def test_application_workflow(db_session, application):
    assert application.match_score >= 0.0
    assert application.match_score <= 1.0
```

## Factory Usage

```python
from database.seeders.factories import (
    CandidateFactory,
    JobFactory,
    ApplicationFactory,
)

# Create a candidate with default fake data
candidate = CandidateFactory()

# Create a job with specific company
job = JobFactory(company=my_company)

# Create an application linking them
application = ApplicationFactory(candidate=candidate, job=job)

# Override specific fields
candidate = CandidateFactory(
    email="test@example.com",
    name="Test User",
    years_experience=5.0,
)

# Create with specific skills
python = SkillFactory(name="Python", category="programming")
candidate = CandidateFactory(skills=[python])
```

## Scale Factors

| Scale | Skills | Users | Companies | Jobs | Candidates | Applications |
|-------|--------|-------|-----------|------|------------|--------------|
| Small | 10 | 4 | 2 | 6 | 20 | 40 |
| Medium | 25 | 10 | 5 | 15 | 50 | 100 |
| Large | 50 | 20 | 10 | 30 | 100 | 200 |

## Pytest Fixtures

All fixtures use an in-memory SQLite database with automatic rollback after each test.

| Fixture | Description |
|---------|-------------|
| `db_engine` | Session-scoped database engine |
| `db_session` | Fresh session per test with rollback |
| `skill` | Single skill |
| `user` | Single user |
| `company` | Single company |
| `job` | Single job (with company) |
| `candidate` | Single candidate |
| `application` | Single application (with candidate + job) |
| `interview` | Single interview (with application + interviewer) |
| `education` | Single education entry |
| `experience` | Single experience entry |
| `note` | Single note |
| `talent_pool` | Single talent pool |
| `skills_batch` | Batch of skills (default 10) |
| `candidates_batch` | Batch of candidates (default 20) |
| `jobs_batch` | Batch of jobs (default 10) |

## Database Schema

```
users ──┬── interviews (as interviewer)
        └── notes (as author)
        └── talent_pools (as creator)

companies ── jobs ── applications ── interviews
                │         │
                │         └── candidates ──┬── skills (M2M)
                │              │           ├── education
                │              │           ├── experience
                │              │           ├── notes
                │              │           └── talent_pools (M2M)
                │              │
                └──────────────┴── skills (M2M)
```

## Adding New Factories

1. Define the model in `models.py`
2. Create a factory class in `factories.py`:

```python
class NewModelFactory(BaseFactory):
    class Meta:
        model = NewModel

    name = factory.LazyAttribute(lambda _: fake.name())
    # ... other fields
```

3. Add a pytest fixture in `conftest.py`:

```python
@pytest.fixture
def new_model(db_session: Session):
    obj = NewModelFactory()
    db_session.add(obj)
    db_session.commit()
    return obj
```

4. Add a seeder function in `seeders.py`

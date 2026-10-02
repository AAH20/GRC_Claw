# Skills Assessor

AI-powered skill assessment platform using LangChain DeepAgents. Assesses candidate skills through agentic AI with skill extraction, proficiency scoring, gap analysis, and learning path recommendations.

## Features

- **Skill Extraction** — Automatically extract skills from resumes, job descriptions, and text
- **Proficiency Scoring** — Score skill proficiency levels using AI analysis
- **Gap Analysis** — Identify skill gaps between current and target profiles
- **Skill Validation** — Validate and verify claimed skills
- **Learning Path Recommendations** — Generate personalized learning paths

## Architecture

```
skills_assessor/
├── agents/          # LangChain DeepAgents implementations
├── api/             # FastAPI routes and handlers
├── integrations/    # External service integrations
├── config/          # Configuration management
├── models/          # Pydantic data models
├── services/        # Business logic services
├── tests/           # Test suite
└── main.py          # Application entry point
```

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the application
uvicorn skills_assessor.main:create_app --factory --reload

# Run tests
pytest
```

## Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/assessments` | Create new assessment |
| GET | `/assessments/{id}` | Get assessment by ID |
| GET | `/assessments` | List all assessments |
| POST | `/assessments/{id}/extract-skills` | Extract skills from text |
| POST | `/assessments/{id}/score` | Score proficiency levels |
| POST | `/assessments/{id}/analyze-gaps` | Analyze skill gaps |
| POST | `/assessments/{id}/validate` | Validate skills |
| POST | `/assessments/{id}/learning-path` | Generate learning path |
| GET | `/skills` | List all skills |
| GET | `/skills/{id}` | Get skill by ID |

## License

MIT

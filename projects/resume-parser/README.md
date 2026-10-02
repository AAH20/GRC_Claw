# Resume Parser

Agentic AI resume parsing service built with FastAPI and LangChain DeepAgents.

## Features

- **Multi-format support**: Parse PDF, DOCX, and TXT resumes
- **5 specialized agents**: ResumeParser, ContactExtractor, SkillsExtractor, ExperienceExtractor, EducationExtractor
- **Structured output**: Pydantic-validated resume data models
- **Production-ready**: Docker, Kubernetes, CI/CD, comprehensive tests

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run locally
uvicorn resume_parser.main:create_app --factory --reload

# Run with Docker
docker-compose up --build

# Run tests
pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/health` | Detailed health check |
| POST | `/api/v1/parse` | Parse resume file |
| POST | `/api/v1/parse/text` | Parse resume from text |
| GET | `/api/v1/resumes` | List parsed resumes |
| GET | `/api/v1/resumes/{id}` | Get parsed resume by ID |
| DELETE | `/api/v1/resumes/{id}` | Delete parsed resume |
| POST | `/api/v1/agents/parse` | Parse with specific agent |
| GET | `/api/v1/agents` | List available agents |
| GET | `/api/v1/agents/{name}` | Get agent info |
| POST | `/api/v1/agents/{name}/run` | Run specific agent |
| GET | `/api/v1/stats` | Service statistics |

## Architecture

```
src/resume_parser/
├── agents/          # LangChain DeepAgents implementations
├── api/             # FastAPI routes and dependencies
├── config/          # Settings and configuration
├── integrations/    # LLM and storage integrations
├── models/          # Pydantic data models
├── services/        # Business logic services
├── utils/           # Utility functions
└── main.py          # Application entry point
```

## License

MIT

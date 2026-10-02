# Candidate Matcher

AI-powered candidate-job matching service using LangChain DeepAgents. Provides semantic similarity matching, skills gap analysis, bias-aware ranking, culture fit assessment, and explainable match results.

## Features

- **SemanticMatcherAgent**: Computes semantic similarity between candidates and jobs using embeddings
- **SkillsGapAnalyzerAgent**: Identifies and quantifies skills gaps between candidate profiles and job requirements
- **BiasAwareRankerAgent**: Ranks candidates with bias detection and mitigation
- **CultureFitAssessorAgent**: Evaluates cultural alignment between candidates and organizations
- **MatchExplainerAgent**: Generates human-readable explanations for match results

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn candidate_matcher.main:create_app --factory --reload

# Or with Docker
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| POST | `/api/v1/match` | Match candidates to a job |
| POST | `/api/v1/match/batch` | Batch match multiple candidates |
| GET | `/api/v1/match/{match_id}` | Get match result by ID |
| POST | `/api/v1/analyze/skills-gap` | Analyze skills gap |
| POST | `/api/v1/analyze/bias` | Run bias analysis |
| POST | `/api/v1/analyze/culture-fit` | Assess culture fit |
| POST | `/api/v1/explain` | Explain a match result |
| GET | `/api/v1/candidates/{candidate_id}` | Get candidate profile |
| POST | `/api/v1/candidates` | Create candidate profile |
| GET | `/api/v1/jobs/{job_id}` | Get job posting |
| POST | `/api/v1/jobs` | Create job posting |

## Architecture

```
src/candidate_matcher/
├── agents/           # LangChain DeepAgents implementations
├── api/              # FastAPI routes and dependencies
├── config/           # Settings and configuration
├── integrations/     # LLM and vector store clients
├── models/           # Pydantic schemas
└── tests/            # Pytest test suite
```

## License

MIT

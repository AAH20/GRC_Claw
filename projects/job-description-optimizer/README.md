# Job Description Optimizer

Agentic AI-powered job description optimizer built with FastAPI and LangChain DeepAgents.

## Features

- **Bias Removal**: Detects and removes gendered, ageist, and culturally biased language
- **SEO Optimization**: Improves search engine visibility for job postings
- **ATS Compatibility**: Ensures compatibility with Applicant Tracking Systems
- **Tone Analysis**: Evaluates and improves the tone of job descriptions
- **Keyword Optimization**: Identifies and suggests relevant industry keywords

## Architecture

```
src/job_description_optimizer/
├── main.py                 # FastAPI application factory
├── config/                 # Settings and configuration
├── models/                 # Pydantic schemas
├── agents/                 # LangChain DeepAgents
│   ├── bias_remover.py
│   ├── seo_optimizer.py
│   ├── ats_compatibility.py
│   ├── tone_analyzer.py
│   └── keyword_optimizer.py
├── api/                    # FastAPI routes
├── integrations/           # External service clients
└── tests/                  # Pytest test suite
```

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn job_description_optimizer.main:create_app --factory --reload

# Or use Docker
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/` | Service info |
| POST | `/optimize` | Full optimization pipeline |
| POST | `/optimize/bias` | Bias removal only |
| POST | `/optimize/seo` | SEO optimization only |
| POST | `/optimize/ats` | ATS compatibility check |
| POST | `/optimize/tone` | Tone analysis only |
| POST | `/optimize/keywords` | Keyword optimization only |
| POST | `/analyze` | Comprehensive analysis |
| GET | `/agents` | List available agents |
| GET | `/agents/{name}` | Agent details |

## License

MIT

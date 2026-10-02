# Talent Pool Manager

An agentic AI-powered talent pool management system built with FastAPI and LangChain DeepAgents.

## Features

- **Candidate Discovery**: AI-powered candidate sourcing from multiple platforms
- **Pool Segmentation**: Intelligent talent pool segmentation based on skills and experience
- **Engagement Optimization**: AI-driven engagement strategy optimization
- **Talent Scoring**: Automated candidate scoring and ranking
- **Outreach Automation**: Personalized outreach message generation and management

## Architecture

```
src/talent_pool_manager/
├── agents/           # LangChain DeepAgents implementations
├── api/              # FastAPI routes and dependencies
├── config/           # Application configuration
├── integrations/     # External service integrations
├── models/           # Pydantic data models
└── tests/            # Test suite
```

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run the application
uvicorn talent_pool_manager.main:create_app --factory --reload
```

### Docker

```bash
docker-compose up --build
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest
```

## License

MIT

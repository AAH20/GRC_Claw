# Agency Marketing

Standalone modularized agentic AI marketing platform for agency workflows. Built with LangChain DeepAgents, grc-marketing-core, and optimized for multi-client agency operations.

## Architecture

```
agency_marketing/
├── agents/           # 5 specialized AI agents
│   ├── research.py       # Market & competitor research
│   ├── strategy.py       # Campaign strategy & planning
│   ├── creative.py       # Content & creative generation
│   ├── launch.py         # Campaign launch & deployment
│   └── optimization.py   # Performance optimization
├── api/              # FastAPI REST endpoints
│   ├── campaigns.py      # Campaign CRUD & lifecycle
│   └── clients.py        # Client management
├── integrations/     # CRM & marketing platform connectors
│   ├── salesforce.py     # Salesforce CRM
│   ├── hubspot.py     # HubSpot CRM
│   └── gohighlevel.py    # GoHighLevel
├── config/           # Configuration management
└── main.py           # Application entry point
```

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run development server
uvicorn agency_marketing.main:app --reload --port 8000
```

## Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

## Kubernetes

```bash
# Deploy to Kubernetes cluster
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI documentation |
| POST | `/api/v1/campaigns` | Create new campaign |
| GET | `/api/v1/campaigns` | List all campaigns |
| GET | `/api/v1/campaigns/{id}` | Get campaign details |
| PUT | `/api/v1/campaigns/{id}` | Update campaign |
| DELETE | `/api/v1/campaigns/{id}` | Delete campaign |
| POST | `/api/v1/clients` | Create new client |
| GET | `/api/v1/clients` | List all clients |
| GET | `/api/v1/clients/{id}` | Get client details |

## Agents

### Research Agent
- Market analysis and trend identification
- Competitor research and benchmarking
- Audience segmentation and insights
- Industry report generation

### Strategy Agent
- Campaign strategy development
- Budget allocation recommendations
- Channel selection and timing
- KPI definition and tracking plans

### Creative Agent
- Ad copy generation (multiple variants)
- Visual content briefs
- Brand voice consistency
- A/B test variant creation

### Launch Agent
- Campaign deployment orchestration
- Multi-channel publishing
- Launch checklist management
- Go-live verification

### Optimization Agent
- Performance monitoring and analysis
- Budget reallocation recommendations
- Creative refresh suggestions
- ROI optimization strategies

## Integrations

### Salesforce
- Lead and opportunity sync
- Campaign member tracking
- Custom field mapping
- Bulk data operations

### HubSpot
- Contact and company sync
- Deal pipeline management
- Email campaign tracking
- Workflow automation

### GoHighLevel
- Funnel management
- Appointment scheduling
- Reputation management
- SMS/Email campaigns

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:
- `OPENAI_API_KEY` - OpenAI API key for LLM operations
- `LANGCHAIN_API_KEY` - LangSmith tracing (optional)
- `SALESFORCE_*` - Salesforce credentials
- `HUBSPOT_API_KEY` - HubSpot API key
- `GOHIGHLEVEL_API_KEY` - GoHighLevel API key

## CI/CD

The project includes GitHub Actions workflows for:
- Linting and type checking (Ruff, mypy)
- Unit and integration tests (pytest)
- Docker image build and push
- Kubernetes deployment

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agency_marketing --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v
```

## License

MIT License - see LICENSE file for details.

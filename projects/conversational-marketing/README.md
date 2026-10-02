# Conversational Marketing

A standalone, modularized agentic AI conversational marketing platform built with LangChain DeepAgents and grc-marketing-core. It provides intelligent conversation handling across multiple chatbot platforms (WhatsApp, Facebook Messenger, Slack) with five specialized agents.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Intent  │ Response │ Handoff  │Optimization│ Analytics  │
│Detection │Generation│  Agent   │  Agent    │   Agent     │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              LangChain DeepAgents + grc-marketing-core    │
├─────────────────────────────────────────────────────────┤
│  WhatsApp  │  Facebook Messenger  │  Slack  │  REST API   │
└─────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Responsibility |
|-------|---------------|
| **Intent Detection** | Classifies user messages into marketing intents (purchase, support, inquiry, complaint, etc.) |
| **Response Generation** | Generates contextually appropriate marketing responses using LLM |
| **Handoff** | Determines when and how to escalate to human agents |
| **Optimization** | Analyzes conversation patterns and suggests improvements |
| **Analytics** | Tracks metrics, generates reports, and provides insights |

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional)
- API keys for your LLM provider (OpenAI, Anthropic, etc.)

### Local Development

```bash
# Clone and navigate
cd conversational-marketing

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run the application
uvicorn conversational_marketing.main:app --reload --port 8000
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t conversational-marketing .
docker run -p 8000:8000 --env-file .env conversational-marketing
```

### Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods -l app=conversational-marketing
kubectl get svc conversational-marketing
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/conversations` | Create a new conversation |
| `GET` | `/api/v1/conversations/{id}` | Get conversation by ID |
| `POST` | `/api/v1/conversations/{id}/messages` | Send a message |
| `GET` | `/api/v1/leads` | List leads |
| `POST` | `/api/v1/leads` | Create a lead |
| `GET` | `/api/v1/analytics/summary` | Get analytics summary |
| `POST` | `/webhooks/whatsapp` | WhatsApp webhook |
| `POST` | `/webhooks/facebook` | Facebook Messenger webhook |
| `POST` | `/webhooks/slack` | Slack webhook |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (dev/staging/prod) | `dev` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `WHATSAPP_TOKEN` | WhatsApp Business API token | — |
| `FACEBOOK_PAGE_TOKEN` | Facebook Page Access Token | — |
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token | — |
| `MAX_CONVERSATION_HISTORY` | Max messages in context | `20` |
| `HANDOFF_THRESHOLD` | Confidence threshold for handoff | `0.6` |

## Project Structure

```
conversational-marketing/
├── src/conversational_marketing/
│   ├── agents/           # Five specialized agents
│   ├── api/              # REST API routers
│   ├── integrations/     # Platform integrations
│   ├── config/           # Configuration management
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic services
│   ├── utils/            # Utility functions
│   ├── main.py           # FastAPI application entry point
│   └── __init__.py
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/conversational_marketing --cov-report=term-missing

# Run specific test file
pytest tests/test_agents.py -v
```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) provides:

- **CI**: Linting (ruff), type checking (mypy), and testing on every push/PR
- **CD**: Docker image build and push to registry on main branch merges
- **Deploy**: Automatic deployment to Kubernetes cluster

## License

MIT

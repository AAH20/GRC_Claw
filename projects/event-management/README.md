# Event Management

A standalone, modularized agentic AI event management system built with FastAPI, LangChain DeepAgents, and grc-marketing-core.

## Architecture

The system consists of five specialized agents orchestrated through a FastAPI application:

| Agent | Responsibility |
|-------|---------------|
| **Planning** | Event strategy, venue selection, budget allocation, timeline creation |
| **Promotion** | Marketing campaigns, social media, email outreach, ticket sales |
| **Execution** | Day-of logistics, vendor coordination, attendee check-in |
| **Follow-up** | Post-event surveys, thank-you emails, lead nurturing |
| **Performance Analytics** | KPI tracking, ROI analysis, attendee engagement metrics |

## Project Structure

```
event-management/
├── src/event_management/
│   ├── agents/           # Five specialized agents
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # Third-party platform connectors
│   ├── config/           # Configuration models
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── config/               # Runtime configuration
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy and configure environment
cp config/.env.example .env

# Run the application
uvicorn event_management.main:app --reload --port 8000
```

### Docker

```bash
docker-compose up --build
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/events` | Create a new event |
| `GET` | `/api/v1/events` | List all events |
| `GET` | `/api/v1/events/{event_id}` | Get event details |
| `PUT` | `/api/v1/events/{event_id}` | Update an event |
| `DELETE` | `/api/v1/events/{event_id}` | Delete an event |
| `POST` | `/api/v1/events/{event_id}/attendees` | Register attendee |
| `GET` | `/api/v1/events/{event_id}/attendees` | List attendees |
| `POST` | `/api/v1/events/{event_id}/plan` | Generate event plan |
| `POST` | `/api/v1/events/{event_id}/promote` | Launch promotion campaign |
| `POST` | `/api/v1/events/{event_id}/execute` | Begin event execution |
| `POST` | `/api/v1/events/{event_id}/follow-up` | Trigger follow-up sequence |
| `GET` | `/api/v1/events/{event_id}/analytics` | Get performance analytics |

## Integrations

- **Eventbrite** — Event creation and ticket management
- **Meetup** — Community event publishing
- **Luma** — Modern event registration and discovery

## Configuration

All configuration is managed via environment variables. See `config/.env.example` for the full list.

## Testing

```bash
pytest tests/ -v --cov=event_management
```

## License

MIT

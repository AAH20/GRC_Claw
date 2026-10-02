# CRM Enhancer

AI-powered CRM enhancement platform with 6 autonomous agents that integrate with Salesforce, HubSpot, and Pipedrive.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Contact  │  Deal    │  Task    │ Meeting  │  Follow-up  │
│Enrichment│ Scoring  │Automation│Scheduling│ Automation  │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              Performance Analytics Agent                  │
├─────────────────────────────────────────────────────────┤
│         Salesforce │ HubSpot │ Pipedrive                 │
└─────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Purpose |
|-------|---------|
| **Contact Enrichment** | Enriches contact records with firmographic and technographic data |
| **Deal Scoring** | Scores deals using ML-based predictive models |
| **Task Automation** | Automates repetitive CRM tasks and workflows |
| **Meeting Scheduling** | Intelligent meeting scheduling with calendar integration |
| **Follow-up Automation** | Automated follow-up sequences and reminders |
| **Performance Analytics** | CRM performance metrics and insights |

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env

# Run the application
uvicorn crm_enhancer.main:app --reload --port 8000
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

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/contacts/enrich` | POST | Enrich a contact record |
| `/api/v1/deals/score` | POST | Score a deal |
| `/api/v1/deals` | GET/POST | List/create deals |
| `/metrics` | GET | Prometheus metrics |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

## Testing

```bash
pytest tests/ -v --cov=src/crm_enhancer
```

## CI/CD

GitHub Actions workflow runs on every push to `main`:
1. Lint and type-check
2. Run tests with coverage
3. Build Docker image
4. Push to container registry
5. Deploy to Kubernetes

## License

MIT

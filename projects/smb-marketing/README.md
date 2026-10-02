# SMB Marketing

> Standalone modularized agentic AI marketing platform for small businesses.

## Overview

SMB Marketing is a production-grade Python application that orchestrates five specialized AI agents — **Content**, **Campaigns**, **Social**, **Email**, and **Analytics** — to automate end-to-end marketing workflows for small and medium-sized businesses.

Built with **LangChain DeepAgents**, **FastAPI**, and **grc-marketing-core**, the platform provides a REST API for managing marketing campaigns, generating content, scheduling social media posts, sending email newsletters, and analyzing performance metrics.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Application                │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ Content  │ Campaigns│  Social  │  Email   │Analytics│
│  Agent   │  Agent   │  Agent   │  Agent   │  Agent  │
├──────────┴──────────┴──────────┴──────────┴─────────┤
│              grc-marketing-core                      │
├─────────────────────────────────────────────────────┤
│  Meta API  │  Google Ads  │  Mailchimp  │  ...      │
└─────────────────────────────────────────────────────┘
```

## Features

- **Content Agent** — Generate blog posts, ad copy, product descriptions, and social captions using LLM-powered content pipelines.
- **Campaigns Agent** — Create, manage, and optimize multi-channel marketing campaigns with budget allocation and scheduling.
- **Social Agent** — Schedule and publish posts across Meta (Facebook/Instagram) with hashtag optimization and best-time analysis.
- **Email Agent** — Design and send email campaigns via Mailchimp with audience segmentation and A/B testing.
- **Analytics Agent** — Aggregate performance data across channels, generate insights, and produce actionable reports.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- API keys for Meta, Google Ads, Mailchimp, and an LLM provider (OpenAI)

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/smb-marketing.git
cd smb-marketing

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp config/.env.example config/.env
# Edit config/.env with your API keys

# Run the application
uvicorn smb_marketing.main:app --reload --port 8000
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# The API will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/content/generate` | Generate marketing content |
| `GET` | `/api/v1/campaigns` | List all campaigns |
| `POST` | `/api/v1/campaigns` | Create a new campaign |
| `GET` | `/api/v1/campaigns/{id}` | Get campaign details |
| `PUT` | `/api/v1/campaigns/{id}` | Update a campaign |
| `DELETE` | `/api/v1/campaigns/{id}` | Delete a campaign |
| `POST` | `/api/v1/social/schedule` | Schedule a social post |
| `POST` | `/api/v1/email/send` | Send an email campaign |
| `GET` | `/api/v1/analytics/report` | Get analytics report |

## Project Structure

```
smb-marketing/
├── .github/workflows/ci-cd.yml   # CI/CD pipeline
├── config/
│   ├── config.yaml               # Application configuration
│   └── .env.example              # Environment variable template
├── k8s/
│   ├── deployment.yaml           # Kubernetes deployment
│   └── service.yaml              # Kubernetes service
├── src/smb_marketing/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── content.py            # Content generation agent
│   │   ├── campaigns.py          # Campaign management agent
│   │   ├── social.py             # Social media agent
│   │   ├── email.py              # Email marketing agent
│   │   └── analytics.py          # Analytics agent
│   ├── api/
│   │   ├── campaigns.py          # Campaign API routes
│   │   └── content.py            # Content API routes
│   └── integrations/
│       ├── meta.py               # Meta (Facebook/Instagram) integration
│       ├── google_ads.py         # Google Ads integration
│       └── mailchimp.py          # Mailchimp integration
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_integrations.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Configuration

All configuration is managed through environment variables (see `config/.env.example`) and the YAML config file (`config/config.yaml`).

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM calls |
| `META_ACCESS_TOKEN` | Meta Graph API access token |
| `META_PAGE_ID` | Facebook Page ID |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads API developer token |
| `GOOGLE_ADS_CUSTOMER_ID` | Google Ads customer ID |
| `MAILCHIMP_API_KEY` | Mailchimp API key |
| `MAILCHIMP_SERVER_PREFIX` | Mailchimp server prefix (e.g., `us1`) |
| `MAILCHIMP_LIST_ID` | Mailchimp audience/list ID |

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) automates:

1. **Lint** — Ruff linting and formatting checks
2. **Type Check** — MyPy static type checking
3. **Test** — Pytest with coverage reporting
4. **Build** — Docker image build and push to registry
5. **Deploy** — Kubernetes deployment on main branch

## License

MIT

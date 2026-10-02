# Social Media Manager

A standalone, modularized agentic AI social media management platform built with LangChain DeepAgents and FastAPI.

## Architecture

The system is composed of 6 autonomous agents, each responsible for a distinct aspect of social media management:

| Agent | Responsibility |
|-------|---------------|
| **Content Creation** | Generates platform-aware post copy, hashtags, and media suggestions |
| **Scheduling** | Plans optimal posting calendars and schedules content across platforms |
| **Engagement** | Monitors and responds to comments, mentions, and DMs |
| **Social Listening** | Tracks brand mentions, sentiment, and trending topics |
| **Influencer Identification** | Discovers and scores potential brand partners |
| **Performance Analytics** | Aggregates metrics and produces insight reports |

## Supported Platforms

- Twitter/X
- Instagram
- Facebook
- LinkedIn
- TikTok

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)

### Local Development

```bash
# Clone and enter the project
cd social-media-manager

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn social_media_manager.main:app --reload --port 8000
```

### Docker

```bash
docker build -t social-media-manager .
docker run -p 8000:8000 --env-file .env social-media-manager
```

### Docker Compose

```bash
docker-compose up -d
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/posts` | Create a new post |
| `GET` | `/api/v1/posts` | List posts |
| `GET` | `/api/v1/posts/{id}` | Get a specific post |
| `DELETE` | `/api/v1/posts/{id}` | Delete a post |
| `GET` | `/api/v1/analytics` | Get analytics dashboard |
| `GET` | `/api/v1/analytics/{platform}` | Platform-specific analytics |
| `POST` | `/api/v1/agents/{agent}/invoke` | Invoke a specific agent |

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

Key settings:

- `APP_ENV` — Environment (development, staging, production)
- `LOG_LEVEL` — Logging verbosity
- `TWITTER_API_KEY` / `TWITTER_API_SECRET` — Twitter credentials
- `INSTAGRAM_ACCESS_TOKEN` — Instagram Graph API token
- `FACEBOOK_ACCESS_TOKEN` — Facebook Graph API token
- `LINKEDIN_ACCESS_TOKEN` — LinkedIn OAuth token
- `TIKTOK_ACCESS_TOKEN` — TikTok API token

## Project Structure

```
social-media-manager/
├── src/social_media_manager/
│   ├── agents/           # 6 autonomous agents
│   ├── api/              # FastAPI route handlers
│   ├── integrations/     # Platform API clients
│   ├── config.py         # Settings management
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Testing

```bash
pytest
```

## License

MIT

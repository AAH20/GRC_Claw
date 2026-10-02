# Video Marketing

A standalone, modularized agentic AI video marketing platform built with FastAPI, LangChain DeepAgents, and grc-marketing-core.

## Architecture

The platform consists of five specialized agents orchestrated through a FastAPI application:

| Agent | Responsibility |
|-------|---------------|
| **Script Generation** | AI-powered video script creation from briefs and topics |
| **Production** | Video asset generation, storyboarding, and rendering pipelines |
| **Editing** | Automated video editing, transitions, captions, and effects |
| **Distribution** | Multi-platform publishing to YouTube, Instagram, and TikTok |
| **Analytics** | Performance tracking, engagement metrics, and ROI analysis |

## Project Structure

```
video-marketing/
├── src/video_marketing/
│   ├── agents/           # Five specialized agents
│   │   ├── script_generation.py
│   │   ├── production.py
│   │   ├── editing.py
│   │   ├── distribution.py
│   │   └── analytics.py
│   ├── api/              # FastAPI route handlers
│   │   ├── videos.py
│   │   └── campaigns.py
│   ├── integrations/     # Platform connectors
│   │   ├── youtube.py
│   │   ├── instagram.py
│   │   └── tiktok.py
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── config/               # Configuration files
├── k8s/                  # Kubernetes manifests
└── .github/workflows/    # CI/CD pipeline
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- API keys for LLM provider and social platforms

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run the application
uvicorn video_marketing.main:app --reload --port 8000
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
| `POST` | `/api/v1/videos` | Create a new video project |
| `GET` | `/api/v1/videos` | List all video projects |
| `GET` | `/api/v1/videos/{id}` | Get video project details |
| `POST` | `/api/v1/videos/{id}/generate` | Generate video from script |
| `POST` | `/api/v1/videos/{id}/publish` | Publish to social platforms |
| `GET` | `/api/v1/campaigns` | List marketing campaigns |
| `POST` | `/api/v1/campaigns` | Create a new campaign |
| `GET` | `/api/v1/analytics/{video_id}` | Get video performance analytics |

## Integrations

- **YouTube** — Video upload, metadata management, and analytics
- **Instagram** — Reels and IGTV publishing
- **TikTok** — Video posting and trend analysis

## Configuration

All configuration is managed via environment variables. See `.env.example` for the full list.

## Testing

```bash
pytest tests/ -v --cov=video_marketing
```

## License

MIT

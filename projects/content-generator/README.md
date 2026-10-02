# Content Generator

A standalone, modularized multi-agent AI content generation pipeline built with LangChain DeepAgents. It orchestrates five specialized agents — **Researcher**, **Strategist**, **Writer**, **SEO Editor**, and **Atomizer** — to produce high-quality, SEO-optimized marketing content in multiple languages (English, Arabic with dialect support).

## Architecture

```
┌─────────────┐    ┌────────────┐    ┌─────────┐    ┌────────────┐    ┌───────────┐
│  Researcher │───▶│ Strategist │───▶│ Writer  │───▶│ SEO Editor │───▶│ Atomizer  │
│  (SerpAPI)  │    │  (Claude)  │    │ (GPT-4) │    │  (GPT-4)   │    │  (Claude) │
└─────────────┘    └────────────┘    └─────────┘    └────────────┘    └───────────┘
```

### Agents

| Agent | Model | Role |
|-------|-------|------|
| **Researcher** | SerpAPI + Claude | Gathers SERP data, competitor insights, and trending topics |
| **Strategist** | Claude | Defines content strategy, target audience, tone, and angle |
| **Writer** | GPT-4 | Produces long-form content (articles, landing pages, social posts) |
| **SEO Editor** | GPT-4 | Optimizes for search: meta tags, keyword density, readability |
| **Atomizer** | Claude | Breaks content into platform-specific micro-content (tweets, LinkedIn, etc.) |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- API keys: OpenAI, Anthropic, SerpAPI

### Local Development

```bash
# Clone and enter the project
cd content-generator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp config/.env.example .env
# Edit .env with your API keys

# Run the server
uvicorn content_generator.main:app --reload --port 8000
```

### Docker

```bash
docker build -t content-generator .
docker run -p 8000:8000 --env-file .env content-generator
```

### Docker Compose

```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/content/generate` | Generate full content pipeline |
| `POST` | `/api/v1/content/translate` | Translate content to target language |
| `POST` | `/api/v1/content/atomize` | Atomize content into micro-content |
| `GET` | `/metrics` | Prometheus metrics |

## Configuration

All configuration is managed via environment variables (see `config/.env.example`) and `config/config.yaml`.

### Supported Languages

- **English** (`en`) — Default
- **Arabic** (`ar`) — Modern Standard Arabic
- **Arabic (Egyptian)** (`ar-EG`) — Egyptian dialect
- **Arabic (Gulf)** (`ar-SA`) — Gulf dialect
- **Arabic (Levantine)** (`ar-LB`) — Levantine dialect

## Project Structure

```
content-generator/
├── config/
│   ├── config.yaml
│   └── .env.example
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── src/
│   └── content_generator/
│       ├── agents/
│       │   ├── researcher.py
│       │   ├── strategist.py
│       │   ├── writer.py
│       │   ├── seo_editor.py
│       │   └── atomizer.py
│       ├── api/
│       │   ├── content.py
│       │   └── translation.py
│       ├── integrations/
│       │   ├── openai.py
│       │   ├── anthropic.py
│       │   └── serpapi.py
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_integrations.py
├── .github/workflows/ci-cd.yml
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## CI/CD

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs on every push to `main`:

1. **Lint** — Ruff + mypy
2. **Test** — pytest with coverage
3. **Build** — Docker image build
4. **Deploy** — Push to registry and deploy to Kubernetes

## License

MIT

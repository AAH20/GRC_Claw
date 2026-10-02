# Employer Branding AI Platform

AI-powered employer branding management platform built with FastAPI and LangChain DeepAgents.

## Features

- **Content Generation**: AI-powered job postings, social media content, blog posts, and more
- **Sentiment Analysis**: Analyze text sentiment with aspect-based analysis and emotion detection
- **Reputation Management**: Monitor and score employer reputation across multiple platforms
- **Review Analysis**: Fetch and analyze reviews from Glassdoor, Indeed, and LinkedIn
- **Brand Strategy**: Create comprehensive employer brand strategies with EVP and content pillars

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Docker (optional)

### Installation

```bash
cd projects/employer-branding
pip install -e ".[dev]"
```

### Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

### Running Locally

```bash
uvicorn employer_branding.main:app --reload
```

### Running with Docker

```bash
docker-compose up --build
```

### Running Tests

```bash
pytest --cov=src/employer_branding
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| GET | `/live` | Liveness probe |
| POST | `/api/v1/content/generate` | Generate brand content |
| GET | `/api/v1/content/` | List content assets |
| GET | `/api/v1/content/{id}` | Get content asset |
| PATCH | `/api/v1/content/{id}` | Update content asset |
| DELETE | `/api/v1/content/{id}` | Delete content asset |
| POST | `/api/v1/content/{id}/publish` | Publish content asset |
| POST | `/api/v1/sentiment/analyze` | Analyze sentiment |
| GET | `/api/v1/sentiment/{id}` | Get sentiment report |
| POST | `/api/v1/sentiment/batch` | Batch sentiment analysis |
| POST | `/api/v1/reputation/analyze` | Analyze reputation |
| GET | `/api/v1/reputation/{id}` | Get reputation score |
| GET | `/api/v1/reputation/company/{name}` | Get company reputation |
| POST | `/api/v1/reputation/compare` | Compare reputations |
| POST | `/api/v1/reviews/fetch` | Fetch reviews |
| GET | `/api/v1/reviews/` | List reviews |
| GET | `/api/v1/reviews/{id}` | Get review |
| GET | `/api/v1/reviews/summary/{name}` | Review summary |
| POST | `/api/v1/strategy/create` | Create brand strategy |
| GET | `/api/v1/strategy/` | List strategies |
| GET | `/api/v1/strategy/{id}` | Get strategy |
| PATCH | `/api/v1/strategy/{id}` | Update strategy |
| DELETE | `/api/v1/strategy/{id}` | Delete strategy |
| POST | `/api/v1/strategy/{id}/activate` | Activate strategy |

## Project Structure

```
src/employer_branding/
├── agents/           # AI agent implementations
│   ├── base.py
│   ├── content_generator.py
│   ├── sentiment_analyzer.py
│   ├── reputation_manager.py
│   ├── review_analyzer.py
│   └── brand_strategy.py
├── api/              # FastAPI route handlers
│   ├── health.py
│   ├── content.py
│   ├── sentiment.py
│   ├── reputation.py
│   ├── reviews.py
│   └── strategy.py
├── config/           # Application configuration
├── integrations/     # External API clients
├── tests/            # Test suite
├── main.py           # Application entry point
└── models.py         # Pydantic data models
```

## License

MIT

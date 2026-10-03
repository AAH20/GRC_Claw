# UGC Marketplace

Unified agentic AI platform for content marketplace operations. Consolidates 10 separate UGC marketplace projects into a single, standalone, modularized Python project.

## Architecture

```mermaid
graph TB
    subgraph "API Layer"
        A[FastAPI Application]
        A --> A1[Content Moderation API]
        A --> A2[Creator Monetization API]
        A --> A3[Content Discovery API]
        A --> A4[Rights Management API]
        A --> A5[Quality Scoring API]
        A --> A6[Fraud Detection API]
        A --> A7[Creator Analytics API]
        A --> A8[Licensing Engine API]
        A --> A9[Community Curation API]
        A --> A10[Content Marketplace API]
    end

    subgraph "Agent Layer"
        B1[Content Moderation Agents]
        B2[Creator Monetization Agents]
        B3[Content Discovery Agents]
        B4[Rights Management Agents]
        B5[Quality Scoring Agents]
        B6[Fraud Detection Agents]
        B7[Creator Analytics Agents]
        B8[Licensing Engine Agents]
        B9[Community Curation Agents]
        B10[Content Marketplace Agents]
    end

    subgraph "Integration Layer"
        C1[Storage Backends]
        C2[Payment Gateways]
        C3[Social Media APIs]
        C4[Notification Services]
        C5[Cache Services]
    end

    subgraph "Infrastructure"
        D1[PostgreSQL]
        D2[Redis]
        D3[Kafka]
        D4[Kubernetes]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4
    A5 --> B5
    A6 --> B6
    A7 --> B7
    A8 --> B8
    A9 --> B9
    A10 --> B10

    B1 --> C1
    B2 --> C2
    B3 --> C3
    B4 --> C1
    B5 --> C5
    B6 --> D3
    B7 --> C3
    B8 --> C1
    B9 --> C4
    B10 --> C2

    C1 --> D1
    C5 --> D2
    C4 --> D3
```

## Modules

### Content Moderation Pipeline
- Text, image, and video moderation agents
- Policy enforcement with regex/keyword matching
- Appeal handling workflow
- Batch moderation support

### Creator Monetization
- Revenue analytics and reporting
- Payout management
- Subscription management
- Tier recommendation engine
- Stripe, PayPal, and Patreon integrations

### Content Discovery
- Semantic search with vector embeddings
- Personalized recommendations
- Trend detection
- Search explanation

### Rights Management
- Copyright infringement detection
- License detection and validation
- Usage tracking
- Takedown request processing

### Quality Scoring
- Readability analysis (Flesch-Kincaid)
- Originality scoring
- Engagement potential scoring
- SEO optimization scoring
- Improvement suggestions

### Fraud Detection
- Anomaly detection
- Pattern matching
- Risk scoring
- Account analysis
- Real-time transaction monitoring

### Creator Analytics
- Audience analysis
- Content performance tracking
- Engagement analysis
- Growth prediction
- Revenue tracking
- YouTube, Twitter, Instagram, TikTok integrations

### Licensing Engine
- License agreement generation
- Terms negotiation
- Compliance tracking
- Royalty calculation
- Contract analysis

### Community Curation
- Content ranking
- Quality filtering
- Topic clustering
- Trend surfacing
- Curation explanation

### Content Marketplace
- Listing management
- Pricing optimization
- Transaction processing
- Trust scoring
- Marketplace analytics

## Quick Start

### Docker

```bash
docker-compose up -d
```

### Local Development

```bash
pip install -e ".[dev]"
uvicorn ugc_marketplace.main:app --reload
```

### Kubernetes

```bash
kubectl apply -k k8s/overlays/development/
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI: http://localhost:8000/openapi.json

## Configuration

All settings are configurable via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment (development/production) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka brokers |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `SECRET_KEY` | `change-me-in-production` | Application secret |

## Testing

```bash
pytest --cov=src/ugc_marketplace --cov-report=term-missing
```

## License

MIT

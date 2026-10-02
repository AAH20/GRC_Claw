# Reputation System

Agentic AI reputation management system with scoring, badges, and trust tiers.

## Features

- **Reputation Scoring**: AI-powered reputation score calculation
- **Badge Management**: Automated badge assignment and evaluation
- **Trust Tiers**: Dynamic trust level management (Bronze → Diamond)
- **History Tracking**: Complete reputation change history
- **AI Explanations**: Human-readable reputation explanations

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn reputation_system.main:app --reload

# Docker
docker-compose up -d
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/health | Health check |
| GET | /api/v1/health/ready | Readiness check |
| POST | /api/v1/reputation/scores | Create reputation score |
| GET | /api/v1/reputation/scores/{member_id} | Get reputation score |
| PUT | /api/v1/reputation/scores/{member_id} | Update reputation score |
| DELETE | /api/v1/reputation/scores/{member_id} | Delete reputation score |
| GET | /api/v1/reputation/scores | List all scores |
| POST | /api/v1/reputation/scores/{member_id}/calculate | Calculate score with AI |
| POST | /api/v1/badges | Create badge |
| GET | /api/v1/badges/{badge_id} | Get badge |
| GET | /api/v1/badges | List badges |
| PUT | /api/v1/badges/{badge_id} | Update badge |
| DELETE | /api/v1/badges/{badge_id} | Delete badge |
| POST | /api/v1/badges/evaluate/{member_id} | Evaluate member badges |
| POST | /api/v1/trust-tiers | Create trust tier |
| GET | /api/v1/trust-tiers/{tier_id} | Get trust tier |
| GET | /api/v1/trust-tiers | List trust tiers |
| PUT | /api/v1/trust-tiers/{tier_id} | Update trust tier |
| DELETE | /api/v1/trust-tiers/{tier_id} | Delete trust tier |
| POST | /api/v1/trust-tiers/evaluate/{member_id} | Evaluate trust tier |
| POST | /api/v1/history | Create history entry |
| GET | /api/v1/history/{entry_id} | Get history entry |
| GET | /api/v1/history/member/{member_id} | Get member history |
| POST | /api/v1/history/analyze/{member_id} | Analyze member history |
| POST | /api/v1/explanations | Create explanation |
| GET | /api/v1/explanations/{explanation_id} | Get explanation |
| GET | /api/v1/explanations/member/{member_id} | Get member explanations |
| POST | /api/v1/explanations/generate/{member_id} | Generate explanation |

## Architecture

```
src/reputation_system/
├── agents/           # AI agents (LangChain DeepAgents)
│   ├── base.py
│   ├── reputation_scorer.py
│   ├── badge_manager.py
│   ├── trust_tier.py
│   ├── reputation_history.py
│   └── reputation_explainer.py
├── api/              # FastAPI routes
│   └── routes/
├── config/           # Settings
├── integrations/     # External services
├── models/           # Pydantic schemas
└── tests/            # pytest tests
```

## License

MIT

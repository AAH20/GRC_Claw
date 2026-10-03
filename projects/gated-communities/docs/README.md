# Gated Communities — Unified Platform

> A production-grade, modular gated community management platform consolidating 10 independent services into a single standalone application.

[![CI/CD](https://img.shields.io/badge/CI%2FCD-passing-brightgreen)](https://github.com/ahmedhassan/gated-communities/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-teal)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Gated Communities is a unified platform for managing gated online communities. It provides a comprehensive set of tools for tier management, moderation, access control, member verification, reputation tracking, compliance monitoring, and community governance — all accessible through a single REST API.

The platform is built with **FastAPI** and leverages **LangChain** for AI-powered agent capabilities across 10 modular domains with 57 specialized agents.

---

## Features

| Module | Description | Agents |
|--------|-------------|--------|
| **Tier Management** | Member tier evaluation, benefits, upgrades | 6 |
| **Moderation Queue** | Auto-moderation, queue optimization, escalation | 7 |
| **Access Control** | Permission evaluation, role management, policy enforcement | 6 |
| **Community Health Scorer** | Toxicity detection, engagement metrics | 2 |
| **Member Verification** | Identity verification, fraud prevention, trust scoring | 6 |
| **Escalation Workflow** | Auto-resolution, SLA tracking, priority routing | 6 |
| **Reputation System** | Reputation scoring, badges, trust tiers | 6 |
| **Compliance Monitor** | Policy tracking, violation detection, audits | 6 |
| **Moderation Analytics** | Trend analysis, predictor, performance metrics | 6 |
| **Community Governance** | Dispute resolution, rule enforcement, policy management | 6 |

**Total: 57 agents across 10 modules**

---

## Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Web[Web App]
        Mobile[Mobile App]
        Admin[Admin Panel]
    end

    subgraph "API Gateway"
        GW[FastAPI Gateway]
        Auth[Auth Middleware]
        RateLimit[Rate Limiter]
    end

    subgraph "Agent Services"
        direction TB
        subgraph "Tier Management"
            TE[Tier Evaluator]
            TA[Tier Analytics]
            TR[Upgrade Recommender]
            BM[Benefit Manager]
            AC[Access Controller]
        end
        subgraph "Moderation Queue"
            AM[Auto Moderator]
            QO[Queue Optimizer]
            HR[Human Review Router]
            PS[Priority Scorer]
            ESC[Escalation]
        end
        subgraph "Access Control"
            PE[Permission Evaluator]
            RM[Role Manager]
            AE[Access Auditor]
            AR[Access Recommender]
            PE2[Policy Enforcer]
        end
        subgraph "Community Health"
            TD[Toxicity Detector]
            EM[Engagement Metrics]
        end
        subgraph "Member Verification"
            IV[Identity Verifier]
            DC[Document Checker]
            FP[Fraud Preventor]
            TS[Trust Scorer]
            EX[Explainer]
        end
        subgraph "Escalation Workflow"
            AR2[Auto Resolver]
            SO[Resolution Optimizer]
            ST[SLA Tracker]
            EA[Escalation Analyzer]
            PR[Priority Router]
        end
        subgraph "Reputation System"
            RS[Reputation Scorer]
            BT[Trust Tier]
            BM2[Badge Manager]
            RH[Reputation History]
            RE[Reputation Explainer]
        end
        subgraph "Compliance Monitor"
            PT[Policy Tracker]
            AR3[Audit Reporter]
            CS[Compliance Scorer]
            VD[Violation Detector]
            REM[Remediation]
        end
        subgraph "Moderation Analytics"
            MP[Moderation Predictor]
            MPerf[Moderator Performance]
            PE3[Policy Effectiveness]
            AE2[Analytics Explainer]
            TA2[Trend Analyzer]
        end
        subgraph "Community Governance"
            DR[Dispute Resolver]
            GA[Governance Analytics]
            RE2[Rule Enforcer]
            PM[Policy Manager]
            GE[Governance Explainer]
        end
    end

    subgraph "Integration Layer"
        LLM[LLM Service]
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Notif[Notifications]
        Ext[External APIs]
    end

    subgraph "Infrastructure"
        K8s[Kubernetes]
        CI[CI/CD Pipeline]
        Mon[Monitoring]
        Log[Logging]
    end

    Web & Mobile & Admin --> GW
    GW --> Auth --> RateLimit
    RateLimit --> Agent Services
    Agent Services --> Integration Layer
    Agent Services --> Infrastructure
```

---

## Quick Start

### Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/ahmedhassan/gated-communities.git
cd gated-communities

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start server
uvicorn gated_communities.main:app --reload
```

### Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n gated-communities
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](api-reference.md) | Full API documentation with examples |
| [Architecture](architecture.md) | System architecture with diagrams |
| [User Guide](user-guide.md) | User guide with screenshots descriptions |
| [Deployment Guide](deployment-guide.md) | Deployment guide for all environments |
| [Development Guide](development-guide.md) | Development setup and contribution guide |

---

## Project Structure

```
gated-communities/
├── src/gated_communities/
│   ├── agents/           # 57 AI agents across 10 modules
│   │   ├── access_control/
│   │   ├── community_governance/
│   │   ├── community_health_scorer/
│   │   ├── compliance_monitor/
│   │   ├── escalation_workflow/
│   │   ├── member_verification/
│   │   ├── moderation_analytics/
│   │   ├── moderation_queue/
│   │   ├── reputation_system/
│   │   └── tier_management/
│   ├── api/              # FastAPI routes
│   ├── integrations/     # External service integrations
│   ├── config/           # Settings and logging
│   ├── models/           # Pydantic schemas
│   └── tests/            # Test suite
├── frontend/             # Next.js frontend
├── k8s/                  # Kubernetes manifests
├── docker/               # Docker compose files
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `REDIS_URL` | — | Redis connection string |
| `LLM_API_KEY` | — | OpenAI API key |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENVIRONMENT` | `production` | Deployment environment |
| `DEBUG` | `false` | Debug mode |
| `SECRET_KEY` | — | Application secret key |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `MODERATION_THRESHOLD` | `0.8` | Auto-moderation threshold |
| `ESCALATION_TIMEOUT_MINUTES` | `30` | Escalation timeout |
| `REPUTATION_DECAY_DAYS` | `90` | Reputation decay period |
| `COMPLIANCE_AUDIT_RETENTION_DAYS` | `365` | Audit log retention |

---

## Contributing

See the [Development Guide](development-guide.md) for setup instructions and contribution guidelines.

---

## License

[MIT](LICENSE) © Ahmed Hassan

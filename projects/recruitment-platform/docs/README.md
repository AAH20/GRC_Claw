# Recruitment Platform — Documentation

## Overview

Welcome to the Recruitment Platform documentation. This directory contains comprehensive documentation for the unified AI-powered recruitment automation system built with FastAPI.

## Documentation Index

| Document | Description |
|----------|-------------|
| [API Reference](./api-reference.md) | Complete API documentation with request/response examples for all 42 endpoints |
| [Architecture](./architecture.md) | System architecture with mermaid diagrams, component descriptions, and technology stack |
| [User Guide](./user-guide.md) | User guide with workflow examples, best practices, and troubleshooting |
| [Deployment Guide](./deployment-guide.md) | Deployment guide for Docker and Kubernetes environments |
| [Development Guide](./development-guide.md) | Development setup, testing, code style, and debugging guide |

## Quick Links

- **API Base URL**: `http://localhost:8000/api/v1`
- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## Project Summary

The Recruitment Platform consolidates 10 independent recruitment sub-projects into a single, production-grade FastAPI application with:

- **50 AI-powered agents** across 10 recruitment domains
- **42 REST API endpoints** with consistent response format
- **12 external service integrations** (OpenAI, ATS, HRMS, Glassdoor, Indeed, LinkedIn, etc.)
- **Production-ready deployment** via Docker and Kubernetes
- **Comprehensive test suite** with pytest
- **CI/CD pipelines** via GitHub Actions

## Agent Domains

| Domain | Agents | API Prefix |
|--------|--------|------------|
| Resume Parser | 5 | `/resume-parser` |
| Candidate Matcher | 5 | `/candidate-matcher` |
| Interview Scheduler | 5 | `/interview-scheduler` |
| Skills Assessor | 5 | `/skills-assessor` |
| Bias Detector | 5 | `/bias-detector` |
| Talent Pool Manager | 5 | `/talent-pool` |
| Recruitment Analytics | 5 | `/analytics` |
| Onboarding Automator | 5 | `/onboarding` |
| Job Description Optimizer | 5 | `/job-description` |
| Employer Branding | 5 | `/employer-branding` |

## Technology Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Validation**: Pydantic v2
- **Database**: PostgreSQL (SQLAlchemy 2.0 + Alembic)
- **Cache**: Redis
- **Task Queue**: Celery
- **Container**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus

## Getting Started

```bash
# Clone and setup
git clone <repository-url>
cd recruitment-platform
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run
python -m recruitment_platform.main

# Or with Docker
docker-compose up --build
```

## License

MIT License

# GRC Onboarding & Training Platform

A standalone, modularized **agentic AI onboarding & training** platform. It builds
personalized onboarding courses, delivers them through your LMS, assesses learner
mastery, optimizes content, and analyzes cohort performance.

## Highlights

- **Five specialized agents** built on [LangChain DeepAgents](https://github.com/langchain-ai/deepagents)
  with the `grc-marketing-core` toolkit:

| Agent | Responsibility |

| --- | --- |

| **Content Creation** | Generate onboarding course outlines, lessons, quizzes and job aids from role metadata. |

| **Delivery** | Orchestrate publishing/scheduling of content across LMS platforms. |

| **Assessment** | Grade open-ended responses, compute mastery, flag remediation. |

| **Optimization** | Recommend content revisions from assessment data and feedback. |

| **Performance Analytics** | Cohort dashboards, completion/engagement trends, alerting signals. |

- **LMS integrations**: Canvas LTI/REST, Moodle Web Services, and SCORM manifest
  validation/packaging.
- **Production-grade**: typed Pydantic v2 models, structlog logging, tenacity
  retries, Prometheus metrics, health endpoints, containerized with a
  non-root Dockerfile and Kubernetes manifests.
- **12-factor**: all configuration through environment variables (see `.env.example`).

## Architecture

```
                ┌──────────────┐
                │  FastAPI app  │  /courses /learners /health /metrics
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
 Content Creation  Delivery     Assessment   Optimization
    Agent          Agent         Agent          Agent
                       │
                       ▼
             Performance Analytics Agent
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     Canvas        Moodle         SCORM
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env            # fill in keys
onboarding                      # uvicorn onboarding.main:app
```

Then open http://localhost:8000/docs.

### Docker

```bash
docker compose up --build
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

## Configuration

All settings are environment variables. See [`.env.example`](.env.example) for
the full list. Sensitive values (LMS tokens, model keys) must never be committed.

## Testing

```bash
pytest                          # unit tests
pytest -m integration          # live LMS tests (requires credentials)
```

## License

Proprietary — internal use only.

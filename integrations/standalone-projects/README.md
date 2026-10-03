# Standalone Modularized Projects

These projects are maintained as independent standalone repositories with their own CI/CD, deployment, and versioning.

## Repositories

| Project | Repository | Description |
|---|---|---|
| **Recruitment Platform** | [AAH20/recruitment-platform](https://github.com/AAH20/recruitment-platform) | AI-powered recruitment platform with resume parsing, candidate matching, interview scheduling, skills assessment, bias detection, talent pool management, onboarding automation, job description optimization, employer branding, and recruitment analytics |
| **UGC Marketplace** | [AAH20/ugc-marketplace](https://github.com/AAH20/ugc-marketplace) | Creator monetization platform with content moderation, content discovery, rights management, quality scoring, fraud detection, creator analytics, licensing engine, community curation, and content marketplace |
| **Gated Communities** | [AAH20/gated-communities](https://github.com/AAH20/gated-communities) | Multi-tier community platform with community health scoring, member verification, escalation workflows, reputation systems, compliance monitoring, moderation analytics, community governance, tier management, and access control |

## Architecture

Each project is a standalone FastAPI + React/Next.js application with:

- **Backend**: FastAPI with SQLAlchemy 2.0, Pydantic v2, Alembic migrations
- **Frontend**: React/Next.js with Tailwind CSS, responsive design
- **Database**: PostgreSQL with UUID primary keys, JSONB for flexible data, full-text search
- **Infrastructure**: Docker Compose, GitHub Actions CI/CD, Terraform, Helm charts
- **Testing**: pytest (unit + integration), Playwright (E2E)
- **Monitoring**: Prometheus metrics, Grafana dashboards, structured logging
- **Security**: JWT authentication, API key auth, role-based access control, rate limiting

## API Endpoints

Each project exposes 20+ REST API endpoints with OpenAPI 3.1 documentation:

- **Recruitment Platform**: `/api/v1/candidates`, `/api/v1/jobs`, `/api/v1/applications`, `/api/v1/interviews`, `/api/v1/assessments`, `/api/v1/skills`, `/api/v1/analytics`, `/api/v1/reports`, `/api/v1/talent-pools`, `/api/v1/employers`
- **UGC Marketplace**: `/api/v1/creators`, `/api/v1/content`, `/api/v1/listings`, `/api/v1/transactions`, `/api/v1/notifications`, `/api/v1/analytics`, `/api/v1/payments`, `/api/v1/reviews`, `/api/v1/categories`, `/api/v1/tags`
- **Gated Communities**: `/api/v1/members`, `/api/v1/communities`, `/api/v1/posts`, `/api/v1/comments`, `/api/v1/events`, `/api/v1/messages`, `/api/v1/analytics`, `/api/v1/reports`, `/api/v1/invitations`, `/api/v1/settings`

## Agent Implementations

Each project includes 10 AI agent implementations:

- **Recruitment Platform**: Resume Parser, Candidate Matcher, Interview Scheduler, Skills Assessor, Bias Detector, Talent Pool Manager, Onboarding Automator, Job Description Optimizer, Employer Branding, Recruitment Analytics
- **UGC Marketplace**: Content Moderation, Creator Monetization, Content Discovery, Rights Management, Quality Scoring, Fraud Detection, Creator Analytics, Licensing Engine, Community Curation, Content Marketplace
- **Gated Communities**: Community Health Scorer, Member Verification, Escalation Workflow, Reputation System, Compliance Monitor, Moderation Analytics, Community Governance, Tier Management, Access Control, Moderation Queue

## Deployment

Each project can be deployed independently:

```bash
# Clone the repository
git clone https://github.com/AAH20/<project>.cd

# Run with Docker Compose
docker-compose up -d

# Or deploy to Kubernetes
helm install <project> ./helm/<project>
```

## License

AGPL-3.0

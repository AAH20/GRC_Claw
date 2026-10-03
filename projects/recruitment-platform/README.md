# Recruitment Platform - Unified AI-Powered Recruitment Automation

## Overview

The Recruitment Platform is a consolidated, modular recruitment system that unifies 10 independent recruitment sub-projects into a single, production-grade FastAPI application. It provides 50 AI-powered agents across 10 recruitment domains, all accessible through a unified REST API.

## Architecture

```
recruitment-platform/
├── src/recruitment_platform/
│   ├── agents/               # 50 AI agents across 10 domains
│   │   ├── resume_parser/     # 5 agents
│   │   ├── candidate_matcher/ # 5 agents
│   │   ├── interview_scheduler/# 5 agents
│   │   ├── skills_assessor/   # 5 agents
│   │   ├── bias_detector/     # 5 agents
│   │   ├── talent_pool_manager/# 5 agents
│   │   ├── recruitment_analytics/# 5 agents
│   │   ├── onboarding_automator/# 5 agents
│   │   ├── job_description_optimizer/# 5 agents
│   │   └── employer_branding/ # 5 agents
│   ├── api/                  # REST API endpoints
│   │   ├── routes/           # Endpoint handlers
│   │   ├── router.py         # API router
│   │   └── dependencies.py   # Shared dependencies
│   ├── config/               # Configuration management
│   ├── integrations/         # External service clients
│   ├── models/               # Pydantic schemas
│   ├── services/             # Business logic layer
│   └── tests/                # Test suite
├── k8s/                      # Kubernetes manifests
├── .github/workflows/        # CI/CD pipelines
├── docs/                     # Documentation
├── diagrams/                 # Architecture diagrams
├── monitoring/               # Monitoring configuration
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (optional)
- Kubernetes cluster (for production)

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd recruitment-platform

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run the application
python -m recruitment_platform.main
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/base/
kubectl apply -f k8s/overlays/production/
```

## API Endpoints

All endpoints are prefixed with `/api/v1`:

| Module | Prefix | Endpoints |
|--------|--------|-----------|
| Health | `/health` | 2 |
| Resume Parser | `/resume-parser` | 3 |
| Candidate Matcher | `/candidate-matcher` | 3 |
| Interview Scheduler | `/interview-scheduler` | 3 |
| Skills Assessor | `/skills-assessor` | 3 |
| Bias Detector | `/bias-detector` | 4 |
| Talent Pool | `/talent-pool` | 4 |
| Analytics | `/analytics` | 5 |
| Onboarding | `/onboarding` | 5 |
| Job Description | `/job-description` | 5 |
| Employer Branding | `/employer-branding` | 5 |

**Total: 42 API endpoints**

## Agent Domains

### 1. Resume Parser (5 agents)
- `ResumeParserAgent` - Orchestrates full resume parsing
- `ContactExtractorAgent` - Extracts contact information
- `EducationExtractorAgent` - Extracts education history
- `ExperienceExtractorAgent` - Extracts work experience
- `SkillsExtractorAgent` - Identifies skills

### 2. Candidate Matcher (5 agents)
- `BiasAwareRanker` - Ranks candidates with bias mitigation
- `CultureFitAssessor` - Assesses culture alignment
- `MatchExplainer` - Explains match decisions
- `SemanticMatcher` - Embedding-based semantic matching
- `SkillsGapAnalyzer` - Analyzes skill gaps

### 3. Interview Scheduler (5 agents)
- `AvailabilityOptimizer` - Finds optimal time slots
- `CalendarSync` - Syncs with external calendars
- `ConflictDetector` - Detects scheduling conflicts
- `Reminder` - Manages interview reminders
- `TimezoneResolver` - Handles timezone conversions

### 4. Skills Assessor (5 agents)
- `GapAnalyzer` - Analyzes skill gaps
- `LearningPathRecommender` - Recommends learning paths
- `ProficiencyScorer` - Scores skill proficiency
- `SkillExtractor` - Extracts skills from assessments
- `SkillValidator` - Validates claimed skills

### 5. Bias Detector (5 agents)
- `DemographicAnalyzer` - Analyzes demographic patterns
- `FairnessScorer` - Computes fairness metrics
- `LanguageBiasDetector` - Detects biased language
- `PatternDetector` - Identifies systemic bias patterns
- `Recommendation` - Generates mitigation recommendations

### 6. Talent Pool Manager (5 agents)
- `CandidateSourcer` - Sources candidates from pools
- `EngagementTracker` - Tracks candidate engagement
- `PoolAnalyzer` - Analyzes pool health
- `TalentRecommender` - Recommends talent for positions
- `TalentTagger` - Tags talent with metadata

### 7. Recruitment Analytics (5 agents)
- `CostAnalyzer` - Analyzes recruitment costs
- `DiversityAnalyzer` - Analyzes diversity metrics
- `FunnelAnalyzer` - Analyzes recruitment funnel
- `PredictiveHiring` - Predicts hiring outcomes
- `SourceTracker` - Tracks source effectiveness

### 8. Onboarding Automator (5 agents)
- `ComplianceChecker` - Verifies compliance requirements
- `DocumentGenerator` - Generates onboarding documents
- `ProgressTracker` - Tracks onboarding progress
- `TaskScheduler` - Schedules onboarding tasks
- `WelcomeMessage` - Generates welcome messages

### 9. Job Description Optimizer (5 agents)
- `ATSCompatibility` - Checks ATS compatibility
- `BiasRemover` - Removes biased language
- `KeywordOptimizer` - Optimizes keywords
- `SEOOptimizer` - Optimizes for search engines
- `ToneAnalyzer` - Analyzes tone

### 10. Employer Branding (5 agents)
- `BrandStrategy` - Develops branding strategies
- `ContentGenerator` - Generates branding content
- `ReputationManager` - Manages employer reputation
- `ReviewAnalyzer` - Analyzes reviews
- `SentimentAnalyzer` - Analyzes sentiment

## Configuration

Configuration is managed via environment variables or `.env` file:

```env
APP_NAME=Recruitment Platform
APP_VERSION=1.0.0
DEBUG=false
HOST=0.0.0.0
PORT=8000
WORKERS=1
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./recruitment.db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=recruitment_platform --cov-report=html

# Run specific test file
pytest src/recruitment_platform/tests/test_agents.py
```

## CI/CD

The project includes GitHub Actions workflows for:
- Automated testing
- Linting and type checking
- Docker image building
- Kubernetes deployment

## Monitoring

Prometheus metrics and health checks are available at:
- `/api/v1/health` - Health check
- `/api/v1/ready` - Readiness check
- `/metrics` - Prometheus metrics

## License

MIT License

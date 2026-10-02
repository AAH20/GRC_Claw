# CI/CD Pipeline Template

Production-grade CI/CD pipeline template for agentic AI marketing projects. Supports multi-project builds, automated testing, security scanning, and deployment to Kubernetes.

## Table of Contents

- [Overview](#overview)
- [Pipeline Stages](#pipeline-stages)
- [Workflows](#workflows)
- [Scripts](#scripts)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Required Secrets](#required-secrets)
- [Usage Examples](#usage-examples)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

---

## Overview

This template provides a complete CI/CD pipeline with the following capabilities:

| Feature | Tools |
|---------|-------|
| **Linting** | Ruff, Mypy, ShellCheck, shfmt |
| **Testing** | Pytest, Coverage, Trivy |
| **Security** | Bandit, Safety, Trivy, Gitleaks |
| **Build** | Docker Buildx, SBOM generation |
| **Deploy** | kubectl, Helm-compatible |
| **Monitoring** | Health checks, Slack notifications |
| **Code Quality** | Codecov, SonarQube, Pre-commit hooks |

---

## Pipeline Stages

```
┌─────────────┐     ┌──────────┐     ┌───────────────┐     ┌───────┐
│    Lint     │────▶│   Test   │────▶│ Security Scan │────▶│ Build │
│  (parallel) │     │(matrix)  │     │  (parallel)   │     │       │
└─────────────┘     └──────────┘     └───────────────┘     └───┬───┘
                                                                │
                    ┌───────────────────────────────────────────┘
                    │
                    ▼
            ┌───────────────┐     ┌──────────────────┐
            │ Deploy Staging│────▶│ Deploy Production│
            │  (auto)       │     │  (manual gate)   │
            └───────────────┘     └──────────────────┘
```

### Stage Details

1. **Lint** — Code quality checks (ruff, mypy, shellcheck)
2. **Test** — Unit and integration tests across Python 3.10–3.12
3. **Security Scan** — Static analysis (bandit), dependency audit (safety), container scan (Trivy)
4. **Build** — Multi-arch Docker image build with SBOM and vulnerability scan
5. **Deploy Staging** — Automatic deployment to staging with health checks
6. **Deploy Production** — Manual approval gate, deployment with health checks and rollback

---

## Workflows

### `ci-cd-template.yml` — Main CI/CD Pipeline

Triggered on pushes to `main`/`develop` and pull requests.

```bash
# Manual trigger with environment selection
gh workflow run ci-cd-template.yml -f environment=staging
```

### `pr-validation.yml` — PR Validation

Triggered on PR events (opened, synchronize, reopened, ready_for_review).

- Validates PR metadata (semantic commit format)
- Runs lint, test, security scan, and build check
- Posts a summary comment on the PR

### `nightly-build.yml` — Nightly Build

Scheduled at 2:00 AM UTC daily.

- Full test matrix (Python 3.9–3.13, Ubuntu/macOS/Windows)
- Security audit with Trivy
- Dependency audit with pip-audit
- Build and push nightly Docker image
- Deploy to staging with health checks
- Slack notification with results

---

## Scripts

All scripts are in `scripts/` and are executable.

### `scripts/lint.sh`

Run ruff and mypy linting checks.

```bash
./scripts/lint.sh              # Standard lint
./scripts/lint.sh --fix        # Auto-fix issues
./scripts/lint.sh --strict     # Strict mypy mode
```

### `scripts/test.sh`

Run pytest with coverage reporting.

```bash
./scripts/test.sh                           # Standard test run
./scripts/test.sh --cov-fail-under 90       # Custom coverage threshold
./scripts/test.sh --markers integration    # Run specific marker
./scripts/test.sh --verbose                 # Verbose output
./scripts/test.sh --no-cov                  # Disable coverage
```

### `scripts/security-scan.sh`

Run bandit and safety security scans.

```bash
./scripts/security-scan.sh                           # Standard scan
./scripts/security-scan.sh --severity-level high     # High severity only
./scripts/security-scan.sh --fail-on-issue            # Fail on any issue
./scripts/security-scan.sh --skip-safety              # Skip dependency check
```

### `scripts/build.sh`

Build and push Docker images.

```bash
./scripts/build.sh --image myapp --tag v1.0.0 --push
./scripts/build.sh --image myapp --tag latest --platforms linux/amd64,linux/arm64
./scripts/build.sh --image myapp --tag dev --build-arg VERSION=1.0.0
```

### `scripts/deploy.sh`

Deploy to Kubernetes.

```bash
./scripts/deploy.sh --environment staging --image registry/app:v1.0.0
./scripts/deploy.sh --environment production --image registry/app:v1.0.0 --wait
./scripts/deploy.sh --environment staging --image registry/app:v1.0.0 --dry-run
```

### `scripts/rollback.sh`

Rollback a deployment.

```bash
./scripts/rollback.sh --environment staging
./scripts/rollback.sh --environment production --to-revision 3
./scripts/rollback.sh --environment staging --dry-run
```

### `scripts/health-check.sh`

Perform HTTP health checks.

```bash
./scripts/health-check.sh --url https://example.com/health
./scripts/health-check.sh --url https://api.example.com/health --json-key status --json-value ok
./scripts/health-check.sh --url https://example.com/health --retries 10 --delay 15
```

---

## Configuration

### `config/codecov.yml`

Codecov coverage reporting configuration with:
- 80% coverage target
- Project, patch, and changes status checks
- Component-based coverage for monorepo support

### `config/sonar-project.properties`

SonarQube/SonarCloud configuration with:
- Python version targeting
- Coverage and test report paths
- Duplication and coverage exclusions

### `config/.pre-commit-config.yaml`

Pre-commit hooks for:
- General file checks (trailing whitespace, large files, merge conflicts)
- Shell script linting and formatting
- Python formatting (black, ruff) and linting (ruff, mypy, bandit)
- Security scanning (bandit, gitleaks)
- Dockerfile linting (hadolint)
- Markdown linting
- GitHub Actions linting

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker with Buildx
- kubectl configured for your cluster
- Poetry for dependency management

### Setup

1. **Copy the template to your project:**

   ```bash
   cp -r pipelines/* /path/to/your/project/
   ```

2. **Install pre-commit hooks:**

   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

3. **Configure GitHub secrets** (see [Required Secrets](#required-secrets))

4. **Customize the workflows** for your project:
   - Update `DOCKER_IMAGE` in workflow files
   - Adjust Python versions in test matrix
   - Modify Kubernetes namespace and deployment names

5. **Run locally:**

   ```bash
   ./scripts/lint.sh
   ./scripts/test.sh
   ./scripts/security-scan.sh
   ```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PYTHON_VERSION` | Python version for CI | Yes |
| `POETRY_VERSION` | Poetry version for CI | Yes |
| `DOCKER_REGISTRY` | Container registry URL | Yes |
| `DOCKER_IMAGE` | Docker image name | Yes |
| `SONAR_HOST_URL` | SonarQube server URL | For SonarQube |
| `SONAR_TOKEN` | SonarQube authentication token | For SonarQube |
| `CODECOV_TOKEN` | Codecov upload token | For Codecov |

---

## Required Secrets

Configure these in your GitHub repository settings (`Settings → Secrets and variables → Actions`):

| Secret | Description | Used By |
|--------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key for EKS | Deploy workflows |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for EKS | Deploy workflows |
| `AWS_REGION` | AWS region for EKS cluster | Deploy workflows |
| `EKS_CLUSTER_NAME` | EKS cluster name | Deploy workflows |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | All workflows |
| `CODECOV_TOKEN` | Codecov upload token | Test workflows |
| `SONAR_HOST_URL` | SonarQube server URL | SonarQube integration |
| `SONAR_TOKEN` | SonarQube authentication token | SonarQube integration |

---

## Usage Examples

### Run full pipeline locally

```bash
# Lint
./scripts/lint.sh --fix

# Test with coverage
./scripts/test.sh --cov-fail-under 85

# Security scan
./scripts/security-scan.sh --fail-on-issue

# Build Docker image
./scripts/build.sh --image myapp --tag $(git rev-parse --short HEAD) --push

# Deploy to staging
./scripts/deploy.sh --environment staging --image myapp:abc123 --wait

# Health check
./scripts/health-check.sh --url https://staging.example.com/health

# Rollback if needed
./scripts/rollback.sh --environment staging
```

### Manual workflow dispatch

```bash
# Deploy to staging
gh workflow run ci-cd-template.yml -f environment=staging

# Deploy to production
gh workflow run ci-cd-template.yml -f environment=production

# Skip tests (emergency deploy)
gh workflow run ci-cd-template.yml -f environment=production -f skip_tests=true
```

---

## Customization

### Adding a new Python version to the test matrix

Edit `.github/workflows/ci-cd-template.yml`:

```yaml
strategy:
  matrix:
    python-version: ["3.10", "3.11", "3.12", "3.13"]  # Add version here
```

### Changing the coverage threshold

Edit `scripts/test.sh`:

```bash
COV_FAIL_UNDER=90  # Change from default 80
```

Or pass it at runtime:

```bash
./scripts/test.sh --cov-fail-under 90
```

### Adding a new deployment environment

1. Create `k8s/new-env/` with Kubernetes manifests
2. Add a new job in `ci-cd-template.yml`
3. Update `scripts/deploy.sh` to handle the new environment

### Using Helm instead of raw kubectl

Replace the `kubectl apply` section in `scripts/deploy.sh`:

```bash
helm upgrade --install "$DEPLOYMENT_NAME" ./charts/app \
    --namespace "$NAMESPACE" \
    --set image.repository="$IMAGE" \
    --set image.tag="$IMAGE_TAG" \
    --wait --timeout "${TIMEOUT}s"
```

---

## Troubleshooting

### Linting fails in CI but passes locally

- Ensure the same versions of ruff/mypy are used (check `pyproject.toml`)
- Run `pre-commit install` to use the same hook versions

### Docker build fails with "no space left on device"

- Enable BuildKit cache: `./scripts/build.sh --cache`
- Clean old images: `docker system prune -a`

### Deployment times out

- Increase timeout: `./scripts/deploy.sh --environment staging --timeout 600`
- Check cluster connectivity: `kubectl cluster-info`
- Verify namespace exists: `kubectl get namespace staging`

### Health check fails after deployment

- Check pod logs: `kubectl logs -n staging -l app=app`
- Verify service endpoint: `kubectl get svc -n staging`
- Check ingress: `kubectl get ingress -n staging`

### Coverage upload fails

- Verify `CODECOV_TOKEN` is set in repository secrets
- Check that `coverage.xml` exists: `ls -la coverage.xml`
- Run Codecov locally: `po run codecov`

---

## License

MIT License — See [LICENSE](../LICENSE) for details.

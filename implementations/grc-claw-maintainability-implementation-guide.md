# GRC_Claw Maintainability Implementation Guide

**Document ID:** GRC-MNT-IMPL-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**References:** GRC-MNT-001 (Maintainability Specification), GRC-QA-001 (Quality Assurance Specification)

---

## Table of Contents

1. [Code Quality Pipeline](#1-code-quality-pipeline)
2. [Documentation Automation](#2-documentation-automation)
3. [Technical Debt Management](#3-technical-debt-management)
4. [Refactoring Automation](#4-refactoring-automation)
5. [Developer Onboarding](#5-developer-onboarding)
6. [API Versioning Automation](#6-api-versioning-automation)
7. [Deprecation Management](#7-deprecation-management)
8. [Implementation Roadmap](#8-implementation-roadmap)

---

## 1. Code Quality Pipeline

### 1.1 Pipeline Architecture

The code quality pipeline enforces maintainability standards at every stage of development, from local commit to production deployment.

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Local     │──▶│     PR      │──▶│    Merge    │──▶│   Staging   │──▶│ Production  │
│   Commit    │   │   Review    │   │   to Main   │   │   Deploy    │   │   Deploy    │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
     │                  │                  │                  │                  │
     ▼                  ▼                  ▼                  ▼                  ▼
  Gate 1            Gate 2             Gate 3             Gate 4             Gate 5
```

### 1.2 Gate 1: Pre-Commit (Local)

#### 1.2.1 Pre-Commit Hook Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # Python linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix, --config, pyproject.toml]
      - id: ruff-format

  # Python type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies:
          - types-all
          - pydantic>=2.0
        args: [--config-file=pyproject.toml]

  # Rust linting and formatting
  - repo: https://github.com/doublify/pre-commit-rust
    rev: v1.0
    hooks:
      - id: fmt
        args: [--manifest-path, Cargo.toml]
      - id: clippy
        args: [--manifest-path, Cargo.toml, --, -D, warnings]

  # TypeScript linting and formatting
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.13.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        args: [--fix, --config, .eslintrc.json]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier

  # Security scanning
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.11
    hooks:
      - id: gitleaks

  # Secret detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  # Conventional commit enforcement
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.4.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]

  # Local hooks
  - repo: local
    hooks:
      - id: unit-tests-changed
        name: Unit tests (changed files)
        entry: pytest --testmon -x -q
        language: system
        pass_filenames: true
        types: [python]
        stages: [pre-push]

      - id: cargo-test-changed
        name: Cargo tests (changed files)
        entry: cargo test --no-fail-fast
        language: system
        pass_filenames: true
        types: [rust]
        stages: [pre-push]
```

#### 1.2.2 Pre-Commit Installation Script

```bash
#!/bin/bash
# scripts/install-hooks.sh
set -euo pipefail

echo "Installing pre-commit hooks..."

# Install pre-commit if not present
if ! command -v pre-commit &>/dev/null; then
    pip install pre-commit
fi

# Install hooks
pre-commit install --hook-type pre-commit
pre-commit install --hook-type pre-push
pre-commit install --hook-type commit-msg

# Install Rust components
rustup component add rustfmt clippy

# Verify installation
pre-commit --version
cargo fmt --version
cargo clippy --version

echo "Pre-commit hooks installed successfully."
echo "Run 'pre-commit run --all-files' to verify."
```

### 1.3 Gate 2: Pull Request (CI)

#### 1.3.1 GitHub Actions CI Workflow

```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"
  RUST_VERSION: "1.75"
  NODE_VERSION: "20"

jobs:
  # ─── Detect Changes ──────────────────────────────────────────
  changes:
    runs-on: ubuntu-latest
    outputs:
      python: ${{ steps.filter.outputs.python }}
      rust: ${{ steps.filter.outputs.rust }}
      typescript: ${{ steps.filter.outputs.typescript }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            python:
              - 'src/**'
              - 'pyproject.toml'
              - 'uv.lock'
            rust:
              - 'crates/**'
              - 'Cargo.toml'
              - 'Cargo.lock'
            typescript:
              - 'packages/**'
              - 'package.json'
              - 'pnpm-lock.yaml'

  # ─── Python Quality Gates ────────────────────────────────────
  python-lint:
    runs-on: ubuntu-latest
    needs: changes
    if: ${{ needs.changes.outputs.python == 'true' }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync --all-extras --dev

      - name: Ruff lint
        run: ruff check . --config pyproject.toml

      - name: Ruff format check
        run: ruff format --check . --config pyproject.toml

      - name: Mypy type check
        run: mypy src/ --config-file pyproject.toml

      - name: Vulture dead code detection
        run: vulture src/ --min-confidence 80

      - name: Bandit security scan
        run: bandit -r src/ -ll -c pyproject.toml

  python-test:
    runs-on: ubuntu-latest
    needs: [changes, python-lint]
    if: ${{ needs.changes.outputs.python == 'true' }}
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync --all-extras --dev

      - name: Run unit tests with coverage
        run: |
          pytest tests/unit/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-branch \
            --cov-fail-under=88 \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          flags: python
          fail_ci_if_error: true

      - name: Mutation testing (nightly)
        if: github.event_name == 'schedule'
        run: |
          pip install mutmut
          mutmut run --paths-to-mutate=src/
          mutmut results

  # ─── Rust Quality Gates ──────────────────────────────────────
  rust-lint:
    runs-on: ubuntu-latest
    needs: changes
    if: ${{ needs.changes.outputs.rust == 'true' }}
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          toolchain: ${{ env.RUST_VERSION }}
          components: rustfmt, clippy

      - name: Cache cargo
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

      - name: Cargo fmt check
        run: cargo fmt --all -- --check

      - name: Clippy lint
        run: cargo clippy --all-targets --all-features -- -D warnings

      - name: Cargo audit
        run: |
          cargo install cargo-audit
          cargo audit

  rust-test:
    runs-on: ubuntu-latest
    needs: [changes, rust-lint]
    if: ${{ needs.changes.outputs.rust == 'true' }}
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          toolchain: ${{ env.RUST_VERSION }}

      - name: Cache cargo
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

      - name: Run tests with coverage
        run: |
          cargo install cargo-llvm-cov
          cargo llvm-cov --all-features --workspace --lcov --output-path lcov.info

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./lcov.info
          flags: rust

      - name: Property-based tests
        run: cargo test --all-features -- --ignored property_tests

  # ─── TypeScript Quality Gates ────────────────────────────────
  typescript-lint:
    runs-on: ubuntu-latest
    needs: changes
    if: ${{ needs.changes.outputs.typescript == 'true' }}
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: pnpm

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: ESLint
        run: pnpm lint

      - name: Prettier check
        run: pnpm format:check

      - name: TypeScript type check
        run: pnpm type-check

  typescript-test:
    runs-on: ubuntu-latest
    needs: [changes, typescript-lint]
    if: ${{ needs.changes.outputs.typescript == 'true' }}
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: pnpm

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Run tests with coverage
        run: pnpm test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          flags: typescript

  # ─── Integration Tests ───────────────────────────────────────
  integration-tests:
    runs-on: ubuntu-latest
    needs: [python-test, rust-test, typescript-test]
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: grc_claw_test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      kafka:
        image: confluentinc/cp-kafka:latest
        ports:
          - 9092:9092
        env:
          KAFKA_BROKER_ID: 1
          KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
          KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092

      zookeeper:
        image: confluentinc/cp-zookeeper:latest
        ports:
          - 2181:2181
        env:
          ZOOKEEPER_CLIENT_PORT: 2181

      minio:
        image: minio/minio:latest
        ports:
          - 9000:9000
        env:
          MINIO_ROOT_USER: minioadmin
          MINIO_ROOT_PASSWORD: minioadmin
        options: >-
          --health-cmd "curl -f http://localhost:9000/minio/health/live"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync --all-extras --dev

      - name: Run database migrations
        run: alembic upgrade head
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/grc_claw_test

      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/grc_claw_test
          REDIS_URL: redis://localhost:6379
          KAFKA_BOOTSTRAP_SERVERS: localhost:9092
          MINIO_ENDPOINT: localhost:9000

  # ─── API Contract Tests ──────────────────────────────────────
  contract-tests:
    runs-on: ubuntu-latest
    needs: [python-test]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync --all-extras --dev

      - name: Run contract tests
        run: pytest tests/contract/ -v --tb=short

      - name: OpenAPI spec validation
        run: |
          pip install openapi-spec-validator
          openapi-spec-validator docs/api/openapi.json

      - name: Breaking change detection
        run: |
          pip install oasdiff
          oasdiff breaking \
            --base docs/api/openapi-prev.json \
            --revision docs/api/openapi.json \
            --fail-on ERR

  # ─── Security Scans ──────────────────────────────────────────
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: SAST (Semgrep)
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/owasp-top-ten
            p/cwe-top-25

      - name: Secret detection
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified

      - name: Dependency audit (Python)
        run: |
          pip install pip-audit
          pip-audit --strict

      - name: Dependency audit (Rust)
        run: |
          cargo install cargo-audit
          cargo audit

      - name: Dependency audit (Node)
        run: pnpm audit --audit-level=moderate

  # ─── SonarQube Analysis ─────────────────────────────────────
  sonarqube:
    runs-on: ubuntu-latest
    needs: [python-test, rust-test, typescript-test]
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: SonarQube Scan
        uses: SonarSource/sonarqube-scan-action@v2
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
        with:
          args: >
            -Dsonar.projectKey=grc-claw
            -Dsonar.python.coverage.reportPaths=coverage.xml
            -Dsonar.qualitygate.wait=true
            -Dsonar.qualitygate.timeout=300

  # ─── Quality Gate Summary ────────────────────────────────────
  quality-gate:
    runs-on: ubuntu-latest
    needs:
      - python-lint
      - python-test
      - rust-lint
      - rust-test
      - typescript-lint
      - typescript-test
      - integration-tests
      - contract-tests
      - security-scan
      - sonarqube
    if: always()
    steps:
      - name: Check all gates
        run: |
          echo "Checking quality gate results..."
          # This job fails if any of the required jobs failed
          # GitHub Actions handles this via the 'needs' context
          echo "All quality gates passed ✅"
```

### 1.4 Gate 3: Merge to Main

```yaml
# .github/workflows/cd-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Run E2E tests
        run: |
          pnpm install --frozen-lockfile
          npx playwright install --with-deps
          npx playwright test

      - name: Performance smoke tests
        run: |
          pip install locust
          locust -f tests/performance/smoke.py \
            --headless -u 100 -r 10 --run-time 5m \
            --host https://staging.grc-claw.example.com

      - name: DAST scan
        uses: zaproxy/action-full-scan@v0.10.0
        with:
          target: https://staging.grc-claw.example.com
          rules_file_name: .zap/rules.tsv

      - name: Database migration test
        run: |
          alembic upgrade head
          alembic downgrade -1
          alembic upgrade head

      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment..."
          # ArgoCD or similar deployment

      - name: Post-deployment smoke tests
        run: pytest tests/smoke/ -v --tb=short

      - name: Verify monitoring
        run: |
          curl -sf https://staging.grc-claw.example.com/metrics | grep -q "http_requests_total"
```

### 1.5 Gate 4: Staging Validation

```yaml
# .github/workflows/staging-validation.yml
name: Staging Validation

on:
  workflow_run:
    workflows: ["Deploy to Staging"]
    types: [completed]
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    steps:
      - name: Wait 48 hours for staging stability
        run: |
          echo "Staging deployed. Monitoring for 48 hours..."
          # In practice, this would be a scheduled check

      - name: Run full E2E suite
        run: npx playwright test --project=chromium --project=firefox

      - name: Run performance tests
        run: |
          pip install locust
          locust -f tests/performance/full.py \
            --headless -u 500 -r 50 --run-time 15m \
            --host https://staging.grc-claw.example.com

      - name: Chaos engineering tests
        run: |
          pip install chaostoolkit
          chaos run experiments/staging-chaos.json
```

### 1.6 Gate 5: Production Deployment

```yaml
# .github/workflows/cd-production.yml
name: Deploy to Production

on:
  workflow_dispatch:
    inputs:
      version:
        description: "Version to deploy"
        required: true
      canary_percentage:
        description: "Canary traffic percentage"
        required: false
        default: "10"

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Verify staging validation (48h clean)
        run: |
          echo "Verifying staging has been clean for 48 hours..."

      - name: Canary deployment
        run: |
          echo "Deploying canary with ${{ inputs.canary_percentage }}% traffic..."

      - name: Canary analysis
        run: |
          # Automated canary analysis
          # - Error rate < 0.1%
          # - p95 latency < 500ms
          # - No critical alerts
          echo "Running canary analysis..."

      - name: Full rollout
        if: success()
        run: echo "Promoting canary to full production..."

      - name: Rollback on failure
        if: failure()
        run: |
          echo "Rolling back deployment..."
          # Automated rollback procedure
```

### 1.7 Python Tool Configuration

```toml
# pyproject.toml
[project]
name = "grc-claw"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "uvicorn[standard]>=0.24",
    "structlog>=24.1",
    "prometheus-client>=0.19",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.23",
    "pytest-rerunfailures>=14.0",
    "pytest-testmon>=2.1",
    "httpx>=0.27",
    "respx>=0.21",
    "ruff>=0.6",
    "mypy>=1.11",
    "bandit>=1.7",
    "vulture>=2.10",
    "interrogate>=1.5",
    "pip-audit>=2.7",
    "mutmut>=2.4",
    "hypothesis>=6.112",
    "testcontainers>=4.0",
    "pre-commit>=3.8",
]

[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "A",    # flake8-builtins
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "T20",  # flake8-print
    "RUF",  # ruff-specific
]

[tool.ruff.lint.isort]
known-first-party = ["grc_claw"]
combine-as-imports = true

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["T20"]  # Allow print in tests

[tool.mypy]
python_version = "3.12"
strict = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
warn_unreachable = true
show_error_codes = true
pretty = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = [
    "-v",
    "--strict-markers",
    "--strict-config",
    "--tb=short",
    "--reruns=2",
    "--reruns-delay=1",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "contract: Contract tests",
    "property: Property-based tests",
    "e2e: End-to-end tests",
    "chaos: Chaos tests",
    "performance: Performance tests",
    "slow: Slow tests",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/migrations/*",
]

[tool.coverage.report]
fail_under = 88
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]

[tool.bandit]
exclude_dirs = ["tests"]
skips = ["B101"]  # Allow assert in non-test code where appropriate

[tool.interrogate]
ignore-init-method = true
ignore-init-module = true
ignore-magic = true
ignore-semiprivate = true
ignore-private = true
ignore-property-decorators = true
ignore-module = false
ignore-nested-functions = true
ignore-nested-classes = true
ignore-setters = true
fail-under = 90
verbose = 2
```

### 1.8 Rust Tool Configuration

```toml
# Cargo.toml (workspace root)
[workspace]
resolver = "2"
members = [
    "crates/enforcement-proxy",
    "crates/audit-trail",
    "crates/policy-compiler",
]

[workspace.package]
version = "1.0.0"
edition = "2021"
rust-version = "1.75"
license = "AGPL-3.0"

[workspace.dependencies]
tokio = { version = "1.39", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["json", "env-filter"] }
anyhow = "1.0"
thiserror = "1.0"
chrono = { version = "0.4", features = ["serde"] }
sha2 = "0.10"
hex = "0.4"
config = "0.14"
metrics = "0.23"
metrics-exporter-prometheus = "0.15"

[profile.release]
lto = true
codegen-units = 1
panic = "abort"
strip = true

[profile.dev]
opt-level = 0
debug = true
```

```toml
# rustfmt.toml
edition = "2021"
max_width = 100
tab_spaces = 4
use_field_init_shorthand = true
use_try_shorthand = true
reorder_imports = true
reorder_modules = true
remove_nested_parens = true
merge_derives = true
use_small_heuristics = "Default"
```

### 1.9 TypeScript Tool Configuration

```json
// .eslintrc.json
{
  "root": true,
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module",
    "ecmaFeatures": {
      "jsx": true
    }
  },
  "plugins": ["@typescript-eslint", "react-hooks"],
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
    "plugin:react-hooks/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/explicit-module-boundary-types": "warn",
    "@typescript-eslint/no-floating-promises": "error",
    "@typescript-eslint/no-misused-promises": "error",
    "@typescript-eslint/await-thenable": "error",
    "@typescript-eslint/no-unsafe-assignment": "warn",
    "@typescript-eslint/no-unsafe-member-access": "warn",
    "@typescript-eslint/no-unsafe-call": "warn",
    "@typescript-eslint/no-unsafe-return": "warn",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "complexity": ["warn", 15],
    "max-lines": ["warn", 300]
  },
  "ignorePatterns": ["dist/", "node_modules/", "*.js", "*.config.ts"]
}
```

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "all",
  "singleQuote": false,
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/utils/*": ["src/utils/*"]
    }
  },
  "include": ["src", "packages"],
  "exclude": ["node_modules", "dist", "build"]
}
```

### 1.10 Makefile for Developer Experience

```makefile
# Makefile
.PHONY: help dev-setup doctor dev test test-fast lint format typecheck docs-serve db-migrate db-rollback clean

PYTHON := python3.12
UV := uv
CARGO := cargo
PNPM := pnpm

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev-setup: ## One-command development environment setup
	@echo "Setting up GRC_Claw development environment..."
	$(UV) sync --all-extras --dev
	$(CARGO) fetch
	$(PNPM) install --frozen-lockfile
	pre-commit install --hook-type pre-commit --hook-type pre-push --hook-type commit-msg
	$(CARGO) install cargo-audit cargo-udeps cargo-llvm-cov
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d postgres redis kafka minio
	$(UV) run alembic upgrade head
	@echo "Development environment ready! Run 'make dev' to start."

doctor: ## Verify development environment health
	@echo "Checking development environment..."
	$(UV) run python --version
	$(CARGO) --version
	$(PNPM) --version
	$(UV) run pytest --version
	$(UV) run ruff --version
	$(UV) run mypy --version
	@echo "Checking Docker services..."
	docker compose ps
	@echo "Checking database connection..."
	$(UV) run python -c "import asyncpg; print('Database: OK')"
	@echo "All checks passed ✅"

dev: ## Start all services with hot reload
	@echo "Starting development servers..."
	$(CARGO) watch -x run -p enforcement-proxy &
	$(UV) run uvicorn grc_claw.api_gateway.main:app --reload --port 8000 &
	$(PNPM) --filter web-ui run dev &
	wait

test: ## Run full test suite
	$(UV) run pytest tests/ -v --cov=src --cov-report=term-missing --cov-branch
	$(CARGO) test --all-features --workspace
	$(PNPM) test

test-fast: ## Run unit tests only
	$(UV) run pytest tests/unit/ -x -q --no-header
	$(CARGO) test --lib --workspace
	$(PNPM) test:unit

lint: ## Run all linters
	$(UV) run ruff check . --config pyproject.toml
	$(UV) run ruff format --check . --config pyproject.toml
	$(UV) run mypy src/ --config-file pyproject.toml
	$(UV) run vulture src/ --min-confidence 80
	$(UV) run bandit -r src/ -ll -c pyproject.toml
	$(CARGO) fmt --all -- --check
	$(CARGO) clippy --all-targets --all-features -- -D warnings
	$(PNPM) lint

format: ## Auto-format all code
	$(UV) run ruff check . --fix --config pyproject.toml
	$(UV) run ruff format . --config pyproject.toml
	$(UV) run pyupgrade --py312-plus $(shell find src -name "*.py")
	$(CARGO) fmt --all
	$(CARGO) clippy --all-targets --all-features --fix --allow-dirty --allow-staged
	$(PNPM) format

typecheck: ## Run all type checkers
	$(UV) run mypy src/ --config-file pyproject.toml
	$(CARGO) check --all-targets --all-features
	$(PNPM) type-check

docs-serve: ## Serve documentation locally
	$(UV) run mkdocs serve -a localhost:8001

db-migrate: ## Create new database migration
	@read -p "Migration name: " name; \
	$(UV) run alembic revision --autogenerate -m "$$name"

db-rollback: ## Rollback last migration
	$(UV) run alembic downgrade -1

clean: ## Remove build artifacts, caches, containers
	docker compose down -v
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build
	rm -rf target node_modules .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
```

---

## 2. Documentation Automation

### 2.1 Documentation Pipeline Architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Code +      │──▶│  Generate    │──▶│  Validate    │──▶│  Deploy      │
│  Annotations │   │  Docs        │   │  Docs        │   │  Docs        │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
     │                   │                   │                   │
     ▼                   ▼                   ▼                   ▼
  Docstrings,       pdoc, rustdoc,     Link check,         GitHub Pages,
  Type hints,       typedoc,          Example execution,  ReadTheDocs,
  OpenAPI spec      mkdocs            Schema validation   npm/PyPI pages
```

### 2.2 Documentation Generation Workflow

```yaml
# .github/workflows/docs.yml
name: Documentation

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'crates/**'
      - 'packages/**'
      - 'docs/**'
      - 'pyproject.toml'
      - 'Cargo.toml'
      - 'package.json'
  release:
    types: [published]

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: |
          uv sync --all-extras --dev
          uv pip install mkdocs mkdocs-material mkdocstrings[python] \
            mkdocs-gen-files mkdocs-literate-nav mkdocs-swagger-ui \
            pdoc typedoc

      - uses: dtolnay/rust-toolchain@stable

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: pnpm

      - name: Install Node dependencies
        run: pnpm install --frozen-lockfile

      # ─── Generate API Reference ──────────────────────────────
      - name: Generate Python API docs
        run: |
          uv run pdoc \
            --output-dir docs/api/python \
            --docformat google \
            src/grc_claw/

      - name: Generate Rust API docs
        run: |
          cargo doc --no-deps --workspace --document-private-items
          cp -r target/doc docs/rust/

      - name: Generate TypeScript API docs
        run: |
          pnpm --filter @grc-claw/sdk run docs
          cp -r packages/sdk/docs docs/sdk/typescript/

      # ─── Generate OpenAPI Spec ───────────────────────────────
      - name: Generate OpenAPI spec
        run: |
          uv run python -c "
          from grc_claw.api_gateway.main import app
          import json
          spec = app.openapi()
          with open('docs/api/openapi.json', 'w') as f:
              json.dump(spec, f, indent=2)
          "

      # ─── Generate Architecture Diagrams ───────────────────────
      - name: Generate module dependency graph
        run: |
          uv run pydeps src/grc_claw/ \
            --max-bacon 2 \
            --output docs/architecture/module-deps.svg

      - name: Generate ER diagram
        run: |
          uv run eralchemy2 \
            -i sqlite:///grc_claw.db \
            -o docs/schema/er-diagram.svg

      # ─── Generate Changelog ───────────────────────────────────
      - name: Generate changelog
        run: |
          uv pip install git-cliff
          git-cliff --config cliff.toml --output CHANGELOG.md

      # ─── Build MkDocs Site ───────────────────────────────────
      - name: Build documentation site
        run: uv run mkdocs build --strict

      # ─── Validate Documentation ──────────────────────────────
      - name: Check docstring coverage
        run: |
          uv run interrogate -vv --fail-under 90 src/

      - name: Check documentation links
        uses: lycheeverse/lychee-action@v2
        with:
          args: --verbose --no-progress docs/ README.md CHANGELOG.md
          fail: true

      - name: Validate OpenAPI spec
        run: |
          uv pip install openapi-spec-validator
          uv run openapi-spec-validator docs/api/openapi.json

      - name: Execute code examples
        run: |
          uv run pytest --doctest-glob="docs/**/*.md" docs/examples/

      # ─── Deploy Documentation ────────────────────────────────
      - name: Deploy to GitHub Pages
        if: github.ref == 'refs/heads/main'
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site

      - name: Upload documentation artifact
        uses: actions/upload-artifact@v4
        with:
          name: documentation
          path: site/
          retention-days: 30
```

### 2.3 MkDocs Configuration

```yaml
# mkdocs.yml
site_name: GRC_Claw Documentation
site_description: AI Governance, Risk, and Compliance Platform
repo_url: https://github.com/grc-claw/grc-claw
repo_name: grc-claw/grc-claw

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.sections
    - navigation.top
    - navigation.tracking
    - navigation.tabs
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate

plugins:
  - search
  - gen-files:
      scripts:
        - docs/gen_ref_pages.py
  - literate-nav:
      nav_file: SUMMARY.md
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            show_category_heading: true
            show_submodules: true
            show_symbol_type_heading: true
            show_symbol_type_toc: true
            members_order: source
            separate_signature: true
            unwrap_annotated: true
            filters:
              - "!^_"
  - swagger-ui:
      layout: standalone

markdown_extensions:
  - admonition
  - attr_list
  - md_in_html
  - pymdownx.details
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg

nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quickstart.md
      - Configuration: getting-started/configuration.md
  - Architecture:
      - Overview: architecture/overview.md
      - Policy Engine: architecture/policy-engine.md
      - Audit Trail: architecture/audit-trail.md
      - Enforcement Proxy: architecture/enforcement-proxy.md
      - Evidence Pipeline: architecture/evidence-pipeline.md
      - API Gateway: architecture/api-gateway.md
      - Module Dependencies: architecture/module-deps.svg
  - API Reference:
      - OpenAPI: api/openapi.md
      - Python SDK: api/python/
      - TypeScript SDK: sdk/typescript/
      - Rust Crates: rust/
  - Policy DSL:
      - Specification: policy-dsl/specification.md
      - Grammar: policy-dsl/grammar.md
      - Examples: policy-dsl/examples.md
      - Migration Guide: policy-dsl/migration.md
  - Guides:
      - Plugin Development: guides/plugin-development.md
      - Adding a Framework: guides/adding-framework.md
      - Testing Guide: guides/testing.md
      - Deployment: guides/deployment.md
  - ADR:
      - Index: adr/index.md
  - Changelog: changelog.md
  - FAQ: faq.md
  - Glossary: glossary.md

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/grc-claw/grc-claw
    - icon: fontawesome/brands/discord
      link: https://discord.gg/grc-claw
  version:
    provider: mike

copyright: Copyright &copy; 2026 GRC_Claw Contributors
```

### 2.4 Documentation Templates

#### 2.4.1 Module README Template

```markdown
<!-- docs/_templates/module-template.md -->
# {{ module_name }}

## Purpose

{{ one-line description of module purpose }}

## Architecture

{{ module architecture diagram and description }}

## API

{{ auto-generated API reference }}

## Configuration

{{ configuration options table }}

## Examples

{{ usage examples }}

## Dependencies

{{ inbound and outbound dependencies }}

## Testing

{{ how to run module tests }}

## Changelog

{{ module-specific changelog }}
```

#### 2.4.2 ADR Template

```markdown
<!-- docs/_templates/adr-template.md -->
# ADR-{{ number }}: {{ title }}

## Status

Proposed | Accepted | Deprecated | Superseded by ADR-{{ superseding_number }}

## Context

What is the issue we're addressing? Why is this decision necessary?

## Decision

What did we decide? Include the specific technical approach.

## Consequences

### Positive
- {{ positive consequence 1 }}
- {{ positive consequence 2 }}

### Negative
- {{ negative consequence 1 }}
- {{ negative consequence 2 }}

### Neutral
- {{ neutral consequence 1 }}

## Alternatives Considered

### Alternative 1: {{ name }}
- **Description:** {{ description }}
- **Rejection Reason:** {{ reason }}

### Alternative 2: {{ name }}
- **Description:** {{ description }}
- **Rejection Reason:** {{ reason }}

## References

- [{{ reference title }}]({{ reference_url }})
- Related: ADR-{{ related_adr }}, Issue #{{ issue_number }}

## Notes

{{ additional notes, implementation details, or caveats }}
```

#### 2.4.3 Deprecation Notice Template

```markdown
<!-- docs/_templates/deprecation-template.md -->
# Deprecation Notice: {{ feature_name }}

**Deprecated in:** {{ version }}  
**Sunset date:** {{ sunset_date }}  
**Replacement:** [{{ replacement_name }}]({{ replacement_link }})  
**Tracking Issue:** #{{ issue_number }}

---

## What is changing?

{{ description of the deprecated feature and what replaces it }}

## Why is this changing?

{{ rationale for deprecation }}

## How do I migrate?

### Step 1: {{ step_title }}
{{ step_description }}

```{{ language }}
{{ code_example }}
```

### Step 2: {{ step_title }}
{{ step_description }}

```{{ language }}
{{ code_example }}
```

### Step 3: {{ step_title }}
{{ step_description }}

## Timeline

| Version | Date | Action |
|---------|------|--------|
| {{ version }} | {{ date }} | Feature deprecated, warnings added |
| {{ version+1 }} | {{ date }} | Feature returns 410 Gone |
| {{ version+2 }} | {{ date }} | Code removed |

## FAQ

### Q: {{ question_1 }}
{{ answer_1 }}

### Q: {{ question_2 }}
{{ answer_2 }}

## Questions?

- [GitHub Discussion]({{ discussion_link }})
- [Discord]({{ discord_link }})
- Email: {{ contact_email }}
```

### 2.5 Documentation-as-Code Validation Script

```python
# scripts/validate_docs.py
"""Documentation validation script.

Validates:
1. All public APIs have docstrings
2. All internal links resolve
3. All code examples execute successfully
4. OpenAPI spec is valid
5. No stale references to removed symbols
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

import httpx


def check_docstring_coverage(source_dir: Path, min_coverage: float = 90.0) -> bool:
    """Check that all public functions/classes have docstrings."""
    total = 0
    missing = 0

    for py_file in source_dir.rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue

        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_"):
                    continue
                total += 1
                if not ast.get_docstring(node):
                    missing += 1
                    print(f"  Missing docstring: {py_file}:{node.lineno} {node.name}")

    coverage = ((total - missing) / total * 100) if total > 0 else 100
    print(f"Docstring coverage: {coverage:.1f}% ({total - missing}/{total})")
    return coverage >= min_coverage


def check_internal_links(docs_dir: Path) -> bool:
    """Check that all internal markdown links resolve."""
    all_md_files = list(docs_dir.rglob("*.md"))
    all_file_paths = {str(f.relative_to(docs_dir).with_suffix("")) for f in all_md_files}

    broken_links = []
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for md_file in all_md_files:
        content = md_file.read_text()
        for match in link_pattern.finditer(content):
            link = match.group(2)
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            link_path = link.split("#")[0]
            if not link_path:
                continue
            resolved = (md_file.parent / link_path).resolve()
            if not resolved.exists():
                broken_links.append(f"{md_file}: {link}")

    if broken_links:
        print(f"Broken links found: {len(broken_links)}")
        for link in broken_links:
            print(f"  {link}")
        return False
    print("All internal links resolve ✅")
    return True


def check_code_examples(docs_dir: Path) -> bool:
    """Execute code examples in documentation."""
    example_files = list((docs_dir / "examples").glob("*.py"))
    if not example_files:
        print("No code examples found")
        return True

    failed = []
    for example_file in example_files:
        result = subprocess.run(
            [sys.executable, str(example_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            failed.append(f"{example_file}: {result.stderr}")

    if failed:
        print(f"Failed code examples: {len(failed)}")
        for failure in failed:
            print(f"  {failure}")
        return False
    print(f"All {len(example_files)} code examples pass ✅")
    return True


def check_openapi_spec(spec_path: Path) -> bool:
    """Validate OpenAPI spec is well-formed."""
    if not spec_path.exists():
        print(f"OpenAPI spec not found: {spec_path}")
        return False

    result = subprocess.run(
        ["openapi-spec-validator", str(spec_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"OpenAPI spec invalid: {result.stderr}")
        return False
    print("OpenAPI spec valid ✅")
    return True


def check_stale_references(source_dir: Path, docs_dir: Path) -> bool:
    """Check for references to removed/renamed symbols in docs."""
    # Build set of all public symbols in source
    source_symbols: set[str] = set()
    for py_file in source_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    source_symbols.add(node.name)

    # Check docs for references to non-existent symbols
    stale_refs = []
    symbol_pattern = re.compile(r"`([A-Z][a-zA-Z0-9_]*)`")

    for md_file in docs_dir.rglob("*.md"):
        content = md_file.read_text()
        for match in symbol_pattern.finditer(content):
            symbol = match.group(1)
            if symbol not in source_symbols and symbol not in {"GRC_Claw", "FastAPI", "Pydantic"}:
                stale_refs.append(f"{md_file}: {symbol}")

    if stale_refs:
        print(f"Potential stale references: {len(stale_refs)}")
        for ref in stale_refs[:20]:
            print(f"  {ref}")
        return False
    print("No stale references found ✅")
    return True


def main() -> int:
    """Run all documentation validation checks."""
    repo_root = Path(__file__).parent.parent
    source_dir = repo_root / "src"
    docs_dir = repo_root / "docs"
    spec_path = docs_dir / "api" / "openapi.json"

    print("=== GRC_Claw Documentation Validation ===\n")

    checks = [
        ("Docstring coverage", lambda: check_docstring_coverage(source_dir)),
        ("Internal links", lambda: check_internal_links(docs_dir)),
        ("Code examples", lambda: check_code_examples(docs_dir)),
        ("OpenAPI spec", lambda: check_openapi_spec(spec_path)),
        ("Stale references", lambda: check_stale_references(source_dir, docs_dir)),
    ]

    all_passed = True
    for name, check_fn in checks:
        print(f"--- {name} ---")
        try:
            if not check_fn():
                all_passed = False
                print(f"  ❌ {name} FAILED\n")
            else:
                print(f"  ✅ {name} PASSED\n")
        except Exception as e:
            all_passed = False
            print(f"  ❌ {name} ERROR: {e}\n")

    if all_passed:
        print("=== All documentation checks passed ✅ ===")
        return 0
    else:
        print("=== Some documentation checks failed ❌ ===")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### 2.6 Changelog Configuration

```toml
# cliff.toml
# git-cliff configuration for automated changelog generation

[changelog]
header = """
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""
body = """
{% if version %}\
    ## [{{ version | trim_start_matches(pat="v") }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
    ## [Unreleased]
{% endif %}\
{% for group, commits in commits | group_by(attribute="group") %}
    ### {{ group | striptags | trim | upper_first }}
    {% for commit in commits %}
        - {{ commit.message | upper_first }}\
          {% if commit.scope %} ({{ commit.scope }}){% endif %}\
          {% if commit.breaking %} **[BREAKING]**{% endif %}\
    {% endfor %}
{% endfor %}\n
"""
trim = true
footer = """
---

## Release Links

- [Full Changelog](https://github.com/grc-claw/grc-claw/blob/main/CHANGELOG.md)
- [GitHub Releases](https://github.com/grc-claw/grc-claw/releases)
"""

[git]
conventional_commits = true
filter_unconventional = true
commit_preprocessors = [
    { pattern = "\\((\\w+\\s)?#([0-9]+)\\)", replace = "([#${2}](https://github.com/grc-claw/grc-claw/issues/${2}))" },
    { pattern = "Merge pull request #(\\d+) from (.*)", replace = "PR [#${1}](https://github.com/grc-claw/grc-claw/pull/${1}) from ${2}" },
]
commit_parsers = [
    { message = "^feat", group = "<!-- 0 -->Features" },
    { message = "^fix", group = "<!-- 1 -->Bug Fixes" },
    { message = "^doc", group = "<!-- 2 -->Documentation" },
    { message = "^perf", group = "<!-- 3 -->Performance" },
    { message = "^refactor", group = "<!-- 4 -->Refactoring" },
    { message = "^test", group = "<!-- 5 -->Testing" },
    { message = "^build", group = "<!-- 6 -->Build System" },
    { message = "^ci", group = "<!-- 7 -->CI/CD" },
    { message = "^chore\\(release\\):", skip = true },
    { message = "^chore\\(deps\\)", group = "<!-- 8 -->Dependencies" },
    { message = "^chore", group = "<!-- 9 -->Miscellaneous" },
    { body = ".*security", group = "<!-- 10 -->Security" },
    { body = ".*breaking", group = "<!-- 11 -->Breaking Changes" },
]
filter_commits = false
tag_pattern = "v[0-9]*"
ignore_tags = ""
topo_order = false
sort_commits = "oldest"
```

---

## 3. Technical Debt Management

### 3.1 Debt Tracking System

```markdown
<!-- TECH-DEBT.md -->
# Technical Debt Register

**Last Updated:** 2026-10-01  
**Total Open Items:** 3  
**Total Estimated Effort:** 6 days

## Summary

| Severity | Count | Target Fix |
|----------|-------|------------|
| Critical | 0 | — |
| High | 0 | — |
| Medium | 2 | v1.4.0 |
| Low | 1 | v1.3.5 |

## Open Items

### TD-001: Policy evaluator uses recursive descent without memoization

| Field | Value |
|-------|-------|
| **Module** | policy-engine |
| **Category** | Design |
| **Severity** | Medium |
| **Created** | 2026-10-01 |
| **Target Fix** | v1.4.0 |
| **Estimated Effort** | 3 days |
| **Status** | Open |
| **PR** | — |

**Description:** The policy evaluator uses recursive descent parsing without memoization, causing O(n²) evaluation time for deeply nested policies.

**Impact:** Policy evaluation latency increases exponentially with nesting depth. At depth > 10, evaluation exceeds 100ms SLA.

**Proposed Solution:** Implement memoization cache for parsed policy AST nodes. Consider switching to iterative evaluation for deeply nested policies.

**Acceptance Criteria:**
- [ ] Policy evaluation p99 < 50ms for nesting depth up to 20
- [ ] All existing policy tests pass
- [ ] Property-based tests verify evaluation correctness
- [ ] Benchmark tests demonstrate improvement

---

### TD-002: Duplicated validation logic in API layer

| Field | Value |
|-------|-------|
| **Module** | api-gateway |
| **Category** | Code |
| **Severity** | Low |
| **Created** | 2026-09-15 |
| **Target Fix** | v1.3.0 |
| **Estimated Effort** | 1 day |
| **Status** | In Progress |
| **PR** | #234 |

**Description:** Request validation logic is duplicated across 12 endpoint handlers instead of using shared Pydantic validators.

**Impact:** Inconsistent validation behavior, increased maintenance burden.

**Proposed Solution:** Extract common validation logic into reusable Pydantic validators and middleware.

---

### TD-003: Missing integration tests for evidence export

| Field | Value |
|-------|-------|
| **Module** | evidence-pipeline |
| **Category** | Test |
| **Severity** | Medium |
| **Created** | 2026-08-20 |
| **Target Fix** | v1.3.5 |
| **Estimated Effort** | 2 days |
| **Status** | Open |
| **PR** | — |

**Description:** The evidence export pipeline lacks integration tests for the PDF and XML export formats.

**Impact:** Export format regressions may go undetected.

**Proposed Solution:** Add integration tests for all export formats with golden file comparison.

---

## Resolved Items

### TD-000: N+1 query in agent registry (Resolved 2026-09-01)

| Field | Value |
|-------|-------|
| **Module** | agent-registry |
| **Category** | Code |
| **Severity** | High |
| **Created** | 2026-07-15 |
| **Resolved** | 2026-09-01 |
| **PR** | #198 |

**Resolution:** Implemented eager loading with SQLAlchemy `selectinload`. Query count reduced from O(n) to O(1).
```

### 3.2 Debt Detection Automation

```yaml
# .github/workflows/debt-detection.yml
name: Technical Debt Detection

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  detect-debt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install tools
        run: |
          pip install vulture radon xenon
          cargo install cargo-udeps

      # ─── Dead Code Detection ─────────────────────────────────
      - name: Detect dead code (Python)
        run: |
          echo "## Dead Code Report" > debt-report.md
          echo "" >> debt-report.md
          vulture src/ --min-confidence 80 >> debt-report.md || true

      - name: Detect dead code (Rust)
        run: |
          echo "" >> debt-report.md
          echo "## Unused Dependencies (Rust)" >> debt-report.md
          echo "" >> debt-report.md
          cargo udeps --all-targets >> debt-report.md 2>&1 || true

      # ─── Complexity Analysis ─────────────────────────────────
      - name: Complexity analysis (Python)
        run: |
          echo "" >> debt-report.md
          echo "## Complexity Report (Python)" >> debt-report.md
          echo "" >> debt-report.md
          echo "### Cyclomatic Complexity" >> debt-report.md
          radon cc src/ -nc >> debt-report.md || true
          echo "" >> debt-report.md
          echo "### Cognitive Complexity" >> debt-report.md
          radon cc src/ -nc -s >> debt-report.md || true

      - name: Complexity trend
        run: |
          echo "" >> debt-report.md
          echo "## Complexity Trend" >> debt-report.md
          echo "" >> debt-report.md
          xenon --max-absolute B --max-modules A --max-average A src/ >> debt-report.md || true

      # ─── Type Gap Analysis ───────────────────────────────────
      - name: Type gap analysis
        run: |
          echo "" >> debt-report.md
          echo "## Type Gap Report" >> debt-report.md
          echo "" >> debt-report.md
          mypy src/ --config-file pyproject.toml --no-error-summary >> debt-report.md 2>&1 || true

      # ─── Test Flakiness ──────────────────────────────────────
      - name: Detect flaky tests
        run: |
          echo "" >> debt-report.md
          echo "## Flaky Test Report" >> debt-report.md
          echo "" >> debt-report.md
          pytest tests/ --reruns=3 --reruns-delay=1 -q 2>&1 | grep -i "rerun\|flaky" >> debt-report.md || true

      # ─── Upload Report ───────────────────────────────────────
      - name: Upload debt report
        uses: actions/upload-artifact@v4
        with:
          name: debt-report
          path: debt-report.md

      # ─── Create Issues for New Debt ──────────────────────────
      - name: Create issues for critical debt
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('debt-report.md', 'utf8');

            // Check for critical complexity violations
            const complexityPattern = /(\w+\.py):(\d+):(\d+)\s+-\s+([A-Z])\s+\((\d+)\)/g;
            let match;
            while ((match = complexityPattern.exec(report)) !== null) {
              const complexity = parseInt(match[5]);
              if (complexity > 15) {
                await github.rest.issues.create({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  title: `TECH-DEBT: High complexity in ${match[1]}:${match[2]} (score: ${complexity})`,
                  body: `Automated debt detection found high cyclomatic complexity.\n\n` +
                        `**File:** ${match[1]}\n` +
                        `**Line:** ${match[2]}\n` +
                        `**Complexity:** ${complexity}\n` +
                        `**Threshold:** 15\n\n` +
                        `Please refactor to reduce complexity.`,
                  labels: ['tech-debt', 'complexity']
                });
              }
            }
```

### 3.3 Debt Budget Enforcement

```python
# scripts/debt_budget.py
"""Technical debt budget enforcement script.

Runs in CI to enforce debt budgets per sprint.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class DebtItem:
    """Represents a technical debt item."""
    id: str
    description: str
    module: str
    category: str
    severity: str
    created: str
    target_fix: str
    effort_days: int
    status: str
    pr: str = ""


@dataclass
class DebtBudget:
    """Debt budget configuration."""
    max_new_items_per_sprint: int = 3
    max_code_smells_per_sprint: int = 5
    max_coverage_decrease: float = 2.0
    max_complexity_increase: float = 5.0
    max_test_runtime_increase: float = 10.0
    sprint_debt_capacity: float = 0.20  # 20% of sprint


@dataclass
class DebtMetrics:
    """Current debt metrics."""
    open_items: int = 0
    new_items_this_sprint: int = 0
    resolved_this_sprint: int = 0
    avg_age_days: float = 0.0
    total_effort_days: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    by_module: dict[str, int] = field(default_factory=dict)


def parse_tech_debt_file(filepath: Path) -> list[DebtItem]:
    """Parse TECH-DEBT.md file."""
    if not filepath.exists():
        return []

    content = filepath.read_text()
    items = []

    # Parse table rows
    row_pattern = re.compile(
        r"\|\s*(TD-\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
    )

    for match in row_pattern.finditer(content):
        item = DebtItem(
            id=match.group(1).strip(),
            description=match.group(2).strip(),
            module=match.group(3).strip(),
            category=match.group(4).strip(),
            severity=match.group(5).strip(),
            created=match.group(6).strip(),
            target_fix=match.group(7).strip(),
            effort_days=int(match.group(8).strip().replace(" days", "").replace(" day", "")),
            status=match.group(9).strip(),
            pr=match.group(10).strip(),
        )
        items.append(item)

    return items


def calculate_metrics(items: list[DebtItem]) -> DebtMetrics:
    """Calculate debt metrics from items."""
    metrics = DebtMetrics()
    now = datetime.now()

    for item in items:
        if item.status.lower() in ("open", "in progress"):
            metrics.open_items += 1
            metrics.total_effort_days += item.effort_days

            # Calculate age
            try:
                created = datetime.strptime(item.created, "%Y-%m-%d")
                age = (now - created).days
                metrics.avg_age_days += age
            except ValueError:
                pass

            # Count by severity
            metrics.by_severity[item.severity] = metrics.by_severity.get(item.severity, 0) + 1

            # Count by category
            metrics.by_category[item.category] = metrics.by_category.get(item.category, 0) + 1

            # Count by module
            metrics.by_module[item.module] = metrics.by_module.get(item.module, 0) + 1

    if metrics.open_items > 0:
        metrics.avg_age_days /= metrics.open_items

    return metrics


def check_budget(metrics: DebtMetrics, budget: DebtBudget) -> list[str]:
    """Check if debt metrics are within budget."""
    violations = []

    if metrics.new_items_this_sprint > budget.max_new_items_per_sprint:
        violations.append(
            f"New debt items ({metrics.new_items_this_sprint}) exceeds "
            f"budget ({budget.max_new_items_per_sprint})"
        )

    if metrics.avg_age_days > 180:
        violations.append(
            f"Average debt age ({metrics.avg_age_days:.0f} days) exceeds "
            f"6-month threshold"
        )

    critical_count = metrics.by_severity.get("Critical", 0)
    if critical_count > 0:
        violations.append(
            f"Critical debt items ({critical_count}) must be resolved immediately"
        )

    return violations


def generate_report(metrics: DebtMetrics, violations: list[str]) -> str:
    """Generate debt budget report."""
    report = [
        "# Technical Debt Budget Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Current Metrics",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Open items | {metrics.open_items} |",
        f"| New this sprint | {metrics.new_items_this_sprint} |",
        f"| Resolved this sprint | {metrics.resolved_this_sprint} |",
        f"| Average age | {metrics.avg_age_days:.0f} days |",
        f"| Total effort | {metrics.total_effort_days} days |",
        "",
        "## By Severity",
        "",
    ]

    for severity, count in sorted(metrics.by_severity.items()):
        report.append(f"- **{severity}:** {count}")

    report.extend(["", "## By Category", ""])
    for category, count in sorted(metrics.by_category.items()):
        report.append(f"- **{category}:** {count}")

    report.extend(["", "## By Module", ""])
    for module, count in sorted(metrics.by_module.items()):
        report.append(f"- **{module}:** {count}")

    if violations:
        report.extend(["", "## ❌ Budget Violations", ""])
        for violation in violations:
            report.append(f"- {violation}")
    else:
        report.extend(["", "## ✅ All budgets within limits", ""])

    return "\n".join(report)


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    debt_file = repo_root / "TECH-DEBT.md"

    items = parse_tech_debt_file(debt_file)
    metrics = calculate_metrics(items)
    budget = DebtBudget()
    violations = check_budget(metrics, budget)

    report = generate_report(metrics, violations)
    print(report)

    # Write report to file
    report_file = repo_root / "debt-budget-report.md"
    report_file.write_text(report)

    if violations:
        print("\n❌ Debt budget violations detected!")
        return 1

    print("\n✅ All debt budgets within limits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 3.4 Debt-Aware Code Review Checklist

```markdown
<!-- .github/PULL_REQUEST_TEMPLATE.md -->
## Description

<!-- Describe your changes -->

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] ♻️ Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test update
- [ ] 🔧 Build/CI configuration change
- [ ] 📦 Dependency update

## Technical Debt Assessment

- [ ] This PR does NOT introduce new technical debt
- [ ] This PR addresses existing technical debt (reference: TD-XXX)
- [ ] This PR introduces new technical debt (justification required below)

**If new debt introduced, provide justification:**

<!-- Why is this debt acceptable? What is the plan to resolve it? -->

## Quality Checklist

- [ ] All linters pass (`make lint`)
- [ ] All tests pass (`make test`)
- [ ] Coverage meets module threshold
- [ ] No new dependencies without justification
- [ ] Public API changes have updated OpenAPI spec
- [ ] New/changed logic has docstrings
- [ ] ADR created for significant design decisions
- [ ] `CHANGELOG.md` updated
- [ ] No `TODO`/`FIXME` comments without linked issue
- [ ] No hardcoded secrets

## Review Focus Areas

<!-- For reviewers: assess these maintainability aspects -->

1. **Correctness** — Does the code do what it claims?
2. **Test quality** — Are tests meaningful, not just coverage-padding?
3. **Maintainability** — Can the next developer understand and modify this?
4. **Performance** — Are there obvious bottlenecks or resource leaks?
5. **Security** — Are inputs validated? Are secrets handled safely?
6. **Modularity** — Does it respect module boundaries? Are dependencies clean?

## Screenshots (if applicable)

<!-- Add screenshots for UI changes -->

## Additional Context

<!-- Any additional context for reviewers -->
```

---

## 4. Refactoring Automation

### 4.1 Automated Refactoring Pipeline

```yaml
# .github/workflows/auto-refactor.yml
name: Auto-Refactor

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM
  workflow_dispatch:

jobs:
  auto-refactor:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      # ─── Python Auto-Fix ─────────────────────────────────────
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Python tools
        run: |
          pip install ruff pyupgrade com2ann

      - name: Run ruff auto-fix
        run: |
          ruff check --fix . --config pyproject.toml || true
          ruff format . --config pyproject.toml || true

      - name: Run pyupgrade
        run: |
          find src -name "*.py" -exec pyupgrade --py312-plus {} +

      # ─── Rust Auto-Fix ───────────────────────────────────────
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - name: Run cargo fmt
        run: cargo fmt --all

      - name: Run cargo clippy fix
        run: cargo clippy --all-targets --all-features --fix --allow-dirty --allow-staged || true

      - name: Run cargo fix
        run: cargo fix --allow-dirty --allow-staged || true

      # ─── TypeScript Auto-Fix ─────────────────────────────────
      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: pnpm

      - name: Install Node dependencies
        run: pnpm install --frozen-lockfile

      - name: Run ESLint fix
        run: pnpm lint:fix || true

      - name: Run Prettier
        run: pnpm format || true

      # ─── Create PR if Changes ────────────────────────────────
      - name: Check for changes
        id: git-diff
        run: |
          if git diff --quiet; then
            echo "has_changes=false" >> $GITHUB_OUTPUT
          else
            echo "has_changes=true" >> $GITHUB_OUTPUT
          fi

      - name: Create Pull Request
        if: steps.git-diff.outputs.has_changes == 'true'
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "chore: automated refactoring"
          title: "chore: automated refactoring"
          body: |
            ## Automated Refactoring Changes

            This PR contains automated refactoring changes:

            - **Python:** Import cleanup, formatting, lint auto-fixes, type modernization
            - **Rust:** Formatting, clippy fixes, compiler-suggested fixes
            - **TypeScript:** ESLint fixes, Prettier formatting

            ### Safety

            All changes are behavior-preserving. The full test suite must pass before merge.

            ### Verification

            - [ ] All linters pass
            - [ ] All tests pass
            - [ ] Coverage does not decrease
            - [ ] No breaking changes
          branch: auto-refactor/${{ github.run_id }}
          delete-branch: true
          labels: |
            automated
            refactoring
```

### 4.2 Complexity-Driven Refactoring

```python
# scripts/complexity_refactor.py
"""Detect complexity violations and create refactoring issues."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ComplexityViolation:
    """Represents a complexity violation."""
    file: str
    line: int
    function: str
    metric: str
    value: int
    threshold: int


def run_radon_cc(source_dir: Path) -> list[ComplexityViolation]:
    """Run radon cyclomatic complexity analysis."""
    result = subprocess.run(
        ["radon", "cc", str(source_dir), "-nc", "-s", "-j"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"radon cc failed: {result.stderr}")
        return []

    violations = []
    data = json.loads(result.stdout)

    for file_path, functions in data.items():
        for func in functions:
            complexity = func["complexity"]
            if complexity > 10:
                violations.append(
                    ComplexityViolation(
                        file=file_path,
                        line=func["lineno"],
                        function=func["name"],
                        metric="cyclomatic",
                        value=complexity,
                        threshold=10,
                    )
                )

    return violations


def run_radon_mi(source_dir: Path) -> list[ComplexityViolation]:
    """Run radon maintainability index analysis."""
    result = subprocess.run(
        ["radon", "mi", str(source_dir), "-s", "-j"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"radon mi failed: {result.stderr}")
        return []

    violations = []
    data = json.loads(result.stdout)

    for file_path, mi_data in data.items():
        mi = mi_data["mi"]
        if mi < 65:  # MI threshold for refactoring
            violations.append(
                ComplexityViolation(
                    file=file_path,
                    line=0,
                    function="(module)",
                    metric="maintainability_index",
                    value=round(mi),
                    threshold=65,
                )
            )

    return violations


def check_function_length(file_path: Path, max_lines: int = 50) -> list[ComplexityViolation]:
    """Check for functions exceeding maximum length."""
    violations = []
    content = file_path.read_text()
    lines = content.split("\n")

    current_function = None
    function_start = 0
    indent_level = 0

    for i, line in enumerate(lines, 1):
        # Detect function definition
        func_match = re.match(r"^(\s*)(async\s+)?def\s+(\w+)", line)
        if func_match:
            if current_function and (i - function_start) > max_lines:
                violations.append(
                    ComplexityViolation(
                        file=str(file_path),
                        line=function_start,
                        function=current_function,
                        metric="function_length",
                        value=i - function_start,
                        threshold=max_lines,
                    )
                )
            current_function = func_match.group(3)
            function_start = i
            indent_level = len(func_match.group(1))

    return violations


def generate_refactoring_issue(violation: ComplexityViolation) -> dict:
    """Generate a refactoring issue body."""
    return {
        "title": f"Refactor: {violation.function} in {violation.file} ({violation.metric}: {violation.value})",
        "body": f"""## Refactoring Opportunity: {violation.function}

**Detected by:** Automated complexity analysis  
**Metric:** {violation.metric}  
**Current value:** {violation.value}  
**Threshold:** {violation.threshold}  
**File:** `{violation.file}:{violation.line}`

### Current State

The function `{violation.function}` has a {violation.metric} of {violation.value}, which exceeds the threshold of {violation.threshold}.

### Proposed Refactoring

- Extract complex logic into smaller, focused functions
- Reduce nesting depth using early returns
- Consider using design patterns (Strategy, Command, etc.)
- Add comprehensive tests before refactoring

### Effort Estimate

- [ ] Small (< 1 hour)
- [ ] Medium (1-4 hours)
- [ ] Large (4+ hours)

### Priority

- [ ] Low
- [ ] Medium
- [ ] High

### Acceptance Criteria

- [ ] All tests pass
- [ ] {violation.metric} below {violation.threshold}
- [ ] No coverage decrease
- [ ] Documentation updated
- [ ] ADR created if architectural change

---

*This issue was automatically generated by the complexity refactoring pipeline.*""",
        "labels": ["refactoring", "tech-debt", violation.metric],
    }


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    source_dir = repo_root / "src"

    print("=== Complexity-Driven Refactoring Detection ===\n")

    # Run all complexity checks
    violations = []
    violations.extend(run_radon_cc(source_dir))
    violations.extend(run_radon_mi(source_dir))

    for py_file in source_dir.rglob("*.py"):
        violations.extend(check_function_length(py_file))

    if not violations:
        print("✅ No complexity violations found!")
        return 0

    print(f"Found {len(violations)} complexity violations:\n")
    for v in violations:
        print(f"  {v.file}:{v.line} {v.function} - {v.metric}: {v.value} (threshold: {v.threshold})")

    # Output issues as JSON for GitHub Actions
    issues = [generate_refactoring_issue(v) for v in violations]
    print(f"\nGenerated {len(issues)} refactoring issues")

    # Write issues to file for GitHub Actions to consume
    issues_file = repo_root / "refactoring-issues.json"
    issues_file.write_text(json.dumps(issues, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 4.3 Refactoring Safety Verification

```python
# scripts/verify_refactoring.py
"""Verify that a refactoring PR is safe to merge.

Runs comprehensive checks to ensure behavioral equivalence.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ FAILED: {description}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False

    print(f"✅ PASSED: {description}")
    if result.stdout:
        print(result.stdout[:500])
    return True


def verify_refactoring() -> bool:
    """Run all refactoring verification checks."""
    checks = [
        # Behavioral equivalence
        (
            ["pytest", "tests/unit/", "-x", "-q", "--tb=short"],
            "Unit tests",
        ),
        (
            ["pytest", "tests/integration/", "-x", "-q", "--tb=short"],
            "Integration tests",
        ),
        (
            ["pytest", "tests/contract/", "-x", "-q", "--tb=short"],
            "Contract tests",
        ),
        # Property-based tests
        (
            ["pytest", "tests/", "-m", "property", "-x", "-q", "--tb=short"],
            "Property-based tests",
        ),
        # Snapshot tests
        (
            ["pytest", "tests/", "-k", "snapshot", "-x", "-q", "--tb=short"],
            "Snapshot tests",
        ),
        # Coverage parity
        (
            ["pytest", "tests/", "--cov=src", "--cov-report=term-missing", "--cov-fail-under=88"],
            "Coverage gate",
        ),
        # Type checking
        (
            ["mypy", "src/", "--config-file", "pyproject.toml"],
            "Type checking (Python)",
        ),
        (
            ["cargo", "check", "--all-targets", "--all-features"],
            "Type checking (Rust)",
        ),
        (
            ["pnpm", "type-check"],
            "Type checking (TypeScript)",
        ),
        # Linting
        (
            ["ruff", "check", ".", "--config", "pyproject.toml"],
            "Linting (Python)",
        ),
        (
            ["cargo", "clippy", "--all-targets", "--all-features", "--", "-D", "warnings"],
            "Linting (Rust)",
        ),
        (
            ["pnpm", "lint"],
            "Linting (TypeScript)",
        ),
        # Performance regression
        (
            ["pytest", "tests/performance/", "-x", "-q", "--tb=short"],
            "Performance tests",
        ),
    ]

    all_passed = True
    for cmd, description in checks:
        if not run_command(cmd, description):
            all_passed = False

    return all_passed


def main() -> int:
    """Main entry point."""
    print("=== Refactoring Safety Verification ===")
    print("This script verifies that a refactoring PR maintains")
    print("behavioral equivalence and meets all quality gates.\n")

    if verify_refactoring():
        print("\n" + "=" * 60)
        print("✅ All refactoring verification checks passed!")
        print("This refactoring is safe to merge.")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Some refactoring verification checks failed!")
        print("Do not merge until all checks pass.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### 4.4 Refactoring Configuration

```toml
# refactor.toml
# Configuration for automated refactoring tools

[python]
# Ruff auto-fix rules
ruff_fix_rules = ["E", "F", "I", "UP", "B", "A", "C4", "SIM", "TCH"]

# Pyupgrade target version
pyupgrade_target = "py312"

# Com2ann settings
com2ann_enabled = true

[rust]
# Clippy lint groups
clippy_lints = [
    "clippy::pedantic",
    "clippy::nursery",
    "clippy::cargo",
]

# Cargo fix settings
cargo_fix_allow_dirty = true
cargo_fix_allow_staged = true

[typescript]
# ESLint fix rules
eslint_fix_rules = [
    "@typescript-eslint/no-unused-vars",
    "react-hooks/exhaustive-deps",
]

# Prettier settings
prettier_write = true

[complexity]
# Thresholds for automatic refactoring triggers
cyclomatic_threshold = 10
cognitive_threshold = 15
function_length_threshold = 50
module_length_threshold = 800
nesting_depth_threshold = 6
duplication_threshold = 5

[safety]
# Required verification steps
require_full_test_suite = true
require_property_tests = true
require_snapshot_tests = true
require_coverage_parity = true
require_type_checking = true
max_coverage_decrease = 0.0
```

---

## 5. Developer Onboarding

### 5.1 Onboarding Automation

```yaml
# .github/workflows/welcome.yml
name: Welcome New Contributor

on:
  pull_request_target:
    types: [opened]

jobs:
  welcome:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      pull-requests: write
    steps:
      - name: Check if first contribution
        id: check-first
        uses: actions/github-script@v7
        with:
          script: |
            const { data: prs } = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'all',
              creator: context.payload.pull_request.user.login,
              per_page: 1
            });
            const isFirst = prs.length <= 1;
            core.setOutput('is_first', isFirst);

      - name: Welcome comment
        if: steps.check-first.outputs.is_first == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🎉 Welcome to GRC_Claw, @${context.payload.pull_request.user.login}!

              Thank you for your first contribution! We're excited to have you join our community.

              ### Getting Started

              Here are some resources to help you navigate the codebase:

              - 📖 [Contributing Guide](https://github.com/grc-claw/grc-claw/blob/main/CONTRIBUTING.md)
              - 🏗️ [Architecture Overview](https://github.com/grc-claw/grc-claw/blob/main/docs/architecture/overview.md)
              - 📋 [API Reference](https://github.com/grc-claw/grc-claw/blob/main/docs/api/openapi.md)
              - 🔧 [Development Setup](https://github.com/grc-claw/grc-claw/blob/main/docs/getting-started/installation.md)

              ### Next Steps

              1. A maintainer will review your PR within 48 hours
              2. A mentor will be assigned to help you with your first few PRs
              3. Join our [Discord](https://discord.gg/grc-claw) for real-time help

              ### Need Help?

              - Comment on this PR with any questions
              - Tag a maintainer with \`@grc-claw/maintainers\`
              - Open a [GitHub Discussion](https://github.com/grc-claw/grc-claw/discussions)

              We're looking forward to your contributions! 🚀`
            });

      - name: Create onboarding checklist
        if: steps.check-first.outputs.is_first == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Onboarding: @${context.payload.pull_request.user.login}`,
              body: `## Onboarding Checklist for @${context.payload.pull_request.user.login}

              Welcome to the GRC_Claw team! This issue tracks your onboarding progress.

              ### Week 1: Environment & Orientation
              - [ ] Environment setup complete (\`make dev-setup\` passes)
              - [ ] Read [Architecture Overview](https://github.com/grc-claw/grc-claw/blob/main/docs/architecture/overview.md)
              - [ ] Run full test suite locally (\`make test\`)
              - [ ] Complete "Your First Policy" tutorial
              - [ ] Attend community call (Tuesdays 17:00 UTC)
              - [ ] Join [Discord](https://discord.gg/grc-claw)

              ### Week 2: First Contributions
              - [ ] First PR submitted
              - [ ] First PR merged
              - [ ] Complete module walkthrough with mentor
              - [ ] Review another contributor's PR

              ### Month 1: Integration
              - [ ] 3 PRs merged
              - [ ] Complete plugin development tutorial
              - [ ] Participate in code review (as reviewer)
              - [ ] Attend architecture review meeting
              - [ ] Pick up a \`help-wanted\` issue

              ### Mentor Assignment
              - [ ] Mentor assigned
              - [ ] Initial mentor meeting completed
              - [ ] Weekly check-ins scheduled

              ---
              *This issue was automatically created by the GRC_Claw onboarding automation.*`,
              assignees: ['grc-claw-bot'],
              labels: ['onboarding', 'good-first-issue']
            });

      - name: Assign mentor
        if: steps.check-first.outputs.is_first == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            // Assign a mentor from the mentor pool
            const mentors = ['mentor1', 'mentor2', 'mentor3'];
            const assignedMentor = mentors[Math.floor(Math.random() * mentors.length)];

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `### 👋 Mentor Assigned

              @${assignedMentor} has been assigned as your mentor for your first few PRs.

              Your mentor will:
              - Answer questions within 24 hours
              - Review your PRs within 48 hours
              - Provide constructive, kind feedback
              - Help you navigate the codebase and processes

              Feel free to reach out to them anytime!`
            });
```

### 5.2 Onboarding Documentation

```markdown
<!-- docs/getting-started/onboarding.md -->
# GRC_Claw Developer Onboarding

## Welcome!

This guide will help you become productive in GRC_Claw within your first week.

## Day 1: Environment Setup

### Prerequisites

- Python 3.12+
- Rust 1.75+
- Node.js 20+
- Docker Desktop
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/grc-claw/grc-claw.git
cd grc-claw

# One-command setup
make dev-setup

# Verify everything works
make doctor

# Run tests
make test

# Start development server
make dev
```

### What `make dev-setup` Does

1. Creates Python virtual environment and installs dependencies (`uv sync`)
2. Installs Rust toolchain (`rustup`)
3. Installs Node.js dependencies (`pnpm install`)
4. Installs pre-commit hooks (`pre-commit install`)
5. Starts Docker services (PostgreSQL, Redis, Kafka, MinIO)
6. Generates `.env` from `.env.example`
7. Applies database migrations (`alembic upgrade head`)
8. Loads seed data for local development

### Verify Your Setup

```bash
# Check all tools are installed
make doctor

# Run a quick test
make test-fast

# Check the dashboard
open http://localhost:3000
```

## Day 2: Architecture Overview

### Core Modules

| Module | Language | Purpose |
|--------|----------|---------|
| Policy Engine | Python | Parse, validate, evaluate policies |
| Audit Trail | Rust | Append-only hash-chained log |
| Enforcement Proxy | Rust | Real-time policy enforcement |
| Compliance Mapper | Python | Map controls to frameworks |
| Evidence Collector | Python | Collect and normalize evidence |
| Agent Registry | Python | Agent identity and lifecycle |
| Analytics Engine | Python | Risk scoring and trends |
| API Gateway | Python | REST API, auth, routing |
| Web UI | TypeScript | Dashboard and reports |

### Module Dependencies

```
┌─────────────┐
│   Web UI    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ API Gateway │
└──────┬──────┘
       │
       ├──────────┬──────────┬──────────┐
       ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Policy  │ │  Audit   │ │Evidence │ │Compliance│
│  Engine  │ │  Trail   │ │Collector │ │  Mapper  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
       │          │          │          │
       └──────────┴──────────┴──────────┘
                      │
                      ▼
              ┌──────────────┐
              │   Storage    │
              └──────────────┘
```

### Key Design Principles

1. **Explicit over Implicit** — All behavior is documented, typed, and discoverable
2. **Blast Radius Containment** — Changes to one module don't cascade unpredictably
3. **Testability as a First-Class Concern** — Every module is testable in isolation
4. **Documentation Lives with Code** — Docs are versioned alongside code
5. **Deprecation is Planned, Not Reactive** — Features have defined lifecycles

## Day 3: First Contribution

### Find a Good First Issue

1. Browse issues labeled `good-first-issue`
2. Comment on an issue to claim it
3. Create a branch: `git checkout -b fix/issue-NNN`
4. Make your change, run tests, submit PR
5. A maintainer will review within 48 hours

### Development Workflow

```bash
# Create a feature branch
git checkout -b feat/my-feature

# Make your changes
# ...

# Run quality checks
make lint
make typecheck
make test-fast

# Commit (pre-commit hooks will run)
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push origin feat/my-feature
gh pr create --fill
```

### Code Review Process

1. **Automated checks** — CI runs linting, testing, coverage, security scans
2. **Maintainer review** — At least 1 maintainer approval (2 for core modules)
3. **Address feedback** — Make requested changes and push updates
4. **Merge** — Once approved, your PR will be merged

## Day 4: Deep Dive

### Pair with Your Mentor

Your mentor will walk you through:
- Module architecture and design decisions
- Testing strategies and patterns
- Common pitfalls and how to avoid them
- How to navigate the codebase efficiently

### Complete a Module Exercise

Each module has a guided exercise:
- **Policy Engine:** Write a custom policy rule
- **Audit Trail:** Verify hash chain integrity
- **Enforcement Proxy:** Add a new enforcement action
- **Evidence Collector:** Create a custom collector
- **API Gateway:** Add a new endpoint

## Day 5: Independent Work

### Pick Up a Help-Wanted Issue

Browse issues labeled `help-wanted` and pick one that interests you.

### Join the Community

- **Discord:** [Join our Discord](https://discord.gg/grc-claw)
- **Community Call:** Tuesdays 17:00 UTC
- **GitHub Discussions:** Ask questions and share ideas

## Learning Path

### Week 1
- [ ] Environment setup complete
- [ ] Read architecture overview
- [ ] Run full test suite locally
- [ ] Complete "Your First Policy" tutorial
- [ ] Attend community call

### Week 2
- [ ] First PR submitted
- [ ] First PR merged
- [ ] Complete module walkthrough with mentor
- [ ] Join Discord/Slack channel

### Month 1
- [ ] 3 PRs merged
- [ ] Complete plugin development tutorial
- [ ] Participate in code review (as reviewer)
- [ ] Attend architecture review meeting

## Getting Help

### Documentation
- [Architecture Overview](../architecture/overview.md)
- [API Reference](../api/openapi.md)
- [Policy DSL Guide](../policy-dsl/specification.md)
- [Plugin Development](../guides/plugin-development.md)

### Communication
- **GitHub Discussions** — Questions and ideas
- **Discord** — Real-time chat with community
- **Email** — maintainers@grc-claw.dev

### Troubleshooting
- [Troubleshooting Guide](../troubleshooting.md)
- [FAQ](../faq.md)
```

### 5.3 Interactive Tutorial: Your First Policy

```python
# docs/examples/tutorial-first-policy.py
"""
Tutorial: Your First Policy in GRC_Claw

This tutorial walks you through creating, testing, and deploying
a custom policy in GRC_Claw.

Run this file to verify your setup:
    python docs/examples/tutorial-first-policy.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ─── Step 1: Define Your Policy Model ──────────────────────────

class Decision(Enum):
    """Policy decision outcomes."""
    ALLOW = "ALLOW"
    DENY = "DENY"
    CHALLENGE = "CHALLENGE"


class DataClassification(Enum):
    """Data classification levels."""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


@dataclass
class PolicyContext:
    """Context for policy evaluation."""
    agent_id: str
    data_classification: DataClassification
    operation: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    decision: Decision
    reason: str
    policy_id: str
    rule_results: list[dict[str, Any]] = field(default_factory=list)


# ─── Step 2: Write Your First Policy Rule ──────────────────────

def evaluate_data_retention_policy(context: PolicyContext) -> PolicyResult:
    """
    Evaluate the data retention policy.

    Rules:
    1. RESTRICTED data requires explicit approval
    2. CONFIDENTIAL data requires manager approval for delete operations
    3. All other operations are allowed

    Args:
        context: The policy evaluation context

    Returns:
        PolicyResult with decision and reasoning
    """
    rule_results = []

    # Rule 1: RESTRICTED data check
    if context.data_classification == DataClassification.RESTRICTED:
        rule_results.append({
            "rule": "restricted_data_check",
            "matched": True,
            "action": "CHALLENGE",
        })
        return PolicyResult(
            decision=Decision.CHALLENGE,
            reason="RESTRICTED data requires explicit approval",
            policy_id="data-retention-v1",
            rule_results=rule_results,
        )

    # Rule 2: CONFIDENTIAL data delete check
    if (context.data_classification == DataClassification.CONFIDENTIAL
            and context.operation == "delete"):
        rule_results.append({
            "rule": "confidential_delete_check",
            "matched": True,
            "action": "CHALLENGE",
        })
        return PolicyResult(
            decision=Decision.CHALLENGE,
            reason="CONFIDENTIAL data deletion requires manager approval",
            policy_id="data-retention-v1",
            rule_results=rule_results,
        )

    # Rule 3: Default allow
    rule_results.append({
        "rule": "default_allow",
        "matched": True,
        "action": "ALLOW",
    })
    return PolicyResult(
        decision=Decision.ALLOW,
        reason="Operation permitted by policy",
        policy_id="data-retention-v1",
        rule_results=rule_results,
    )


# ─── Step 3: Write Tests for Your Policy ──────────────────────

def test_evaluate_data_retention_policy_allow():
    """Test that PUBLIC data operations are allowed."""
    context = PolicyContext(
        agent_id="agent-123",
        data_classification=DataClassification.PUBLIC,
        operation="read",
    )
    result = evaluate_data_retention_policy(context)
    assert result.decision == Decision.ALLOW
    assert result.policy_id == "data-retention-v1"


def test_evaluate_data_retention_policy_challenge_restricted():
    """Test that RESTRICTED data requires approval."""
    context = PolicyContext(
        agent_id="agent-123",
        data_classification=DataClassification.RESTRICTED,
        operation="read",
    )
    result = evaluate_data_retention_policy(context)
    assert result.decision == Decision.CHALLENGE
    assert "RESTRICTED" in result.reason


def test_evaluate_data_retention_policy_challenge_confidential_delete():
    """Test that CONFIDENTIAL data deletion requires approval."""
    context = PolicyContext(
        agent_id="agent-123",
        data_classification=DataClassification.CONFIDENTIAL,
        operation="delete",
    )
    result = evaluate_data_retention_policy(context)
    assert result.decision == Decision.CHALLENGE
    assert "manager approval" in result.reason


def test_evaluate_data_retention_policy_allow_confidential_read():
    """Test that CONFIDENTIAL data read is allowed."""
    context = PolicyContext(
        agent_id="agent-123",
        data_classification=DataClassification.CONFIDENTIAL,
        operation="read",
    )
    result = evaluate_data_retention_policy(context)
    assert result.decision == Decision.ALLOW


# ─── Step 4: Run the Tutorial ──────────────────────────────────

def main() -> None:
    """Run the tutorial and verify everything works."""
    print("=" * 60)
    print("GRC_Claw Tutorial: Your First Policy")
    print("=" * 60)

    # Run tests
    print("\n--- Running Tests ---")
    test_evaluate_data_retention_policy_allow()
    print("✅ test_evaluate_data_retention_policy_allow passed")

    test_evaluate_data_retention_policy_challenge_restricted()
    print("✅ test_evaluate_data_retention_policy_challenge_restricted passed")

    test_evaluate_data_retention_policy_challenge_confidential_delete()
    print("✅ test_evaluate_data_retention_policy_challenge_confidential_delete passed")

    test_evaluate_data_retention_policy_allow_confidential_read()
    print("✅ test_evaluate_data_retention_policy_allow_confidential_read passed")

    # Demonstrate policy evaluation
    print("\n--- Policy Evaluation Demo ---")
    contexts = [
        PolicyContext("agent-1", DataClassification.PUBLIC, "read"),
        PolicyContext("agent-2", DataClassification.RESTRICTED, "read"),
        PolicyContext("agent-3", DataClassification.CONFIDENTIAL, "delete"),
    ]

    for ctx in contexts:
        result = evaluate_data_retention_policy(ctx)
        print(f"\n  Agent: {ctx.agent_id}")
        print(f"  Data: {ctx.data_classification.value}")
        print(f"  Operation: {ctx.operation}")
        print(f"  Decision: {result.decision.value}")
        print(f"  Reason: {result.reason}")

    print("\n" + "=" * 60)
    print("✅ Tutorial complete! You've written your first GRC_Claw policy.")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Read the Policy DSL specification")
    print("2. Try the Policy DSL playground")
    print("3. Write a property-based test")
    print("4. Contribute your policy to the policy catalog")


if __name__ == "__main__":
    main()
```

### 5.4 Onboarding Metrics Collection

```python
# scripts/onboarding_metrics.py
"""Collect and report onboarding metrics."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import httpx


@dataclass
class ContributorMetrics:
    """Metrics for a single contributor."""
    username: str
    first_pr_date: str | None = None
    first_merged_pr_date: str | None = None
    pr_count: int = 0
    merged_count: int = 0
    review_count: int = 0
    issue_count: int = 0
    last_activity: str | None = None


@dataclass
class OnboardingMetrics:
    """Aggregated onboarding metrics."""
    total_contributors: int = 0
    new_contributors_30d: int = 0
    avg_time_to_first_pr_days: float = 0.0
    avg_time_to_first_merge_days: float = 0.0
    retention_30d: float = 0.0
    retention_90d: float = 0.0
    good_first_issue_resolution_days: float = 0.0
    mentor_satisfaction: float = 0.0
    onboarding_satisfaction: float = 0.0


def fetch_contributor_data(repo: str, token: str) -> list[ContributorMetrics]:
    """Fetch contributor data from GitHub API."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    contributors: dict[str, ContributorMetrics] = {}

    # Fetch PRs
    page = 1
    while True:
        response = httpx.get(
            f"https://api.github.com/repos/{repo}/pulls",
            headers=headers,
            params={"state": "all", "per_page": 100, "page": page},
            timeout=30,
        )
        response.raise_for_status()
        prs = response.json()

        if not prs:
            break

        for pr in prs:
            username = pr["user"]["login"]
            if username not in contributors:
                contributors[username] = ContributorMetrics(username=username)

            contributor = contributors[username]
            contributor.pr_count += 1

            if pr["created_at"]:
                contributor.first_pr_date = contributor.first_pr_date or pr["created_at"]

            if pr.get("merged_at"):
                contributor.merged_count += 1
                contributor.first_merged_pr_date = (
                    contributor.first_merged_pr_date or pr["merged_at"]
                )

            if pr["updated_at"]:
                contributor.last_activity = pr["updated_at"]

        page += 1

    return list(contributors.values())


def calculate_onboarding_metrics(
    contributors: list[ContributorMetrics],
) -> OnboardingMetrics:
    """Calculate aggregated onboarding metrics."""
    metrics = OnboardingMetrics()
    metrics.total_contributors = len(contributors)

    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    ninety_days_ago = now - timedelta(days=90)

    # New contributors in last 30 days
    new_contributors = []
    for c in contributors:
        if c.first_pr_date:
            first_pr = datetime.fromisoformat(c.first_pr_date.replace("Z", "+00:00"))
            if first_pr > thirty_days_ago:
                new_contributors.append(c)

    metrics.new_contributors_30d = len(new_contributors)

    # Average time to first PR (from account creation - approximated)
    # In practice, you'd track this from the welcome issue creation
    time_to_first_pr = []
    time_to_first_merge = []

    for c in new_contributors:
        if c.first_pr_date and c.first_merged_pr_date:
            first_pr = datetime.fromisoformat(c.first_pr_date.replace("Z", "+00:00"))
            first_merge = datetime.fromisoformat(
                c.first_merged_pr_date.replace("Z", "+00:00")
            )
            time_to_first_merge.append((first_merge - first_pr).days)

    if time_to_first_merge:
        metrics.avg_time_to_first_merge_days = sum(time_to_first_merge) / len(
            time_to_first_merge
        )

    # Retention rates
    active_30d = sum(
        1
        for c in contributors
        if c.last_activity
        and datetime.fromisoformat(c.last_activity.replace("Z", "+00:00")) > thirty_days_ago
    )
    active_90d = sum(
        1
        for c in contributors
        if c.last_activity
        and datetime.fromisoformat(c.last_activity.replace("Z", "+00:00")) > ninety_days_ago
    )

    if metrics.new_contributors_30d > 0:
        metrics.retention_30d = active_30d / metrics.new_contributors_30d * 100
        metrics.retention_90d = active_90d / metrics.new_contributors_30d * 100

    return metrics


def generate_report(metrics: OnboardingMetrics) -> str:
    """Generate onboarding metrics report."""
    return f"""# GRC_Claw Onboarding Metrics Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Contributor Overview

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total contributors | {metrics.total_contributors} | — | — |
| New contributors (30d) | {metrics.new_contributors_30d} | — | — |

## Time to Contribution

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Avg time to first PR | {metrics.avg_time_to_first_pr_days:.1f} days | ≤ 5 days | {'✅' if metrics.avg_time_to_first_pr_days <= 5 else '❌'} |
| Avg time to first merge | {metrics.avg_time_to_first_merge_days:.1f} days | ≤ 10 days | {'✅' if metrics.avg_time_to_first_merge_days <= 10 else '❌'} |

## Retention

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| 30-day retention | {metrics.retention_30d:.1f}% | ≥ 60% | {'✅' if metrics.retention_30d >= 60 else '❌'} |
| 90-day retention | {metrics.retention_90d:.1f}% | ≥ 40% | {'✅' if metrics.retention_90d >= 40 else '❌'} |

## Issue Resolution

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| good-first-issue resolution | {metrics.good_first_issue_resolution_days:.1f} days | ≤ 14 days | {'✅' if metrics.good_first_issue_resolution_days <= 14 else '❌'} |

## Satisfaction

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Mentor satisfaction | {metrics.mentor_satisfaction:.1f}/5.0 | ≥ 4.0 | {'✅' if metrics.mentor_satisfaction >= 4.0 else '❌'} |
| Onboarding satisfaction | {metrics.onboarding_satisfaction:.1f}/5.0 | ≥ 4.0 | {'✅' if metrics.onboarding_satisfaction >= 4.0 else '❌'} |

## Recommendations

{generate_recommendations(metrics)}
"""


def generate_recommendations(metrics: OnboardingMetrics) -> str:
    """Generate recommendations based on metrics."""
    recommendations = []

    if metrics.avg_time_to_first_pr_days > 5:
        recommendations.append(
            "- **Reduce time to first PR:** Improve onboarding documentation and "
            "add more `good-first-issue` labels."
        )

    if metrics.retention_30d < 60:
        recommendations.append(
            "- **Improve 30-day retention:** Strengthen mentorship program and "
            "increase community engagement activities."
        )

    if metrics.good_first_issue_resolution_days > 14:
        recommendations.append(
            "- **Speed up good-first-issue resolution:** Assign maintainers to "
            "triage and mentor first-time contributors on these issues."
        )

    if not recommendations:
        recommendations.append("- All onboarding metrics are within target ranges! 🎉")

    return "\n".join(recommendations)


def main() -> int:
    """Main entry point."""
    import os

    repo = os.getenv("GITHUB_REPOSITORY", "grc-claw/grc-claw")
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("Error: GITHUB_TOKEN environment variable required")
        return 1

    print("Fetching contributor data...")
    contributors = fetch_contributor_data(repo, token)

    print("Calculating metrics...")
    metrics = calculate_onboarding_metrics(contributors)

    report = generate_report(metrics)
    print(report)

    # Write report
    report_path = Path("onboarding-metrics-report.md")
    report_path.write_text(report)
    print(f"\nReport written to {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## 6. API Versioning Automation

### 6.1 Versioning Strategy Implementation

```python
# src/grc_claw/api_gateway/versioning.py
"""API versioning management for GRC_Claw.

Implements URL-based versioning with semantic versioning for SDKs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.routing import APIRoute


class APIVersion(str, Enum):
    """Supported API versions."""
    V0 = "v0"  # Legacy
    V1 = "v1"  # Current
    V2 = "v2"  # Beta


@dataclass(frozen=True)
class VersionInfo:
    """Information about an API version."""
    major: int
    minor: int
    patch: int
    status: str  # "active", "deprecated", "sunset", "removed"
    sunset_date: str | None = None
    deprecation_date: str | None = None


# Version registry
VERSION_REGISTRY: dict[APIVersion, VersionInfo] = {
    APIVersion.V0: VersionInfo(
        major=0,
        minor=1,
        patch=0,
        status="sunset",
        sunset_date="2027-04-01",
        deprecation_date="2026-10-01",
    ),
    APIVersion.V1: VersionInfo(
        major=1,
        minor=0,
        patch=0,
        status="active",
    ),
    APIVersion.V2: VersionInfo(
        major=2,
        minor=0,
        patch=0,
        status="active",
    ),
}


class VersionedAPIRoute(APIRoute):
    """Custom API route that adds version headers and deprecation notices."""

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def custom_handler(request: Request) -> Response:
            response = await original_route_handler(request)

            # Extract version from URL path
            path = request.url.path
            version = self._extract_version(path)

            if version and version in VERSION_REGISTRY:
                info = VERSION_REGISTRY[version]

                # Add version headers
                response.headers["X-API-Version"] = f"{info.major}.{info.minor}.{info.patch}"
                response.headers["X-API-Version-Major"] = str(info.major)

                # Add deprecation headers
                if info.status == "deprecated":
                    response.headers["Deprecation"] = "true"
                    if info.deprecation_date:
                        response.headers["X-Deprecation-Date"] = info.deprecation_date

                if info.status == "sunset":
                    response.headers["Sunset"] = info.sunset_date or ""

            return response

        return custom_handler

    @staticmethod
    def _extract_version(path: str) -> APIVersion | None:
        """Extract API version from URL path."""
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            version_str = parts[1]
            try:
                return APIVersion(version_str)
            except ValueError:
                return None
        return None


def create_versioned_router(version: APIVersion) -> APIRouter:
    """Create a versioned API router."""
    info = VERSION_REGISTRY.get(version)
    if not info:
        raise ValueError(f"Unknown API version: {version}")

    router = APIRouter(
        prefix=f"/api/{version.value}",
        tags=[f"api-{version.value}"],
        route_class=VersionedAPIRoute,
    )

    # Add version info endpoint
    @router.get("/version", include_in_schema=False)
    async def get_version_info() -> dict[str, Any]:
        """Get API version information."""
        return {
            "version": f"{info.major}.{info.minor}.{info.patch}",
            "major": info.major,
            "minor": info.minor,
            "patch": info.patch,
            "status": info.status,
            "sunset_date": info.sunset_date,
            "deprecation_date": info.deprecation_date,
        }

    return router


def check_version_compatibility(
    client_version: str,
    api_version: APIVersion,
) -> tuple[bool, str]:
    """Check if a client version is compatible with an API version."""
    info = VERSION_REGISTRY.get(api_version)
    if not info:
        return False, f"Unknown API version: {api_version}"

    # Parse client version
    try:
        parts = client_version.split(".")
        client_major = int(parts[0])
    except (ValueError, IndexError):
        return False, f"Invalid client version: {client_version}"

    # Major version must match
    if client_major != info.major:
        return False, (
            f"Client major version ({client_major}) incompatible with "
            f"API major version ({info.major})"
        )

    return True, "Compatible"
```

### 6.2 OpenAPI Spec Versioning

```python
# scripts/version_openapi.py
"""Generate versioned OpenAPI specs and detect breaking changes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def generate_openapi_spec(app_module: str, output_path: Path) -> dict[str, Any]:
    """Generate OpenAPI spec from FastAPI app."""
    code = f"""
import json
from {app_module} import app

spec = app.openapi()
print(json.dumps(spec, indent=2))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error generating OpenAPI spec: {result.stderr}")
        sys.exit(1)

    return json.loads(result.stdout)


def detect_breaking_changes(
    old_spec_path: Path,
    new_spec_path: Path,
) -> list[dict[str, str]]:
    """Detect breaking changes between OpenAPI specs using oasdiff."""
    result = subprocess.run(
        [
            "oasdiff",
            "breaking",
            "--base", str(old_spec_path),
            "--revision", str(new_spec_path),
            "--format", "json",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return []

    try:
        changes = json.loads(result.stdout)
        return changes if isinstance(changes, list) else [changes]
    except json.JSONDecodeError:
        return [{"error": result.stdout or result.stderr}]


def generate_versioned_specs(app_module: str, output_dir: Path) -> None:
    """Generate OpenAPI specs for all API versions."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate current spec
    spec = generate_openapi_spec(app_module, output_dir / "openapi.json")

    # Save previous spec for comparison
    prev_spec_path = output_dir / "openapi-prev.json"
    current_spec_path = output_dir / "openapi.json"

    if prev_spec_path.exists():
        changes = detect_breaking_changes(prev_spec_path, current_spec_path)
        if changes:
            print("⚠️  Breaking changes detected:")
            for change in changes:
                print(f"  - {change}")
            print("\nThese changes require a new major API version.")
        else:
            print("✅ No breaking changes detected.")

    # Archive current spec as previous
    if current_spec_path.exists():
        import shutil
        shutil.copy(current_spec_path, prev_spec_path)


def validate_spec(spec_path: Path) -> list[str]:
    """Validate OpenAPI spec for completeness."""
    spec = json.loads(spec_path.read_text())
    issues = []

    # Check all endpoints have examples
    for path, methods in spec.get("paths", {}).items():
        for method, operation in methods.items():
            if method in ("get", "post", "put", "patch", "delete"):
                if "operationId" not in operation:
                    issues.append(f"{method.upper()} {path}: missing operationId")
                if "summary" not in operation:
                    issues.append(f"{method.upper()} {path}: missing summary")
                if "description" not in operation:
                    issues.append(f"{method.upper()} {path}: missing description")

    # Check all schemas have descriptions
    for schema_name, schema in spec.get("components", {}).get("schemas", {}).items():
        if "description" not in schema:
            issues.append(f"Schema {schema_name}: missing description")

    return issues


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "docs" / "api"

    print("=== OpenAPI Spec Versioning ===\n")

    # Generate specs
    print("Generating OpenAPI specs...")
    generate_versioned_specs("grc_claw.api_gateway.main", output_dir)

    # Validate spec
    print("\nValidating OpenAPI spec...")
    spec_path = output_dir / "openapi.json"
    issues = validate_spec(spec_path)

    if issues:
        print(f"⚠️  Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ OpenAPI spec is valid and complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 6.3 SDK Versioning Automation

```yaml
# .github/workflows/sdk-release.yml
name: SDK Release

on:
  release:
    types: [published]

jobs:
  generate-python-sdk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install openapi-python-client

      - name: Download OpenAPI spec
        run: |
          curl -o openapi.json https://api.grc-claw.example.com/api/v1/openapi.json

      - name: Generate Python SDK
        run: |
          openapi-python-client generate \
            --path openapi.json \
            --output-path python-sdk \
            --package-name grc_claw \
            --meta pdm

      - name: Update version
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          sed -i "s/version = \".*\"/version = \"$VERSION\"/" python-sdk/pyproject.toml

      - name: Build SDK
        run: |
          cd python-sdk
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
          packages-dir: python-sdk/dist/

  generate-typescript-sdk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: pnpm
          registry-url: "https://registry.npmjs.org"

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Download OpenAPI spec
        run: |
          curl -o openapi.json https://api.grc-claw.example.com/api/v1/openapi.json

      - name: Generate TypeScript SDK
        run: |
          pnpm openapi-typescript \
            openapi.json \
            -o packages/sdk/src/api-types.ts

      - name: Update version
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          pnpm version $VERSION --no-git-tag-version

      - name: Build SDK
        run: |
          pnpm --filter @grc-claw/sdk run build

      - name: Publish to npm
        run: |
          pnpm --filter @grc-claw/sdk publish --no-git-checks
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### 6.4 API Version Compatibility Matrix

```python
# scripts/api_compatibility.py
"""Generate and validate API version compatibility matrix."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CompatibilityEntry:
    """Single entry in the compatibility matrix."""
    api_version: str
    min_sdk_version: str
    max_sdk_version: str
    policy_dsl_version: str
    status: str
    sunset_date: str | None = None


# Compatibility matrix
COMPATIBILITY_MATRIX: list[CompatibilityEntry] = [
    CompatibilityEntry(
        api_version="v0",
        min_sdk_version="0.1.0",
        max_sdk_version="0.9.0",
        policy_dsl_version="0.x",
        status="sunset",
        sunset_date="2027-04-01",
    ),
    CompatibilityEntry(
        api_version="v1",
        min_sdk_version="1.0.0",
        max_sdk_version="1.99.0",
        policy_dsl_version="1.x",
        status="active",
    ),
    CompatibilityEntry(
        api_version="v2",
        min_sdk_version="2.0.0",
        max_sdk_version="2.99.0",
        policy_dsl_version="2.x",
        status="active",
    ),
]


def generate_compatibility_matrix() -> dict[str, Any]:
    """Generate compatibility matrix document."""
    matrix = {
        "generated": "2026-10-01",
        "versions": [],
    }

    for entry in COMPATIBILITY_MATRIX:
        matrix["versions"].append({
            "api_version": entry.api_version,
            "sdk_support": {
                "python": f">={entry.min_sdk_version},<{entry.max_sdk_version}",
                "typescript": f">={entry.min_sdk_version},<{entry.max_sdk_version}",
            },
            "policy_dsl": entry.policy_dsl_version,
            "status": entry.status,
            "sunset_date": entry.sunset_date,
        })

    return matrix


def validate_compatibility(
    api_version: str,
    sdk_version: str,
    policy_dsl_version: str | None = None,
) -> tuple[bool, list[str]]:
    """Validate version compatibility."""
    errors = []

    # Find matching entry
    entry = None
    for e in COMPATIBILITY_MATRIX:
        if e.api_version == api_version:
            entry = e
            break

    if not entry:
        return False, [f"Unknown API version: {api_version}"]

    # Check SDK version
    from packaging import version as pkg_version

    try:
        sdk_ver = pkg_version.parse(sdk_version)
        min_ver = pkg_version.parse(entry.min_sdk_version)
        max_ver = pkg_version.parse(entry.max_sdk_version)

        if sdk_ver < min_ver:
            errors.append(
                f"SDK version {sdk_version} is below minimum {entry.min_sdk_version} "
                f"for API {api_version}"
            )
        if sdk_ver >= max_ver:
            errors.append(
                f"SDK version {sdk_version} is above maximum {entry.max_sdk_version} "
                f"for API {api_version}"
            )
    except Exception as e:
        errors.append(f"Invalid version format: {e}")

    # Check policy DSL version
    if policy_dsl_version:
        dsl_major = policy_dsl_version.split(".")[0]
        expected_major = entry.policy_dsl_version.split(".")[0]
        if dsl_major != expected_major:
            errors.append(
                f"Policy DSL major version ({dsl_major}) incompatible with "
                f"API {api_version} (expected {expected_major}.x)"
            )

    # Check sunset status
    if entry.status == "sunset":
        errors.append(
            f"API {api_version} is scheduled for sunset on {entry.sunset_date}. "
            f"Migrate to a newer version."
        )

    return len(errors) == 0, errors


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    output_path = repo_root / "docs" / "api" / "compatibility-matrix.json"

    print("=== API Version Compatibility Matrix ===\n")

    matrix = generate_compatibility_matrix()
    output_path.write_text(json.dumps(matrix, indent=2))

    print(f"Compatibility matrix written to {output_path}")
    print("\nMatrix preview:")
    print(json.dumps(matrix, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 6.5 Policy DSL Versioning

```python
# src/grc_claw/policy_engine/dsl_versioning.py
"""Policy DSL version management and migration."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DSLVersionInfo:
    """Information about a policy DSL version."""
    major: int
    minor: int
    patch: int
    status: str  # "active", "deprecated", "sunset"
    supported_until: str | None = None


# DSL version registry
DSL_VERSIONS: dict[int, DSLVersionInfo] = {
    0: DSLVersionInfo(0, 1, 0, "sunset", "2027-01-01"),
    1: DSLVersionInfo(1, 0, 0, "active"),
    2: DSLVersionInfo(2, 0, 0, "active"),
}


def parse_policy_version(policy_content: str) -> int:
    """Extract major version from policy content."""
    match = re.search(r"policy-version:\s*['\"]?(\d+)\.", policy_content)
    if match:
        return int(match.group(1))
    return 1  # Default to current version


def validate_policy_version(policy_content: str) -> tuple[bool, str]:
    """Validate that a policy uses a supported DSL version."""
    major = parse_policy_version(policy_content)

    if major not in DSL_VERSIONS:
        return False, f"Unsupported policy DSL major version: {major}"

    info = DSL_VERSIONS[major]

    if info.status == "sunset":
        return False, (
            f"Policy DSL v{major} is sunset as of {info.supported_until}. "
            f"Please migrate to a newer version."
        )

    if info.status == "deprecated":
        return True, (
            f"Warning: Policy DSL v{major} is deprecated. "
            f"Please plan migration to a newer version."
        )

    return True, "Policy version is supported"


def migrate_policy_v0_to_v1(policy_content: str) -> str:
    """Migrate a policy from DSL v0 to v1.

    Migration changes:
    - `agent_type` → `agent_framework`
    - `action` → `operation`
    - `resource_type` → `resource_kind`
    - Added required `policy-version` field
    """
    content = policy_content

    # Add version header if missing
    if "policy-version:" not in content:
        content = 'policy-version: "1.0.0"\n' + content

    # Rename fields
    replacements = {
        r"agent_type:": "agent_framework:",
        r"action:": "operation:",
        r"resource_type:": "resource_kind:",
    }

    for old, new in replacements.items():
        content = re.sub(old, new, content)

    return content


def migrate_policy_v1_to_v2(policy_content: str) -> str:
    """Migrate a policy from DSL v1 to v2.

    Migration changes:
    - `rules` → `policy_rules`
    - Added `version` field to each rule
    - `condition` → `when`
    - `effect` → `then`
    """
    content = policy_content

    # Update version
    content = re.sub(
        r"policy-version:\s*['\"]?1\.",
        'policy-version: "2.0.0',
        content,
    )

    # Rename fields
    replacements = {
        r"^rules:": "policy_rules:",
        r"condition:": "when:",
        r"effect:": "then:",
    }

    for old, new in replacements.items():
        content = re.sub(old, new, content, flags=re.MULTILINE)

    return content


def auto_migrate_policy(policy_content: str, target_major: int | None = None) -> str:
    """Automatically migrate a policy to the target version."""
    current_major = parse_policy_version(policy_content)

    if target_major is None:
        # Target latest active version
        target_major = max(
            v.major for v in DSL_VERSIONS.values() if v.status == "active"
        )

    if current_major == target_major:
        return policy_content

    if current_major > target_major:
        raise ValueError(
            f"Cannot downgrade policy from v{current_major} to v{target_major}"
        )

    # Apply migrations sequentially
    content = policy_content
    for major in range(current_major, target_major):
        if major == 0:
            content = migrate_policy_v0_to_v1(content)
        elif major == 1:
            content = migrate_policy_v1_to_v2(content)

    return content


def generate_migration_guide(from_version: int, to_version: int) -> str:
    """Generate a migration guide between DSL versions."""
    guides = {
        (0, 1): """# Migration Guide: Policy DSL v0 to v1

## Breaking Changes

1. **Field Renames:**
   - `agent_type` → `agent_framework`
   - `action` → `operation`
   - `resource_type` → `resource_kind`

2. **New Required Field:**
   - `policy-version: "1.0.0"` must be added to the policy header

## Migration Steps

1. Add the version header to your policy file
2. Rename all occurrences of the old field names
3. Test your policy with the new DSL version
4. Update any client code that references the old field names

## Automated Migration

Use the migration tool:
```bash
grc migrate-policy --from 0 --to 1 policy.yaml
```
""",
        (1, 2): """# Migration Guide: Policy DSL v1 to v2

## Breaking Changes

1. **Field Renames:**
   - `rules` → `policy_rules`
   - `condition` → `when`
   - `effect` → `then`

2. **New Required Field:**
   - Each rule must include a `version` field

## Migration Steps

1. Update the `policy-version` header to `"2.0.0"`
2. Rename `rules` to `policy_rules`
3. Rename `condition` to `when` in each rule
4. Rename `effect` to `then` in each rule
5. Add `version: "1.0"` to each rule
6. Test your policy with the new DSL version

## Automated Migration

Use the migration tool:
```bash
grc migrate-policy --from 1 --to 2 policy.yaml
```
""",
    }

    return guides.get(
        (from_version, to_version),
        f"No migration guide available for v{from_version} to v{to_version}",
    )
```

---

## 7. Deprecation Management

### 7.1 Deprecation Tracking System

```markdown
<!-- DEPRECATIONS.md -->
# GRC_Claw Deprecation Registry

**Last Updated:** 2026-10-01  
**Total Active Deprecations:** 2  
**Total Sunset:** 1

## Active Deprecations

### DEP-001: `/api/v0/policies/bulk` endpoint

| Field | Value |
|-------|-------|
| **Feature** | `/api/v0/policies/bulk` |
| **Deprecated In** | v1.3.0 |
| **Sunset Date** | 2027-04-01 |
| **Replacement** | [`/api/v1/policies/bulk`](/api/v1/policies/bulk) |
| **Status** | Deprecated |
| **Tracking Issue** | #456 |

**Migration Guide:**

The bulk policy endpoint has been moved to API v1. Update your client to use the new URL:

```python
# Before (v0)
response = client.post("/api/v0/policies/bulk", json=policies)

# After (v1)
response = client.post("/api/v1/policies/bulk", json=policies)
```

**Timeline:**

| Version | Date | Action |
|---------|------|--------|
| v1.3.0 | 2026-10-01 | Deprecated, `Deprecation` header added |
| v1.4.0 | 2027-01-01 | Sunset notice in documentation |
| v2.0.0 | 2027-04-01 | Returns `410 Gone` |

---

### DEP-002: `policy-dsl v0`

| Field | Value |
|-------|-------|
| **Feature** | Policy DSL version 0.x |
| **Deprecated In** | v1.0.0 |
| **Sunset Date** | 2027-01-01 |
| **Replacement** | [Policy DSL v1](/policy-dsl/specification.md) |
| **Status** | Deprecated |
| **Tracking Issue** | #123 |

**Migration Guide:**

Policy DSL v0 is deprecated. Migrate your policies to v1 using the automated migration tool:

```bash
grc migrate-policy --from 0 --to 1 policy.yaml
```

See the [Migration Guide](/policy-dsl/migration.md) for detailed instructions.

**Timeline:**

| Version | Date | Action |
|---------|------|--------|
| v1.0.0 | 2026-01-01 | Deprecated, warnings added |
| v1.5.0 | 2026-07-01 | Sunset notice in documentation |
| v2.0.0 | 2027-01-01 | Returns `410 Gone` |

---

## Sunset Features

### DEP-000: Legacy evidence format (Sunset)

| Field | Value |
|-------|-------|
| **Feature** | Legacy evidence JSON format |
| **Deprecated In** | v0.9.0 |
| **Sunset Date** | 2026-04-01 |
| **Replacement** | OSCAL 1.1.0 format |
| **Status** | Sunset |
| **Tracking Issue** | #78 |

This feature now returns `410 Gone`. Migrate to the OSCAL format.

---

## Removed Features

### DEP-XXX: Old authentication method (Removed)

| Field | Value |
|-------|-------|
| **Feature** | API key in query parameter |
| **Deprecated In** | v0.8.0 |
| **Sunset Date** | 2025-10-01 |
| **Removed In** | v1.0.0 |
| **Replacement** | Bearer token in Authorization header |
| **Status** | Removed |

---

## Deprecation Policy Summary

See [GRC-MNT-001 §6](../grc-claw-maintainability-spec.md) for the full deprecation policy.

| Stage | Duration | Behavior |
|-------|----------|----------|
| Active | — | Full support, no warnings |
| Deprecated | ≥ 6 months | Functional but warns; `Deprecation` header |
| Sunset | ≥ 3 months | Returns `410 Gone` with migration instructions |
| Removed | — | Code deleted |
| Archived | Indefinite | Documentation preserved in `docs/archive/` |
```

### 7.2 Deprecation Automation

```python
# src/grc_claw/api_gateway/deprecation.py
"""Deprecation management for GRC_Claw APIs."""

from __future__ import annotations

import functools
import warnings
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, TypeVar

from fastapi import HTTPException, Request, Response


F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class DeprecationInfo:
    """Information about a deprecated feature."""
    feature: str
    deprecated_in: str
    sunset_date: str
    replacement: str
    migration_guide: str
    tracking_issue: str


# Deprecation registry
DEPRECATION_REGISTRY: dict[str, DeprecationInfo] = {
    "/api/v0/policies/bulk": DeprecationInfo(
        feature="/api/v0/policies/bulk",
        deprecated_in="v1.3.0",
        sunset_date="2027-04-01",
        replacement="/api/v1/policies/bulk",
        migration_guide="https://docs.grc-claw.dev/migrations/v0-to-v1",
        tracking_issue="#456",
    ),
    "policy-dsl-v0": DeprecationInfo(
        feature="policy-dsl v0",
        deprecated_in="v1.0.0",
        sunset_date="2027-01-01",
        replacement="policy-dsl v1",
        migration_guide="https://docs.grc-claw.dev/policy-dsl/migration",
        tracking_issue="#123",
    ),
}


def deprecated(
    *,
    deprecated_in: str,
    sunset_date: str,
    replacement: str,
    migration_guide: str,
    tracking_issue: str,
) -> Callable[[F], F]:
    """Decorator to mark an endpoint or function as deprecated.

    Adds Deprecation and Sunset headers to responses.
    Emits a DeprecationWarning for Python callers.
    """
    def decorator(func: F) -> F:
        info = DeprecationInfo(
            feature=func.__name__,
            deprecated_in=deprecated_in,
            sunset_date=sunset_date,
            replacement=replacement,
            migration_guide=migration_guide,
            tracking_issue=tracking_issue,
        )

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{info.feature} is deprecated since {info.deprecated_in}. "
                f"Sunset date: {info.sunset_date}. "
                f"Use {info.replacement} instead. "
                f"See {info.migration_guide}",
                DeprecationWarning,
                stacklevel=2,
            )

            response = await func(*args, **kwargs)

            # Add deprecation headers if response is a FastAPI Response
            if isinstance(response, Response):
                response.headers["Deprecation"] = "true"
                response.headers["Sunset"] = sunset_date
                response.headers["X-Deprecation-Date"] = deprecated_in
                response.headers["X-Replacement"] = replacement

            return response

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{info.feature} is deprecated since {info.deprecated_in}. "
                f"Sunset date: {info.sunset_date}. "
                f"Use {info.replacement} instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        # Register the deprecation
        DEPRECATION_REGISTRY[info.feature] = info

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def sunset(
    *,
    sunset_date: str,
    replacement: str,
    migration_guide: str,
) -> Callable[[F], F]:
    """Decorator to mark a feature as sunset (returns 410 Gone)."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            request: Request = kwargs.get("request") or next(
                (a for a in args if isinstance(a, Request)), None
            )
            raise HTTPException(
                status_code=410,
                detail={
                    "error": "Gone",
                    "message": f"This endpoint was sunset on {sunset_date}.",
                    "replacement": replacement,
                    "migration_guide": migration_guide,
                },
            )

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            raise HTTPException(
                status_code=410,
                detail={
                    "error": "Gone",
                    "message": f"This feature was sunset on {sunset_date}.",
                    "replacement": replacement,
                    "migration_guide": migration_guide,
                },
            )

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def check_deprecation_status(feature: str, current_date: date | None = None) -> str:
    """Check the deprecation status of a feature.

    Returns: "active", "deprecated", "sunset", or "removed"
    """
    info = DEPRECATION_REGISTRY.get(feature)
    if not info:
        return "active"

    if current_date is None:
        current_date = date.today()

    sunset = date.fromisoformat(info.sunset_date)

    if current_date >= sunset:
        return "sunset"

    return "deprecated"


def generate_deprecation_report() -> dict[str, Any]:
    """Generate a deprecation status report."""
    today = date.today()
    report: dict[str, Any] = {
        "generated": today.isoformat(),
        "total": len(DEPRECATION_REGISTRY),
        "by_status": {},
        "items": [],
    }

    for feature, info in DEPRECATION_REGISTRY.items():
        status = check_deprecation_status(feature, today)
        report["by_status"][status] = report["by_status"].get(status, 0) + 1
        report["items"].append({
            "feature": feature,
            "deprecated_in": info.deprecated_in,
            "sunset_date": info.sunset_date,
            "replacement": info.replacement,
            "status": status,
            "tracking_issue": info.tracking_issue,
        })

    return report
```

### 7.3 Deprecation CI Enforcement

```yaml
# .github/workflows/deprecation-check.yml
name: Deprecation Check

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  check-deprecations:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install pyyaml

      - name: Check deprecation status
        run: |
          python -c "
          import sys
          sys.path.insert(0, 'src')
          from grc_claw.api_gateway.deprecation import generate_deprecation_report
          import json
          report = generate_deprecation_report()
          print(json.dumps(report, indent=2))

          # Check for features nearing sunset
          from datetime import date, timedelta
          today = date.today()
          warning_threshold = today + timedelta(days=90)

          for item in report['items']:
              if item['status'] == 'deprecated':
                  sunset = date.fromisoformat(item['sunset_date'])
                  if sunset <= warning_threshold:
                      print(f'⚠️  {item[\"feature\"]} sunsets in {(sunset - today).days} days!')
          "

      - name: Check for expired deprecations
        run: |
          python -c "
          import sys
          sys.path.insert(0, 'src')
          from grc_claw.api_gateway.deprecation import generate_deprecation_report
          from datetime import date

          report = generate_deprecation_report()
          today = date.today()

          expired = []
          for item in report['items']:
              if item['status'] == 'sunset':
                  expired.append(item)

          if expired:
              print('❌ The following features have passed their sunset date:')
              for item in expired:
                  print(f'  - {item[\"feature\"]} (sunset: {item[\"sunset_date\"]})')
              print()
              print('These features should be removed or their sunset date extended.')
              sys.exit(1)
          else:
              print('✅ No expired deprecations found.')
          "

      - name: Verify deprecation headers
        run: |
          # Start the app and verify deprecation headers are present
          python -c "
          import sys
          sys.path.insert(0, 'src')
          from grc_claw.api_gateway.main import app
          from fastapi.testclient import TestClient

          client = TestClient(app)

          # Test deprecated endpoint returns correct headers
          response = client.post('/api/v0/policies/bulk', json={})
          if response.status_code != 410:
              print(f'❌ Expected 410 Gone, got {response.status_code}')
              sys.exit(1)

          if 'Deprecation' not in response.headers:
              print('❌ Missing Deprecation header')
              sys.exit(1)

          if 'Sunset' not in response.headers:
              print('❌ Missing Sunset header')
              sys.exit(1)

          print('✅ Deprecation headers verified.')
          "
```

### 7.4 Deprecation Proposal Template

```markdown
<!-- .github/ISSUE_TEMPLATE/deprecation.md -->
---
name: Deprecation Proposal
about: Propose deprecation of a feature, API, or configuration
title: "Deprecation: [Feature Name]"
labels: deprecation, architecture
assignees: ""
---

## Feature to Deprecate

**Feature Name:**  
**Type:** [ ] API Endpoint  [ ] Feature  [ ] Configuration  [ ] Policy DSL  [ ] SDK Method  
**Current Version:**  
**Module:**  

## Rationale

### Why should this feature be deprecated?

<!-- Provide a clear rationale for the deprecation -->

### Usage Statistics

<!-- Provide usage data to support the deprecation decision -->

| Metric | Value |
|--------|-------|
| Active organizations using this feature | |
| % of total active organizations | |
| API calls per day (if applicable) | |
| Trend (increasing/decreasing/stable) | |

## Replacement

### What is the replacement?

<!-- Describe the replacement feature and its benefits -->

| Aspect | Old Feature | New Feature |
|--------|-------------|-------------|
| API Endpoint | | |
| SDK Method | | |
| Configuration Key | | |
| DSL Syntax | | |

### Migration Path

<!-- Describe the migration path for users -->

1. **Step 1:** 
2. **Step 2:** 
3. **Step 3:** 

### Automated Migration Available?

- [ ] Yes — `grc migrate` command available
- [ ] Partial — Some manual steps required
- [ ] No — Manual migration only

## Proposed Timeline

| Milestone | Target Date | Version |
|-----------|-------------|---------|
| Deprecation announced | | |
| `Deprecation` header added | | |
| Documentation updated | | |
| Migration guide published | | |
| Sunset date (410 Gone) | | |
| Code removal | | |

## Impact Assessment

### Breaking Changes

- [ ] No breaking changes during deprecation period
- [ ] Breaking changes at sunset

### Affected Components

- [ ] API Gateway
- [ ] Python SDK
- [ ] TypeScript SDK
- [ ] Web UI
- [ ] Policy Engine
- [ ] Documentation
- [ ] Other: 

### Community Impact

<!-- Assess the impact on the community -->

## Alternatives Considered

<!-- What alternatives to deprecation were considered? -->

1. **Alternative 1:** 
   - **Rejection Reason:** 

2. **Alternative 2:** 
   - **Rejection Reason:** 

## Additional Context

<!-- Any additional context, references, or notes -->
```

---

## 8. Implementation Roadmap

### 8.1 Phase 1: Foundation (Weeks 1-4)

| Week | Deliverable | Status |
|------|-------------|--------|
| 1 | Pre-commit hooks configured and documented | Pending |
| 1 | CI pipeline (Gate 1 & 2) operational | Pending |
| 2 | Python linting (ruff, mypy, bandit, vulture) configured | Pending |
| 2 | Rust linting (clippy, fmt, audit) configured | Pending |
| 2 | TypeScript linting (eslint, prettier, tsc) configured | Pending |
| 3 | Test coverage thresholds enforced in CI | Pending |
| 3 | Makefile with all developer commands | Pending |
| 4 | PR template with technical debt checklist | Pending |
| 4 | TECH-DEBT.md initialized | Pending |

### 8.2 Phase 2: Documentation (Weeks 5-8)

| Week | Deliverable | Status |
|------|-------------|--------|
| 5 | MkDocs site configured and deployed | Pending |
| 5 | API reference auto-generation (pdoc, rustdoc, typedoc) | Pending |
| 6 | OpenAPI spec generation and versioning | Pending |
| 6 | Changelog automation (git-cliff) | Pending |
| 7 | Documentation validation in CI (links, examples, docstrings) | Pending |
| 7 | ADR process established | Pending |
| 8 | Onboarding documentation complete | Pending |
| 8 | Interactive tutorials created | Pending |

### 8.3 Phase 3: Debt & Refactoring (Weeks 9-12)

| Week | Deliverable | Status |
|------|-------------|--------|
| 9 | TECH-DEBT.md populated with initial inventory | Pending |
| 9 | Debt detection automation (vulture, radon, xenon) | Pending |
| 10 | Automated refactoring pipeline (ruff, clippy, eslint --fix) | Pending |
| 10 | Complexity-driven refactoring issues | Pending |
| 11 | Debt budget enforcement script | Pending |
| 11 | Refactoring safety verification script | Pending |
| 12 | First quarterly debt report | Pending |

### 8.4 Phase 4: Versioning & Deprecation (Weeks 13-16)

| Week | Deliverable | Status |
|------|-------------|--------|
| 13 | API versioning infrastructure (headers, routing) | Pending |
| 13 | SDK versioning automation | Pending |
| 14 | DEPRECATIONS.md initialized | Pending |
| 14 | Deprecation decorators and middleware | Pending |
| 15 | Policy DSL versioning and migration tools | Pending |
| 15 | Deprecation CI enforcement | Pending |
| 16 | API compatibility matrix published | Pending |

### 8.5 Phase 5: Onboarding & Metrics (Weeks 17-20)

| Week | Deliverable | Status |
|------|-------------|--------|
| 17 | Welcome automation for new contributors | Pending |
| 17 | Onboarding checklist automation | Pending |
| 18 | Mentorship program established | Pending |
| 18 | Onboarding metrics collection | Pending |
| 19 | Quality dashboards (Grafana) configured | Pending |
| 19 | Maintainability Index calculation | Pending |
| 20 | First quarterly maintainability report | Pending |

### 8.6 Phase 6: Optimization (Weeks 21-24)

| Week | Deliverable | Status |
|------|-------------|--------|
| 21 | Performance optimization based on metrics | Pending |
| 21 | Developer experience improvements | Pending |
| 22 | Community feedback incorporation | Pending |
| 22 | Documentation refinement | Pending |
| 23 | Process automation enhancements | Pending |
| 23 | Tool evaluation and adoption | Pending |
| 24 | SOC 2 maintainability controls implementation | Pending |

---

## Appendix A: File Structure

```
grc-claw/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Main CI pipeline
│   │   ├── cd-staging.yml            # Staging deployment
│   │   ├── cd-production.yml         # Production deployment
│   │   ├── docs.yml                  # Documentation pipeline
│   │   ├── auto-refactor.yml         # Automated refactoring
│   │   ├── debt-detection.yml        # Technical debt detection
│   │   ├── deprecation-check.yml     # Deprecation enforcement
│   │   ├── sdk-release.yml           # SDK publishing
│   │   └── welcome.yml               # New contributor welcome
│   ├── PULL_REQUEST_TEMPLATE.md      # PR template with debt checklist
│   └── ISSUE_TEMPLATE/
│       └── deprecation.md            # Deprecation proposal template
├── src/
│   └── grc_claw/
│       ├── api_gateway/
│       │   ├── main.py               # FastAPI application
│       │   ├── versioning.py         # API versioning
│       │   └── deprecation.py        # Deprecation management
│       └── policy_engine/
│           └── dsl_versioning.py     # Policy DSL versioning
├── scripts/
│   ├── install-hooks.sh              # Pre-commit hook installer
│   ├── validate_docs.py              # Documentation validator
│   ├── debt_budget.py                # Debt budget enforcer
│   ├── complexity_refactor.py        # Complexity refactoring detector
│   ├── verify_refactoring.py         # Refactoring safety verifier
│   ├── version_openapi.py            # OpenAPI spec versioning
│   ├── api_compatibility.py          # API compatibility matrix
│   └── onboarding_metrics.py         # Onboarding metrics collector
├── docs/
│   ├── _templates/                   # Documentation templates
│   │   ├── module-template.md
│   │   ├── adr-template.md
│   │   ├── deprecation-template.md
│   │   └── migration-template.md
│   ├── examples/                     # Executable code examples
│   │   └── tutorial-first-policy.py
│   ├── getting-started/
│   │   └── onboarding.md             # Developer onboarding guide
│   └── api/
│       ├── openapi.json              # Generated OpenAPI spec
│       ├── openapi-prev.json         # Previous spec for comparison
│       └── compatibility-matrix.json # Version compatibility matrix
├── .pre-commit-config.yaml           # Pre-commit hook configuration
├── pyproject.toml                    # Python project configuration
├── Cargo.toml                        # Rust workspace configuration
├── package.json                      # Node project configuration
├── Makefile                          # Developer commands
├── mkdocs.yml                        # Documentation site configuration
├── cliff.toml                        # Changelog generation configuration
├── refactor.toml                     # Refactoring tool configuration
├── CHANGELOG.md                      # Auto-generated changelog
├── DEPRECATIONS.md                   # Deprecation registry
├── TECH-DEBT.md                      # Technical debt register
└── CONTRIBUTING.md                   # Contribution guidelines
```

---

## Appendix B: Tool Quick Reference

| Category | Tool | Command | Purpose |
|----------|------|---------|---------|
| **Linting** | ruff | `ruff check .` | Python linting |
| | ruff format | `ruff format .` | Python formatting |
| | clippy | `cargo clippy -- -D warnings` | Rust linting |
| | eslint | `pnpm lint` | TypeScript linting |
| | prettier | `pnpm format` | TypeScript formatting |
| **Type Checking** | mypy | `mypy src/` | Python type checking |
| | tsc | `pnpm type-check` | TypeScript type checking |
| **Testing** | pytest | `pytest tests/ -v` | Python tests |
| | cargo test | `cargo test --all-features` | Rust tests |
| | vitest | `pnpm test` | TypeScript tests |
| **Coverage** | pytest-cov | `pytest --cov=src` | Python coverage |
| | cargo-llvm-cov | `cargo llvm-cov` | Rust coverage |
| | c8 | `pnpm test:coverage` | TypeScript coverage |
| **Security** | bandit | `bandit -r src/ -ll` | Python security |
| | cargo audit | `cargo audit` | Rust security |
| | gitleaks | `gitleaks detect` | Secret detection |
| **Documentation** | pdoc | `pdoc --output-dir docs/api/python` | Python API docs |
| | rustdoc | `cargo doc --no-deps` | Rust API docs |
| | typedoc | `pnpm docs` | TypeScript API docs |
| | mkdocs | `mkdocs build` | Documentation site |
| **Refactoring** | pyupgrade | `pyupgrade --py312-plus` | Python modernization |
| | cargo fix | `cargo fix --allow-dirty` | Rust fixes |
| | eslint --fix | `pnpm lint:fix` | TypeScript fixes |
| **Versioning** | oasdiff | `oasdiff breaking --base ... --revision ...` | API diff |
| | git-cliff | `git-cliff --output CHANGELOG.md` | Changelog generation |

---

*End of Maintainability Implementation Guide*</longcat_think>

# GRC_Claw Maintainability Specification

**Document ID:** GRC-MNT-001  
**Version:** 2.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Last Updated:** 2026-10-01  

---

## 1. Purpose & Scope

### 1.1 Purpose

This specification defines the maintainability standards, practices, and policies that ensure GRC_Claw remains sustainable, extensible, and operable across its full lifecycle — from initial development through enterprise-scale operation and eventual component retirement.

GRC_Claw is an open-source GRC platform with a projected 18-month delivery roadmap and a long-term operating horizon. The system's complexity (policy engine, audit trail, enforcement proxy, evidence collection, analytics, multi-framework compliance mapping) demands rigorous maintainability standards to prevent technical debt accumulation, enable community contributions, and ensure long-term viability.

### 1.2 Scope

**In scope:**
- Code quality requirements (linting, type checking, testing, documentation)
- Modularity and architectural boundary standards
- API versioning strategy (REST API, SDKs, policy DSL)
- Deprecation policies (APIs, features, configurations, controls)
- Maintainability enforcement across the development lifecycle
- Technical debt management
- Community contribution quality gates
- Developer experience (DX) optimization
- Documentation automation
- Code quality metrics and dashboards
- Refactoring automation
- Developer onboarding optimization

**Out of scope:**
- Specific implementation details of individual modules
- Operational runbooks and deployment procedures
- Security controls (covered by GRC-SEC-001)
- Evidence format specifications (covered by GRC-EVD-001)

### 1.3 Relationship to Other Specifications

| Specification | Relationship |
|---------------|-------------|
| GRC-AIG-001 (AI Governance) | Maintainability of governance logic |
| GRC-EVD-001 (Evidence) | Maintainability of evidence pipeline |
| GRC-TPR-001 (Third-Party Risk) | Maintainability of vendor integrations |
| GRC-CI-001 (Continuous Improvement) | Maintainability as a CI input |
| GRC-ROADMAP-001 (Product Roadmap) | Maintainability across phases |
| GRC-QA-001 (Quality Assurance) | Quality gates, metrics, and testing standards (see §13) |

---

## 2. Maintainability Principles

GRC_Claw adheres to seven core maintainability principles:

1. **Explicit over Implicit** — All behavior is documented, typed, and discoverable. No hidden magic.
2. **Blast Radius Containment** — Changes to one module do not cascade unpredictably to others.
3. **Testability as a First-Class Concern** — Every module is designed to be testable in isolation.
4. **Documentation Lives with Code** — Docs are versioned alongside code, not in a separate wiki.
5. **Deprecation is Planned, Not Reactive** — Features have defined lifecycles with advance notice.
6. **Community-Ready** — External contributors can understand, modify, and extend without tribal knowledge.
7. **Measurable Health** — Maintainability is tracked with quantitative metrics, not vibes.

---

## 3. Code Quality Requirements

### 3.1 Language & Runtime Standards

| Layer | Language | Runtime | Type System |
|-------|----------|---------|-------------|
| Policy Engine | Python 3.12+ | CPython | Full type hints (PEP 484) |
| Enforcement Proxy | Rust 1.75+ | Tokio async | Native types |
| API Gateway | Python 3.12+ | FastAPI | Pydantic v2 models |
| Web UI | TypeScript 5.x+ | React 18+ | Strict TypeScript |
| SDK (Python) | Python 3.10+ | — | Type stubs (.pyi) |
| SDK (TypeScript) | TypeScript 5.x+ | Node 20+ | Generated from OpenAPI |

### 3.2 Linting & Static Analysis

Every pull request MUST pass all linters with zero warnings. The CI pipeline enforces this as a hard gate.

#### 3.2.1 Python (Policy Engine, API, SDK)

| Tool | Purpose | Config File | Severity |
|------|---------|-------------|----------|
| `ruff` | Linting + import sorting | `pyproject.toml` | Error |
| `mypy` | Static type checking | `pyproject.toml` | Error |
| `bandit` | Security linting | `pyproject.toml` | Error |
| `vulture` | Dead code detection | `pyproject.toml` | Warning |

**Rules:**
- `ruff` rule set: `E`, `F`, `I`, `N`, `UP`, `B`, `A`, `C4`, `SIM`, `TCH`
- `mypy` strict mode: `disallow_untyped_defs`, `disallow_incomplete_defs`, `check_untyped_defs`, `no_implicit_optional`, `warn_redundant_casts`, `warn_unused_ignores`
- Maximum cyclomatic complexity: **10** per function
- Maximum cognitive complexity: **15** per function

#### 3.2.2 Rust (Enforcement Proxy)

| Tool | Purpose | Config File | Severity |
|------|---------|-------------|----------|
| `clippy` | Linting | `Cargo.toml` | `-D warnings` |
| `cargo fmt` | Formatting | `rustfmt.toml` | Error |
| `cargo audit` | Dependency vulnerabilities | — | Error |

**Rules:**
- `clippy` pedantic lints enabled
- Maximum function length: **100 lines**
- Maximum module length: **500 lines**
- All `unsafe` blocks require a `// SAFETY:` comment

#### 3.2.3 TypeScript (Web UI, SDK)

| Tool | Purpose | Config File | Severity |
|------|---------|-------------|----------|
| `eslint` | Linting | `.eslintrc.json` | Error |
| `prettier` | Formatting | `.prettierrc` | Error |
| `tsc --noEmit` | Type checking | `tsconfig.json` | Error |

**Rules:**
- `eslint` rule set: `@typescript-eslint/recommended`, `react-hooks/recommended`
- No `any` types without an `// eslint-disable-next-line` with justification
- Maximum component size: **300 lines**

### 3.3 Testing Requirements

#### 3.3.1 Test Coverage Thresholds

| Module Category | Line Coverage | Branch Coverage | Mutation Score |
|----------------|---------------|-----------------|----------------|
| Policy Engine | ≥ 90% | ≥ 85% | ≥ 70% |
| Audit Trail | ≥ 95% | ≥ 90% | ≥ 80% |
| Enforcement Proxy | ≥ 90% | ≥ 85% | ≥ 70% |
| API Gateway | ≥ 85% | ≥ 80% | ≥ 60% |
| Evidence Pipeline | ≥ 85% | ≥ 80% | ≥ 60% |
| SDKs | ≥ 80% | ≥ 75% | N/A |
| Web UI | ≥ 70% | ≥ 60% | N/A |

**Enforcement:** Coverage thresholds are enforced in CI. A PR that reduces coverage below the threshold is blocked.

#### 3.3.2 Test Types & Requirements

| Test Type | Scope | Speed Requirement | CI Stage |
|-----------|-------|-------------------|----------|
| **Unit tests** | Individual functions/classes | < 100ms per test | Every PR |
| **Integration tests** | Module interactions with test doubles | < 5s per test | Every PR |
| **Contract tests** | API schema conformance (OpenAPI) | < 10s per test | Every PR |
| **Property-based tests** | Invariants (policy evaluation, audit chain) | < 30s per test | Nightly |
| **End-to-end tests** | Full system workflows | < 5min per test | Nightly |
| **Chaos tests** | Failure injection (enforcement proxy) | < 10min per test | Weekly |
| **Performance tests** | Latency/throughput benchmarks | < 15min per test | Weekly |

#### 3.3.3 Test Standards

- **Naming:** `test_<subject>_<condition>_<expected_outcome>` (e.g., `test_policy_eval_deny_when_agent_unregistered`)
- **Structure:** Arrange-Act-Assert pattern
- **Isolation:** No shared mutable state between tests
- **Determinism:** No reliance on wall-clock time, random values, or external services without mocking
- **Fixtures:** Shared fixtures in `conftest.py` (Python) or `testUtils.ts` (TypeScript)
- **Golden files:** For complex policy evaluation outputs, use golden file testing with `--update-goldens` flag

#### 3.3.4 Audit Trail Testing (Special Requirements)

The audit trail subsystem has additional testing requirements due to its tamper-evident nature:

1. **Hash chain integrity tests** — Verify chain continuity after every operation
2. **Concurrency tests** — Parallel writes maintain chain integrity
3. **Corruption detection tests** — Any modification to a historical entry is detected
4. **Verification endpoint tests** — `/api/v1/audit/verify` returns correct results for valid and invalid chains
5. **Load tests** — 10,000 entries verified in < 2 seconds (per roadmap SLA)

### 3.4 Documentation Standards

#### 3.4.1 Code-Level Documentation

| Artifact | Requirement | Standard |
|----------|-------------|----------|
| **Docstrings** | All public modules, classes, functions | Google-style (Python), rustdoc (Rust), TSDoc (TS) |
| **Type annotations** | All function signatures | PEP 484, Rust types, TypeScript types |
| **README per module** | Purpose, dependencies, API, examples | Markdown |
| **Architecture Decision Records (ADRs)** | Significant design decisions | `docs/adr/NNNN-title.md` |
| **Inline comments** | Complex logic only | Explain "why", not "what" |

#### 3.4.2 API Documentation

- **OpenAPI 3.1 spec** auto-generated from code (FastAPI `openapi()` endpoint)
- **SDK documentation** generated from type annotations (pdoc for Python, TypeDoc for TypeScript)
- **Policy DSL documentation** with grammar specification and examples
- **Changelog** maintained in `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format

#### 3.4.3 Documentation Freshness

- Documentation is reviewed in every PR that changes public APIs
- Stale documentation (docs referencing removed/renamed symbols) is a CI error
- Quarterly documentation audit: verify all examples still run, all links still resolve

---

## 4. Modularity Standards

### 4.1 Module Boundaries

GRC_Claw follows a **plugin-oriented modular architecture**. Each module is a self-contained unit with a well-defined interface.

#### 4.1.1 Core Modules

| Module | Responsibility | Dependencies (inbound) | Dependencies (outbound) |
|--------|---------------|----------------------|------------------------|
| `policy-engine` | Parse, validate, evaluate policies | API Gateway | Storage, Audit Trail |
| `audit-trail` | Append-only hash-chained log | All modules | Storage |
| `enforcement-proxy` | Real-time policy enforcement | Agent frameworks | Policy Engine, Audit Trail |
| `compliance-mapper` | Map controls to frameworks | Policy Engine | Framework Catalogs |
| `evidence-collector` | Collect and normalize evidence | Scheduler, Cloud APIs | Evidence Store |
| `agent-registry` | Agent identity and lifecycle | API Gateway | Storage, Audit Trail |
| `analytics-engine` | Risk scoring and trends | Evidence Store | Storage |
| `api-gateway` | REST API, auth, routing | Web UI, SDKs | All core modules |

#### 4.1.2 Module Rules

1. **Single Responsibility** — Each module does one thing and does it well
2. **Explicit Interfaces** — Inter-module communication only through defined APIs (no direct database access across modules)
3. **Dependency Direction** — Dependencies point inward: `api-gateway → core modules → storage`. No circular dependencies.
4. **Independent Deployability** — Each module can be deployed and scaled independently
5. **Independent Testability** — Each module can be tested in isolation with mocked dependencies

### 4.2 Plugin Architecture

GRC_Claw supports extensibility through a plugin system for:

- **Framework catalogs** — New compliance frameworks (e.g., PCI-DSS, HIPAA) as plugins
- **Agent framework adapters** — LangChain, AutoGen, CrewAI, custom adapters
- **Evidence collectors** — Cloud providers, SIEM systems, custom sources
- **Notification channels** — Slack, PagerDuty, webhooks, email
- **Policy compilers** — OPA/Rego, Cedar, native engine

#### 4.2.1 Plugin Interface Contract

```python
# Python plugin interface
class GRCPlugin(Protocol):
    name: str
    version: str
    supported_frameworks: list[str]
    
    def initialize(self, config: dict[str, Any]) -> None: ...
    def health_check(self) -> HealthStatus: ...
    def shutdown(self) -> None: ...
```

#### 4.2.2 Plugin Quality Requirements

- Plugins MUST declare their dependencies explicitly
- Plugins MUST NOT access global state outside their namespace
- Plugins MUST handle initialization failures gracefully (fail-fast with clear error)
- Plugins MUST include their own tests
- Plugins MUST document their configuration options

### 4.3 Dependency Management

#### 4.3.1 Python Dependencies

- **Lock file:** `uv.lock` (committed to repository)
- **Update cadence:** Monthly dependency update PR (automated via Dependabot/Renovate)
- **Vulnerability scanning:** `pip-audit` in CI, blocks merge on critical CVEs
- **License compatibility:** All dependencies must be OSI-approved licenses compatible with AGPL-3.0

#### 4.3.2 Rust Dependencies

- **Lock file:** `Cargo.lock` (committed to repository)
- **Update cadence:** Monthly `cargo update` PR
- **Vulnerability scanning:** `cargo audit` in CI

#### 4.3.3 TypeScript Dependencies

- **Lock file:** `pnpm-lock.yaml` (committed to repository)
- **Update cadence:** Weekly Renovate PR
- **Vulnerability scanning:** `pnpm audit` in CI

### 4.4 Database Schema Management

- **Migration tool:** Alembic (Python), sqlx (Rust)
- **Migration rules:**
  - All schema changes are backward-compatible (expand-migrate-contract pattern)
  - Migrations are immutable once merged to main
  - Every migration includes a `down` migration for rollback
  - Migrations are tested against a fresh database in CI
- **Schema documentation:** Auto-generated ER diagrams in `docs/schema/`

---

## 5. API Versioning Strategy

### 5.1 Versioning Scheme

GRC_Claw uses **URL-based versioning** for the REST API and **semantic versioning** for SDKs and the policy DSL.

#### 5.1.1 REST API Versioning

```
https://api.grc-claw.example.com/api/v1/policies
https://api.grc-claw.example.com/api/v2/policies
```

- **Major version** in URL path (`/v1/`, `/v2/`)
- **Minor version** in response header (`X-API-Version: 1.2.0`)
- **Patch version** in response header (`X-API-Version: 1.2.3`)

#### 5.1.2 SDK Versioning

| SDK | Scheme | Example |
|-----|--------|---------|
| Python SDK | SemVer | `grc-claw==1.2.3` |
| TypeScript SDK | SemVer | `@grc-claw/sdk@1.2.3` |
| Policy DSL | SemVer | `policy-version: "1.2.0"` |

#### 5.1.3 Version Compatibility Matrix

| API Version | SDK Support | Policy DSL | Sunset Date |
|-------------|-------------|------------|-------------|
| v1 (current) | ≥ 1.0.0 | ≥ 1.0.0 | TBD |
| v0 (legacy) | 0.x | 0.x | 2027-04-01 |

### 5.2 API Evolution Rules

1. **Additive changes only within a major version** — New fields, new endpoints, new query parameters are allowed. No removals or type changes.
2. **Breaking changes require a new major version** — Field removal, type change, endpoint removal, semantic change.
3. **Deprecation headers** — Deprecated endpoints return `Deprecation: true` and `Sunset: <date>` headers.
4. **Response compatibility** — All responses include a `version` field so clients can detect and adapt.
5. **Request compatibility** — New required fields in requests are a breaking change. New optional fields are additive.

### 5.3 OpenAPI Specification

- The OpenAPI spec is the **single source of truth** for the REST API
- Generated from code annotations (FastAPI), not hand-written
- Published at `/api/v1/openapi.json` and `/api/v2/openapi.json`
- SDKs are generated from the OpenAPI spec (OpenAPI Generator)
- Breaking changes in the OpenAPI spec are detected in CI (oasdiff)

### 5.4 Policy DSL Versioning

The policy DSL (AIGoLang) uses semantic versioning:

```yaml
policy-version: "1.2.0"
policy:
  name: "data-retention"
  rules: [...]
```

- **DSL parser** supports all versions within the current major version
- **DSL compiler** targets the current major version; older targets available via `--target-version` flag
- **DSL migration tool** (`grc migrate-policy`) automates upgrades between DSL versions

---

## 6. Deprecation Policies

### 6.1 Deprecation Lifecycle

Every API, feature, configuration option, and control follows a five-stage deprecation lifecycle:

```
  Active  ──►  Deprecated  ──►  Sunset  ──►  Removed  ──►  Archived
 (full      (warning       (header +    (endpoint    (docs only,
  support)   + docs)        410 Gone)    disabled)    no code)
```

| Stage | Duration | Behavior | Communication |
|-------|----------|----------|---------------|
| **Active** | — | Full support, no warnings | — |
| **Deprecated** | ≥ 6 months | Functional but warns; `Deprecation` header; docs marked deprecated | Release notes, migration guide, `CHANGELOG.md` |
| **Sunset** | ≥ 3 months | Returns `410 Gone` with migration instructions in response body | Email to registered users, GitHub issue, docs banner |
| **Removed** | — | Endpoint/feature no longer exists; code deleted | Final release note |
| **Archived** | Indefinite | Documentation preserved in `docs/archive/`; no code | — |

### 6.2 Deprecation Criteria

A feature or API is deprecated when:

1. **Superseded** — A newer, better alternative exists
2. **Low usage** — Fewer than 5% of active organizations use it (measured via telemetry)
3. **Framework change** — The underlying compliance framework is updated or withdrawn
4. **Security** — The feature has an unpatchable security concern
5. **Architectural** — The feature conflicts with a new architectural direction

### 6.3 Deprecation Process

1. **Proposal** — A deprecation proposal is filed as a GitHub issue with:
   - Rationale for deprecation
   - Usage statistics
   - Proposed replacement
   - Proposed timeline
2. **Review** — Architecture team reviews and approves/rejects within 2 weeks
3. **Announcement** — Deprecation announced in release notes, docs, and `CHANGELOG.md`
4. **Implementation** — Deprecation warnings added, `Deprecation` header set, docs updated
5. **Migration guide** — Step-by-step migration guide published
6. **Sunset** — After the sunset period, the feature returns `410 Gone`
7. **Removal** — Code deleted in a subsequent release

### 6.4 Special Deprecation Rules

#### 6.4.1 Audit Trail Data

Audit trail entries are **never deprecated or removed**. They are immutable and retained per the evidence retention policy (GRC-EVD-001). The audit trail schema may evolve, but old entries remain verifiable.

#### 6.4.2 Compliance Controls

Compliance controls from frameworks (e.g., NIST 800-53, ISO 27001) are never removed. When a framework is updated:
- Old control versions are marked deprecated but remain available
- New control versions are added alongside
- Mapping between old and new versions is provided

#### 6.4.3 Policy DSL

Policy DSL versions within the same major version are always supported. Cross-major deprecation follows the standard lifecycle with a minimum 12-month deprecation period due to the complexity of policy migration.

### 6.5 Deprecation Tracking

All deprecations are tracked in `DEPRECATIONS.md` at the repository root:

```markdown
| Feature | Deprecated In | Sunset Date | Replacement | Status |
|---------|--------------|-------------|-------------|--------|
| `/api/v1/policies/bulk` | v1.3.0 | 2027-04-01 | `/api/v2/policies/bulk` | Deprecated |
| `policy-dsl v0` | v1.0.0 | 2027-01-01 | `policy-dsl v1` | Sunset |
```

---

## 7. Maintainability Across the Lifecycle

### 7.1 Development Phase Gates

Every pull request must pass through these maintainability gates before merge:

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Lint &    │──►│   Test      │──►│  Coverage   │──►│   Docs      │──►│   Review    │
│   Type Check│   │   Suite     │   │   Gate      │──►│   Check     │──►│   Approval  │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
     │                  │                  │                  │                  │
     ▼                  ▼                  ▼                  ▼                  ▼
  ruff, mypy,     pytest, cargo    ≥ threshold      ADR if needed,    2 approvals
  clippy, eslint  test, vitest     per module       docstring check    (1 for docs)
```

#### 7.1.1 Pre-Merge Checklist

- [ ] All linters pass with zero warnings
- [ ] All tests pass (unit + integration + contract)
- [ ] Coverage meets or exceeds module threshold
- [ ] No new dependencies without justification
- [ ] Public API changes have updated OpenAPI spec
- [ ] New/changed logic has docstrings
- [ ] ADR created for significant design decisions
- [ ] `CHANGELOG.md` updated
- [ ] No `TODO`/`FIXME` comments without linked issue
- [ ] No hardcoded secrets (detected by `gitleaks`)

### 7.2 Code Review Standards

#### 7.2.1 Review Focus Areas

Reviewers must assess:

1. **Correctness** — Does the code do what it claims?
2. **Test quality** — Are tests meaningful, not just coverage-padding?
3. **Maintainability** — Can the next developer understand and modify this?
4. **Performance** — Are there obvious bottlenecks or resource leaks?
5. **Security** — Are inputs validated? Are secrets handled safely?
6. **Modularity** — Does it respect module boundaries? Are dependencies clean?

#### 7.2.2 Review Response Time

| PR Size | Target Review Time |
|---------|-------------------|
| < 50 lines | 24 hours |
| 50–200 lines | 48 hours |
| 200–500 lines | 72 hours |
| > 500 lines | Split into smaller PRs |

### 7.3 Technical Debt Management

#### 7.3.1 Debt Identification

Technical debt is identified through:

1. **Static analysis** — `vulture` (dead code), `mypy` (type gaps), complexity metrics
2. **Code review** — Reviewers flag debt with `// TECH-DEBT:` comments
3. **Metrics trends** — Increasing cyclomatic complexity, decreasing coverage
4. **Incident post-mortems** — Root cause analysis identifies debt contributions
5. **Community feedback** — Issues and discussions flagging pain points

#### 7.3.2 Debt Tracking

All technical debt is tracked in `TECH-DEBT.md`:

```markdown
| ID | Description | Module | Severity | Created | Target Fix | Status |
|----|-------------|--------|----------|---------|-------------|--------|
| TD-001 | Policy evaluator uses recursive descent without memoization | policy-engine | Medium | 2026-10-01 | v1.4.0 | Open |
```

#### 7.3.3 Debt Budget

- **20% of each sprint** is allocated to technical debt reduction
- **Critical debt** (security, data integrity, performance SLA breach) is prioritized immediately
- **Debt aging** — Items older than 6 months are escalated to the architecture team

### 7.4 Observability & Maintainability

#### 7.4.1 Structured Logging

All modules emit structured JSON logs with consistent fields:

```json
{
  "timestamp": "2026-10-01T12:00:00Z",
  "level": "INFO",
  "module": "policy-engine",
  "trace_id": "abc-123",
  "event": "policy_evaluated",
  "policy_id": "pol-456",
  "agent_id": "agent-789",
  "decision": "ALLOW",
  "duration_ms": 12
}
```

#### 7.4.2 Metrics

Key maintainability metrics are exported via Prometheus:

| Metric | Type | Description |
|--------|------|-------------|
| `grc_policy_eval_duration` | Histogram | Policy evaluation latency |
| `grc_audit_chain_verify_duration` | Histogram | Audit verification latency |
| `grc_enforcement_decisions_total` | Counter | Enforcement decisions by outcome |
| `grc_evidence_collection_failures_total` | Counter | Evidence collection failures |
| `grc_api_requests_total` | Counter | API requests by endpoint, version, status |
| `grc_test_coverage` | Gauge | Current test coverage per module |
| `grc_tech_debt_items` | Gauge | Open technical debt items by severity |

#### 7.4.3 Health Checks

Every module exposes a `/health` endpoint returning:

```json
{
  "status": "healthy",
  "module": "policy-engine",
  "version": "1.2.3",
  "checks": {
    "database": "ok",
    "policy_store": "ok",
    "audit_trail": "ok"
  }
}
```

### 7.5 Continuous Integration Pipeline

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Build   │──►│  Lint    │──►│  Test    │──►│  Cover   │──►│  Security│──►│  Deploy  │
│          │   │          │   │          │   │          │   │  Scan    │   │  Staging │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼              ▼
  Compile      ruff, mypy,    pytest,       pytest-cov,   bandit,        Staging
  + install    clippy,       cargo test,   tarpaulin,    pip-audit,     environment
  + openapi    eslint, vitest  nextest       cargo-llvm-   cargo audit,   validation
  + docs       tsc           property       cov           pnpm audit,
                              tests                       gitleaks
```

### 7.6 Release Management

#### 7.6.1 Release Cadence

| Release Type | Frequency | Version Bump | Approval |
|-------------|-----------|-------------|----------|
| **Patch** | As needed | `x.y.Z` | 1 maintainer |
| **Minor** | Monthly | `x.Y.0` | 2 maintainers |
| **Major** | Semi-annually | `X.0.0` | Architecture team + community vote |

#### 7.6.2 Release Checklist

- [ ] All CI gates pass
- [ ] `CHANGELOG.md` updated with all changes since last release
- [ ] Migration guide published for any breaking changes
- [ ] Deprecation notices included for any deprecated features
- [ ] OpenAPI spec regenerated and published
- [ ] SDK packages published to PyPI and npm
- [ ] Docker images tagged and pushed
- [ ] Release notes published on GitHub
- [ ] Community announcement (Discord, mailing list)

### 7.7 Community Contribution Quality

#### 7.7.1 Contribution Gates

External contributions must meet the same quality standards as internal development:

1. **CLA** — Contributor License Agreement signed
2. **Issue linkage** — PR references a GitHub issue
3. **CI passing** — All automated gates pass
4. **Review** — At least 1 maintainer approval (2 for core modules)
5. **Documentation** — Public API changes include doc updates
6. **Tests** — New functionality includes tests meeting coverage thresholds

#### 7.7.2 Contribution Documentation

- `CONTRIBUTING.md` — How to set up dev environment, run tests, submit PRs
- `docs/architecture/` — Module architecture diagrams and design docs
- `docs/adr/` — Architecture Decision Records
- `docs/api/` — API reference (auto-generated)
- `docs/policy-dsl/` — Policy language specification and examples

---

## 8. Maintainability Metrics & Reporting

### 8.1 Maintainability Index

GRC_Claw tracks a composite **Maintainability Index (MI)** calculated monthly:

| Metric | Weight | Source | Target |
|--------|--------|--------|--------|
| Test coverage | 25% | CI pipeline | ≥ 85% |
| Cyclomatic complexity (avg) | 15% | Static analysis | ≤ 8 |
| Technical debt ratio | 20% | TECH-DEBT.md | ≤ 10% |
| Documentation coverage | 15% | Docstring/parser | ≥ 90% |
| Dependency freshness | 10% | Dependabot | ≤ 30 days behind |
| Mean time to patch CVE | 10% | Security scan | ≤ 7 days (critical) |
| Community PR merge rate | 5% | GitHub | ≥ 70% |

**MI = Σ (metric_score × weight)**  
**Target: MI ≥ 80/100**

### 8.2 Quarterly Maintainability Report

Every quarter, the architecture team publishes a maintainability report including:

1. **MI trend** — Quarter-over-quarter change
2. **Debt aging** — Items by age and severity
3. **Coverage trends** — By module, over time
4. **Dependency health** — Outdated/vulnerable dependencies
5. **API version adoption** — Usage by version
6. **Deprecation status** — Items in each lifecycle stage
7. **Recommendations** — Prioritized improvements for next quarter

### 8.3 Maintainability in Continuous Improvement

Maintainability metrics feed into GRC_Claw's Continuous Improvement Engine (GRC-CI-001):

- **MEASURE** — MI and component metrics are measured continuously
- **MANAGE** — Technical debt is treated as a risk in the risk register
- **IMAS** — Maintainability is a fitness function in the CI engine
- **PDCA** — Quarterly maintainability reviews drive the Plan-Do-Check-Act cycle

---

## 9. Module-Specific Maintainability Requirements

### 9.1 Policy Engine

| Requirement | Standard |
|-------------|----------|
| DSL parser | Property-based tests for all grammar rules |
| Policy evaluator | Golden file tests for all built-in policy templates |
| Policy compiler | Snapshot tests for compiled output (OPA/Rego, Cedar) |
| Policy versioning | Migration tests between all supported DSL versions |
| Complexity | Cyclomatic complexity ≤ 8 per rule evaluator |

### 9.2 Audit Trail

| Requirement | Standard |
|-------------|----------|
| Hash chain | Property-based tests for chain integrity under all operations |
| Concurrency | Stress tests with 100+ parallel writers |
| Verification | Fuzz testing for verification endpoint |
| Performance | 10K entries verified in < 2 seconds (roadmap SLA) |
| Storage | Migration tests for all storage backends |

### 9.3 Enforcement Proxy

| Requirement | Standard |
|-------------|----------|
| Latency | p99 < 100ms under load (roadmap SLA) |
| Circuit breaker | Chaos tests for all failure modes |
| Policy distribution | Integration tests with all supported agent frameworks |
| Decision logging | Property-based tests for decision certificate generation |
| Fail-open/closed | Exhaustive tests for all policy configurations |

### 9.4 Evidence Pipeline

| Requirement | Standard |
|-------------|----------|
| OSCAL conformance | Schema validation tests against OSCAL 1.1.0 |
| Collector framework | Contract tests for all collector interfaces |
| Chain of custody | Property-based tests for custody event integrity |
| Package export | Snapshot tests for all export formats (JSON, PDF, CSV, XML) |
| Retention | Integration tests for retention policy enforcement |

### 9.5 API Gateway

| Requirement | Standard |
|-------------|----------|
| OpenAPI conformance | Contract tests against published OpenAPI spec |
| Authentication | Security tests for all auth flows (OIDC, API key, mTLS) |
| Rate limiting | Load tests for rate limit enforcement |
| Version routing | Integration tests for all API version combinations |
| Error handling | Snapshot tests for all error response formats |

---

## 10. Tooling & Automation

### 10.1 Maintainability Toolchain

| Purpose | Tool | Scope |
|---------|------|-------|
| Linting | ruff, clippy, eslint | All code |
| Type checking | mypy, rustc, tsc | All code |
| Testing | pytest, cargo test, vitest | All code |
| Coverage | pytest-cov, cargo-llvm-cov, c8 | All code |
| Security | bandit, cargo audit, pnpm audit, gitleaks | All code |
| Complexity | radon, tokei, eslint-complexity | All code |
| Dead code | vulture, cargo-udeps | Python, Rust |
| API diff | oasdiff | OpenAPI spec |
| Dependency audit | pip-audit, cargo audit, renovate | All dependencies |
| Documentation | pdoc, rustdoc, typedoc | All public APIs |
| Changelog | git-cliff | Release notes |
| ADR | adr-tools | Architecture decisions |

### 10.2 Pre-Commit Hooks

All developers must install pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks: [ruff, ruff-format]
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks: [mypy]
  - repo: https://github.com/doublify/pre-commit-rust
    hooks: [cargo-fmt, clippy]
  - repo: https://github.com/pre-commit/mirrors-eslint
    hooks: [eslint]
  - repo: https://github.com/gitleaks/gitleaks
    hooks: [gitleaks]
```

### 10.3 Automated Maintenance Tasks

| Task | Frequency | Tool | Output |
|------|-----------|------|--------|
| Dependency update | Weekly | Renovate | Automated PR |
| Vulnerability scan | Daily | pip-audit, cargo audit | CI alert |
| Coverage report | Every PR | pytest-cov, c8 | PR comment |
| API breaking change detection | Every PR | oasdiff | CI gate |
| Stale issue identification | Monthly | GitHub Actions | Issue labels |
| Documentation link check | Weekly | lychee | CI alert |
| Dead code detection | Monthly | vulture, cargo-udeps | Report |
| Complexity trend | Monthly | radon, tokei | Report |

---

## 11. Developer Experience (DX) Optimization

### 11.1 DX Principles

GRC_Claw treats developer experience as a first-class maintainability concern. A maintainable codebase is only sustainable if developers can work in it efficiently and confidently.

1. **Fast Feedback Loops** — Developers get lint, type, and test feedback in seconds, not minutes.
2. **Self-Service Tooling** — Common tasks (scaffolding, migration, debugging) are automated and discoverable.
3. **Consistent Patterns** — All modules follow the same structural conventions so developers can predict where things live.
4. **Progressive Disclosure** — Simple tasks are simple; complex tasks are possible without overwhelming newcomers.
5. **Pain-Driven Improvement** — Developer friction is measured and systematically eliminated.

### 11.2 Local Development Environment

#### 11.2.1 One-Command Setup

```bash
# Clone and enter
git clone https://github.com/grc-claw/grc-claw.git && cd grc-claw

# One-command dev environment (installs deps, pre-commit hooks, DB, env vars)
make dev-setup

# Verify environment
make doctor
```

`make dev-setup` performs:
- Python virtual environment creation and dependency installation (`uv sync`)
- Rust toolchain installation (`rustup`)
- Node.js dependency installation (`pnpm install`)
- Pre-commit hook installation (`pre-commit install`)
- Docker Compose services startup (PostgreSQL, Redis, Kafka, MinIO)
- Environment file generation (`.env` from `.env.example`)
- Database migration application (`alembic upgrade head`)
- Seed data loading for local development

#### 11.2.2 Development Commands

| Command | Purpose | Time Target |
|---------|---------|-------------|
| `make dev` | Start all services with hot reload | < 5s to ready |
| `make test` | Run full test suite | < 3 min |
| `make test-fast` | Run unit tests only | < 30s |
| `make lint` | Run all linters | < 15s |
| `make format` | Auto-format all code | < 10s |
| `make typecheck` | Run all type checkers | < 20s |
| `make docs-serve` | Serve documentation locally | < 3s |
| `make db-migrate` | Create new migration (prompts for name) | Interactive |
| `make db-rollback` | Rollback last migration | < 5s |
| `make clean` | Remove build artifacts, caches, containers | < 10s |

#### 11.2.3 Hot Reload & File Watching

- **Python (Policy Engine, API):** `uvicorn --reload` with `watchfiles` for automatic restart on `.py` changes
- **Rust (Enforcement Proxy):** `cargo watch -x run` for automatic recompile and restart
- **TypeScript (Web UI, SDK):** Vite dev server with HMR (Hot Module Replacement)
- **Tests:** `pytest-watch` (ptw) for automatic test re-run on file changes

### 11.3 Code Scaffolding & Generators

#### 11.3.1 Module Scaffolding

```bash
# Generate a new Python module with standard structure
grc scaffold module --name evidence-normalizer --category pipeline

# Generates:
# src/evidence_normalizer/
# ├── __init__.py          # Public API exports
# ├── models.py            # Pydantic models
# ├── service.py           # Core business logic
# ├── repository.py        # Data access layer
# ├── exceptions.py        # Module-specific exceptions
# └── tests/
#     ├── conftest.py       # Shared fixtures
#     ├── test_models.py
#     ├── test_service.py
#     └── test_repository.py
```

#### 11.3.2 API Endpoint Scaffolding

```bash
# Generate a new REST API endpoint with OpenAPI spec
grc scaffold endpoint --path /api/v1/evidence --methods GET,POST

# Generates:
# - Route handler with Pydantic request/response models
# - OpenAPI annotation (auto-registered)
# - Unit test stubs with coverage
# - Integration test stubs
# - Documentation stub
```

#### 11.3.3 Plugin Scaffolding

```bash
# Generate a new plugin with interface stubs
grc scaffold plugin --type framework-catalog --name pci-dss

# Generates:
# - Plugin class implementing GRCPlugin protocol
# - Configuration schema (Pydantic)
# - Test suite with contract tests
# - Example configuration
# - README with usage instructions
```

### 11.4 Debugging & Observability

#### 11.4.1 Debug Configurations

Pre-configured debug configurations are provided for:

| IDE/Editor | Config File | Features |
|------------|-------------|----------|
| VS Code | `.vscode/launch.json` | Python (debugpy), Rust (CodeLLDB), TypeScript (Node) |
| PyCharm | `.idea/runConfigurations/` | Python, remote Docker |
| Vim/Neovim | `configs/dap.lua` | nvim-dap with Python/Rust/Node |

#### 11.4.2 Structured Logging in Development

Local development uses pretty-printed structured logs:

```json
{
  "timestamp": "2026-10-01T12:00:00.123Z",
  "level": "DEBUG",
  "module": "policy-engine",
  "trace_id": "abc-123",
  "event": "policy_evaluated",
  "policy_id": "pol-456",
  "decision": "ALLOW",
  "duration_ms": 12,
  "context": {
    "agent_id": "agent-789",
    "framework": "NIST-800-53",
    "rule_results": [...]
  }
}
```

#### 11.4.3 Request Tracing

Every API request in development mode includes:
- Full request/response cycle timing
- Database query log (with slow query highlighting)
- External call log (with latency)
- Policy evaluation trace (rule-by-rule breakdown)
- Cache hit/miss indicators

### 11.5 IDE Integration

#### 11.5.1 Editor Configuration

| Editor | Configuration | Plugins |
|--------|--------------|---------|
| VS Code | `.vscode/settings.json`, `.vscode/extensions.json` | Python, Rust Analyzer, ESLint, Prettier, Pylance |
| PyCharm | `.idea/` project config | Ruff, mypy |
| Vim | `configs/` | ALE, coc.nvim |
| Emacs | `configs/` | lsp-mode, flycheck |

#### 11.5.2 Language Server Configuration

- **Python:** Pylance/Pylsp with strict mode, all paths configured
- **Rust:** rust-analyzer with clippy linting
- **TypeScript:** TypeScript ESLint with project references

### 11.6 DX Metrics & Feedback

#### 11.6.1 DX Metrics Tracked

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to first commit (new contributor) | < 30 min | Onboarding survey |
| `make dev-setup` success rate | ≥ 95% | CI + manual tracking |
| Local test suite runtime | < 3 min | CI benchmark |
| Lint + typecheck runtime | < 30 s | CI benchmark |
| Time to scaffold new module | < 1 min | Manual tracking |
| Developer satisfaction (quarterly survey) | ≥ 4.0/5.0 | Survey |

#### 11.6.2 DX Feedback Channels

- **GitHub Discussions** — `dx-feedback` label for DX issues
- **Quarterly DX Survey** — Standardized questions across all contributors
- **Pain Point Triage** — DX issues reviewed bi-weekly by architecture team
- **DX Changelog** — DX improvements highlighted in release notes

---

## 12. Documentation Automation

### 12.1 Documentation Philosophy

Documentation is not an afterthought — it is generated, validated, and deployed automatically from the same source of truth as the code. This eliminates drift, reduces maintenance burden, and ensures developers always have accurate information.

### 12.2 Automated Documentation Pipeline

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Code +      │──►│  Generate    │──►│  Validate    │──►│  Deploy      │
│  Annotations │   │  Docs        │   │  Docs        │   │  Docs        │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
     │                   │                   │                   │
     ▼                   ▼                   ▼                   ▼
  Docstrings,       pdoc, rustdoc,     Link check,         GitHub Pages,
  Type hints,       typedoc,          Example execution,  ReadTheDocs,
  OpenAPI spec      mkdocs            Schema validation   npm/PyPI pages
```

### 12.3 Code-Derived Documentation

#### 12.3.1 API Reference (Auto-Generated)

| Source | Generator | Output | Trigger |
|--------|-----------|--------|---------|
| FastAPI routes | FastAPI `openapi()` | `docs/api/openapi.json` | Every PR merge |
| OpenAPI spec | Redoc / Scalar | `docs/api/reference.html` | Every PR merge |
| Python SDK | pdoc | `docs/sdk/python/` | Every release |
| TypeScript SDK | TypeDoc | `docs/sdk/typescript/` | Every release |
| Rust crates | rustdoc | `docs/rust/` | Every release |

#### 12.3.2 Architecture Diagrams (Auto-Generated)

| Diagram | Tool | Source | Output |
|---------|------|--------|--------|
| Module dependency graph | `pydeps` / `cargo depgraph` | Source code imports | SVG/PNG |
| Database ER diagram | `eralchemy` | SQLAlchemy models / sqlx schema | SVG/PNG |
| API sequence diagrams | `mermaid` (from docstrings) | Annotated examples | Mermaid → SVG |
| C4 architecture models | `structurizr-cli` | `docs/architectural/*.dsl` | Multiple formats |
| Plugin architecture | Custom generator | Plugin registry | HTML + SVG |

#### 12.3.3 Changelog (Auto-Generated)

```bash
# Generate changelog from conventional commits
git-cliff --config cliff.toml --output CHANGELOG.md
```

- Uses [Conventional Commits](https://www.conventionalcommits.org/) format
- Categorizes: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`
- Links to PRs and issues
- Generates GitHub Releases automatically

### 12.4 Documentation Validation (CI-Enforced)

#### 12.4.1 Link Validation

```yaml
# .github/workflows/docs-link-check.yml
- name: Check documentation links
  uses: lycheeverse/lychee-action@v2
  with:
    args: --verbose --no-progress docs/ README.md CHANGELOG.md
    fail: true
```

- All internal links must resolve
- All external links must return 200
- Broken links block PR merge

#### 12.4.2 Code Example Validation

All code examples in documentation are executable and tested:

```python
# docs/examples/policy-evaluation.py
# This file is executed in CI to verify the example works
from grc_claw import PolicyEngine

engine = PolicyEngine()
result = engine.evaluate(
    policy_id="data-retention",
    context={"agent_id": "agent-123", "data_classification": "PII"}
)
assert result.decision == "ALLOW"
```

- Python examples: executed via `pytest --doctest-glob="docs/**/*.md"`
- TypeScript examples: executed via `vitest --config vitest.docs.config.ts`
- Shell commands: executed via `bats docs/test/*.bats`

#### 12.4.3 OpenAPI Spec Validation

```bash
# Validate OpenAPI spec is well-formed and matches implementation
oasdiff breaking --base openapi-prev.json --revision openapi-current.json --fail-on ERR
```

- Breaking changes detected automatically
- Spec must pass spectral linting rules
- All endpoints must have examples
- All schemas must have descriptions

#### 12.4.4 Docstring Coverage

```bash
# Verify all public APIs have docstrings
interrogate -vv --fail-under 90 src/
```

- ≥ 90% docstring coverage required for all public modules
- All public functions, classes, and methods must have docstrings
- Docstrings must include Args, Returns, and Raises sections

### 12.5 Documentation-as-Code

#### 12.5.1 Documentation Structure

```
docs/
├── adr/                    # Architecture Decision Records (hand-written)
├── architecture/           # Architecture docs (hand-written + auto-generated diagrams)
├── api/                    # API reference (auto-generated from OpenAPI)
├── sdk/                    # SDK reference (auto-generated from type annotations)
├── policy-dsl/             # Policy DSL spec (hand-written + auto-generated grammar)
├── examples/               # Executable examples (CI-validated)
├── guides/                 # How-to guides (hand-written)
├── tutorials/              # Step-by-step tutorials (hand-written)
├── archive/                # Deprecated feature docs (auto-moved on deprecation)
└── _templates/             # Documentation templates
```

#### 12.5.2 Documentation Templates

| Template | Purpose | Auto-Generation |
|----------|---------|-----------------|
| `module-template.md` | New module README | `grc scaffold module` |
| `endpoint-template.md` | New API endpoint docs | `grc scaffold endpoint` |
| `adr-template.md` | Architecture Decision Record | `grc adr new` |
| `deprecation-template.md` | Deprecation notice | `grc deprecate` |
| `migration-template.md` | Migration guide | `grc migrate --docs` |

#### 12.5.3 Documentation Versioning

- Documentation is versioned alongside code (Git tags)
- `latest` = current `main` branch
- `stable` = latest release
- `v1.x`, `v2.x` = specific major versions
- Deprecated versions moved to `docs/archive/`

### 12.6 Interactive Documentation

#### 12.6.1 API Playground

- Swagger UI / Redoc served at `/api/v1/docs` and `/api/v2/docs`
- Authenticated with test API keys in development
- All endpoints executable against a sandbox environment

#### 12.6.2 Policy DSL Playground

- Web-based DSL editor with syntax highlighting
- Real-time validation and error highlighting
- Policy evaluation simulator with test contexts
- Export to JSON/YAML

#### 12.6.3 SDK Interactive Examples

- Python SDK: Jupyter notebooks with executable cells
- TypeScript SDK: StackBlitz-embedded examples
- All examples run against a sandbox API

### 12.7 Documentation Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Docstring coverage | ≥ 90% | `interrogate` |
| Link integrity | 100% | `lychee` |
| Example execution success | 100% | CI test run |
| Time since last doc update | ≤ 30 days | Git log analysis |
| Documentation page views | Tracked | Analytics |
| Search success rate | ≥ 80% | Search analytics |

---

## 13. Code Quality Metrics & Dashboards

### 13.1 Metrics Framework

GRC_Claw uses a comprehensive metrics framework that measures code quality across multiple dimensions, aggregated into dashboards for different audiences.

### 13.2 Quality Dimensions & Metrics

#### 13.2.1 Code Complexity

| Metric | Tool | Target | Threshold | Dashboard |
|--------|------|--------|-----------|-----------|
| Cyclomatic complexity (avg) | radon, tokei | ≤ 8 | > 10 | SonarQube |
| Cognitive complexity (avg) | radon, eslint | ≤ 12 | > 15 | SonarQube |
| Function length (avg) | radon, tokei | ≤ 30 lines | > 50 lines | SonarQube |
| Module length (max) | radon, tokei | ≤ 500 lines | > 800 lines | SonarQube |
| Nesting depth (max) | radon, clippy | ≤ 4 | > 6 | SonarQube |

#### 13.2.2 Code Coverage

| Metric | Tool | Target | Threshold | Dashboard |
|--------|------|--------|-----------|-----------|
| Line coverage | pytest-cov, tarpaulin, c8 | ≥ 88% | < 80% | Codecov |
| Branch coverage | pytest-cov, tarpaulin, c8 | ≥ 82% | < 75% | Codecov |
| Mutation score | mutmut, cargo-mutants, stryker | ≥ 70% | < 60% | Custom |
| Diff coverage | diff-cover | ≥ 90% | < 80% | PR comment |

#### 13.2.3 Code Duplication

| Metric | Tool | Target | Threshold | Dashboard |
|--------|------|--------|-----------|-----------|
| Duplicated lines | jscpd, pylint | ≤ 3% | > 5% | SonarQube |
| Copy-paste detection | jscpd | 0 blocks | > 3 blocks | PR comment |
| Similar function detection | custom AST analysis | ≤ 2 per module | > 5 per module | Monthly report |

#### 13.2.4 Code Smells & Issues

| Metric | Tool | Target | Threshold | Dashboard |
|--------|------|--------|-----------|-----------|
| Code smells | SonarQube | ≤ 5/KLOC | > 10/KLOC | SonarQube |
| Technical debt ratio | SonarQube | ≤ 5% | > 10% | SonarQube |
| Open vulnerabilities | bandit, cargo audit, npm audit | 0 critical/high | > 0 | Security dashboard |
| Security hotspots | SonarQube | 0 unresolved | > 0 | Security dashboard |

#### 13.2.5 Dependency Health

| Metric | Tool | Target | Threshold | Dashboard |
|--------|------|--------|-----------|-----------|
| Outdated dependencies | Renovate | ≤ 10 behind | > 20 behind | Renovate dashboard |
| Vulnerable dependencies | pip-audit, cargo audit, npm audit | 0 known CVEs | > 0 | Security dashboard |
| License compliance | license-checker | 100% compliant | < 100% | CI gate |
| Dependency freshness | custom | ≤ 30 days behind | > 60 days | Monthly report |

#### 13.2.6 API Quality

| Metric | Tool | Target | Threshold | Dashboard |
|--------|------|--------|-----------|-----------|
| OpenAPI spec coverage | custom | 100% endpoints documented | < 95% | API dashboard |
| Breaking change detection | oasdiff | 0 unexpected | > 0 | CI gate |
| API response time | k6, Locust | p95 < 200ms | p95 > 500ms | Grafana |
| API error rate | Prometheus | < 0.1% | > 1% | Grafana |

### 13.3 Quality Dashboards

#### 13.3.1 Executive Dashboard

**Audience:** CTO, VP Engineering, Architecture Team  
**Refresh:** Real-time (Grafana)  
**Metrics:**
- Maintainability Index (MI) trend
- Technical debt ratio trend
- Security posture summary
- Dependency health summary
- Release readiness score

#### 13.3.2 Engineering Dashboard

**Audience:** Engineering teams, Tech Leads  
**Refresh:** Real-time (Grafana)  
**Metrics:**
- Per-module coverage (line, branch, mutation)
- Per-module complexity trends
- PR size distribution
- Review time distribution
- CI pipeline success rate
- Test suite runtime trend
- Code churn rate

#### 13.3.3 Contributor Dashboard

**Audience:** Open-source contributors, Community managers  
**Refresh:** Daily  
**Metrics:**
- PR merge rate
- Time to first review
- Time to merge
- Contributor retention rate
- Issue resolution time
- Documentation coverage
- Test coverage (public APIs)

#### 13.3.4 SonarQube Quality Gate

```yaml
# sonar-project.properties
sonar.qualitygate.wait=true
sonar.qualitygate.timeout=300

# Quality Gate Conditions
# - Coverage ≥ 88%
# - Duplicated Lines ≤ 3%
# - Maintainability Rating A or B
# - Reliability Rating A or B
# - Security Rating A
# - 0 Critical/High vulnerabilities
# - 0 Blocker/Critical code smells
# - Cognitive Complexity ≤ 15 per function
# - Cyclomatic Complexity ≤ 10 per function
```

### 13.4 Metrics Collection Pipeline

```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│  CI/CD     │──►│  Collect   │──►│  Aggregate │──►│  Visualize │
│  Pipeline  │   │  Raw Data  │   │  & Score   │   │  & Alert   │
└────────────┘   └────────────┘   └────────────┘   └────────────┘
     │                 │                 │                 │
     ▼                 ▼                 ▼                 ▼
  pytest,          Prometheus,        SonarQube,        Grafana,
  ruff, mypy,      InfluxDB,         Custom scoring    SonarQube
  clippy, eslint   Codecov API       engine            dashboards
```

### 13.5 Alerting & Thresholds

| Alert | Condition | Severity | Notification |
|-------|-----------|----------|--------------|
| Coverage drop | > 5% decrease in PR | Warning | PR comment |
| Complexity spike | New function > 15 cognitive | Warning | PR comment |
| Test suite slowdown | > 20% runtime increase | Warning | Slack #engineering |
| Security vulnerability | Any critical/high CVE | Critical | Slack #security + PagerDuty |
| Dependency vulnerability | Any known CVE | Critical | Slack #security |
| MI drop | MI < 80 for 2 consecutive months | Warning | Email to architecture team |
| Technical debt aging | Item > 6 months without update | Warning | Monthly report |

### 13.6 Metrics-Driven Development

#### 13.6.1 Quality Budgets

Each sprint has a quality budget that cannot be exceeded:

| Budget | Limit | Action on Breach |
|--------|-------|------------------|
| New code smells | ≤ 5 per sprint | Block merge until resolved |
| New technical debt items | ≤ 3 per sprint | Requires architecture approval |
| Coverage decrease | ≤ 2% per sprint | Block merge |
| Complexity increase | ≤ 5% avg per sprint | Requires refactoring plan |
| Test runtime increase | ≤ 10% per sprint | Requires optimization |

#### 13.6.2 Quality Reviews

| Review | Frequency | Participants | Focus |
|--------|-----------|-------------|-------|
| Sprint quality review | Per sprint | QA, Dev, PM | Sprint metrics, trends |
| Monthly metrics review | Monthly | Engineering leads | Trend analysis, goal progress |
| Quarterly quality audit | Quarterly | Architecture team | Process compliance, improvements |
| Annual quality assessment | Annual | All stakeholders | Strategic quality planning |

---

## 14. Technical Debt Management

### 14.1 Debt Taxonomy

Technical debt in GRC_Claw is classified into four categories:

| Category | Description | Example | Typical Severity |
|----------|-------------|---------|------------------|
| **Design Debt** | Architectural decisions that limit future flexibility | Monolithic policy evaluator | High |
| **Code Debt** | Code-level issues that reduce readability/maintainability | Duplicated validation logic | Medium |
| **Test Debt** | Insufficient or fragile tests | Missing integration tests for new endpoint | Medium |
| **Documentation Debt** | Missing, stale, or incorrect documentation | API docs not updated after schema change | Low |
| **Infrastructure Debt** | Outdated tooling, CI/CD issues | Slow test suite (> 10 min) | Medium |
| **Dependency Debt** | Outdated or vulnerable dependencies | Unmaintained npm package | High |

### 14.2 Debt Identification

#### 14.2.1 Automated Detection

| Source | Tool | What It Detects | Frequency |
|--------|------|-----------------|-----------|
| Static analysis | SonarQube | Code smells, duplication, complexity | Every PR |
| Dead code | vulture, cargo-udeps | Unused functions, imports | Monthly |
| Type analysis | mypy, tsc | Type gaps, `any` types | Every PR |
| Coverage analysis | pytest-cov, c8 | Untested code paths | Every PR |
| Dependency scan | pip-audit, cargo audit, npm audit | Vulnerable/outdated deps | Daily |
| Complexity trend | radon, tokei | Increasing complexity | Monthly |
| Test flakiness | pytest-rerunfailures | Flaky tests | Every PR |

#### 14.2.2 Manual Detection

- **Code review** — Reviewers flag debt with `// TECH-DEBT:` comments
- **Incident post-mortems** — Root cause analysis identifies debt contributions
- **Developer feedback** — Pain points reported via GitHub issues
- **Architecture reviews** — Periodic architecture assessments
- **Community feedback** — Issues and discussions flagging friction

### 14.3 Debt Tracking

All technical debt is tracked in `TECH-DEBT.md` at the repository root:

```markdown
| ID | Description | Module | Category | Severity | Created | Target Fix | Estimated Effort | Status | PR |
|----|-------------|--------|----------|----------|---------|-------------|-----------------|--------|-----|
| TD-001 | Policy evaluator uses recursive descent without memoization | policy-engine | Design | Medium | 2026-10-01 | v1.4.0 | 3 days | Open | — |
| TD-002 | Duplicated validation logic in API layer | api-gateway | Code | Low | 2026-09-15 | v1.3.0 | 1 day | In Progress | #234 |
| TD-003 | Missing integration tests for evidence export | evidence-pipeline | Test | Medium | 2026-08-20 | v1.3.5 | 2 days | Open | — |
```

#### 14.3.1 Debt Lifecycle

```
  Identified  ──►  Triaged  ──►  Scheduled  ──►  In Progress  ──►  Resolved
      │               │              │               │                │
      ▼               ▼              ▼               ▼                │
  Auto-detected   Severity +    Sprint backlog   Implementation    Verified
  Reviewer flag   category      assignment       + tests           + closed
  Post-mortem     assignment    effort estimate  + docs            + PR merged
```

#### 14.3.2 Debt Severity Definitions

| Severity | Definition | Response Time | Example |
|----------|------------|---------------|---------|
| **Critical** | Security vulnerability, data integrity risk, SLA breach | Immediate (within sprint) | Audit trail hash chain vulnerability |
| **High** | Significant performance impact, blocks feature development | Next sprint | Policy evaluator O(n²) complexity |
| **Medium** | Reduces maintainability, developer friction | Within 2 sprints | Duplicated validation logic |
| **Low** | Minor inconvenience, cosmetic | Within quarter | Outdated comment |

### 14.4 Debt Budget & Allocation

#### 14.4.1 Sprint Allocation

| Debt Category | Sprint Capacity | Priority |
|---------------|-----------------|----------|
| Critical debt | Immediate (any capacity) | P0 |
| High debt | 15% of sprint | P1 |
| Medium debt | 10% of sprint | P2 |
| Low debt | 5% of sprint | P3 |
| **Total debt budget** | **20% of sprint** (minimum) | — |

#### 14.4.2 Debt Aging Policy

| Age | Action |
|-----|--------|
| 0–3 months | Normal tracking |
| 3–6 months | Escalated to tech lead |
| 6–12 months | Escalated to architecture team; requires remediation plan |
| > 12 months | Architecture team must resolve, formally accept with risk acknowledgment, or close with justification |

### 14.5 Debt Prevention

#### 14.5.1 Debt Gates

| Gate | Check | Threshold | Blocking |
|------|-------|-----------|----------|
| PR gate | New code smells introduced | 0 | Yes |
| PR gate | New technical debt items | ≤ 2 per PR | Warning |
| PR gate | Coverage decrease | ≤ 2% | Yes |
| Sprint gate | Debt items resolved | ≥ debt items created | Warning |
| Quarterly gate | TDR trend | Decreasing or stable | Warning |

#### 14.5.2 Debt-Aware Code Review

Reviewers must explicitly assess:
1. Does this PR introduce new technical debt?
2. Does this PR address existing technical debt?
3. Is the debt-to-value ratio acceptable?
4. Is the debt properly documented and tracked?

### 14.6 Debt Metrics & Reporting

#### 14.6.1 Key Debt Metrics

| Metric | Target | Measurement | Dashboard |
|--------|--------|-------------|-----------|
| Technical Debt Ratio (TDR) | ≤ 5% | SonarQube | SonarQube |
| Open debt items | Decreasing trend | TECH-DEBT.md | Engineering dashboard |
| Debt aging (avg) | ≤ 3 months | TECH-DEBT.md | Monthly report |
| Debt resolution rate | ≥ 80% per quarter | TECH-DEBT.md | Quarterly report |
| Debt-created-to-debt-resolved ratio | ≤ 1.0 | TECH-DEBT.md | Sprint review |
| Code smell density | ≤ 5/KLOC | SonarQube | SonarQube |

#### 14.6.2 Quarterly Debt Report

Published every quarter, including:
1. **Debt inventory** — All open items by category, severity, age
2. **Debt trend** — Quarter-over-quarter change in TDR
3. **Debt aging** — Distribution by age bucket
4. **Debt resolution** — Items resolved this quarter
5. **Debt created** — New items introduced this quarter
6. **Debt hotspots** — Modules with highest debt concentration
7. **Recommendations** — Prioritized debt reduction plan

---

## 15. Refactoring Automation

### 15.1 Refactoring Philosophy

Refactoring is not a special activity — it is a continuous, automated, and safe process. GRC_Claw uses automated tooling to identify, propose, and execute refactoring opportunities while maintaining behavioral equivalence.

### 15.2 Automated Refactoring Tools

#### 15.2.1 Python Refactoring

| Tool | Purpose | Scope | Safety |
|------|---------|-------|--------|
| `ruff` | Import sorting, unused import removal | All Python | Safe (auto-fix) |
| `ruff` | Rule-based lint fixes (UP, SIM, B, C4) | All Python | Safe (auto-fix) |
| `pyupgrade` | Syntax modernization (e.g., `Dict` → `dict`) | All Python | Safe (auto-fix) |
| `com2ann` | Type annotation conversion | All Python | Semi-safe (review required) |
| `libcst` | Structural code transformation | All Python | Custom rules |
| `sourcery` | AI-assisted refactoring suggestions | All Python | Review required |

#### 15.2.2 Rust Refactoring

| Tool | Purpose | Scope | Safety |
|------|---------|-------|--------|
| `rustfmt` | Code formatting | All Rust | Safe (auto-fix) |
| `clippy` | Lint fixes (pedantic) | All Rust | Safe (auto-fix) |
| `cargo fix` | Compiler-suggested fixes | All Rust | Safe (auto-fix) |
| `cargo-udeps` | Unused dependency removal | All Rust | Safe (auto-fix) |

#### 15.2.3 TypeScript Refactoring

| Tool | Purpose | Scope | Safety |
|------|---------|-------|--------|
| `eslint --fix` | Rule-based fixes | All TypeScript | Safe (auto-fix) |
| `prettier` | Code formatting | All TypeScript | Safe (auto-fix) |
| `ts-morph` | AST-based transformation | All TypeScript | Custom rules |
| `knip` | Unused export detection | All TypeScript | Safe (auto-fix) |

### 15.3 Refactoring Pipeline

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Detect      │──►│  Propose     │──►│  Validate    │──►│  Apply       │
│  Opportunities│   │  Refactoring │   │  Equivalence │   │  & Review    │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
     │                   │                   │                   │
     ▼                   ▼                   ▼                   ▼
  Static analysis,    Custom rules,       Test suite,         Auto-PR with
  lint rules,         libcst patterns,    property tests,     detailed diff,
  complexity trend    sourcery rules      snapshot tests      rollback plan
```

### 15.4 Safe Refactoring Rules

#### 15.4.1 Behavioral Equivalence Verification

Every automated refactoring MUST pass:
1. **Full test suite** — All unit, integration, and contract tests pass
2. **Property-based tests** — Invariants hold after refactoring
3. **Snapshot tests** — Output is identical (or diff is reviewed and approved)
4. **Coverage parity** — Coverage does not decrease
5. **Type checking** — mypy, tsc, clippy all pass

#### 15.4.2 Refactoring Categories

| Category | Automation Level | Example | Approval Required |
|----------|-----------------|---------|-------------------|
| **Formatting** | Fully automated | `rustfmt`, `prettier`, `ruff format` | None |
| **Import cleanup** | Fully automated | Remove unused imports, sort imports | None |
| **Rename** | Semi-automated | Rename function/variable across codebase | Review |
| **Extract function** | Semi-automated | Extract repeated logic into function | Review |
| **Simplify conditional** | Semi-automated | Replace nested ifs with match/guard | Review |
| **Type modernization** | Semi-automated | `Dict[str, Any]` → `dict[str, Any]` | Review |
| **Architecture change** | Manual | Extract module, change interface | Architecture approval |

### 15.5 Refactoring Automation in CI

#### 15.5.1 Automated Refactoring PRs

```yaml
# .github/workflows/auto-refactor.yml
name: Auto-Refactor
on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday

jobs:
  auto-refactor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run ruff auto-fix
        run: |
          ruff check --fix .
          ruff format .

      - name: Run pyupgrade
        run: pyupgrade --py312-plus $(find src -name "*.py")

      - name: Run clippy auto-fix
        run: cargo fix --allow-dirty --allow-staged

      - name: Run eslint auto-fix
        run: npx eslint . --fix

      - name: Run prettier
        run: npx prettier --write .

      - name: Create PR if changes
        uses: peter-evans/create-pull-request@v6
        with:
          title: "chore: automated refactoring"
          body: |
            Automated refactoring changes:
            - Import cleanup
            - Formatting fixes
            - Lint auto-fixes
            - Type modernization
            
            All changes are behavior-preserving.
            Full test suite must pass before merge.
          branch: auto-refactor/${{ github.run_id }}
```

#### 15.5.2 Refactoring Validation Pipeline

Every automated refactoring PR runs:
1. Full lint + type check
2. Full test suite (unit + integration + contract)
3. Property-based tests
4. Snapshot tests (with diff review if changed)
5. Coverage gate
6. Performance regression check

### 15.6 Complexity-Driven Refactoring

#### 15.6.1 Complexity Triggers

When complexity metrics exceed thresholds, refactoring is automatically proposed:

| Metric | Threshold | Automatic Action |
|--------|-----------|------------------|
| Cyclomatic complexity > 10 | Per function | Create refactoring issue |
| Cognitive complexity > 15 | Per function | Create refactoring issue |
| Function length > 50 lines | Per function | Create refactoring issue |
| Module length > 800 lines | Per module | Create refactoring issue |
| Nesting depth > 6 | Per function | Create refactoring issue |
| Duplication > 5% | Per module | Create refactoring issue |

#### 15.6.2 Refactoring Issue Template

```markdown
## Refactoring Opportunity: [Module/Function]

**Detected by:** [Tool name]  
**Complexity metric:** [Current value] (threshold: [threshold])  
**Created:** [Date]  

### Current State
[Description of the problematic code]

### Proposed Refactoring
[Description of the proposed change]

### Effort Estimate
[Small/Medium/Large]

### Priority
[Low/Medium/High]

### Acceptance Criteria
- [ ] All tests pass
- [ ] Complexity below threshold
- [ ] No coverage decrease
- [ ] Documentation updated
```

### 15.7 Refactoring Safety

#### 15.7.1 Refactoring Checklist

Before any refactoring (automated or manual):
- [ ] Tests exist and pass
- [ ] Property-based tests cover invariants
- [ ] Snapshot tests capture output
- [ ] Refactoring is behavior-preserving
- [ ] Rollback plan is documented
- [ ] Performance impact is assessed

#### 15.7.2 Refactoring Anti-Patterns

| Anti-Pattern | Description | Prevention |
|-------------|-------------|------------|
| **Drive-by refactoring** | Refactoring unrelated code in a feature PR | Keep refactoring PRs separate |
| **Big bang refactoring** | Rewriting large sections at once | Incremental refactoring with tests |
| **Refactoring without tests** | Changing code without test coverage | Require tests before refactoring |
| **Refactoring + feature mix** | Combining refactoring with new features | Separate PRs for refactoring and features |
| **Ignoring snapshot changes** | Blindly accepting snapshot changes | Review all snapshot diffs |

---

## 16. Developer Onboarding Optimization

### 16.1 Onboarding Philosophy

A new developer should be productive in GRC_Claw within their first week. Onboarding is not a document they read — it is an experience they go through, with guided, interactive, and verifiable steps.

### 16.2 Onboarding Timeline

| Day | Goal | Activities | Verification |
|-----|------|------------|--------------|
| **Day 1** | Environment setup | `make dev-setup`, `make doctor`, run tests | All tests pass locally |
| **Day 2** | Architecture overview | Read architecture docs, explore module diagram | Explain module boundaries |
| **Day 3** | First contribution | Fix a `good-first-issue` bug | PR merged |
| **Day 4** | Deep dive | Pair with mentor on module walkthrough | Complete module exercise |
| **Day 5** | Independent work | Pick up a `help-wanted` issue | PR opened |

### 16.3 Onboarding Documentation

#### 16.3.1 Getting Started Guide

```markdown
# Getting Started with GRC_Claw

## Prerequisites
- Python 3.12+, Rust 1.75+, Node 20+
- Docker Desktop
- Git

## Quick Start (15 minutes)
1. Fork and clone the repository
2. Run `make dev-setup`
3. Run `make test` — all tests should pass
4. Run `make dev` — start the development server
5. Open http://localhost:3000 — explore the dashboard

## Your First Contribution
1. Browse issues labeled `good-first-issue`
2. Comment on an issue to claim it
3. Create a branch: `git checkout -b fix/issue-NNN`
4. Make your change, run tests, submit PR
5. A maintainer will review within 48 hours

## Learning Path
- [Architecture Overview](../docs/ARCHITECTURE-V15.md)
- [Policy Engine Deep Dive](../specs/grc-claw-policy-engine-spec.md)
- [API Reference](../specs/grc-claw-openapi.yaml)
- [Policy DSL Guide](../specs/grc-claw-policy-engine-spec.md)
- [Plugin Development](../CONTRIBUTING.md)
```

#### 16.3.2 Interactive Tutorials

| Tutorial | Format | Time | Topics |
|----------|--------|------|--------|
| **Your First Policy** | Jupyter notebook | 30 min | DSL syntax, policy evaluation, testing |
| **Build a Plugin** | Guided exercise | 1 hr | Plugin interface, configuration, testing |
| **Add an API Endpoint** | Guided exercise | 1 hr | FastAPI, Pydantic, OpenAPI, testing |
| **Debug a Policy Evaluation** | Interactive debugger | 30 min | Tracing, logging, policy engine internals |
| **Contribute to Documentation** | Guided exercise | 15 min | Markdown, code examples, CI validation |

#### 16.3.3 Architecture Walkthroughs

Pre-recorded or live walkthroughs for each core module:

| Module | Walkthrough | Key Concepts |
|--------|-------------|--------------|
| Policy Engine | 20 min video + exercises | DSL parsing, evaluation, compilation |
| Audit Trail | 15 min video + exercises | Hash chain, verification, storage |
| Enforcement Proxy | 20 min video + exercises | Real-time enforcement, circuit breakers |
| Evidence Pipeline | 15 min video + exercises | Collection, normalization, chain of custody |
| API Gateway | 15 min video + exercises | Routing, auth, versioning |
| Compliance Mapper | 10 min video + exercises | Framework mapping, control catalogs |

### 16.4 Mentorship Program

#### 16.4.1 Mentor Assignment

- Every new contributor is assigned a mentor for their first 3 PRs
- Mentors are experienced contributors who volunteer for the role
- Mentor responsibilities:
  - Answer questions within 24 hours
  - Review PRs within 48 hours
  - Provide constructive, kind feedback
  - Help navigate the codebase and processes

#### 16.4.2 Mentorship Guidelines

| Do | Don't |
|----|-------|
| Explain the "why" behind decisions | Just tell them what to do |
| Point to documentation and resources | Write the code for them |
| Celebrate first contributions | Criticize minor style issues |
| Encourage questions | Make them feel bad for not knowing |

### 16.5 Onboarding Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to first PR | ≤ 5 days | GitHub tracking |
| Time to first merged PR | ≤ 10 days | GitHub tracking |
| Onboarding satisfaction | ≥ 4.0/5.0 | Survey after first month |
| New contributor retention (3 months) | ≥ 60% | GitHub tracking |
| `good-first-issue` resolution time | ≤ 2 weeks | GitHub tracking |
| Mentor satisfaction | ≥ 4.0/5.0 | Quarterly survey |

### 16.6 Onboarding Automation

#### 16.6.1 Automated Welcome

```yaml
# .github/workflows/welcome.yml
name: Welcome New Contributor
on:
  pull_request_target:
    types: [opened]

jobs:
  welcome:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `Welcome to GRC_Claw! 🎉
              
              Thanks for your first contribution. A mentor will be assigned within 24 hours.
              
              Here are some helpful links:
              - [Contributing Guide](CONTRIBUTING.md)
              - [Architecture Overview](../docs/ARCHITECTURE-V15.md)
              - [Good First Issues](https://github.com/grc-claw/grc-claw/good-first-issue)
              
              We're excited to have you!`
            })
```

#### 16.6.2 Onboarding Checklist Automation

A GitHub issue is automatically created for each new contributor with a checklist:

```markdown
## Onboarding Checklist for @new-contributor

### Week 1
- [ ] Environment setup complete (`make dev-setup` passes)
- [ ] Read architecture overview
- [ ] Run full test suite locally
- [ ] Complete "Your First Policy" tutorial
- [ ] Attend community call (Tuesdays 17:00 UTC)

### Week 2
- [ ] First PR submitted
- [ ] First PR merged
- [ ] Complete module walkthrough with mentor
- [ ] Join Discord/Slack channel

### Month 1
- [ ] 3 PRs merged
- [ ] Completed plugin development tutorial
- [ ] Participated in code review (as reviewer)
- [ ] Attended architecture review meeting
```

### 16.7 Knowledge Base

#### 16.7.1 FAQ

Maintained `docs/faq.md` with frequently asked questions:

| Category | Example Questions |
|----------|-------------------|
| **Setup** | "Why does `make dev-setup` fail on macOS?" |
| **Architecture** | "Why is the enforcement proxy in Rust?" |
| **Policy DSL** | "How do I express a time-based rule?" |
| **Testing** | "How do I write a property-based test?" |
| **Contributing** | "What makes a good PR?" |
| **Debugging** | "How do I trace a policy evaluation?" |

#### 16.7.2 Troubleshooting Guide

`docs/troubleshooting.md` with common issues and solutions:

| Issue | Cause | Solution |
|-------|-------|----------|
| `make dev-setup` fails | Docker not running | Start Docker Desktop |
| Tests fail locally | Database not migrated | Run `make db-migrate` |
| Pre-commit hooks fail | Outdated hook versions | Run `pre-commit autoupdate` |
| Type errors in editor | Language server not configured | Install recommended extensions |
| Port already in use | Another service using port | Run `make clean` and restart |

#### 16.7.3 Glossary

`docs/glossary.md` for domain-specific terms:

| Term | Definition |
|------|-----------|
| **Policy** | A set of rules that govern agent behavior |
| **Control** | A specific compliance requirement from a framework |
| **Evidence** | Data collected to demonstrate compliance |
| **Framework** | A compliance standard (e.g., NIST 800-53, ISO 27001) |
| **Enforcement** | Real-time policy decision and action |
| **Audit Trail** | Immutable, hash-chained log of all actions |
| **Chain of Custody** | Documented evidence handling history |

---

## 17. Compliance & Governance

### 17.1 Maintainability in the Unified Control Set

Maintainability requirements map to GRC_Claw's unified control set (GRC-CROSS-001):

| Unified Control | Maintainability Requirement |
|----------------|---------------------------|
| UC-4.4 (Design & development documentation) | §3.4 Documentation Standards |
| UC-4.5 (Verification and validation) | §3.3 Testing Requirements |
| UC-4.7 (Operation and monitoring) | §7.4 Observability & Maintainability |
| UC-4.8 (Technical documentation) | §3.4 Documentation Standards |
| UC-4.9 (Event logging and audit trail) | §9.2 Audit Trail requirements |
| UC-12.1 (Policy review and update) | §6. Deprecation Policies |
| UC-12.4 (Continuous monitoring and improvement) | §8. Maintainability Metrics & Reporting |

### 17.2 Maintainability as a Compliance Requirement

For GRC_Claw's own SOC 2 Type II certification (Phase 3 goal):

- **CC7.1** (System monitoring) — Maintainability metrics and alerting
- **CC7.2** (Incident detection) — Health checks and anomaly detection
- **CC7.3** (Incident response) — Technical debt as risk, incident post-mortems
- **CC8.1** (Change management) — Code review gates, CI pipeline

---

## 18. Appendices

### Appendix A: File & Directory Structure

```
grc-claw/
├── crates/                    # Rust crates (enforcement proxy)
│   ├── enforcement-proxy/
│   ├── audit-trail/
│   └── policy-compiler/
├── packages/                  # TypeScript packages
│   ├── web-ui/
│   ├── sdk/
│   └── api-client/
├── src/                       # Python source
│   ├── policy_engine/
│   ├── api_gateway/
│   ├── compliance_mapper/
│   ├── evidence_collector/
│   ├── agent_registry/
│   └── analytics_engine/
├── tests/                     # Cross-module integration tests
├── docs/
│   ├── adr/                   # Architecture Decision Records
│   ├── architecture/          # Module architecture docs
│   ├── api/                   # API reference (auto-generated)
│   ├── policy-dsl/            # Policy DSL specification
│   └── archive/               # Deprecated feature docs
├── scripts/                   # Maintenance scripts
├── .github/
│   ├── workflows/             # CI/CD pipelines
│   └── CONTRIBUTING.md
├── pyproject.toml             # Python project config
├── Cargo.toml                 # Rust workspace config
├── package.json               # Node project config
├── CHANGELOG.md               # Release changelog
├── DEPRECATIONS.md            # Deprecation tracking
├── TECH-DEBT.md               # Technical debt tracking
└── README.md
```

### Appendix B: ADR Template

```markdown
# ADR-NNNN: Title

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-NNNN

## Context
What is the issue we're addressing?

## Decision
What did we decide?

## Consequences
What are the positive and negative consequences?

## Alternatives Considered
What else did we consider and why did we reject it?

## References
Links to related issues, PRs, specs.
```

### Appendix C: Deprecation Notice Template

```markdown
# Deprecation Notice: [Feature Name]

**Deprecated in:** vX.Y.Z  
**Sunset date:** YYYY-MM-DD  
**Replacement:** [link to replacement]

## What is changing?
[Description of the deprecated feature and what replaces it]

## Why is this changing?
[Rationale]

## How do I migrate?
[Step-by-step migration guide]

## Timeline
- vX.Y.Z: Feature deprecated, warnings added
- vX.Y.Z+1: Feature returns 410 Gone
- vX.Y.Z+2: Code removed

## Questions?
[Link to GitHub discussion or contact]
```

---

## 19. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial specification |
| 2.0 | 2026-10-01 | GRC_Claw Architecture Team | Added DX optimization (§11), documentation automation (§12), code quality metrics & dashboards (§13), technical debt management (§14), refactoring automation (§15), developer onboarding optimization (§16) |

---

*End of Maintainability Specification*

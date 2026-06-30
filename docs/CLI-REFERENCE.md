# GRC_Claw CLI Reference

> **Version:** v16.0 | **Last Updated:** 2026-06-30

Complete reference for the `grc` command-line interface — 27 commands covering compliance scanning, evidence management, framework crosswalking, agent automation, sovereign deployment, marketplace operations, and procurement workflows.

---

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [Environment Variables](#environment-variables)
- [Configuration File (grcfile.yaml)](#configuration-file-grcfileyaml)
- [Exit Codes](#exit-codes)
- [Shell Completion](#shell-completion)
- [Commands](#commands)
  - [grc init](#grc-init)
  - [grc scan .](#grc-scan-)
  - [grc plan](#grc-plan)
  - [grc apply](#grc-apply)
  - [grc audit](#grc-audit)
  - [grc status](#grc-status)
  - [grc drift](#grc-drift)
  - [grc diff](#grc-diff)
  - [grc report](#grc-report)
  - [grc doctor](#grc-doctor)
  - [grc iac-scan .](#grc-iac-scan-)
  - [grc pqc-scan .](#grc-pqc-scan-)
  - [grc ai-bom generate](#grc-ai-bom-generate)
  - [grc ai-bom publish](#grc-ai-bom-publish)
  - [grc frameworks list](#grc-frameworks-list)
  - [grc agent run](#grc-agent-run)
  - [grc sovereign init](#grc-sovereign-init)
  - [grc version](#grc-version)
  - [grc marketplace list](#grc-marketplace-list)
  - [grc marketplace install](#grc-marketplace-install)
  - [grc marketplace publish](#grc-marketplace-publish)
  - [grc evidence list](#grc-evidence-list)
  - [grc evidence verify](#grc-evidence-verify)
  - [grc trust score](#grc-trust-score)
  - [grc verifier room](#grc-verifier-room)
  - [grc benchmark compare](#grc-benchmark-compare)
  - [grc procurement packet](#grc-procurement-packet)

---

## Installation

### npm (recommended)

```bash
npm install -g @grc-claw/cli
```

### Homebrew (macOS / Linux)

```bash
brew tap a2zsoc/grc https://github.com/AAH20/GRC_Claw
brew install grc-claw
```

### From source

```bash
git clone https://github.com/AAH20/GRC_Claw
cd GRC_Claw && npm install && npm run build
```

### Verify installation

```bash
grc version
```

---

## Global Options

These options apply to all `grc` commands.

| Option | Default | Description |
|--------|---------|-------------|
| `--json` | `false` | Output results as JSON |
| `--quiet`, `-q` | `false` | Suppress non-essential output |
| `--verbose`, `-v` | `false` | Enable verbose logging |
| `--config <path>` | `./grcfile.yaml` | Path to configuration file |
| `--output <path>` | stdout | Write output to file |
| `--format <fmt>` | `table` | Output format: `json`, `table`, `csv`, `yaml` |
| `--no-color` | `false` | Disable colored output |
| `--api-key <key>` | — | Override API key (env: `GRC_CLAW_API_KEY`) |
| `--tenant <id>` | — | Override tenant (env: `GRC_CLAW_TENANT`) |
| `--environment <env>` | `production` | Target environment: `production`, `staging`, `development` |

**Examples:**

```bash
grc scan . --json --quiet
grc report --format yaml --output report.yaml
grc audit --verbose --config custom-grcfile.yaml
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GRC_CLAW_API_KEY` | API key for A2Z SOC authentication | — |
| `GRC_CLAW_TENANT` | Default tenant ID | — |
| `GRC_SOVEREIGN_URL` | Sovereign stack base URL | `http://localhost:3000` |
| `SOVEREIGN_MODE` | Route all LLM traffic through local Ollama (`true`/`false`) | `false` |
| `GRC_LLM_PROVIDER` | LLM provider: `openai`, `anthropic`, `ollama` | `openai` |
| `GRC_LLM_MODEL` | Model override | — |
| `GRC_LOG_LEVEL` | Log level: `debug`, `info`, `warn`, `error` | `info` |
| `GRC_EVIDENCE_DIR` | Local evidence storage directory | `.grc/evidence` |
| `A2Z_SOC_BASE_URL` | A2Z SOC platform base URL | `https://a2zsoc.com` |
| `NO_COLOR` | Disable colored output when set | — |

---

## Configuration File (grcfile.yaml)

The `grcfile.yaml` defines project-level settings, framework scope, and tool preferences.

```yaml
# grcfile.yaml — GRC_Claw project configuration
version: "1.0"
project: "my-project"
frameworks:
  - soc2
  - iso27001
  - nist-csf
scan:
  paths:
    - .
    - ./src
    - ./infra
  exclude:
    - node_modules
    - .git
    - dist
iac:
  paths:
    - ./terraform
    - ./kubernetes
  rules:
    - encryption-at-rest
    - public-access
    - logging
pqc:
  paths:
    - ./src
  patterns:
    - rsa
    - ecdsa
    - aes-cbc
ai-bom:
  output: ./ai-bom.json
  frameworks:
    - eu-ai-act
    - iso-42001
agent:
  trust-threshold: 80
  auto-pause: true
  approval-required:
    - deploy
    - delete
    - production-write
evidence:
  dir: .grc/evidence
  hash-chain: true
  rfc3161-timestamp: true
connectors:
  github:
    enabled: true
  okta:
    enabled: true
  jira:
    enabled: false
marketplace:
  registry: "https://marketplace.grc-claw.com"
```

### Configuration fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Config schema version (`"1.0"`) |
| `project` | string | Project name identifier |
| `frameworks` | list | Compliance frameworks to evaluate |
| `scan.paths` | list | Directories to scan |
| `scan.exclude` | list | Glob patterns to exclude |
| `iac.paths` | list | IaC directories to scan |
| `iac.rules` | list | IaC compliance rules to apply |
| `pqc.paths` | list | Directories to scan for PQC migration |
| `pqc.patterns` | list | Cryptographic patterns to detect |
| `ai-bom.output` | string | AI BOM output file path |
| `ai-bom.frameworks` | list | Frameworks for AI BOM alignment |
| `agent.trust-threshold` | int | Minimum trust score (0-100) before auto-pause |
| `agent.auto-pause` | bool | Auto-pause agent when trust score drops |
| `evidence.dir` | string | Local evidence directory |
| `evidence.hash-chain` | bool | Enable SHA-256 hash chaining |
| `evidence.rfc3161-timestamp` | bool | Enable RFC 3161 timestamping |
| `connectors.<name>.enabled` | bool | Toggle connector |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error or command failure |
| `2` | Invalid arguments or usage error |
| `3` | Configuration file not found or invalid |
| `4` | Network or API connection error |
| `5` | Authentication failure |
| `6` | Scan found compliance violations (severity: high/critical) |
| `7` | Drift detected from baseline |
| `8` | Evidence integrity verification failed |
| `9` | Agent trust score below threshold (auto-paused) |

---

## Shell Completion

Enable tab completion for your shell.

### Bash

```bash
grc completion bash > /etc/bash_completion.d/grc
# or
source <(grc completion bash)
```

### Zsh

```bash
grc completion zsh > "${fpath[1]}/_grc"
# or
source <(grc completion zsh)
```

### Fish

```bash
grc completion fish > ~/.config/fish/completions/grc.fish
```

### PowerShell

```powershell
grc completion powershell > grc.ps1
# then dot-source or add to your profile
```

---

## Commands

---

### `grc init`

**Syntax:**

```bash
grc init [options]
```

**Description:**

Scaffold a `grcfile.yaml` configuration file and a GitHub Actions compliance workflow (`.github/workflows/grc-scan.yml`) in the current directory. Detects existing project structure to pre-populate framework and scan paths.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--frameworks <list>` | `soc2,iso27001` | Comma-separated list of frameworks to enable |
| `--github-actions` | `true` | Generate GitHub Actions workflow |
| `--force` | `false` | Overwrite existing grcfile.yaml |

**Examples:**

```bash
# Initialize with defaults
grc init

# Initialize with specific frameworks
grc init --frameworks soc2,nist-csf,cmmc

# Force overwrite existing config
grc init --force
```

**Output format:**

```
✓ Created grcfile.yaml
✓ Created .github/workflows/grc-scan.yml
  Frameworks: soc2, iso27001
  Scan paths: ./src, ./lib
```

**Related commands:** `grc scan .`, `grc doctor`, `grc frameworks list`

---

### `grc scan .`

**Syntax:**

```bash
grc scan <path> [options]
```

**Description:**

Scan a codebase for compliance violations across 12 built-in rules. Produces a posture score (0-100) and maps findings to framework control IDs (SOC 2, ISO 27001, NIST CSF, etc.).

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--framework <fw>` | all in `grcfile.yaml` | Target specific framework |
| `--severity <level>` | `all` | Filter by severity: `low`, `medium`, `high`, `critical` |
| `--rules <list>` | all 12 | Comma-separated rule IDs to run |
| `--fix` | `false` | Suggest auto-remediation commands |
| `--output <path>` | stdout | Write results to file |

**Scan rules (12):**

| # | Rule | Maps to |
|---|------|---------|
| 1 | Hardcoded secrets detection | SOC 2 CC6.1 |
| 2 | Logging compliance | SOC 2 CC7.2 |
| 3 | Encryption at rest | SOC 2 CC6.7, ISO 27001 A.10.1 |
| 4 | Access control patterns | SOC 2 CC6.1, ISO 27001 A.9 |
| 5 | Audit trail integrity | SOC 2 CC7.2, ISO 27001 A.12.4 |
| 6 | Error handling patterns | SOC 2 CC7.3 |
| 7 | Input validation | ISO 27001 A.14.2 |
| 8 | Transport security (TLS) | SOC 2 CC6.1, NIST SC-8 |
| 9 | Dependency vulnerability patterns | SOC 2 CC6.1 |
| 10 | Configuration file exposure | SOC 2 CC6.1 |
| 11 | Race condition patterns | ISO 27001 A.14.2 |
| 12 | Hardcoded credentials in config | SOC 2 CC6.1 |

**Examples:**

```bash
# Scan current directory
grc scan .

# Scan specific directory with framework filter
grc scan ./src --framework soc2

# Scan with JSON output and severity filter
grc scan . --json --severity high
```

**Output format:**

```
┌─────────────────────────────────────────┐
│  Compliance Scan Results                │
│  Posture Score: 72/100                  │
│  Findings: 14 (3 high, 5 medium, 6 low)│
└─────────────────────────────────────────┘

FINDINGS:

  [HIGH] SEC-001: Hardcoded API key in src/config.ts:42
    Control: SOC 2 CC6.1 | Rule: secrets-detection
    Fix: Use environment variables or Vault

  [MED]  LOG-003: Missing structured logging in src/api/handler.ts
    Control: SOC 2 CC7.2 | Rule: logging-compliance
    Fix: Add structured JSON logger

  ...
```

**Related commands:** `grc plan`, `grc iac-scan .`, `grc pqc-scan .`

---

### `grc plan`

**Syntax:**

```bash
grc plan [options]
```

**Description:**

Generate a prioritized compliance remediation plan based on scan findings. Produces a step-by-step action plan with control mappings, estimated effort, and risk reduction impact.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--framework <fw>` | all | Filter plan by framework |
| `--priority <level>` | `all` | Filter by priority: `critical`, `high`, `medium`, `low` |
| `--effort <level>` | `all` | Filter by effort: `quick-win`, `moderate`, `significant` |
| `--output <path>` | stdout | Write plan to file |

**Examples:**

```bash
# Generate plan from latest scan
grc plan

# Plan for SOC 2 only, critical priority
grc plan --framework soc2 --priority critical

# Export plan as JSON
grc plan --json --output plan.json
```

**Output format:**

```
Compliance Remediation Plan
━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority 1 (Critical):
  1. Remove hardcoded secrets from src/config.ts
     Control: CC6.1 | Effort: quick-win | Risk Reduction: 15%
     Run: grc apply --task SEC-001

  2. Enable TLS enforcement in nginx.conf
     Control: CC6.1 | Effort: moderate | Risk Reduction: 10%
     Run: grc apply --task NET-002

Priority 2 (High):
  ...

Estimated total risk reduction: 42%
Estimated total effort: 8 hours
```

**Related commands:** `grc scan .`, `grc apply`

---

### `grc apply`

**Syntax:**

```bash
grc apply [options]
```

**Description:**

Apply remediation actions from a compliance plan to the local project. Executes safe changes automatically and flags manual steps for user approval.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--task <id>` | all | Apply a specific task ID |
| `--dry-run` | `false` | Preview changes without applying |
| `--auto-approve` | `false` | Skip confirmation prompts |
| `--plan <path>` | `.grc/plan.json` | Path to plan file |

**Examples:**

```bash
# Apply all remediations
grc apply

# Preview changes without applying
grc apply --dry-run

# Apply specific task
grc apply --task SEC-001
```

**Output format:**

```
Applying remediation plan...

  [✓] SEC-001: Created .env.example with placeholder for API key
  [✓] SEC-003: Added .gitignore rule for .env files
  [!] NET-002: Manual action required — update nginx.conf TLS settings
  [✓] LOG-003: Added structured logger to src/api/handler.ts

Applied: 3 auto | 1 manual | 0 skipped
Run `grc audit` to verify changes.
```

**Related commands:** `grc plan`, `grc audit`

---

### `grc audit`

**Syntax:**

```bash
grc audit [options]
```

**Description:**

Run a full compliance audit across all configured frameworks. Collects evidence, evaluates controls, generates trust scores, and produces an audit-ready report with evidence lineage.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--framework <fw>` | all | Audit specific framework |
| `--evidence-dir <path>` | `.grc/evidence` | Evidence storage directory |
| `--format <fmt>` | `table` | Output format: `json`, `table`, `pdf` |
| `--output <path>` | stdout | Write report to file |
| `--include-agent-actions` | `false` | Include agent action receipts in audit |

**Examples:**

```bash
# Full audit across all frameworks
grc audit

# SOC 2 audit with JSON output
grc audit --framework soc2 --json

# Audit including agent actions, export to PDF
grc audit --include-agent-actions --format pdf --output audit-report.pdf
```

**Output format:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Compliance Audit Report
  Project: my-project | Date: 2026-06-30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Framework: SOC 2 Type II
  Controls Evaluated: 42
  Passed: 34 (81%)
  Partial: 5 (12%)
  Failed: 3 (7%)
  Trust Score: 76/100

Framework: ISO 27001
  Controls Evaluated: 93
  Passed: 78 (84%)
  Partial: 11 (12%)
  Failed: 4 (4%)
  Trust Score: 81/100

Evidence Collected: 147 artifacts
Evidence Integrity: SHA-256 hash chain verified
Timestamp: RFC 3161 (FreeTSA.org)

Failed Controls:
  CC6.1 — No MFA enforcement on admin panel
  CC8.1 — Missing change management documentation
  A.12.4 — Audit log retention < 90 days
```

**Related commands:** `grc status`, `grc report`, `grc trust score`

---

### `grc status`

**Syntax:**

```bash
grc status [options]
```

**Description:**

Display current compliance posture across all configured frameworks. Shows posture score, control coverage, evidence freshness, and active drift status.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--framework <fw>` | all | Filter by framework |
| `--compact` | `false` | Show compact single-line summary |

**Examples:**

```bash
# Full status
grc status

# Compact status for CI
grc status --compact

# SOC 2 status only
grc status --framework soc2 --json
```

**Output format:**

```
Compliance Posture — my-project
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  SOC 2:     72/100  ████████████████░░░░  81% controls passing
  ISO 27001: 81/100  ██████████████████░░  84% controls passing
  NIST CSF:  68/100  ███████████████░░░░░  76% controls passing

  Overall:   74/100

  Evidence:  147 artifacts | Last collected: 2h ago
  Drift:     2 changes detected since last baseline
  Agent:     Trust score 85/100 | Status: active
```

**Related commands:** `grc audit`, `grc drift`, `grc trust score`

---

### `grc drift`

**Syntax:**

```bash
grc drift [options]
```

**Description:**

Detect compliance drift from the last established baseline. Compares current control state, evidence freshness, and configuration against the baseline and reports changes with severity scoring.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--baseline <ref>` | latest | Git ref or timestamp for baseline |
| `--framework <fw>` | all | Filter by framework |
| `--severity <level>` | `all` | Filter by severity |
| `--fix` | `false` | Suggest remediation for drift |

**Examples:**

```bash
# Check drift from latest baseline
grc drift

# Drift against a specific git commit
grc drift --baseline abc1234

# Drift with severity filter
grc drift --severity high --fix
```

**Output format:**

```
Compliance Drift Report
━━━━━━━━━━━━━━━━━━━━━━━

  Baseline: 2026-06-28T10:00:00Z (abc1234)
  Current:  2026-06-30T14:30:00Z

  Drifts Detected: 2

  [HIGH] src/config.ts:42 — Secret pattern reintroduced
    Control: CC6.1 | Severity: high
    Drift: Baseline clean → Current violation

  [MED]  terraform/s3.tf:18 — Public bucket ACL re-enabled
    Control: CC6.7 | Severity: medium
    Drift: Baseline private → Current public

  Run `grc apply --task DRIFT-001` to remediate.
```

**Related commands:** `grc status`, `grc scan .`, `grc plan`

---

### `grc diff`

**Syntax:**

```bash
grc diff [options]
```

**Description:**

Crosswalk delta between two git refs or between two compliance frameworks. Shows control coverage changes, mapping differences, and evidence impact across the diff.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--from <ref>` | previous commit | Source git ref |
| `--to <ref>` | HEAD | Target git ref |
| `--framework <fw>` | all | Filter by framework |
| `--crosswalk` | `false` | Show cross-framework equivalencies |

**Examples:**

```bash
# Diff between last two commits
grc diff

# Diff between two specific commits
grc diff --from v1.0.0 --to v1.1.0

# Crosswalk diff between frameworks
grc diff --from soc2 --to iso27001 --crosswalk
```

**Output format:**

```
Compliance Diff: abc1234..def5678
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Controls Added:    3
  Controls Modified: 5
  Controls Removed:  1
  Evidence Changes:  12

  Crosswalk Equivalencies:
    SOC 2 CC6.1 ↔ ISO 27001 A.9.4.2 ↔ NIST AC-2
    SOC 2 CC7.2 ↔ ISO 27001 A.12.4.1 ↔ NIST AU-6
```

**Related commands:** `grc drift`, `grc frameworks list`, `grc report`

---

### `grc report`

**Syntax:**

```bash
grc report [options]
```

**Description:**

Generate a compliance evidence report in multiple formats (JSON, PDF, OSCAL, OCSF, STIX, SARIF, AI-BOM). Reports include evidence lineage, control mappings, trust scores, and verifier links.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--format <fmt>` | `json` | Report format: `json`, `pdf`, `oscal`, `ocsf`, `stix`, `sarif`, `ai-bom` |
| `--framework <fw>` | all | Filter by framework |
| `--output <path>` | stdout | Write report to file |
| `--include-evidence` | `false` | Embed full evidence artifacts |
| `--signed` | `false` | Cryptographically sign report |

**Examples:**

```bash
# JSON report for SOC 2
grc report --framework soc2

# OSCAL 1.1.2 SSP export
grc report --format oscal --output ssp-export.json

# AI BOM report (EU AI Act Article 53)
grc report --format ai-bom --output ai-bom-$(date +%F).json

# Signed PDF report
grc report --format pdf --signed --output audit-report.pdf
```

**Output format:**

```
Generating compliance report...

  Format: JSON
  Framework: SOC 2
  Controls: 42 evaluated
  Evidence: 147 artifacts included
  Trust Score: 76/100
  Signed: Yes (SHA-256 + RFC 3161)

  Report written to: ./soc2-report-2026-06-30.json
  Evidence hash: sha256:a1b2c3d4...
```

**Related commands:** `grc audit`, `grc ai-bom generate`, `grc evidence list`

---

### `grc doctor`

**Syntax:**

```bash
grc doctor [options]
```

**Description:**

Run environment health checks to verify GRC_Claw dependencies, configuration, connectors, and runtime state. Diagnoses issues with Node.js, PostgreSQL, LLM providers, and evidence integrity.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--fix` | `false` | Attempt automatic remediation of detected issues |
| `--check <item>` | all | Check specific component: `node`, `config`, `db`, `llm`, `evidence`, `connectors` |

**Examples:**

```bash
# Full environment check
grc doctor

# Auto-fix detected issues
grc doctor --fix

# Check only database and LLM connectivity
grc doctor --check db,llm
```

**Output format:**

```
GRC_Claw Environment Diagnostics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [✓] Node.js v20.12.0 (>= 20 required)
  [✓] npm v10.5.0
  [✓] @grc-claw/cli v16.0.0
  [✓] grcfile.yaml found
  [✓] Evidence directory: .grc/evidence (147 artifacts)
  [!] PostgreSQL connection: staging unreachable (optional)
  [✓] LLM provider: OpenAI configured
  [✓] A2Z SOC: authenticated (tenant: tenant_abc)
  [✓] GitHub Actions workflow: present

  Issues: 1 warning | 0 errors
  Run with --fix to attempt auto-remediation.
```

**Related commands:** `grc init`, `grc version`, `grc status`

---

### `grc iac-scan .`

**Syntax:**

```bash
grc iac-scan <path> [options]
```

**Description:**

Scan Terraform, CloudFormation, and Kubernetes manifests for compliance misconfigurations. Checks 8 IaC rules covering encryption, public access, logging, IAM, networking, and security groups.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--framework <fw>` | all | Map findings to specific framework |
| `--rules <list>` | all 8 | Comma-separated rule IDs |
| `--severity <level>` | `all` | Filter by severity |
| `--output <path>` | stdout | Write results to file |

**IaC scan rules (8):**

| # | Rule | Maps to |
|---|------|---------|
| 1 | Encryption at rest disabled | SOC 2 CC6.7, ISO A.10.1 |
| 2 | Public S3 bucket access | SOC 2 CC6.1, NIST AC-3 |
| 3 | Open security groups (0.0.0.0/0) | SOC 2 CC6.1, NIST SC-7 |
| 4 | Missing CloudTrail/logging | SOC 2 CC7.2, NIST AU-2 |
| 5 | IAM wildcard policies | SOC 2 CC6.1, NIST AC-6 |
| 6 | Unencrypted EBS volumes | SOC 2 CC6.7 |
| 7 | Public RDS instances | SOC 2 CC6.1, NIST SC-7 |
| 8 | Missing Kubernetes RBAC | SOC 2 CC6.3, NIST AC-2 |

**Examples:**

```bash
# Scan Terraform directory
grc iac-scan ./terraform

# Scan Kubernetes manifests
grc iac-scan ./k8s --framework nist-csf

# IaC scan with JSON output
grc iac-scan . --json --severity high
```

**Output format:**

```
IaC Compliance Scan Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Path: ./terraform
  Findings: 6 (2 high, 3 medium, 1 low)

  [HIGH] s3.tf:12 — Public S3 bucket access
    Control: SOC 2 CC6.1 | Rule: public-access
    Fix: Set acl = "private" or use aws_s3_bucket_public_access_block

  [HIGH] sg.tf:25 — Open security group (0.0.0.0/0)
    Control: NIST SC-7 | Rule: open-security-group
    Fix: Restrict cidr_blocks to specific IP ranges

  ...
```

**Related commands:** `grc scan .`, `grc pqc-scan .`, `grc plan`

---

### `grc pqc-scan .`

**Syntax:**

```bash
grc pqc-scan <path> [options]
```

**Description:**

Scan codebase and infrastructure for post-quantum cryptography (PQC) migration readiness. Detects 6 quantum-vulnerable cryptographic patterns (RSA, ECDSA, DSA, AES-CBC, DH, ECDH) and generates a NIST PQC migration roadmap.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--patterns <list>` | all 6 | Comma-separated patterns to scan |
| `--output <path>` | stdout | Write results to file |
| `--roadmap` | `false` | Generate NIST PQC migration roadmap |

**PQC patterns detected (6):**

| # | Pattern | Migration Target |
|---|---------|-----------------|
| 1 | RSA key generation/usage | ML-KEM-768 (Kyber) |
| 2 | ECDSA signatures | ML-DSA-65 (Dilithium) |
| 3 | DSA signatures | ML-DSA-65 |
| 4 | AES-CBC mode | AES-256-GCM or ML-KEM hybrid |
| 5 | Diffie-Hellman key exchange | ML-KEM-768 |
| 6 | ECDH key agreement | ML-KEM-1024 hybrid |

**Examples:**

```bash
# Scan for PQC vulnerabilities
grc pqc-scan ./src

# Generate migration roadmap
grc pqc-scan . --roadmap --output pqc-roadmap.json

# Scan specific patterns
grc pqc-scan . --patterns rsa,ecdsa
```

**Output format:**

```
Post-Quantum Cryptography Migration Scan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Findings: 18 quantum-vulnerable patterns

  RSA usage:           8 instances (src/crypto/, src/auth/)
  ECDSA usage:         5 instances (src/keys/, src/tls/)
  Diffie-Hellman:      3 instances (src/handshake/)
  AES-CBC:             2 instances (src/storage/)

  Migration priority:
    CRITICAL: src/auth/verify.ts:34 — RSA-2048 signature verification
    HIGH:     src/keys/keygen.ts:12 — ECDSA P-256 key generation
    MEDIUM:   src/storage/encrypt.ts:8 — AES-256-CBC mode

  Estimated migration effort: 16 hours
  NIST deadline alignment: FIPS 203/204 compliance by 2030
```

**Related commands:** `grc scan .`, `grc iac-scan .`, `grc report`

---

### `grc ai-bom generate`

**Syntax:**

```bash
grc ai-bom generate [options]
```

**Description:**

Generate an AI Bill of Materials (AI-BOM) documenting all AI systems, models, tools, frameworks, and data sources in scope. Aligns with EU AI Act Article 53 and ISO 42001 requirements.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--output <path>` | `ai-bom.json` | Output file path |
| `--format <fmt>` | `json` | Format: `json`, `cyclonedx`, `spdx` |
| `--framework <list>` | `eu-ai-act,iso-42001` | Framework alignment |

**Examples:**

```bash
# Generate AI BOM
grc ai-bom generate

# CycloneDX format
grc ai-bom generate --format cyclonedx --output ai-bom.cdx.json

# Specific framework alignment
grc ai-bom generate --framework iso-42001 --output ai-bom-iso.json
```

**Output format:**

```json
{
  "aibom_version": "1.0",
  "generated_at": "2026-06-30T14:30:00Z",
  "generator": "@grc-claw/cli@16.0.0",
  "project": "my-project",
  "ai_systems": [
    {
      "name": "GRC Copilot",
      "type": "llm_assistant",
      "model": "claude-3-opus",
      "provider": "anthropic",
      "frameworks": ["eu-ai-act", "iso-42001"],
      "risk_tier": "high",
      "controls": ["ISO42001-A.6.2", "EU-AIA-9"]
    }
  ],
  "models": [],
  "tools": [],
  "frameworks": [],
  "data_sources": []
}
```

**Related commands:** `grc ai-bom publish`, `grc report --format ai-bom`

---

### `grc ai-bom publish`

**Syntax:**

```bash
grc ai-bom publish [options]
```

**Description:**

Publish an AI BOM to the A2Z SOC registry for tracking, compliance alignment, and procurement readiness. Requires authentication.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--file <path>` | `ai-bom.json` | AI BOM file to publish |
| `--version <ver>` | auto-increment | BOM version tag |
| `--dry-run` | `false` | Validate without publishing |

**Examples:**

```bash
# Publish AI BOM
grc ai-bom publish

# Publish specific file
grc ai-bom publish --file my-ai-bom.json

# Validate before publishing
grc ai-bom publish --dry-run
```

**Output format:**

```
Publishing AI BOM to A2Z SOC registry...

  ✓ Validated: 3 AI systems, 5 models, 8 tools
  ✓ Published: ai-bom@v1.2.0
  Registry URL: https://a2zsoc.com/ai-bom/my-project/v1.2.0
  Compliance: EU AI Act Article 53 ✓ | ISO 42001 ✓
```

**Related commands:** `grc ai-bom generate`, `grc marketplace publish`

---

### `grc frameworks list`

**Syntax:**

```bash
grc frameworks list [options]
```

**Description:**

List all available compliance framework packs with control counts, mapping coverage, and installation status.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--installed` | `false` | Show only installed frameworks |
| `--output <path>` | stdout | Write results to file |

**Examples:**

```bash
# List all frameworks
grc frameworks list

# List only installed frameworks
grc frameworks list --installed

# JSON output
grc frameworks list --json
```

**Output format:**

```
Available Compliance Frameworks (13)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Framework        Controls  Mappings  Status
  ───────────────  ────────  ────────  ──────
  soc2               42        375      installed
  iso27001           93        412      installed
  nist-csf          106        389      installed
  nist-800-53       245        356      installed
  hipaa             184        298      available
  pci-dss           264        312      available
  gdpr              118        287      available
  fedramp           325        345      available
  cmmc              130        276      available
  iso-42001          27        198      installed
  eu-ai-act          82        167      available
  dora              156        234      available
  nis2              102        218      available

  Total: 1,874 controls | 3,767 mappings
```

**Related commands:** `grc init`, `grc diff`, `grc marketplace list`

---

### `grc agent run`

**Syntax:**

```bash
grc agent run [options]
```

**Description:**

Launch the autonomous 3-phase compliance agent (plan -> act -> verify). Discovers controls, executes remediations within policy constraints, collects evidence, and issues verifiable credentials. Auto-pauses when trust score drops below threshold.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--org <name>` | — | Organization identifier |
| `--phases <list>` | `plan,act,verify` | Phases to execute |
| `--max-actions <n>` | 50 | Maximum actions per run |
| `--trust-threshold <n>` | 80 | Auto-pause threshold (0-100) |
| `--dry-run` | `false` | Plan phase only, no execution |
| `--approval-token <token>` | — | Token for destructive actions |

**Examples:**

```bash
# Run full agent cycle
grc agent run

# Dry run (plan only)
grc agent run --dry-run

# Run with organization context and max actions
grc agent run --org acme-corp --max-actions 10

# Run specific phases
grc agent run --phases plan,verify
```

**Output format:**

```
GRC_Claw Autonomous Agent
━━━━━━━━━━━━━━━━━━━━━━━━━

  Phase 1: PLAN
    Controls discovered: 42
    Gaps identified: 7
    Remediation actions: 5

  Phase 2: ACT
    [✓] Auto-fixed: removed hardcoded secret in src/config.ts
    [✓] Auto-fixed: added .gitignore rule for .env
    [!] Manual review required: TLS config change
    [✓] Created evidence: log-rotation enabled in nginx.conf

  Phase 3: VERIFY
    Evidence collected: 4 artifacts
    Controls verified: 5/5
    Trust score: 85/100 (above threshold)
    Verifiable credentials: 3 issued

  Agent Status: completed
  Duration: 45s
  Trust Score: 85/100
```

**Related commands:** `grc status`, `grc trust score`, `grc evidence verify`

---

### `grc sovereign init`

**Syntax:**

```bash
grc sovereign init [options]
```

**Description:**

Write a Docker Compose stack (`docker-compose.sovereign.yml`) with Ollama as the sole LLM backend for air-gapped or sovereign deployments. No data leaves your network.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--output <path>` | `docker-compose.sovereign.yml` | Output file path |
| `--model <name>` | `llama3` | Ollama model to deploy |
| `--port <port>` | `11434` | Ollama API port |

**Examples:**

```bash
# Generate sovereign stack
grc sovereign init

# Custom model and output
grc sovereign init --model codellama --output docker-compose.yml

# Use with SOVEREIGN_MODE
SOVEREIGN_MODE=true grc sovereign init
docker compose -f docker-compose.sovereign.yml up
```

**Output format:**

```
Generating sovereign deployment stack...

  ✓ Created docker-compose.sovereign.yml
  Services: ollama, grc-claw-gateway, supabase, nginx
  LLM: Ollama (llama3) on localhost:11434
  Data stays local: ✓

  Start with:
    docker compose -f docker-compose.sovereign.yml up -d
```

**Related commands:** `grc agent run`, `grc doctor`

---

### `grc version`

**Syntax:**

```bash
grc version [options]
```

**Description:**

Print the GRC_Claw CLI version, build information, and linked package versions.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--json` | `false` | Output as JSON |

**Examples:**

```bash
grc version
grc version --json
```

**Output format:**

```
GRC_Claw CLI v16.0.0
Build: 2026-06-30T00:00:00Z
Node: v20.12.0
Packages:
  @grc-claw/sdk        v0.8.0
  @grc-claw/agent-runtime  v0.8.0
  @grc-claw/frameworks     v0.8.0
  @grc-claw/evidence       v0.8.0
  @grc-claw/mcp-server     v0.8.0
License: MIT
```

**Related commands:** `grc doctor`

---

### `grc marketplace list`

**Syntax:**

```bash
grc marketplace list [options]
```

**Description:**

List available compliance packs in the GRC_Claw marketplace. Shows pack names, authors, ratings, versions, and compatibility.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--category <cat>` | all | Filter by category: `framework`, `connector`, `automation` |
| `--search <query>` | — | Search packs by name or description |
| `--output <path>` | stdout | Write results to file |

**Examples:**

```bash
# List all marketplace packs
grc marketplace list

# Search for SOC 2 related packs
grc marketplace list --search soc2

# List only connector packs
grc marketplace list --category connector
```

**Output format:**

```
GRC_Claw Marketplace — Compliance Packs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Pack                       Author       Version  Rating  Category
  ─────────────────────────  ───────────  ───────  ──────  ────────
  soc2-autopilot             grc-claw     1.2.0    ★★★★★   automation
  iso42001-starter           grc-claw     1.0.3    ★★★★☆   framework
  cmmc-level2-assessment     community    0.9.1    ★★★★☆   framework
  github-connector           grc-claw     1.1.0    ★★★★★   connector
  crowdstrike-edr            community    0.8.0    ★★★☆☆   connector
  terraform-compliance       grc-claw     1.0.0    ★★★★☆   automation

  6 packs available | 2 categories
```

**Related commands:** `grc marketplace install`, `grc marketplace publish`, `grc frameworks list`

---

### `grc marketplace install`

**Syntax:**

```bash
grc marketplace install <pack-name> [options]
```

**Description:**

Install a compliance pack from the GRC_Claw marketplace. Downloads, validates, and integrates the pack into the local project configuration.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--version <ver>` | latest | Specific version to install |
| `--dry-run` | `false` | Preview installation without applying |

**Examples:**

```bash
# Install latest version
grc marketplace install soc2-autopilot

# Install specific version
grc marketplace install cmmc-level2-assessment --version 0.9.1

# Preview installation
grc marketplace install iso42001-starter --dry-run
```

**Output format:**

```
Installing compliance pack: soc2-autopilot@latest

  ✓ Resolved: soc2-autopilot@1.2.0
  ✓ Downloaded: 12 files (248 KB)
  ✓ Verified: signed provenance (SHA-256)
  ✓ Installed: soc2-autopilot
  ✓ Updated: grcfile.yaml (added soc2-autopilot to packs)

  Run `grc scan .` to evaluate with new pack.
```

**Related commands:** `grc marketplace list`, `grc frameworks list`, `grc scan .`

---

### `grc marketplace publish`

**Syntax:**

```bash
grc marketplace publish <pack-path> [options]
```

**Description:**

Publish a compliance pack to the GRC_Claw marketplace. Validates pack structure, signs provenance, and uploads to the registry. Requires authentication.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--dry-run` | `false` | Validate without publishing |
| `--sign` | `true` | Sign pack with cryptographic provenance |

**Examples:**

```bash
# Publish pack
grc marketplace publish ./my-pack

# Validate before publishing
grc marketplace publish ./my-pack --dry-run

# Publish without signing
grc marketplace publish ./my-pack --sign=false
```

**Output format:**

```
Publishing compliance pack: my-custom-soc2-pack

  ✓ Validated: pack.yaml schema valid
  ✓ Signed: SHA-256 provenance (key: abc123...)
  ✓ Uploaded: my-custom-soc2-pack@1.0.0
  Registry: https://marketplace.grc-claw.com/packs/my-custom-soc2-pack
```

**Related commands:** `grc marketplace list`, `grc marketplace install`

---

### `grc evidence list`

**Syntax:**

```bash
grc evidence list [options]
```

**Description:**

List evidence artifacts in the local evidence vault or remote A2Z SOC registry. Shows artifact IDs, types, timestamps, hash status, and control mappings.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--framework <fw>` | all | Filter by framework |
| `--type <type>` | all | Filter by evidence type: `log_entry`, `screenshot`, `config_export`, `scan_result`, `agent_receipt` |
| `--limit <n>` | 50 | Maximum number of results |
| `--freshness <days>` | — | Filter by evidence age in days |

**Examples:**

```bash
# List all evidence artifacts
grc evidence list

# List SOC 2 evidence
grc evidence list --framework soc2

# List recent evidence (last 7 days)
grc evidence list --freshness 7

# List agent receipts
grc evidence list --type agent_receipt --json
```

**Output format:**

```
Evidence Artifacts (147)
━━━━━━━━━━━━━━━━━━━━━━━━

  ID          Type            Created      Hash          Framework   Control
  ──────────  ──────────────  ───────────  ────────────  ──────────  ───────
  evn_01J0..  log_entry       2h ago       sha256:a1b2.. soc2        CC6.1
  evn_01J0..  scan_result     6h ago       sha256:c3d4.. soc2        CC7.2
  evn_01J0..  config_export   1d ago       sha256:e5f6.. iso27001    A.12.4
  evn_01J0..  agent_receipt   2d ago       sha256:g7h8.. soc2        CC8.1

  Total: 147 artifacts | Hash chain: valid | Last updated: 2h ago
```

**Related commands:** `grc evidence verify`, `grc audit`, `grc report`

---

### `grc evidence verify`

**Syntax:**

```bash
grc evidence verify [options]
```

**Description:**

Verify the integrity of evidence artifacts by re-computing SHA-256 hashes and validating the hash chain. Checks for tampering, missing links, and RFC 3161 timestamp validity.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--all` | `false` | Verify all evidence artifacts |
| `--id <event-id>` | — | Verify evidence for a specific event |
| `--output <path>` | stdout | Write verification report to file |

**Examples:**

```bash
# Verify all evidence
grc evidence verify --all

# Verify specific event evidence
grc evidence verify --id evt_01J0abc123

# Verify and export report
grc evidence verify --all --output evidence-verify.json
```

**Output format:**

```
Evidence Integrity Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Artifacts verified: 147/147
  Hash chain: ✓ valid (no broken links)
  RFC 3161 timestamps: ✓ all valid
  Tamper detection: ✓ no anomalies

  Verification time: 1.2s
  Last verification: 2026-06-30T14:30:00Z

  Exit code: 0 (all verified)
```

**Related commands:** `grc evidence list`, `grc audit`

---

### `grc trust score`

**Syntax:**

```bash
grc trust score [options]
```

**Description:**

Calculate the current trust score across five weighted factors: evidence freshness (25%), vulnerability exposure (25%), control test pass rate (20%), training completion (15%), and incident transparency (15%). Produces a 0-100 score with A-F grade.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--framework <fw>` | all | Filter by framework |
| `--breakdown` | `false` | Show detailed factor breakdown |
| `--output <path>` | stdout | Write score to file |

**Examples:**

```bash
# Overall trust score
grc trust score

# Detailed breakdown
grc trust score --breakdown

# Framework-specific score
grc trust score --framework soc2 --json
```

**Output format:**

```
Trust Score Assessment
━━━━━━━━━━━━━━━━━━━━━━

  Overall Score: 76/100  Grade: C

  Factor Breakdown:
    Evidence Freshness:        22/25  (88%)
    Vulnerability Exposure:    18/25  (72%)
    Control Test Pass Rate:    16/20  (80%)
    Training Completion:       12/15  (80%)
    Incident Transparency:     8/15   (53%)

  Trend: +3 points since last assessment (30 days ago)
  Badge: /api/trust-score/badge.svg (embeddable)
```

**Related commands:** `grc audit`, `grc status`, `grc agent run`

---

### `grc verifier room`

**Syntax:**

```bash
grc verifier room [options]
```

**Description:**

Manage verifier rooms for auditors, customers, primes, insurers, and regulators. Create scoped access rooms where external parties can verify evidence, controls, and trust claims without raw data access.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--create` | — | Create a new verifier room |
| `--list` | — | List existing verifier rooms |
| `--id <room-id>` | — | Access specific room |
| `--scope <role>` | `auditor` | Room role: `auditor`, `insurer`, `procurement`, `prime`, `regulator` |
| `--expires <days>` | 30 | Room access expiration |

**Examples:**

```bash
# Create auditor verifier room
grc verifier room --create --scope auditor

# List existing rooms
grc verifier room --list

# Create procurement room with custom expiry
grc verifier room --create --scope procurement --expires 90

# Access specific room
grc verifier room --id room_abc123
```

**Output format:**

```
Verifier Room Created
━━━━━━━━━━━━━━━━━━━━━

  Room ID:   room_01J0abc123
  Scope:     auditor
  Expires:   2026-09-28
  URL:       https://a2zsoc.com/verify/room_01J0abc123

  Accessible evidence:
    - 147 artifacts (redacted for auditor safety)
    - 42 SOC 2 controls
    - Trust score: 76/100
    - Hash chain: verified

  Share link: copied to clipboard
```

**Related commands:** `grc evidence verify`, `grc trust score`, `grc report`

---

### `grc benchmark compare`

**Syntax:**

```bash
grc benchmark compare [options]
```

**Description:**

Compare your compliance posture against anonymized peer benchmarks across industry cohorts and organization sizes. Shows percentile rankings per framework based on opt-in anonymized data.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--framework <fw>` | all | Compare specific framework |
| `--industry <type>` | auto-detect | Industry cohort: `tech`, `finance`, `healthcare`, `government`, `manufacturing` |
| `--size <level>` | auto-detect | Org size: `startup`, `smb`, `mid-market`, `enterprise` |
| `--output <path>` | stdout | Write comparison to file |

**Examples:**

```bash
# Overall benchmark comparison
grc benchmark compare

# SOC 2 benchmark for tech companies
grc benchmark compare --framework soc2 --industry tech

# Enterprise benchmark comparison
grc benchmark compare --size enterprise --json
```

**Output format:**

```
Peer Benchmark Comparison
━━━━━━━━━━━━━━━━━━━━━━━━━

  Industry: tech | Size: mid-market | Peers: 1,247 organizations

  Framework      Your Score  Peer Median  Percentile  Gap
  ─────────────  ──────────  ───────────  ──────────  ────
  SOC 2            72/100      68/100       62nd       +4
  ISO 27001        81/100      74/100       71st       +7
  NIST CSF         68/100      65/100       58th       +3

  Strengths:  ISO 27001 above 70th percentile
  Gaps:        NIST CSF at median — opportunity to differentiate

  Data source: A2Z SOC Benchmark Intelligence Network (opt-in)
  Last updated: 2026-06-30
```

**Related commands:** `grc status`, `grc trust score`, `grc report`

---

### `grc procurement packet`

**Syntax:**

```bash
grc procurement packet [options]
```

**Description:**

Generate a procurement-ready compliance packet for CMMC, NIST 800-171, ISO 42001, SOC 2, and defense industrial base requirements. Produces buyer-specific answer kits, evidence envelopes, AI BOM, SBOM, and questionnaire responses.

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--buyer <type>` | `general` | Buyer type: `dod`, `prime`, `auditor`, `insurer`, `board`, `msp` |
| `--framework <fw>` | all | Filter by framework |
| `--include <artifacts>` | all | Comma-separated: `ssp`, `poam`, `sprs`, `ai-bom`, `sbom`, `evidence`, `questionnaire` |
| `--output <path>` | `./procurement-packet` | Output directory |
| `--format <fmt>` | `json` | Format: `json`, `pdf`, `oscal` |

**Examples:**

```bash
# General procurement packet
grc procurement packet

# DoD-specific packet with CMMC focus
grc procurement packet --buyer dod --framework cmmc

# Auditor packet with all artifacts
grc procurement packet --buyer auditor --include ssp,poam,ai-bom,evidence

# Board-ready PDF packet
grc procurement packet --buyer board --format pdf
```

**Output format:**

```
Generating procurement packet...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Buyer type: dod
  Frameworks: cmmc, nist-800-171, iso-42001

  Artifacts generated:
    [✓] System Security Plan (SSP) — OSCAL 1.1.2
    [✓] Plan of Action & Milestones (POA&M)
    [✓] SPRS Score: 87/110
    [✓] AI Bill of Materials (AI-BOM)
    [✓] Evidence envelope (147 artifacts, SHA-256 signed)
    [✓] Questionnaire answer kit (32 questions)
    [✓] CUI boundary diagram
    [✓] Supplier risk summary

  Output: ./procurement-packet/
  Packet hash: sha256:9a8b7c6d...
  Verifier link: https://a2zsoc.com/verify/pkt_01J0...

  Ready for submission to prime contractor.
```

**Related commands:** `grc audit`, `grc ai-bom generate`, `grc report`, `grc verifier room`

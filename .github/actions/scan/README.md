# GRC Claw Security Scan Action

Scans pull requests for IaC misconfigurations and exposed secrets, then maps findings to SOC2 / compliance controls via the A2Z SOC PR Security Gate API.

## Usage

```yaml
# .github/workflows/grc-gate.yml
name: GRC Security Gate
on: [pull_request]

jobs:
  grc-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: grc-claw/scan-action@v1
        with:
          api-url: ${{ secrets.GRC_API_URL }}
          api-key: ${{ secrets.GRC_API_KEY }}
          severity-threshold: critical   # optional, default: critical
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `api-url` | yes | — | Your A2Z SOC API base URL (e.g. `https://a2zsoc.com`) |
| `api-key` | yes | — | Your GRC Claw API key (from Settings > API Keys) |
| `severity-threshold` | no | `critical` | Fail the check on findings at or above this severity (`critical`, `high`, `medium`, `low`) |

## Outputs

| Output | Description |
|--------|-------------|
| `status` | Scan result: `pass`, `warn`, or `fail` |
| `findings-count` | Total number of findings detected |

## What it does

1. Runs `grc scan iac` — checks Terraform, CloudFormation, Kubernetes manifests for misconfigurations.
2. Runs `grc scan secrets` — detects hard-coded credentials, tokens, and private keys.
3. POSTs findings to `/api/platform/github-pr-gate` on your A2Z SOC instance.
4. The API maps findings to SOC2 controls (via `framework_control_mappings`) and writes a `proof_ledger` entry for every passing PR.
5. Posts a step summary with scan status and controls mapped.
6. Exits with code 1 if `status=fail` and the severity threshold is met (blocks the PR).

## Secrets setup

In your GitHub repo: **Settings > Secrets and variables > Actions**

- `GRC_API_URL` — e.g. `https://a2zsoc.com`
- `GRC_API_KEY` — from A2Z SOC > Settings > API Keys

## Evidence collection

Every PR that passes the gate automatically creates an evidence record in the A2Z SOC proof ledger under control `CC8.1` (SOC2 Change Management). This satisfies auditor requests for continuous change-management evidence without manual screenshots.

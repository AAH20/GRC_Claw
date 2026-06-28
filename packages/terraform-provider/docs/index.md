# GRC Terraform Provider

Manage A2Z SOC GRC controls and evidence as infrastructure-as-code using the `grc` Terraform provider.

Published at: [registry.terraform.io/providers/a2zsoc/grc](https://registry.terraform.io/providers/a2zsoc/grc)

## Requirements

- [Terraform](https://www.terraform.io/downloads) >= 1.0
- Go >= 1.21 (to build from source)
- An A2Z SOC API key (`GRC_API_KEY`)

## Usage

```hcl
terraform {
  required_providers {
    grc = {
      source  = "a2zsoc/grc"
      version = "~> 0.8"
    }
  }
}

provider "grc" {
  api_url = "https://a2zsoc.com"
  api_key = var.grc_api_key
}

resource "grc_control" "soc2_cc6_1" {
  org_slug   = "acme-corp"
  framework  = "soc2"
  control_id = "CC6.1"
  title      = "Logical Access Controls"
  status     = "compliant"
  evidence_url = "https://storage.a2zsoc.com/evidence/cc6-1-access-review.pdf"
}

resource "grc_evidence" "cc6_1_access_review" {
  org_slug      = "acme-corp"
  control_id    = "CC6.1"
  evidence_type = "report"
  description   = "Quarterly access review report for CC6.1"
  file_url      = "https://storage.a2zsoc.com/evidence/cc6-1-access-review.pdf"
  recorded_at   = "2026-06-01T00:00:00Z"
}
```

## Provider Configuration

| Attribute | Type   | Required | Env Var       | Description                              |
|-----------|--------|----------|---------------|------------------------------------------|
| `api_url` | string | yes      | `GRC_API_URL` | Base URL of the A2Z SOC GRC API          |
| `api_key` | string | yes      | `GRC_API_KEY` | API key used for Bearer authentication   |

## Resources

### `grc_control`

Manages a compliance control record.

| Attribute     | Type   | Required | Description                                               |
|---------------|--------|----------|-----------------------------------------------------------|
| `org_slug`    | string | yes      | Organization slug                                         |
| `framework`   | string | yes      | Framework (soc2, iso27001, hipaa, ...)                   |
| `control_id`  | string | yes      | Control identifier (e.g. CC6.1)                          |
| `title`       | string | yes      | Human-readable control title                             |
| `status`      | string | yes      | `compliant` \| `non_compliant` \| `not_applicable`       |
| `evidence_url`| string | no       | URL to supporting evidence                               |

### `grc_evidence`

Manages an evidence record in the proof ledger.

| Attribute      | Type   | Required | Description                                      |
|----------------|--------|----------|--------------------------------------------------|
| `org_slug`     | string | yes      | Organization slug                                |
| `control_id`   | string | yes      | Control this evidence supports                   |
| `evidence_type`| string | yes      | `screenshot` \| `log` \| `report` \| `policy` \| `attestation` \| `other` |
| `description`  | string | yes      | Description of the evidence                      |
| `file_url`     | string | no       | URL to the artifact                              |
| `recorded_at`  | string | no       | ISO 8601 timestamp (defaults to server time)     |

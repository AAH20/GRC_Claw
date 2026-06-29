# GRC Claw Sovereign Deployment

Deploy the complete GRC Claw stack into your own cloud account for air-gapped or data-residency-regulated environments (UAE, KSA, India, EU financial services, US government).

## What's included

- Supabase (self-hosted via Docker) — PostgreSQL 15 + Auth + Storage + Realtime
- Ollama — local LLM inference (replaces Anthropic API for sovereign mode)
- GRC Claw API — the full platform API
- Nginx — reverse proxy with TLS termination
- Automated backups to your S3-compatible storage

## Prerequisites

- AWS, Azure, or GCP account with admin access
- Terraform >= 1.5
- Docker + Docker Compose
- A domain name with DNS control

## Quick start

```bash
# Clone and configure
git clone https://github.com/AAH20/GRC_Claw
cd GRC_Claw/deploy/sovereign

# Copy and edit config
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Deploy (AWS example)
terraform init
terraform plan
terraform apply

# After deploy, initialize the platform
./scripts/init-sovereign.sh
```

## Data residency

All data stays within your cloud account. No data is sent to external services in sovereign mode:
- LLM inference: Ollama (llama3.1:8b or mistral) runs locally
- Email: configure your own SMTP
- No telemetry or phone-home

## Supported regions

| Cloud | Regions |
|-------|---------|
| AWS | Any (tested: me-south-1 Bahrain, ap-south-1 Mumbai, eu-central-1 Frankfurt) |
| Azure | Any (tested: uaenorth, southindia, germanywestcentral) |
| GCP | Any (tested: me-west1, asia-south1) |

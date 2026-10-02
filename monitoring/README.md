# GRC Claw — Monitoring & Observability

Production-grade monitoring setup for all 75 GRC Claw projects, including the 30 new projects across three domains.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐
│  Projects   │────▶│  Prometheus  │────▶│  Grafana  │
│  (/metrics) │     │  (scraping)  │     │ (visuals) │
└─────────────┘     └──────┬───────┘     └───────────┘
                           │
                    ┌──────▼───────┐
                    │ Alertmanager │
                    │  (alerts)    │
                    └──────────────┘
```

## File Layout

```
monitoring/
├── prometheus/
│   └── prometheus.yml          # Prometheus scrape config (all 75 projects)
├── grafana/
│   └── dashboards/
│       ├── recruitment-platforms.json   # Recruitment domain dashboard
│       ├── ugc-marketplaces.json         # UGC marketplaces dashboard
│       └── gated-communities.json       # Gated communities dashboard
├── alerts/
│   └── alert-rules.yml         # Prometheus alerting rules
└── README.md                   # This file
```

## Quick Start

### 1. Start Prometheus

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/alerts/alert-rules.yml:/etc/prometheus/alert-rules.yml \
  prom/prometheus:latest
```

### 2. Start Grafana

```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -v $(pwd)/grafana/dashboards:/var/lib/grafana/dashboards \
  grafana/grafana:latest
```

### 3. Start Alertmanager

```bash
docker run -d \
  --name alertmanager \
  -p 9093:9093 \
  prom/alertmanager:latest
```

### 4. Import Dashboards

1. Open Grafana at `http://localhost:3000`
2. Navigate to **Dashboards → Import**
3. Upload each JSON file from `grafana/dashboards/`
4. Select the Prometheus data source

## Monitored Projects

### Recruitment Platforms (10)
| Job | Target |
|-----|--------|
| talent-finder | talent-finder:8080 |
| job-board-pro | job-board-pro:8080 |
| career-hub | career-hub:8080 |
| hire-flow | hire-flow:8080 |
| recruiter-connect | recruiter-connect:8080 |
| talent-pool | talent-pool:8080 |
| job-match | job-match:8080 |
| career-launch | career-launch:8080 |
| hire-smart | hire-smart:8080 |
| talent-link | talent-link:8080 |

### UGC Marketplaces (10)
| Job | Target |
|-----|--------|
| content-bazaar | content-bazaar:8080 |
| creator-hub | creator-hub:8080 |
| media-market | media-market:8080 |
| ugc-exchange | ugc-exchange:8080 |
| content-craft | content-craft:8080 |
| creator-space | creator-space:8080 |
| media-hub | media-hub:8080 |
| ugc-store | ugc-store:8080 |
| content-vault | content-vault:8080 |
| creator-market | creator-market:8080 |

### Gated Communities (10)
| Job | Target |
|-----|--------|
| exclusive-club | exclusive-club:8080 |
| private-circle | private-circle:8080 |
| vip-lounge | vip-lounge:8080 |
| members-only | members-only:8080 |
| inner-circle | inner-circle:8080 |
| elite-network | elite-network:8080 |
| gated-garden | gated-garden:8080 |
| private-haven | private-haven:8080 |
| exclusive-access | exclusive-access:8080 |
| members-guild | members-guild:8080 |

## Alert Rules

| Alert | Severity | Condition |
|-------|----------|-----------|
| InstanceDown | critical | `up == 0` for 1m |
| HighErrorRate | critical | 5xx rate > 5% for 2m |
| HighLatency | warning | P95 latency > 1s for 5m |
| HighCPUUsage | warning | CPU > 80% for 5m |
| HighMemoryUsage | warning | Memory > 500MB for 5m |
| DiskSpaceLow | critical | Disk < 10% for 5m |
| RecruitmentJobFailure | warning | > 5 job posting failures/hr |
| RecruitmentSlowMatching | warning | P95 matching > 30s for 10m |
| UGCUploadFailure | warning | > 10 upload failures/hr |
| UGCModerationBacklog | warning | > 100 items pending for 10m |
| GatedAccessFailures | warning | > 5 access failures/hr |
| GatedPaymentFailures | critical | > 3 payment failures/hr |

## Dashboards

Each dashboard includes:
- **Request Rate** — per-project RPS
- **Error Rate** — 5xx percentage
- **P95 Latency** — 95th percentile response time
- **Instance Health** — up/down status
- **Domain-Specific Metrics** — job failures, moderation queue, payment failures, etc.
- **Resource Usage** — CPU and memory per project

All dashboards support project-level filtering via the `project` template variable.

## Metrics Endpoint

Each project must expose a `/metrics` endpoint in Prometheus format:

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 1027
```

## Production Checklist

- [ ] Configure Alertmanager notification channels (Slack, PagerDuty, email)
- [ ] Set up persistent storage for Prometheus (volume mount)
- [ ] Enable Grafana authentication (LDAP/OAuth)
- [ ] Configure TLS for all endpoints
- [ ] Set up log aggregation (Loki/ELK)
- [ ] Configure distributed tracing (Tempo/Jaeger)
- [ ] Add runbooks for each alert
- [ ] Test alert firing in staging
- [ ] Set up Grafana snapshot/backup
- [ ] Configure retention policies (default: 15 days)

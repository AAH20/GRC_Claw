# Onboarding & Training

## Project Overview

Customer onboarding and training platform that guides new users to activation with personalized learning paths and progress tracking.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `onboarding-training` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- Personalized onboarding flows based on user role and goals
- Interactive product tours and walkthroughs
- In-app guidance and tooltips
- Training content library with videos and tutorials
- Progress tracking and completion certificates
- Onboarding email sequences and drip campaigns
- User activation scoring and intervention triggers
- Onboarding analytics and drop-off analysis

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/onboarding-training

# Using pip
pip install grc-claw-onboarding-training
```

### Basic Usage

```python
from grc_claw import OnboardingTraining

ot = OnboardingTraining(
    activation_criteria={{"steps_completed": 5, "key_action": "first_campaign_created"}},
    email_provider="sendgrid"
)

flow = ot.start_onboarding(
    user_id="user_123",
    user_role="marketer",
    company_size="50-200",
    goals=["email_marketing", "automation"]
)

print(f"Flow: {{flow.name}} | Steps: {{flow.step_count}} | Est. Time: {{flow.estimated_minutes}}min")

progress = ot.get_progress(user_id="user_123")
print(f"Progress: {{progress.percent_complete}}% | Current Step: {{progress.current_step}}")

training = ot.enroll(
    user_id="user_123",
    course="email_marketing_fundamentals",
    pace="self_paced"
)

if training.completed:
    certificate = ot.issue_certificate(
        user_id="user_123",
        course_id=training.course_id,
        name="Email Marketing Certified"
    )
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `ONBOARDING_FLOWS` | Onboarding flow definitions by user segment |
| `TRAINING_CONTENT_LIBRARY` | Training content library path |
| `ACTIVATION_CRITERIA` | User activation criteria definition |
| `EMAIL_SEQUENCE_PROVIDER` | Email sequence provider |
| `PROGRESS_TRACKING_INTERVAL` | Progress tracking frequency in minutes (default: 15) |
| `CERTIFICATE_TEMPLATE` | Certificate template path |
| `INTERVENTION_TRIGGERS` | Intervention trigger definitions |

### Environment File Example

```env
# .env
GRC_CLAW_API_KEY=your_api_key_here
GRC_CLAW_ENV=production
```

---

## Deployment

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```bash
docker build -t grc-claw/onboarding-training .
docker run -p 3000:3000 --env-file .env grc-claw/onboarding-training
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: onboarding-training
  labels:
    app: onboarding-training
spec:
  replicas: 2
  selector:
    matchLabels:
      app: onboarding-training
  template:
    metadata:
      labels:
        app: onboarding-training
    spec:
      containers:
      - name: onboarding-training
        image: grc-claw/onboarding-training:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: onboarding-training
spec:
  selector:
    app: onboarding-training
  ports:
  - port: 80
    targetPort: 3000
```

### Serverless (AWS Lambda)

```bash
# Package and deploy
npm run build
serverless deploy --stage production
```

---

## API Reference

### Endpoints

- `POST /api/v1/onboarding/start - Start onboarding flow`
- `GET /api/v1/onboarding/{user_id}/progress - Get onboarding progress`
- `POST /api/v1/onboarding/{user_id}/complete-step - Mark step complete`
- `POST /api/v1/training/enroll - Enroll user in training`
- `GET /api/v1/training/{user_id}/progress - Get training progress`
- `POST /api/v1/training/{user_id}/certificate - Issue certificate`
- `GET /api/v1/onboarding/analytics - Get onboarding analytics`

### Authentication

All API requests require a Bearer token:

```bash
curl -H "Authorization: Bearer $GRC_CLAW_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.grc-claw.com/api/v1/...
```

### Rate Limits

| Tier | Requests/min | Burst |
|---|---|---|
| Free | 60 | 10 |
| Pro | 600 | 100 |
| Enterprise | 6000 | 1000 |

### Error Handling

All errors follow RFC 7807 (Problem Details):

```json
{
  "type": "https://api.grc-claw.com/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid input parameters",
  "instance": "/api/v1/resource"
}
```

---

## Examples

### SDK Usage

```python
from grc_claw import OnboardingTraining

ot = OnboardingTraining(
    activation_criteria={{"steps_completed": 5, "key_action": "first_campaign_created"}},
    email_provider="sendgrid"
)

flow = ot.start_onboarding(
    user_id="user_123",
    user_role="marketer",
    company_size="50-200",
    goals=["email_marketing", "automation"]
)

print(f"Flow: {{flow.name}} | Steps: {{flow.step_count}} | Est. Time: {{flow.estimated_minutes}}min")

progress = ot.get_progress(user_id="user_123")
print(f"Progress: {{progress.percent_complete}}% | Current Step: {{progress.current_step}}")

training = ot.enroll(
    user_id="user_123",
    course="email_marketing_fundamentals",
    pace="self_paced"
)

if training.completed:
    certificate = ot.issue_certificate(
        user_id="user_123",
        course_id=training.course_id,
        name="Email Marketing Certified"
    )
```

### cURL Examples

```bash
# Health check
curl https://api.grc-claw.com/api/v1/health

# Authenticate
curl -X POST https://api.grc-claw.com/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your_key"}'
```

### Webhook Integration

```json
{
  "url": "https://your-app.com/webhooks/onboarding-training",
  "events": ["resource.created", "resource.updated", "resource.deleted"],
  "secret": "your_webhook_secret"
}
```

---

## Monitoring & Observability

### Health Checks

```bash
GET /api/v1/health
# Returns: {"status": "ok", "version": "1.0.0", "uptime": 3600}
```

### Metrics (Prometheus)

```
# HELP grc_claw_onboarding-training_requests_total Total requests
# TYPE grc_claw_onboarding-training_requests_total counter
grc_claw_onboarding-training_requests_total{method="POST",status="200"} 1234
```

### Logging

Structured JSON logging to stdout:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "message": "Request completed",
  "duration_ms": 45,
  "status_code": 200
}
```

---

## Contributing

See [GRC Claw Contributing Guide](../../CONTRIBUTING.md).

---

## License

See [GRC Claw License](../../LICENSE).

---

## Support

- **Documentation**: [docs.grc-claw.com](https://docs.grc-claw.com)
- **Issues**: [GitHub Issues](https://github.com/grc-claw/grc-claw/issues)
- **Community**: [Discord](https://discord.gg/grc-claw)

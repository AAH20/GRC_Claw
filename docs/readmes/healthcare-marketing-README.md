# Healthcare Marketing

## Project Overview

Healthcare marketing platform with HIPAA-compliant tools for patient acquisition, engagement, and retention.

**GRC Claw Marketing Platform — Project Module**

| | |
|---|---|
| **Project** | `healthcare-marketing` |
| **Category** | Marketing Technology |
| **Status** | Production |
| **License** | See [GRC Claw License](../../LICENSE) |

---

## Features

- HIPAA-compliant email and SMS marketing
- Patient acquisition campaign management
- Provider referral tracking and management
- Patient education content management
- Appointment reminder and no-show reduction
- Patient satisfaction surveying and NPS
- Healthcare content marketing and SEO
- Patient portal engagement and communication

---

## Quick Start

### Prerequisites

- Node.js 18+ or Python 3.9+
- GRC Claw SDK installed (`npm install @grc-claw/sdk` or `pip install grc-claw`)
- API credentials for the module

### Installation

```bash
# Using npm
npm install @grc-claw/healthcare-marketing

# Using pip
pip install grc-claw-healthcare-marketing
```

### Basic Usage

```python
from grc_claw import HealthcareMarketing

hm = HealthcareMarketing(
    hipaa_compliant=True,
    encryption_provider="aws_kms"
)

campaign = hm.create_campaign(
    name="New Patient Welcome",
    type="email",
    audience="new_patients_30d",
    content="welcome_packet",
    hipaa_compliant=True
)

hm.send_appointment_reminder(
    patient_id="pat_123",
    appointment_id="apt_456",
    provider="Dr. Smith",
    datetime="2024-01-20T14:00:00",
    channels=["sms", "email"],
    timing_hours_before=[24, 2]
)

referral = hm.track_referral(
    referring_provider="dr_jones@clinic.com",
    patient_name="John Doe",
    service="cardiology_consult",
    status="scheduled"
)

hm.send_patient_education(
    patient_id="pat_123",
    topic="diabetes_management",
    format="email",
    language="en"
)
```

---

## Configuration

All configuration is managed via environment variables or a `.env` file in your project root.

| Variable | Description |
|---|---|
| `HIPAA_COMPLIANCE_MODE` | Enable HIPAA compliance (default: true) |
| `ENCRYPTION_PROVIDER` | Encryption provider for PHI |
| `PROVIDER_REFERRAL_NETWORK` | Provider referral network configuration |
| `APPOINTMENT_REMINDER_SCHEDULE` | Appointment reminder schedule |
| `PATIENT_EDUCATION_LIBRARY` | Patient education content library |
| `SATISFACTION_SURVEY_SCHEDULE` | Patient satisfaction survey schedule |

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
docker build -t grc-claw/healthcare-marketing .
docker run -p 3000:3000 --env-file .env grc-claw/healthcare-marketing
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: healthcare-marketing
  labels:
    app: healthcare-marketing
spec:
  replicas: 2
  selector:
    matchLabels:
      app: healthcare-marketing
  template:
    metadata:
      labels:
        app: healthcare-marketing
    spec:
      containers:
      - name: healthcare-marketing
        image: grc-claw/healthcare-marketing:latest
        ports:
        - containerPort: 3000
        envFrom:
        - secretRef:
            name: grc-claw-secrets
---
apiVersion: v1
kind: Service
metadata:
  name: healthcare-marketing
spec:
  selector:
    app: healthcare-marketing
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

- `POST /api/v1/campaigns - Create healthcare campaign`
- `POST /api/v1/appointments/remind - Send appointment reminder`
- `POST /api/v1/referrals/track - Track provider referral`
- `POST /api/v1/patients/educate - Send patient education`
- `POST /api/v1/surveys/satisfaction - Send satisfaction survey`
- `GET /api/v1/compliance/audit - Get HIPAA compliance audit`
- `GET /api/v1/analytics - Get healthcare marketing analytics`

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
from grc_claw import HealthcareMarketing

hm = HealthcareMarketing(
    hipaa_compliant=True,
    encryption_provider="aws_kms"
)

campaign = hm.create_campaign(
    name="New Patient Welcome",
    type="email",
    audience="new_patients_30d",
    content="welcome_packet",
    hipaa_compliant=True
)

hm.send_appointment_reminder(
    patient_id="pat_123",
    appointment_id="apt_456",
    provider="Dr. Smith",
    datetime="2024-01-20T14:00:00",
    channels=["sms", "email"],
    timing_hours_before=[24, 2]
)

referral = hm.track_referral(
    referring_provider="dr_jones@clinic.com",
    patient_name="John Doe",
    service="cardiology_consult",
    status="scheduled"
)

hm.send_patient_education(
    patient_id="pat_123",
    topic="diabetes_management",
    format="email",
    language="en"
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
  "url": "https://your-app.com/webhooks/healthcare-marketing",
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
# HELP grc_claw_healthcare-marketing_requests_total Total requests
# TYPE grc_claw_healthcare-marketing_requests_total counter
grc_claw_healthcare-marketing_requests_total{method="POST",status="200"} 1234
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

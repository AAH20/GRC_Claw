# UGC Marketplace API Reference

## Overview

The UGC Marketplace API is a RESTful HTTP API built with FastAPI. It provides a unified interface for content marketplace operations including moderation, monetization, discovery, rights management, quality scoring, fraud detection, analytics, licensing, curation, and marketplace transactions.

**Base URL:** `http://localhost:8000/api/v1`

**Content Type:** `application/json`

**API Version:** 1.0.0

---

## Authentication

The API currently uses a simple API key verification pattern. Pass the API key as a query parameter or header:

```
X-API-Key: your-api-key-here
```

> **Note:** In production, configure proper authentication via OAuth2, JWT, or API gateway.

---

## Health Endpoints

### Health Check

Check if the service is running.

```
GET /api/v1/health
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

### Readiness Check

Check if the service is ready to accept traffic.

```
GET /api/v1/health/ready
```

**Response (200 OK):**

```json
{
  "status": "ready",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

### Liveness Check

Check if the service is alive.

```
GET /api/v1/health/live
```

**Response (200 OK):**

```json
{
  "status": "alive",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

## Content Moderation

### Moderate Text

Analyze text content for policy violations.

```
POST /api/v1/moderation/moderate/text
```

**Request Body:**

```json
{
  "content": "Text content to analyze",
  "content_type": "text",
  "user_id": "user-123",
  "metadata": {"source": "upload"},
  "callback_url": "https://example.com/webhook"
}
```

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "content_type": "text",
  "action": "allow",
  "confidence": 0.95,
  "categories": [],
  "reasons": [],
  "policy_violations": [],
  "processing_time_ms": 45.2,
  "created_at": "2024-01-15T10:30:00.000000",
  "agent_trace": {}
}
```

### Moderate Image

Analyze image content for policy violations.

```
POST /api/v1/moderation/moderate/image
```

**Request Body:**

```json
{
  "content": "https://example.com/image.jpg",
  "content_type": "image",
  "user_id": "user-123",
  "metadata": {"source": "upload"}
}
```

**Response:** Same schema as text moderation.

### Moderate Video

Analyze video content for policy violations.

```
POST /api/v1/moderation/moderate/video
```

**Request Body:**

```json
{
  "content": "https://example.com/video.mp4",
  "content_type": "video",
  "user_id": "user-123",
  "metadata": {"source": "upload"}
}
```

**Response:** Same schema as text moderation.

### Batch Moderation

Moderate multiple content items in a single request.

```
POST /api/v1/moderation/moderate/batch
```

**Request Body:**

```json
{
  "items": [
    {
      "content": "First text to check",
      "content_type": "text",
      "user_id": "user-123"
    },
    {
      "content": "https://example.com/image.png",
      "content_type": "image",
      "user_id": "user-123"
    }
  ],
  "priority": "normal"
}
```

**Response (200 OK):**

```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "request_id": "550e8400-e29b-41d4-a716-446655440002",
      "content_type": "text",
      "action": "allow",
      "confidence": 0.95,
      "categories": [],
      "reasons": [],
      "policy_violations": [],
      "processing_time_ms": 32.1,
      "created_at": "2024-01-15T10:30:00.000000"
    }
  ],
  "total_processed": 2,
  "total_flagged": 0,
  "total_blocked": 0
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| items | array | Yes | - | Array of moderation requests (1-100 items) |
| priority | string | No | `normal` | Processing priority: `low`, `normal`, `high` |

---

## Creator Monetization

### Record Metric

Record a metric data point for analytics.

```
POST /api/v1/monetization/metrics
```

**Request Body:**

```json
{
  "name": "revenue",
  "value": 150.00,
  "label": "subscription"
}
```

**Response (201 Created):**

```json
{
  "name": "revenue",
  "recorded": true,
  "point": {
    "timestamp": "2024-01-15T10:30:00.000000",
    "value": 150.00,
    "label": "subscription"
  }
}
```

### List Metrics

List all available metrics.

```
GET /api/v1/monetization/metrics
```

**Response (200 OK):**

```json
{
  "metrics": ["revenue", "subscribers", "views"],
  "count": 3
}
```

### Generate Report

Generate an analytics report for a specific period.

```
POST /api/v1/monetization/reports
```

**Request Body:**

```json
{
  "report_id": "report-2024-01",
  "creator_id": "creator-123",
  "period_start": "2024-01-01T00:00:00",
  "period_end": "2024-01-31T23:59:59"
}
```

**Response (201 Created):**

```json
{
  "report_id": "report-2024-01",
  "creator_id": "creator-123",
  "period": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-31T23:59:59"
  },
  "metrics": {
    "revenue": [
      {"timestamp": "2024-01-15T10:30:00", "value": 150.00, "label": "subscription"}
    ]
  },
  "summary": {
    "revenue_total": 150.00,
    "revenue_avg": 150.00,
    "revenue_max": 150.00,
    "revenue_min": 150.00
  },
  "insights": ["Total revenue: $150.00"],
  "generated_at": "2024-01-15T10:30:00.000000"
}
```

### Get Report

Retrieve a previously generated report.

```
GET /api/v1/monetization/reports/{report_id}
```

**Response (200 OK):** The report object.

### Forecast Metric

Forecast a metric for future days using linear regression.

```
POST /api/v1/monetization/forecast
```

**Request Body:**

```json
{
  "name": "revenue",
  "days": 30
}
```

**Response (200 OK):**

```json
{
  "metric": "revenue",
  "days": 30,
  "forecast": [
    {"date": "2024-02-14T10:30:00", "value": 165.00},
    {"date": "2024-02-15T10:30:00", "value": 167.50}
  ]
}
```

### Revenue Report

Get a revenue report for a creator.

```
GET /api/v1/monetization/revenue/{creator_id}
```

**Response (200 OK):**

```json
{
  "report_id": "rev-creator-123",
  "creator_id": "creator-123",
  "period_start": "2023-12-16T10:30:00",
  "period_end": "2024-01-15T10:30:00",
  "total_revenue": "0.00",
  "subscription_revenue": "0.00",
  "tip_revenue": "0.00",
  "merchandise_revenue": "0.00",
  "sponsorship_revenue": "0.00",
  "other_revenue": "0.00",
  "subscriber_count": 0,
  "active_subscribers": 0,
  "churned_subscribers": 0,
  "currency": "USD",
  "insights": ["No data available for this period"],
  "generated_at": "2024-01-15T10:30:00"
}
```

---

## Content Discovery

### Search Content

Search content with semantic and keyword matching.

```
GET /api/v1/discovery/search?query=python+tutorial&limit=10
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | Search query |
| limit | integer | No | 10 | Maximum results |

**Response (200 OK):**

```json
{
  "query": "python tutorial",
  "results": [],
  "count": 0
}
```

### Get Recommendations

Get personalized content recommendations for a user.

```
GET /api/v1/discovery/recommendations/{user_id}?limit=10
```

**Response (200 OK):**

```json
{
  "user_id": "user-123",
  "recommendations": [],
  "count": 0
}
```

### Get Trending

Get trending content, optionally filtered by category.

```
GET /api/v1/discovery/trending?category=technology&limit=10
```

**Response (200 OK):**

```json
{
  "category": "technology",
  "trending": [],
  "count": 0
}
```

---

## Rights Management

### Create License

Create a new content license.

```
POST /api/v1/rights/licenses
```

**Response (201 Created):**

```json
{
  "status": "created"
}
```

### List Licenses

List all licenses.

```
GET /api/v1/rights/licenses
```

**Response (200 OK):** Array of license objects.

### Get License

Get a license by ID.

```
GET /api/v1/rights/licenses/{license_id}
```

**Response (200 OK):**

```json
{
  "license_id": "license-123"
}
```

### Detect License

Detect license for content.

```
POST /api/v1/rights/detect
```

**Response (200 OK):**

```json
{
  "detected": true
}
```

### Revoke License

Revoke a license.

```
DELETE /api/v1/rights/licenses/{license_id}
```

**Response:** 204 No Content

### File Infringement Report

File a copyright infringement report.

```
POST /api/v1/rights/infringement/report
```

**Response (201 Created):**

```json
{
  "status": "filed"
}
```

### List Infringement Reports

List infringement reports for content.

```
GET /api/v1/rights/infringement/reports/{content_id}
```

**Response (200 OK):** Array of infringement reports.

### Detect Infringement

Detect potential infringement.

```
POST /api/v1/rights/infringement/detect
```

**Response (200 OK):**

```json
{
  "infringement_detected": false
}
```

### Submit Takedown Request

Submit a takedown request.

```
POST /api/v1/rights/takedown/request
```

**Response (201 Created):**

```json
{
  "status": "submitted"
}
```

### Record Usage

Record content usage.

```
POST /api/v1/rights/usage/record
```

**Response (201 Created):**

```json
{
  "status": "recorded"
}
```

### Validate Rights

Validate content usage rights.

```
POST /api/v1/rights/validate
```

**Response (201 Created):**

```json
{
  "valid": true
}
```

---

## Quality Scoring

### Score Content

Score content quality across all dimensions.

```
POST /api/v1/quality/score?content=Your+content+here&content_type=text
```

**Response (200 OK):**

```json
{
  "content_type": "text",
  "scores": {}
}
```

### Score Readability

Score content readability using Flesch-Kincaid.

```
POST /api/v1/quality/score/readability?content=Your+content+here
```

**Response (200 OK):**

```json
{
  "dimension": "readability",
  "score": 0.7,
  "level": "medium"
}
```

### Score Originality

Score content originality.

```
POST /api/v1/quality/score/originality?content=Your+content+here
```

**Response (200 OK):**

```json
{
  "dimension": "originality",
  "score": 0.6,
  "level": "medium"
}
```

### Score Engagement

Score content engagement potential.

```
POST /api/v1/quality/score/engagement?content=Your+content+here
```

**Response (200 OK):**

```json
{
  "dimension": "engagement",
  "score": 0.5,
  "level": "medium"
}
```

### Score SEO

Score content SEO optimization.

```
POST /api/v1/quality/score/seo?content=Your+content+here
```

**Response (200 OK):**

```json
{
  "dimension": "seo",
  "score": 0.4,
  "level": "low"
}
```

### Get Improvements

Get content improvement suggestions.

```
POST /api/v1/quality/improvements?content=Your+content+here
```

**Response (200 OK):**

```json
{
  "suggestions": []
}
```

### List Dimensions

List available scoring dimensions.

```
GET /api/v1/quality/dimensions
```

**Response (200 OK):**

```json
{
  "dimensions": ["readability", "originality", "engagement", "seo"],
  "count": 4
}
```

---

## Fraud Detection

### Analyze Transaction

Analyze a transaction for fraud.

```
POST /api/v1/fraud/analyze
```

**Request Body:**

```json
{
  "transaction_id": "txn-123",
  "amount": 99.99,
  "user_id": "user-456",
  "timestamp": "2024-01-15T10:30:00"
}
```

**Response (200 OK):**

```json
{
  "transaction_id": "txn-123",
  "risk_score": 0.5
}
```

### Batch Analyze

Analyze a batch of transactions.

```
POST /api/v1/fraud/analyze/batch
```

**Request Body:**

```json
{
  "transactions": [
    {"transaction_id": "txn-1", "amount": 50.00},
    {"transaction_id": "txn-2", "amount": 200.00}
  ]
}
```

**Response (200 OK):**

```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "reports": [],
  "summary": {
    "total": 2
  }
}
```

### Detect Patterns

Detect fraud patterns in a transaction.

```
POST /api/v1/fraud/patterns/detect
```

**Response (200 OK):** Array of detected patterns.

### Detect Anomalies

Detect anomalies in a transaction.

```
POST /api/v1/fraud/anomalies/detect
```

**Response (200 OK):** Array of detected anomalies.

### Score Risk

Score risk for a transaction.

```
POST /api/v1/fraud/risk/score
```

**Response (200 OK):**

```json
{
  "overall_score": 0.5
}
```

### Analyze Account

Analyze an account for fraud risk.

```
POST /api/v1/fraud/accounts/analyze?account_id=acc-123
```

**Response (200 OK):**

```json
{
  "account_id": "acc-123",
  "risk_level": "medium",
  "risk_score": 0.5
}
```

### Start Monitoring

Start monitoring transactions for an account.

```
POST /api/v1/fraud/monitoring/start?account_id=acc-123
```

**Response (200 OK):**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "account_id": "acc-123",
  "status": "active"
}
```

### Stop Monitoring

Stop a monitoring session.

```
POST /api/v1/fraud/monitoring/stop?session_id=550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK):**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "stopped"
}
```

---

## Creator Analytics

### Growth Prediction

Get growth prediction for a creator.

```
GET /api/v1/analytics/growth/{creator_id}
```

**Response (200 OK):**

```json
{
  "creator_id": "creator-123",
  "predictions": {}
}
```

### Content Performance

Get content performance metrics.

```
GET /api/v1/analytics/content/{content_id}
```

**Response (200 OK):**

```json
{
  "content_id": "content-123",
  "metrics": {}
}
```

### Audience Analysis

Get audience analysis for a creator.

```
GET /api/v1/analytics/audience/{creator_id}
```

**Response (200 OK):**

```json
{
  "creator_id": "creator-123",
  "demographics": {}
}
```

### Revenue Report

Get revenue report for a creator.

```
GET /api/v1/analytics/revenue/{creator_id}
```

**Response (200 OK):**

```json
{
  "creator_id": "creator-123",
  "revenue": {}
}
```

### Engagement Report

Get engagement report for a creator.

```
GET /api/v1/analytics/engagement/{creator_id}
```

**Response (200 OK):**

```json
{
  "creator_id": "creator-123",
  "engagement": {}
}
```

---

## Licensing Engine

### Create License

Create a new license agreement.

```
POST /api/v1/licensing/licenses
```

**Request Body:**

```json
{
  "licensor": "creator-123",
  "licensee": "user-456",
  "content_id": "content-789",
  "terms": {"type": "non-exclusive", "duration": "1 year"}
}
```

**Response (201 Created):**

```json
{
  "status": "created",
  "license_id": "00000000-0000-0000-0000-000000000000"
}
```

### List Licenses

List all licenses.

```
GET /api/v1/licensing/licenses
```

**Response (200 OK):** Array of license objects.

### Get License

Get a license by ID.

```
GET /api/v1/licensing/licenses/{license_id}
```

**Response (200 OK):**

```json
{
  "license_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Update License

Update a license.

```
PATCH /api/v1/licensing/licenses/{license_id}
```

**Response (200 OK):**

```json
{
  "license_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "updated"
}
```

### Delete License

Delete a license.

```
DELETE /api/v1/licensing/licenses/{license_id}
```

**Response:** 204 No Content

### Activate License

Activate a license.

```
POST /api/v1/licensing/licenses/{license_id}/activate
```

**Response (200 OK):**

```json
{
  "license_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active"
}
```

### Revoke License

Revoke a license.

```
POST /api/v1/licensing/licenses/{license_id}/revoke
```

**Response (200 OK):**

```json
{
  "license_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "revoked"
}
```

### Create Negotiation

Create a new negotiation.

```
POST /api/v1/licensing/negotiations
```

**Response (201 Created):**

```json
{
  "status": "created",
  "negotiation_id": "00000000-0000-0000-0000-000000000000"
}
```

### Compliance Check

Run a compliance check.

```
POST /api/v1/licensing/compliance/check
```

**Response (201 Created):**

```json
{
  "status": "checked",
  "compliant": true
}
```

### Calculate Royalties

Calculate royalties.

```
POST /api/v1/licensing/royalties/calculate
```

**Response (201 Created):**

```json
{
  "status": "calculated",
  "total_royalty": 0.0
}
```

### Analyze Contract

Analyze a contract.

```
POST /api/v1/licensing/contracts/analyze
```

**Response (201 Created):**

```json
{
  "status": "analyzed",
  "overall_risk": "low"
}
```

---

## Community Curation

### Curate Content

Curate content for a community feed.

```
POST /api/v1/curation/curate
```

**Request Body:**

```json
{
  "items": [
    {"content_id": "c1", "score": 0.9},
    {"content_id": "c2", "score": 0.7}
  ],
  "context": "technology"
}
```

**Response (200 OK):**

```json
{
  "curated": [],
  "explanations": {}
}
```

### Rank Content

Rank content items.

```
POST /api/v1/curation/rank
```

**Response (200 OK):** Array of ranked content.

### Surface Trends

Surface trending content.

```
POST /api/v1/curation/trends
```

**Response (200 OK):** Array of trending content.

### Filter by Quality

Filter content by quality.

```
POST /api/v1/curation/filter
```

**Response (200 OK):** Array of quality assessments.

### Cluster Topics

Cluster content by topic.

```
POST /api/v1/curation/cluster
```

**Response (200 OK):** Array of topic clusters.

### Explain Curation

Explain curation decisions.

```
POST /api/v1/curation/explain
```

**Response (200 OK):** Curation explanations.

---

## Content Marketplace

### Create Listing

Create a new marketplace listing.

```
POST /api/v1/marketplace/listings
```

**Request Body:**

```json
{
  "title": "Digital Art Pack",
  "description": "High-quality digital art assets",
  "price": 29.99,
  "category": "digital-art",
  "creator_id": "creator-123"
}
```

**Response (201 Created):**

```json
{
  "status": "created"
}
```

### List Listings

List all marketplace listings.

```
GET /api/v1/marketplace/listings
```

**Response (200 OK):** Array of listing objects.

### Get Listing

Get a listing by ID.

```
GET /api/v1/marketplace/listings/{listing_id}
```

**Response (200 OK):**

```json
{
  "listing_id": "listing-123"
}
```

### Update Listing

Update a listing.

```
PUT /api/v1/marketplace/listings/{listing_id}
```

**Response (200 OK):**

```json
{
  "listing_id": "listing-123",
  "status": "updated"
}
```

### Delete Listing

Delete a listing.

```
DELETE /api/v1/marketplace/listings/{listing_id}
```

**Response:** 204 No Content

### Create Transaction

Create a new marketplace transaction.

```
POST /api/v1/marketplace/transactions
```

**Response (201 Created):**

```json
{
  "status": "created"
}
```

### Process Transaction

Process a transaction.

```
POST /api/v1/marketplace/transactions/{transaction_id}/process
```

**Response (200 OK):**

```json
{
  "transaction_id": "txn-123",
  "status": "processing"
}
```

### Complete Transaction

Complete a transaction.

```
POST /api/v1/marketplace/transactions/{transaction_id}/complete
```

**Response (200 OK):**

```json
{
  "transaction_id": "txn-123",
  "status": "completed"
}
```

### Refund Transaction

Refund a transaction.

```
POST /api/v1/marketplace/transactions/{transaction_id}/refund
```

**Response (200 OK):**

```json
{
  "transaction_id": "txn-123",
  "status": "refunded"
}
```

### Trust Score

Get trust score for a user.

```
GET /api/v1/marketplace/trust/{user_id}
```

**Response (200 OK):**

```json
{
  "user_id": "user-123"
}
```

### Create Pricing

Create a pricing entry.

```
POST /api/v1/marketplace/pricing
```

**Response (201 Created):**

```json
{
  "status": "created"
}
```

### Optimize Pricing

Optimize pricing for a listing.

```
POST /api/v1/marketplace/pricing/{pricing_id}/optimize
```

**Response (200 OK):**

```json
{
  "pricing_id": "pricing-123",
  "optimized": true
}
```

### Marketplace Analytics

Get marketplace analytics report.

```
GET /api/v1/marketplace/analytics/report
```

**Response (200 OK):**

```json
{
  "report_id": "default"
}
```

### Demand Prediction

Predict demand for a category.

```
GET /api/v1/marketplace/analytics/demand-prediction/{category}
```

**Response (200 OK):**

```json
{
  "category": "digital-art",
  "predicted_demand": 0.5
}
```

---

## Error Responses

All endpoints return standard HTTP error responses:

```json
{
  "detail": "Error description"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request — Invalid input |
| 401 | Unauthorized — Missing or invalid API key |
| 403 | Forbidden — Insufficient permissions |
| 404 | Not Found — Resource does not exist |
| 409 | Conflict — Resource already exists |
| 422 | Validation Error — Invalid request body |
| 429 | Too Many Requests — Rate limit exceeded |
| 500 | Internal Server Error |

---

## Rate Limiting

The API enforces rate limiting to ensure fair usage:

- **API endpoints:** 10 requests/second (burst: 20)
- **General endpoints:** 30 requests/second (burst: 50)

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1705312800
```

---

## SDK Examples

### Python

```python
import httpx

async with httpx.AsyncClient() as client:
    # Health check
    response = await client.get("http://localhost:8000/api/v1/health")
    print(response.json())

    # Moderate text
    response = await client.post(
        "http://localhost:8000/api/v1/moderation/moderate/text",
        json={
            "content": "Hello world",
            "content_type": "text",
            "user_id": "user-123"
        }
    )
    print(response.json())
```

### cURL

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Moderate text
curl -X POST http://localhost:8000/api/v1/moderation/moderate/text \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello world", "content_type": "text"}'

# Search content
curl "http://localhost:8000/api/v1/discovery/search?query=python&limit=5"
```

### JavaScript

```javascript
// Health check
const response = await fetch('http://localhost:8000/api/v1/health');
const data = await response.json();
console.log(data);

// Moderate text
const moderation = await fetch('http://localhost:8000/api/v1/moderation/moderate/text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content: 'Hello world',
    content_type: 'text',
    user_id: 'user-123'
  })
});
const result = await moderation.json();
console.log(result);
```

---

## Interactive Documentation

When the server is running, interactive API documentation is available at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

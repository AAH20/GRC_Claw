# UGC Marketplace User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Content Moderation](#content-moderation)
4. [Creator Monetization](#creator-monetization)
5. [Content Discovery](#content-discovery)
6. [Rights Management](#rights-management)
7. [Quality Scoring](#quality-scoring)
8. [Fraud Detection](#fraud-detection)
9. [Creator Analytics](#creator-analytics)
10. [Licensing Engine](#licensing-engine)
11. [Community Curation](#community-curation)
12. [Content Marketplace](#content-marketplace)
13. [Troubleshooting](#troubleshooting)

---

## Introduction

Welcome to the UGC Marketplace user guide. This guide will help you understand and use the UGC Marketplace platform effectively. The platform provides a comprehensive set of tools for content marketplace operations, powered by AI agents.

### Who Is This For?

- **Content Creators** — Manage your content, track earnings, and grow your audience
- **Platform Moderators** — Review and moderate content at scale
- **Marketplace Operators** — Manage listings, transactions, and trust scores
- **Developers** — Integrate with the API and extend functionality

---

## Getting Started

### Accessing the Platform

Once the platform is running, access it through:

| Interface | URL | Description |
|-----------|-----|-------------|
| Web Frontend | http://localhost:3000 | Next.js web application |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API documentation |
| API Docs (ReDoc) | http://localhost:8000/redoc | Alternative API documentation |
| API Base | http://localhost:8000/api/v1 | REST API endpoint |

### Verifying the Installation

Check that the service is healthy:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

## Content Moderation

The content moderation system helps you analyze and filter user-generated content across text, images, and video.

### Moderating Text

Use the text moderation endpoint to check text content for policy violations.

**API Call:**

```bash
curl -X POST http://localhost:8000/api/v1/moderation/moderate/text \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your text content here",
    "content_type": "text",
    "user_id": "user-123"
  }'
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "content_type": "text",
  "action": "allow",
  "confidence": 0.95,
  "categories": [],
  "reasons": [],
  "policy_violations": [],
  "processing_time_ms": 45.2
}
```

**Actions Explained:**

| Action | Description |
|--------|-------------|
| `allow` | Content is safe to publish |
| `flag` | Content needs review |
| `block` | Content violates policies |
| `escalate` | Content needs human review |

### Moderating Images

```bash
curl -X POST http://localhost:8000/api/v1/moderation/moderate/image \
  -H "Content-Type: application/json" \
  -d '{
    "content": "https://example.com/image.jpg",
    "content_type": "image",
    "user_id": "user-123"
  }'
```

### Moderating Video

```bash
curl -X POST http://localhost:8000/api/v1/moderation/moderate/video \
  -H "Content-Type: application/json" \
  -d '{
    "content": "https://example.com/video.mp4",
    "content_type": "video",
    "user_id": "user-123"
  }'
```

### Batch Moderation

For high-volume moderation, use the batch endpoint to process up to 100 items at once:

```bash
curl -X POST http://localhost:8000/api/v1/moderation/moderate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"content": "Text 1", "content_type": "text"},
      {"content": "https://example.com/img.png", "content_type": "image"}
    ],
    "priority": "normal"
  }'
```

---

## Creator Monetization

Track and optimize your creator revenue.

### Recording Metrics

Record revenue and subscriber metrics:

```bash
curl -X POST http://localhost:8000/api/v1/monetization/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "name": "revenue",
    "value": 150.00,
    "label": "subscription"
  }'
```

### Generating Reports

Generate analytics reports for a specific period:

```bash
curl -X POST http://localhost:8000/api/v1/monetization/reports \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "monthly-report-jan-2024",
    "creator_id": "creator-123",
    "period_start": "2024-01-01T00:00:00",
    "period_end": "2024-01-31T23:59:59"
  }'
```

### Forecasting

Forecast future metrics:

```bash
curl -X POST http://localhost:8000/api/v1/monetization/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "name": "revenue",
    "days": 30
  }'
```

---

## Content Discovery

Find and recommend content to users.

### Searching Content

```bash
curl "http://localhost:8000/api/v1/discovery/search?query=python+tutorial&limit=10"
```

### Getting Recommendations

```bash
curl "http://localhost:8000/api/v1/discovery/recommendations/user-123?limit=10"
```

### Viewing Trending Content

```bash
curl "http://localhost:8000/api/v1/discovery/trending?category=technology&limit=10"
```

---

## Rights Management

Manage content licenses, infringement reports, and takedown requests.

### Creating a License

```bash
curl -X POST http://localhost:8000/api/v1/rights/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "licensor": "creator-123",
    "licensee": "user-456",
    "content_id": "content-789"
  }'
```

### Filing an Infringement Report

```bash
curl -X POST http://localhost:8000/api/v1/rights/infringement/report \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "content-789",
    "reporter_id": "user-456",
    "reason": "Copyright violation"
  }'
```

### Submitting a Takedown Request

```bash
curl -X POST http://localhost:8000/api/v1/rights/takedown/request \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "content-789",
    "requester_id": "rights-holder-123"
  }'
```

---

## Quality Scoring

Analyze and improve your content quality.

### Scoring Content

Get quality scores across all dimensions:

```bash
curl -X POST "http://localhost:8000/api/v1/quality/score?content=Your+content+here&content_type=text"
```

### Individual Dimension Scores

**Readability:**

```bash
curl -X POST "http://localhost:8000/api/v1/quality/score/readability?content=Your+content+here"
```

**Originality:**

```bash
curl -X POST "http://localhost:8000/api/v1/quality/score/originality?content=Your+content+here"
```

**Engagement:**

```bash
curl -X POST "http://localhost:8000/api/v1/quality/score/engagement?content=Your+content+here"
```

**SEO:**

```bash
curl -X POST "http://localhost:8000/api/v1/quality/score/seo?content=Your+content+here"
```

### Getting Improvement Suggestions

```bash
curl -X POST "http://localhost:8000/api/v1/quality/improvements?content=Your+content+here"
```

---

## Fraud Detection

Protect your marketplace from fraudulent transactions.

### Analyzing a Transaction

```bash
curl -X POST http://localhost:8000/api/v1/fraud/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn-123",
    "amount": 99.99,
    "user_id": "user-456"
  }'
```

### Analyzing an Account

```bash
curl -X POST "http://localhost:8000/api/v1/fraud/accounts/analyze?account_id=acc-123"
```

### Starting Transaction Monitoring

```bash
curl -X POST "http://localhost:8000/api/v1/fraud/monitoring/start?account_id=acc-123"
```

---

## Creator Analytics

Understand your audience and grow your channel.

### Growth Prediction

```bash
curl "http://localhost:8000/api/v1/analytics/growth/creator-123"
```

### Content Performance

```bash
curl "http://localhost:8000/api/v1/analytics/content/content-123"
```

### Audience Analysis

```bash
curl "http://localhost:8000/api/v1/analytics/audience/creator-123"
```

### Revenue Report

```bash
curl "http://localhost:8000/api/v1/analytics/revenue/creator-123"
```

### Engagement Report

```bash
curl "http://localhost:8000/api/v1/analytics/engagement/creator-123"
```

---

## Licensing Engine

Manage license agreements and negotiations.

### Creating a License

```bash
curl -X POST http://localhost:8000/api/v1/licensing/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "licensor": "creator-123",
    "licensee": "user-456",
    "content_id": "content-789",
    "terms": {"type": "non-exclusive", "duration": "1 year"}
  }'
```

### Starting a Negotiation

```bash
curl -X POST http://localhost:8000/api/v1/licensing/negotiations \
  -H "Content-Type: application/json" \
  -d '{
    "license_id": "license-123",
    "proposer": "user-456"
  }'
```

### Running a Compliance Check

```bash
curl -X POST http://localhost:8000/api/v1/licensing/compliance/check \
  -H "Content-Type: application/json" \
  -d '{
    "license_id": "license-123"
  }'
```

### Calculating Royalties

```bash
curl -X POST http://localhost:8000/api/v1/licensing/royalties/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "license_id": "license-123",
    "usage_count": 1000
  }'
```

---

## Community Curation

Curate content for community feeds.

### Curating Content

```bash
curl -X POST http://localhost:8000/api/v1/curation/curate \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"content_id": "c1", "score": 0.9},
      {"content_id": "c2", "score": 0.7}
    ],
    "context": "technology"
  }'
```

### Ranking Content

```bash
curl -X POST http://localhost:8000/api/v1/curation/rank \
  -H "Content-Type: application/json" \
  -d '{
    "items": ["c1", "c2", "c3"]
  }'
```

### Surfacing Trends

```bash
curl -X POST http://localhost:8000/api/v1/curation/trends \
  -H "Content-Type: application/json" \
  -d '{
    "category": "technology"
  }'
```

---

## Content Marketplace

Buy and sell content on the marketplace.

### Creating a Listing

```bash
curl -X POST http://localhost:8000/api/v1/marketplace/listings \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Digital Art Pack",
    "description": "High-quality digital art assets",
    "price": 29.99,
    "category": "digital-art",
    "creator_id": "creator-123"
  }'
```

### Browsing Listings

```bash
curl http://localhost:8000/api/v1/marketplace/listings
```

### Creating a Transaction

```bash
curl -X POST http://localhost:8000/api/v1/marketplace/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": "listing-123",
    "buyer_id": "user-456",
    "amount": 29.99
  }'
```

### Checking Trust Score

```bash
curl "http://localhost:8000/api/v1/marketplace/trust/user-123"
```

### Optimizing Pricing

```bash
curl -X POST "http://localhost:8000/api/v1/marketplace/pricing/pricing-123/optimize"
```

---

## Troubleshooting

### Common Issues

#### Service Unavailable

If the health check fails:

```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs backend

# Restart services
docker-compose restart
```

#### Database Connection Errors

```bash
# Verify PostgreSQL is running
docker-compose exec postgres pg_isready -U ugc_user

# Check database logs
docker-compose logs postgres
```

#### Redis Connection Errors

```bash
# Verify Redis is running
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping

# Check Redis logs
docker-compose logs redis
```

#### API Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Invalid input | Check request body format |
| 404 Not Found | Resource doesn't exist | Verify the ID/URL |
| 409 Conflict | Duplicate resource | Use a different ID |
| 422 Validation Error | Missing required fields | Check API schema |
| 429 Rate Limited | Too many requests | Slow down requests |
| 500 Server Error | Internal error | Check server logs |

### Getting Help

- **API Documentation:** http://localhost:8000/docs
- **Log Files:** `docker-compose logs -f`
- **GitHub Issues:** https://github.com/your-org/ugc-marketplace/issues

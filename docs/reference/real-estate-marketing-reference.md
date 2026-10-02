# Real Estate Marketing API Reference

> Last updated: 2026-10-02 | Base URL: `http://localhost:8000`

AI-powered marketing automation for real estate. Property listings, lead nurturing, virtual tours, analytics, and reporting.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /](#get-)
  - [GET /health](#get-health)
  - [Properties](#properties)
    - [POST /api/v1/properties](#post-apiv1properties)
    - [GET /api/v1/properties](#get-apiv1properties)
    - [GET /api/v1/properties/{property_id}](#get-apiv1propertiesproperty_id)
    - [PUT /api/v1/properties/{property_id}](#put-apiv1propertiesproperty_id)
    - [DELETE /api/v1/properties/{property_id}](#delete-apiv1propertiesproperty_id)
  - [Leads](#leads)
    - [POST /api/v1/leads](#post-apiv1leads)
    - [GET /api/v1/leads](#get-apiv1leads)
    - [GET /api/v1/leads/{lead_id}](#get-apiv1leadslead_id)
    - [PUT /api/v1/leads/{lead_id}](#put-apiv1leadslead_id)
    - [DELETE /api/v1/leads/{lead_id}](#delete-apiv1leadslead_id)
  - [Nurture](#nurture)
    - [POST /api/v1/leads/{lead_id}/nurture](#post-apiv1leadslead_idnurture)
  - [Analytics](#analytics)
    - [POST /api/v1/analytics/events](#post-apiv1analyticsevents)
    - [GET /api/v1/analytics/metrics](#get-apiv1analyticsmetrics)
    - [GET /api/v1/analytics/funnel](#get-apiv1analyticsfunnel)
    - [GET /api/v1/analytics/roi](#get-apiv1analyticsroi)
  - [Reports](#reports)
    - [POST /api/v1/reports/generate](#post-apiv1reportsgenerate)
- [Data Models](#data-models)
- [Error Codes](#error-codes)
- [Authentication](#authentication)

---

## Overview

The Real Estate Marketing API provides programmatic access to AI-driven marketing automation for real estate operations. It manages property listings, lead nurturing, virtual tours, marketing analytics, and automated reporting.

**Base Path:** `/api/v1`

**Technology:** FastAPI with Pydantic v2 models, structured logging via structlog, and CORS middleware.

---

## Endpoints

### GET /

Root endpoint with basic API information.

**Response (200):**

```json
{
  "name": "Real Estate Marketing API",
  "version": "0.1.0",
  "documentation": "/docs"
}
```

---

### GET /health

Health check endpoint for load balancers and monitoring.

**Response (200):**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-10-02T12:00:00Z",
  "services": {
    "api": "up",
    "database": "up",
    "redis": "up"
  }
}
```

---

## Properties

### POST /api/v1/properties

Create a new property listing with AI-optimized content.

**Request Body:**

```json
{
  "title": "Luxury Villa in Beverly Hills",
  "description": "Stunning 5-bedroom villa with pool and city views",
  "property_type": "single_family",
  "status": "active",
  "price": 2500000,
  "address": {
    "street": "123 Rodeo Drive",
    "city": "Beverly Hills",
    "state": "CA",
    "zip_code": "90210",
    "country": "US",
    "latitude": 34.0736,
    "longitude": -118.4004
  },
  "bedrooms": 5,
  "bathrooms": 4.5,
  "square_feet": 4200,
  "lot_size": 0.5,
  "year_built": 2018,
  "images": [
    "https://cdn.example.com/property/001/exterior.jpg",
    "https://cdn.example.com/property/001/interior.jpg"
  ],
  "amenities": ["pool", "garage", "garden", "smart_home"],
  "virtual_tour_url": "https://tours.example.com/property/001",
  "listing_agent": "agent_001",
  "mls_number": "MLS-2026-001"
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Luxury Villa in Beverly Hills",
  "description": "Stunning 5-bedroom villa with pool and city views",
  "property_type": "single_family",
  "status": "active",
  "price": 2500000,
  "address": {
    "street": "123 Rodeo Drive",
    "city": "Beverly Hills",
    "state": "CA",
    "zip_code": "90210",
    "country": "US",
    "latitude": 34.0736,
    "longitude": -118.4004
  },
  "bedrooms": 5,
  "bathrooms": 4.5,
  "square_feet": 4200,
  "lot_size": 0.5,
  "year_built": 2018,
  "images": ["https://cdn.example.com/property/001/exterior.jpg"],
  "amenities": ["pool", "garage", "garden", "smart_home"],
  "virtual_tour_url": "https://tours.example.com/property/001",
  "listing_agent": "agent_001",
  "mls_number": "MLS-2026-001",
  "created_at": "2026-10-02T12:00:00Z",
  "updated_at": "2026-10-02T12:00:00Z",
  "is_published": false,
  "view_count": 0,
  "lead_count": 0
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/properties \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Luxury Villa",
    "description": "Stunning villa with pool",
    "property_type": "single_family",
    "price": 2500000,
    "address": {
      "street": "123 Rodeo Drive",
      "city": "Beverly Hills",
      "state": "CA",
      "zip_code": "90210"
    }
  }'
```

---

### GET /api/v1/properties

List all property listings with pagination.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20) |
| `status` | string | No | Filter by status: active, pending, sold, expired, draft |
| `property_type` | string | No | Filter by type: single_family, condo, townhouse, multi_family, land, commercial |
| `min_price` | float | No | Minimum price filter |
| `max_price` | float | No | Maximum price filter |
| `city` | string | No | Filter by city |

**Response (200):**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Luxury Villa in Beverly Hills",
      "property_type": "single_family",
      "status": "active",
      "price": 2500000,
      "address": {
        "city": "Beverly Hills",
        "state": "CA"
      },
      "bedrooms": 5,
      "bathrooms": 4.5,
      "square_feet": 4200
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### GET /api/v1/properties/{property_id}

Get a specific property by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `property_id` | string (UUID) | Yes | Property identifier |

**Response (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Luxury Villa in Beverly Hills",
  "description": "Stunning 5-bedroom villa with pool and city views",
  "property_type": "single_family",
  "status": "active",
  "price": 2500000,
  "address": {
    "street": "123 Rodeo Drive",
    "city": "Beverly Hills",
    "state": "CA",
    "zip_code": "90210",
    "country": "US"
  },
  "bedrooms": 5,
  "bathrooms": 4.5,
  "square_feet": 4200,
  "lot_size": 0.5,
  "year_built": 2018,
  "images": ["https://cdn.example.com/property/001/exterior.jpg"],
  "amenities": ["pool", "garage", "garden"],
  "virtual_tour_url": "https://tours.example.com/property/001",
  "listing_agent": "agent_001",
  "mls_number": "MLS-2026-001",
  "created_at": "2026-10-02T12:00:00Z",
  "updated_at": "2026-10-02T12:00:00Z",
  "is_published": false,
  "view_count": 0,
  "lead_count": 0
}
```

---

### PUT /api/v1/properties/{property_id}

Update an existing property listing.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `property_id` | string (UUID) | Yes | Property identifier |

**Request Body:**

```json
{
  "title": "Updated Villa Title",
  "price": 2750000,
  "status": "pending",
  "amenities": ["pool", "garage", "garden", "smart_home", "wine_cellar"]
}
```

**Response (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Villa Title",
  "price": 2750000,
  "status": "pending",
  "updated_at": "2026-10-02T12:30:00Z"
}
```

---

### DELETE /api/v1/properties/{property_id}

Delete a property listing.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `property_id` | string (UUID) | Yes | Property identifier |

**Response:** `204 No Content`

---

## Leads

### POST /api/v1/leads

Create a new marketing lead.

**Request Body:**

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "source": "website",
  "status": "new",
  "budget_min": 500000,
  "budget_max": 1000000,
  "preferred_location": "Beverly Hills, CA",
  "notes": "Looking for a family home with pool",
  "tags": ["buyer", "pre-qualified"],
  "assigned_agent": "agent_001",
  "score": 0.0
}
```

**Response (201):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "source": "website",
  "status": "new",
  "budget_min": 500000,
  "budget_max": 1000000,
  "preferred_location": "Beverly Hills, CA",
  "notes": "Looking for a family home with pool",
  "tags": ["buyer", "pre-qualified"],
  "assigned_agent": "agent_001",
  "score": 0.0,
  "created_at": "2026-10-02T12:00:00Z",
  "updated_at": "2026-10-02T12:00:00Z",
  "last_contacted_at": null,
  "converted_at": null,
  "properties_viewed": [],
  "emails_sent": 0
}
```

---

### GET /api/v1/leads

List all leads with pagination and filtering.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number |
| `page_size` | integer | No | Items per page |
| `status` | string | No | Filter by status: new, contacted, qualified, nurturing, converted, lost |
| `source` | string | No | Filter by source: zillow, realtor, website, referral, social_media, email_campaign, open_house |
| `assigned_agent` | string | No | Filter by assigned agent |
| `min_score` | float | No | Minimum lead score (0-100) |
| `max_score` | float | No | Maximum lead score (0-100) |

**Response (200):**

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "source": "website",
      "status": "new",
      "score": 72.5
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### GET /api/v1/leads/{lead_id}

Get a specific lead by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lead_id` | string (UUID) | Yes | Lead identifier |

**Response (200):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "source": "website",
  "status": "new",
  "budget_min": 500000,
  "budget_max": 1000000,
  "preferred_location": "Beverly Hills, CA",
  "tags": ["buyer", "pre-qualified"],
  "assigned_agent": "agent_001",
  "score": 72.5,
  "created_at": "2026-10-02T12:00:00Z",
  "updated_at": "2026-10-02T12:00:00Z",
  "last_contacted_at": null,
  "converted_at": null,
  "properties_viewed": [],
  "emails_sent": 0
}
```

---

### PUT /api/v1/leads/{lead_id}

Update an existing lead.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lead_id` | string (UUID) | Yes | Lead identifier |

**Request Body:**

```json
{
  "status": "contacted",
  "score": 75.0,
  "notes": "Called, very interested in Beverly Hills properties",
  "tags": ["buyer", "pre-qualified", "hot"]
}
```

**Response (200):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "contacted",
  "score": 75.0,
  "updated_at": "2026-10-02T12:30:00Z"
}
```

---

### DELETE /api/v1/leads/{lead_id}

Delete a lead.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lead_id` | string (UUID) | Yes | Lead identifier |

**Response:** `204 No Content`

---

## Nurture

### POST /api/v1/leads/{lead_id}/nurture

Trigger an AI-powered nurture sequence for a lead.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lead_id` | string (UUID) | Yes | Lead identifier |

**Request Body:**

```json
{
  "sequence_type": "standard",
  "custom_message": "Hi John, I found some properties that match your criteria"
}
```

**Response (200):**

```json
{
  "lead_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "active",
  "message": "Nurture sequence 'standard' activated",
  "next_action": "welcome_email",
  "scheduled_at": "2026-10-02T12:00:00Z"
}
```

---

## Analytics

### POST /api/v1/analytics/events

Track a marketing analytics event.

**Request Body:**

```json
{
  "event_type": "property_view",
  "property_id": "550e8400-e29b-41d4-a716-446655440000",
  "lead_id": "660e8400-e29b-41d4-a716-446655440001",
  "source": "zillow",
  "medium": "organic",
  "campaign": "spring_listing",
  "metadata": {
    "device": "mobile",
    "duration_seconds": 145
  }
}
```

**Response (200):**

```json
{
  "tracked": true
}
```

---

### GET /api/v1/analytics/metrics

Get key marketing metrics summary.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | datetime (ISO 8601) | No | Start of date range (default: 30 days ago) |
| `end_date` | datetime (ISO 8601) | No | End of date range (default: now) |

**Response (200):**

```json
[
  {
    "name": "impressions",
    "value": 45230,
    "change_7d": 12.5,
    "change_30d": 28.3,
    "trend": "up"
  },
  {
    "name": "clicks",
    "value": 3420,
    "change_7d": 8.2,
    "change_30d": 15.7,
    "trend": "up"
  },
  {
    "name": "leads",
    "value": 285,
    "change_7d": -3.1,
    "change_30d": 10.4,
    "trend": "up"
  },
  {
    "name": "conversions",
    "value": 42,
    "change_7d": 5.0,
    "change_30d": 22.1,
    "trend": "up"
  },
  {
    "name": "revenue",
    "value": 1250000,
    "change_7d": 15.3,
    "change_30d": 35.2,
    "trend": "up"
  }
]
```

---

### GET /api/v1/analytics/funnel

Get marketing funnel analysis.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | datetime (ISO 8601) | No | Start of date range |
| `end_date` | datetime (ISO 8601) | No | End of date range |

**Response (200):**

```json
{
  "stages": [
    {
      "stage": "impression",
      "count": 45230,
      "conversion_rate": 100.0,
      "dropoff_rate": 0.0
    },
    {
      "stage": "click",
      "count": 3420,
      "conversion_rate": 7.6,
      "dropoff_rate": 92.4
    },
    {
      "stage": "lead",
      "count": 285,
      "conversion_rate": 8.3,
      "dropoff_rate": 91.7
    },
    {
      "stage": "qualified",
      "count": 156,
      "conversion_rate": 54.7,
      "dropoff_rate": 45.3
    },
    {
      "stage": "conversion",
      "count": 42,
      "conversion_rate": 26.9,
      "dropoff_rate": 73.1
    }
  ],
  "overall_conversion_rate": 0.09,
  "total_leads": 285,
  "total_conversions": 42
}
```

---

### GET /api/v1/analytics/roi

Calculate return on investment for marketing campaigns.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `campaign_id` | string | No | Filter by campaign ID |
| `start_date` | datetime (ISO 8601) | No | Start of date range |
| `end_date` | datetime (ISO 8601) | No | End of date range |

**Response (200):**

```json
{
  "total_spend": 15000,
  "total_revenue": 1250000,
  "roi_percentage": 8233.3,
  "cost_per_lead": 52.63,
  "cost_per_acquisition": 357.14,
  "attributed_conversions": 42,
  "campaign_id": null
}
```

---

## Reports

### POST /api/v1/reports/generate

Generate a marketing report.

**Request Body:**

```json
{
  "report_type": "performance",
  "start_date": "2026-09-01T00:00:00Z",
  "end_date": "2026-10-01T00:00:00Z",
  "property_ids": [
    "550e8400-e29b-41d4-a716-446655440000"
  ],
  "format": "pdf"
}
```

**Response (200):**

```json
{
  "report_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "completed",
  "download_url": "https://reports.example.com/reports/performance_20261002.pdf",
  "message": "Report 'performance' generated successfully"
}
```

---

## Data Models

### Property

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique property identifier |
| `title` | string | Property listing title (1-255 chars) |
| `description` | string | Property description (1-5000 chars) |
| `property_type` | PropertyType | Type of property |
| `status` | PropertyStatus | Listing status |
| `price` | float | Listing price (> 0) |
| `address` | Address | Physical address |
| `bedrooms` | float | Number of bedrooms (>= 0) |
| `bathrooms` | float | Number of bathrooms (>= 0) |
| `square_feet` | float | Interior square footage (> 0) |
| `lot_size` | float | Lot size in acres (> 0) |
| `year_built` | int | Year built (1800-2100) |
| `images` | list[string] | Image URLs |
| `amenities` | list[string] | Property amenities |
| `virtual_tour_url` | string | Virtual tour URL |
| `listing_agent` | string | Assigned agent ID |
| `mls_number` | string | MLS listing number |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `is_published` | bool | Whether listing is published |
| `view_count` | int | Total view count |
| `lead_count` | int | Total lead count |

### PropertyType Enum

| Value | Description |
|-------|-------------|
| `single_family` | Single-family home |
| `condo` | Condominium |
| `townhouse` | Townhouse |
| `multi_family` | Multi-family property |
| `land` | Land/lot |
| `commercial` | Commercial property |

### PropertyStatus Enum

| Value | Description |
|-------|-------------|
| `active` | Active listing |
| `pending` | Pending sale |
| `sold` | Sold |
| `expired` | Listing expired |
| `draft` | Draft listing |

### Lead

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique lead identifier |
| `first_name` | string | First name (1-100 chars) |
| `last_name` | string | Last name (1-100 chars) |
| `email` | string (EmailStr) | Email address |
| `phone` | string | Phone number (max 20 chars) |
| `source` | LeadSource | Lead source |
| `status` | LeadStatus | Lead status |
| `budget_min` | float | Minimum budget (> 0) |
| `budget_max` | float | Maximum budget (> 0) |
| `preferred_location` | string | Preferred location |
| `notes` | string | Notes (max 2000 chars) |
| `tags` | list[string] | Tags |
| `assigned_agent` | string | Assigned agent ID |
| `score` | float | Lead score (0-100) |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `last_contacted_at` | datetime | Last contact timestamp |
| `converted_at` | datetime | Conversion timestamp |
| `properties_viewed` | list[UUID] | Viewed property IDs |
| `emails_sent` | int | Emails sent count |

### LeadStatus Enum

| Value | Description |
|-------|-------------|
| `new` | New lead |
| `contacted` | Contacted |
| `qualified` | Qualified |
| `nurturing` | In nurture sequence |
| `converted` | Converted |
| `lost` | Lost lead |

### LeadSource Enum

| Value | Description |
|-------|-------------|
| `zillow` | Zillow |
| `realtor` | Realtor.com |
| `website` | Website |
| `referral` | Referral |
| `social_media` | Social media |
| `email_campaign` | Email campaign |
| `open_house` | Open house |

### Address

| Field | Type | Description |
|-------|------|-------------|
| `street` | string | Street address (1-255 chars) |
| `city` | string | City (1-100 chars) |
| `state` | string | State code (2 chars) |
| `zip_code` | string | ZIP code (5-10 chars) |
| `country` | string | Country code (default: US) |
| `latitude` | float | Latitude (-90 to 90) |
| `longitude` | float | Longitude (-180 to 180) |

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid authentication |
| `AUTHORIZATION_DENIED` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `UNPROCESSABLE_ENTITY` | 422 | Business logic validation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Response Format

```json
{
  "error": "Resource Not Found",
  "detail": "Property 550e8400-e29b-41d4-a716-446655440000 not found",
  "code": "RESOURCE_NOT_FOUND"
}
```

---

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <token>
```

In debug mode, CORS allows all origins. In production, CORS is restricted to configured origins only.

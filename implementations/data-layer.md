# Data Layer & CDP Integration Architecture

**Agentic AI Marketing Systems — Data Layer Design**

---

## Table of Contents

1. [Customer Data Platform (CDP) Architecture](#1-customer-data-platform-cdp-architecture)
2. [Identity Resolution & Unification](#2-identity-resolution--unification)
3. [Event Streaming & Ingestion](#3-event-streaming--ingestion)
4. [Data Warehouse Design](#4-data-warehouse-design)
5. [Real-Time Profile Updates](#5-real-time-profile-updates)
6. [CRM Integration](#6-crm-integration)
7. [Data Governance & Privacy](#7-data-governance--privacy)
8. [Data Flow Diagrams](#8-data-flow-diagrams)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Customer Data Platform (CDP) Architecture

### 1.1 Overview

The CDP serves as the central nervous system for agentic AI marketing. It unifies customer data from all touchpoints, resolves identities, maintains real-time profiles, and feeds AI agents with contextual, consented, and actionable customer intelligence.

### 1.2 Architectural Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONSUMPTION LAYER                            │
│  AI Agents │ Marketing Automation │ Personalization │ Analytics │
├─────────────────────────────────────────────────────────────────┤
│                    ORCHESTRATION LAYER                          │
│  Profile API │ Segment Engine │ Journey Builder │ ML Pipeline  │
├─────────────────────────────────────────────────────────────────┤
│                    PROCESSING LAYER                             │
│  Identity Resolution │ Event Processing │ Enrichment │ ML/AI   │
├─────────────────────────────────────────────────────────────────┤
│                    STORAGE LAYER                                │
│  Profile Store │ Event Store │ Warehouse │ Feature Store       │
├─────────────────────────────────────────────────────────────────┤
│                    INGESTION LAYER                              │
│  SDKs │ Webhooks │ API │ Batch ETL │ Streaming Connectors     │
├─────────────────────────────────────────────────────────────────┤
│                    SOURCE LAYER                                 │
│  Web │ Mobile │ CRM │ POS │ Email │ Ads │ Support │ IoT       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Ingestion API** | REST + GraphQL | Accept events from all sources |
| **Stream Processor** | Apache Kafka / Redpanda | Real-time event routing & processing |
| **Identity Graph** | Neo4j / Amazon Neptune | Store & query identity relationships |
| **Profile Store** | Redis + DynamoDB | Sub-10ms profile lookups |
| **Data Warehouse** | Snowflake / BigQuery | Analytics & ML training data |
| **Feature Store** | Feast / Tecton | ML feature serving |
| **Consent Manager** | Custom + OneTrust | Privacy & consent enforcement |
| **Segment Engine** | Custom (Rust/Go) | Real-time audience segmentation |

### 1.4 Deployment Model

- **Cloud-native**: Kubernetes-based microservices
- **Multi-region**: Active-active in US-East, EU-Central, APAC
- **Hybrid**: On-prem connectors for legacy CRM systems
- **Edge**: CDN-level event collection for sub-50ms ingestion

---

## 2. Identity Resolution & Unification

### 2.1 Identity Graph Model

The identity graph is the foundation of the CDP. It links all identifiers to a unified customer profile.

```
┌──────────────────────────────────────────────────────────────┐
│                    UNIFIED CUSTOMER PROFILE                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Email   │  │ Phone   │  │ Device  │  │ Cookie  │        │
│  │ hash    │  │ hash    │  │ IDFA/GAID│  │ ID      │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │               │
│       └────────────┴─────┬──────┴────────────┘               │
│                          │                                    │
│                   ┌──────┴──────┐                            │
│                   │  Person ID  │  (deterministic +          │
│                   │  (UUID v5)  │   probabilistic)            │
│                   └──────┬──────┘                            │
│                          │                                    │
│       ┌──────────────────┼──────────────────┐                │
│       │                  │                  │                 │
│  ┌────┴────┐       ┌────┴────┐       ┌────┴────┐           │
│  │ Account │       │ Household│       │ Company │           │
│  │ ID      │       │ ID      │       │ ID      │           │
│  └─────────┘       └─────────┘       └─────────┘           │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Resolution Strategies

#### Deterministic Matching (Exact)
- Email address (normalized, lowercased)
- Phone number (E.164 format)
- Customer ID (CRM, loyalty program)
- Device ID (IDFA, GAID, IDFV)
- Hashed login credentials

#### Probabilistic Matching (Fuzzy)
- Name + address combination
- Name + postal code
- Device fingerprint + behavioral patterns
- IP address + user agent + temporal proximity

#### Resolution Rules

```python
# Pseudocode for identity resolution pipeline
class IdentityResolver:
    def resolve(self, event):
        # Step 1: Deterministic lookup
        person_id = self.deterministic_match(event)
        
        if person_id:
            self.merge_identifiers(person_id, event.identifiers)
            return person_id
        
        # Step 2: Probabilistic scoring
        candidates = self.probabilistic_match(event, threshold=0.85)
        
        if len(candidates) == 1 and candidates[0].score > 0.95:
            self.merge_identifiers(candidates[0].person_id, event.identifiers)
            return candidates[0].person_id
        
        # Step 3: Create new profile
        return self.create_profile(event.identifiers)
    
    def deterministic_match(self, event):
        for identifier in event.identifiers:
            person_id = self.graph.get_node(identifier)
            if person_id:
                return person_id
        return None
```

### 2.3 Identity Graph Schema

```cypher
// Neo4j schema for identity graph
CREATE CONSTRAINT person_id IF NOT EXISTS
FOR (p:Person) REQUIRE p.person_id IS UNIQUE;

CREATE CONSTRAINT identifier_value IF NOT EXISTS
FOR (i:Identifier) REQUIRE i.value IS UNIQUE;

// Node types
(:Person {
  person_id: string,           // UUID v5
  created_at: datetime,
  updated_at: datetime,
  confidence_score: float,     // 0.0 - 1.0
  merge_count: integer,
  status: string               // active, merged, deleted
})

(:Identifier {
  type: string,                // email, phone, device_id, cookie_id
  value: string,               // hashed
  source: string,              // web, mobile, crm, pos
  first_seen: datetime,
  last_seen: datetime,
  confidence: float
})

(:Household {
  household_id: string,
  address_hash: string,
  income_bracket: string,
  size: integer
})

(:Company {
  company_id: string,
  domain: string,
  industry: string,
  size: string
})

// Relationship types
(:Person)-[:HAS_IDENTIFIER {confidence, source}]->(:Identifier)
(:Person)-[:BELONGS_TO]->(:Household)
(:Person)-[:WORKS_AT {title, department}]->(:Company)
(:Person)-[:MERGED_INTO {timestamp, reason}]->(:Person)
(:Person)-[:RELATED_TO {type, strength}]->(:Person)
```

### 2.4 Merge & Split Logic

**Merge Conditions:**
- Same email + same phone (confidence: 1.0)
- Same device + same name + same address (confidence: 0.95)
- Same email + similar name + same postal code (confidence: 0.85)

**Split Conditions:**
- Conflicting PII (different DOB, different SSN last-4)
- User-initiated profile separation
- Fraud detection signals

**Merge Audit Trail:**
Every merge/split operation is logged with:
- Timestamp and actor (system/user/agent)
- Source profiles and target profiles
- Confidence score and matching attributes
- Reversible merge token (for undo within 30 days)

---

## 3. Event Streaming & Ingestion

### 3.1 Event Taxonomy

All events follow a unified schema:

```json
{
  "event_id": "uuid-v4",
  "event_type": "string",           // page_view, purchase, email_open, etc.
  "event_version": "1.0",
  "timestamp": "ISO-8601",
  "received_at": "ISO-8601",
  
  "identifiers": {
    "email_hash": "sha256:...",
    "phone_hash": "sha256:...",
    "device_id": "...",
    "cookie_id": "...",
    "customer_id": "...",
    "session_id": "..."
  },
  
  "context": {
    "channel": "web|mobile|email|pos|call",
    "app_version": "...",
    "device_type": "...",
    "os": "...",
    "browser": "...",
    "ip_hash": "sha256:...",
    "user_agent": "...",
    "url": "...",
    "referrer": "...",
    "utm_source": "...",
    "utm_medium": "...",
    "utm_campaign": "..."
  },
  
  "properties": {
    // Event-specific payload
  },
  
  "consent": {
    "marketing": true,
    "analytics": true,
    "personalization": true,
    "timestamp": "ISO-8601"
  }
}
```

### 3.2 Event Categories

| Category | Events | Volume (est.) |
|----------|--------|---------------|
| **Behavioral** | page_view, click, scroll, search, video_play | 50K/sec |
| **Transactional** | purchase, cart_add, cart_remove, refund | 5K/sec |
| **Engagement** | email_open, email_click, push_open, sms_reply | 10K/sec |
| **Identity** | login, logout, register, profile_update | 2K/sec |
| **Lifecycle** | signup, activation, churn_risk, winback | 500/sec |
| **Attribution** | ad_click, ad_impression, landing_page | 20K/sec |

### 3.3 Ingestion Architecture

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│   Web    │  │  Mobile  │  │   CRM    │  │   POS    │
│   SDK    │  │   SDK    │  │ Webhook  │  │  Batch   │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────┐
│              API GATEWAY (Kong / Envoy)              │
│         Rate Limiting │ Auth │ Validation            │
└─────────────────────┬───────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  Kafka   │ │  Kafka   │ │  Kafka   │
    │ behavior │ │transaction│ │ identity │
    │  topic   │ │  topic   │ │  topic   │
    └────┬─────┘ └────┬─────┘ └────┬─────┘
         │             │             │
         └─────────────┼─────────────┘
                       ▼
              ┌────────────────┐
              │ Stream Process │
              │  (Flink/ksqlDB)│
              └───────┬────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    ┌─────────┐ ┌──────────┐ ┌──────────┐
    │ Profile │ │ Warehouse│ │  Real-time│
    │ Store   │ │  (S3)    │ │  Cache    │
    └─────────┘ └──────────┘ └──────────┘
```

### 3.4 Kafka Topic Design

| Topic | Partitions | Retention | RF | Purpose |
|-------|-----------|-----------|-----|---------|
| `events.behavioral` | 64 | 7 days | 3 | High-volume behavioral events |
| `events.transactional` | 32 | 30 days | 3 | Purchase & revenue events |
| `events.identity` | 16 | 90 days | 3 | Identity & consent changes |
| `events.engagement` | 32 | 7 days | 3 | Email, push, SMS events |
| `profile.updates` | 32 | 3 days | 3 | Profile change events |
| `profile.enriched` | 16 | 3 days | 3 | ML-enriched profile events |
| `consent.changes` | 8 | 365 days | 3 | Consent audit trail |
| `dead.letter` | 8 | 30 days | 3 | Failed events |

### 3.5 Ingestion SDKs

**JavaScript (Web):**
```javascript
// Lightweight (< 5KB gzipped) event tracker
class CDPConsent {
  constructor(config) {
    this.endpoint = config.endpoint;
    this.apiKey = config.apiKey;
    this.queue = [];
    this.flushInterval = config.flushInterval || 5000;
    this.batchSize = config.batchSize || 20;
  }
  
  track(eventType, properties = {}) {
    this.queue.push({
      event_type: eventType,
      event_version: '1.0',
      timestamp: new Date().toISOString(),
      identifiers: this.getIdentifiers(),
      context: this.getContext(),
      properties,
      consent: this.getConsent()
    });
    
    if (this.queue.length >= this.batchSize) {
      this.flush();
    }
  }
  
  async flush() {
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0, this.batchSize);
    
    await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({ events: batch }),
      keepalive: true  // For page unload
    });
  }
  
  getIdentifiers() {
    return {
      cookie_id: this.getCookie('_cdp_id'),
      email_hash: this.getEmailHash(),
      device_id: this.getDeviceId(),
      session_id: this.getSessionId()
    };
  }
}
```

**Mobile (iOS/Android):**
- Native SDKs with offline queueing
- Background sync when connectivity returns
- Battery-aware batching
- App lifecycle event tracking

### 3.6 Data Quality Gates

Every event passes through validation:

1. **Schema Validation**: JSON Schema enforcement
2. **PII Detection**: Automatic PII scanning & hashing
3. **Deduplication**: Event ID-based dedup (24-hour window)
4. **Enrichment**: GeoIP, device parsing, UTM normalization
5. **Consent Check**: Reject events without valid consent
6. **Rate Limiting**: Per-source throttling

---

## 4. Data Warehouse Design

### 4.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA WAREHOUSE                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Raw Zone   │  │  Cleaned     │  │  Curated     │      │
│  │  (S3/GCS)    │  │  Zone        │  │  Zone        │      │
│  │              │  │  (Snowflake) │  │  (Snowflake) │      │
│  │ • Raw events │→ │ • Validated  │→ │ • Star schema│      │
│  │ • Raw API    │  │ • Normalized │  │ • Aggregates │      │
│  │   responses  │  │ • Deduped    │  │ • Features   │      │
│  │ • Audit logs │  │ • Enriched   │  │ • ML labels  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Feature     │  │  Analytics   │  │  Data Marts  │      │
│  │  Store       │  │  Sandbox     │  │              │      │
│  │  (Feast)     │  │  (Snowflake) │  │ • Marketing  │      │
│  │              │  │              │  │ • Sales      │      │
│  │ • Real-time  │  │ • Ad-hoc     │  │ • Product    │      │
│  │ • Batch      │  │   queries    │  │ • Finance    │      │
│  │ • Training   │  │ • Data sci   │  │ • Executive  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Star Schema Design

#### Fact Tables

```sql
-- Core event fact table
CREATE TABLE fact_events (
    event_id            VARCHAR(36) PRIMARY KEY,
    event_type          VARCHAR(50) NOT NULL,
    event_timestamp     TIMESTAMP_NTZ NOT NULL,
    received_timestamp  TIMESTAMP_NTZ NOT NULL,
    
    -- Foreign keys to dimensions
    person_id           VARCHAR(36) NOT NULL,
    session_id          VARCHAR(36),
    device_id           VARCHAR(36),
    channel_id          INTEGER NOT NULL,
    campaign_id         INTEGER,
    content_id          INTEGER,
    
    -- Degenerate dimensions
    event_properties    VARIANT,        -- JSON blob
    
    -- Measures
    revenue             DECIMAL(18,2),
    quantity            INTEGER,
    
    -- Metadata
    etl_batch_id        VARCHAR(36),
    source_system       VARCHAR(50),
    created_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (event_timestamp, person_id);

-- Purchase fact table
CREATE TABLE fact_purchases (
    purchase_id         VARCHAR(36) PRIMARY KEY,
    person_id           VARCHAR(36) NOT NULL,
    order_id            VARCHAR(36) NOT NULL,
    purchase_timestamp   TIMESTAMP_NTZ NOT NULL,
    
    -- Financial
    subtotal            DECIMAL(18,2),
    tax                 DECIMAL(18,2),
    shipping            DECIMAL(18,2),
    discount            DECIMAL(18,2),
    total               DECIMAL(18,2),
    currency            VARCHAR(3),
    
    -- Attribution
    attribution_model   VARCHAR(20),    -- first_touch, last_touch, linear
    touchpoint_count    INTEGER,
    first_touch_channel VARCHAR(50),
    last_touch_channel  VARCHAR(50),
    
    -- Fulfillment
    status              VARCHAR(20),
    fulfillment_date    DATE,
    
    FOREIGN KEY (person_id) REFERENCES dim_person(person_id)
);

-- Email engagement fact table
CREATE TABLE fact_email_engagement (
    engagement_id       VARCHAR(36) PRIMARY KEY,
    person_id           VARCHAR(36) NOT NULL,
    campaign_id         INTEGER NOT NULL,
    email_send_id       VARCHAR(36) NOT NULL,
    
    -- Timestamps
    sent_at             TIMESTAMP_NTZ,
    delivered_at        TIMESTAMP_NTZ,
    opened_at           TIMESTAMP_NTZ,
    clicked_at          TIMESTAMP_NTZ,
    converted_at        TIMESTAMP_NTZ,
    
    -- Engagement metrics
    open_count          INTEGER DEFAULT 0,
    click_count         INTEGER DEFAULT 0,
    conversion_count    INTEGER DEFAULT 0,
    
    -- Content
    subject_line        VARCHAR(500),
    email_variant       VARCHAR(10),    -- A/B test variant
    
    FOREIGN KEY (person_id) REFERENCES dim_person(person_id)
);
```

#### Dimension Tables

```sql
-- Person dimension (SCD Type 2)
CREATE TABLE dim_person (
    person_id           VARCHAR(36) PRIMARY KEY,
    person_key          VARCHAR(36) NOT NULL,  -- Surrogate key for SCD
    
    -- Attributes
    email_hash          VARCHAR(64),
    phone_hash          VARCHAR(64),
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    date_of_birth       DATE,
    gender              VARCHAR(20),
    
    -- Address
    address_hash        VARCHAR(64),
    city                VARCHAR(100),
    state               VARCHAR(50),
    postal_code         VARCHAR(20),
    country             VARCHAR(2),
    
    -- Segments
    lifecycle_stage     VARCHAR(20),    -- lead, prospect, customer, churned
    customer_tier       VARCHAR(20),    -- bronze, silver, gold, platinum
    lifetime_value      DECIMAL(18,2),
    churn_risk_score    DECIMAL(5,4),
    
    -- SCD Type 2 columns
    effective_date      DATE NOT NULL,
    expiration_date     DATE,
    is_current          BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    first_seen_at       TIMESTAMP_NTZ,
    last_seen_at        TIMESTAMP_NTZ,
    merge_count         INTEGER DEFAULT 0,
    source_system       VARCHAR(50)
);

-- Channel dimension
CREATE TABLE dim_channel (
    channel_id          INTEGER PRIMARY KEY,
    channel_name        VARCHAR(50) NOT NULL,   -- web, mobile, email, pos
    channel_category    VARCHAR(50),            -- owned, paid, earned
    channel_detail      VARCHAR(100),           -- ios_app, android_app
    is_active           BOOLEAN DEFAULT TRUE
);

-- Campaign dimension
CREATE TABLE dim_campaign (
    campaign_id         INTEGER PRIMARY KEY,
    campaign_name       VARCHAR(200) NOT NULL,
    campaign_type       VARCHAR(50),            -- email, push, display, search
    start_date          DATE,
    end_date            DATE,
    budget              DECIMAL(18,2),
    target_audience     VARCHAR(200),
    utm_source          VARCHAR(100),
    utm_medium          VARCHAR(100),
    utm_campaign        VARCHAR(200),
    created_by          VARCHAR(100),
    status              VARCHAR(20)
);

-- Date dimension
CREATE TABLE dim_date (
    date_key            INTEGER PRIMARY KEY,    -- YYYYMMDD
    full_date           DATE NOT NULL,
    day_of_week         INTEGER,
    day_name            VARCHAR(10),
    day_of_month        INTEGER,
    day_of_year         INTEGER,
    week_of_year        INTEGER,
    month_number        INTEGER,
    month_name          VARCHAR(10),
    quarter             INTEGER,
    year                INTEGER,
    fiscal_quarter      INTEGER,
    is_weekend          BOOLEAN,
    is_holiday          BOOLEAN,
    holiday_name        VARCHAR(50)
);
```

### 4.3 Aggregation Tables

```sql
-- Daily person summary (materialized view)
CREATE TABLE agg_person_daily (
    person_id           VARCHAR(36) NOT NULL,
    date_key            INTEGER NOT NULL,
    
    -- Engagement metrics
    sessions            INTEGER DEFAULT 0,
    page_views          INTEGER DEFAULT 0,
    events              INTEGER DEFAULT 0,
    time_on_site        INTEGER DEFAULT 0,      -- seconds
    
    -- Transaction metrics
    orders              INTEGER DEFAULT 0,
    revenue             DECIMAL(18,2) DEFAULT 0,
    items_purchased     INTEGER DEFAULT 0,
    
    -- Email metrics
    emails_sent         INTEGER DEFAULT 0,
    emails_opened       INTEGER DEFAULT 0,
    emails_clicked      INTEGER DEFAULT 0,
    
    -- Channel breakdown (JSON)
    channel_breakdown   VARIANT,
    
    PRIMARY KEY (person_id, date_key)
);

-- Real-time segment membership
CREATE TABLE agg_segment_membership (
    segment_id          INTEGER NOT NULL,
    person_id           VARCHAR(36) NOT NULL,
    entered_at          TIMESTAMP_NTZ,
    exited_at           TIMESTAMP_NTZ,
    is_current          BOOLEAN DEFAULT TRUE,
    
    PRIMARY KEY (segment_id, person_id, entered_at)
);
```

### 4.4 ETL/ELT Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Kafka   │    │  Stream  │    │  Batch   │    │  dbt     │
│  Topics  │ →  │  Ingest  │ →  │  Ingest  │ →  │  Models  │
│          │    │ (Flink)  │    │ (Airflow)│    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │               │               │
                     ▼               ▼               ▼
               ┌──────────┐   ┌──────────┐   ┌──────────┐
               │  S3 Raw  │   │  S3 Raw  │   │ Snowflake│
               │  (Parquet)│   │  (CSV)   │   │  Models  │
               └──────────┘   └──────────┘   └──────────┘
```

**Pipeline Schedule:**
- **Real-time**: Kafka → Flink → Profile Store (sub-second)
- **Near-real-time**: Kafka → Flink → Warehouse (5-minute micro-batches)
- **Batch**: Airflow → dbt → Warehouse (hourly/daily)
- **ML Features**: Airflow → Feature Store (daily + real-time updates)

---

## 5. Real-Time Profile Updates

### 5.1 Profile Update Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Event   │     │  Kafka   │     │  Flink   │     │  Profile │
│  Source  │ ──→ │  Topic   │ ──→ │  Job     │ ──→ │  Store   │
└──────────┘     └──────────┘     └────┬─────┘     └──────────┘
                                       │
                              ┌────────┼────────┐
                              ▼        ▼        ▼
                         ┌────────┐ ┌────────┐ ┌────────┐
                         │Identity│ │Segment │ │ Feature│
                         │Resolve │ │Eval    │ │Compute │
                         └────────┘ └────────┘ └────────┘
```

### 5.2 Profile Data Model

```json
{
  "person_id": "uuid-v5",
  "version": 42,
  "updated_at": "2026-10-01T10:30:00Z",
  
  "identifiers": {
    "emails": [
      {"hash": "sha256:...", "is_primary": true, "verified": true}
    ],
    "phones": [
      {"hash": "sha256:...", "is_primary": true, "verified": true}
    ],
    "devices": [
      {"id": "...", "type": "mobile", "os": "iOS", "first_seen": "..."}
    ],
    "external_ids": {
      "crm_id": "...",
      "loyalty_id": "...",
      "adobe_id": "..."
    }
  },
  
  "attributes": {
    "first_name": "...",
    "last_name": "...",
    "date_of_birth": "...",
    "gender": "...",
    "preferred_language": "en",
    "preferred_currency": "USD",
    "timezone": "America/New_York"
  },
  
  "address": {
    "street_hash": "...",
    "city": "...",
    "state": "...",
    "postal_code": "...",
    "country": "US",
    "geo": {"lat": 40.7128, "lon": -74.0060}
  },
  
  "segments": [
    {"id": 1, "name": "high_value", "entered_at": "..."},
    {"id": 2, "name": "email_engaged", "entered_at": "..."}
  ],
  
  "metrics": {
    "lifetime_value": 1250.00,
    "total_orders": 15,
    "total_revenue": 1250.00,
    "avg_order_value": 83.33,
    "last_purchase_at": "...",
    "first_purchase_at": "...",
    "purchase_frequency_days": 14.5,
    "email_open_rate_30d": 0.45,
    "email_click_rate_30d": 0.12,
    "web_sessions_30d": 8,
    "web_time_30d_seconds": 1200,
    "churn_risk_score": 0.23,
    "engagement_score": 0.78,
    "propensity_to_purchase": 0.65
  },
  
  "consent": {
    "marketing": {"granted": true, "timestamp": "...", "source": "..."},
    "analytics": {"granted": true, "timestamp": "...", "source": "..."},
    "personalization": {"granted": true, "timestamp": "...", "source": "..."},
    "data_sharing": {"granted": false, "timestamp": "...", "source": "..."}
  },
  
  "preferences": {
    "communication_channel": "email",
    "email_frequency": "weekly",
    "product_categories": ["electronics", "home"],
    "content_topics": ["technology", "diy"]
  },
  
  "timeline": [
    {"timestamp": "...", "event": "profile_created", "source": "web"},
    {"timestamp": "...", "event": "email_verified", "source": "web"},
    {"timestamp": "...", "event": "first_purchase", "source": "pos"},
    {"timestamp": "...", "event": "segment_entered:high_value", "source": "system"}
  ]
}
```

### 5.3 Real-Time Update Pipeline

```python
# Apache Flink job for real-time profile updates
class ProfileUpdateJob:
    def __init__(self):
        self.profile_store = RedisCluster()
        self.identity_resolver = IdentityResolver()
        self.segment_engine = SegmentEngine()
        self.feature_computer = FeatureComputer()
    
    def process(self, event):
        # Step 1: Resolve identity
        person_id = self.identity_resolver.resolve(event)
        
        # Step 2: Fetch current profile
        profile = self.profile_store.get(person_id)
        
        # Step 3: Update profile based on event type
        updated_profile = self.apply_event(profile, event)
        
        # Step 4: Recompute derived metrics
        updated_profile = self.feature_computer.compute(updated_profile)
        
        # Step 5: Evaluate segment membership
        segment_changes = self.segment_engine.evaluate(updated_profile)
        updated_profile.segments = segment_changes.current
        
        # Step 6: Update profile store
        self.profile_store.set(person_id, updated_profile, ttl=90_days)
        
        # Step 7: Publish profile update event
        self.publish_profile_update(person_id, updated_profile, segment_changes)
        
        # Step 8: Update real-time features
        self.feature_store.update_realtime(person_id, updated_profile)
    
    def apply_event(self, profile, event):
        event_type = event['event_type']
        
        if event_type == 'page_view':
            profile.metrics.web_sessions_30d += 1
            profile.metrics.web_time_30d_seconds += event.properties.get('duration', 0)
        
        elif event_type == 'purchase':
            profile.metrics.total_orders += 1
            profile.metrics.total_revenue += event.properties['revenue']
            profile.metrics.lifetime_value += event.properties['revenue']
            profile.metrics.avg_order_value = (
                profile.metrics.total_revenue / profile.metrics.total_orders
            )
            profile.metrics.last_purchase_at = event['timestamp']
        
        elif event_type == 'email_open':
            profile.metrics.email_open_rate_30d = self.compute_rolling_rate(
                profile, 'email_open', window_days=30
            )
        
        # Update timeline
        profile.timeline.append({
            'timestamp': event['timestamp'],
            'event': event_type,
            'source': event['context']['channel']
        })
        
        # Keep only last 100 timeline entries
        profile.timeline = profile.timeline[-100:]
        
        return profile
```

### 5.4 Profile API

```graphql
# GraphQL API for profile access
type Query {
  # Get profile by person ID
  profile(personId: ID!): Profile
  
  # Get profile by identifier (email, phone, etc.)
  profileByIdentifier(
    type: IdentifierType!
    value: String!
  ): Profile
  
  # Search profiles
  searchProfiles(
    filter: ProfileFilter
    sort: ProfileSort
    pagination: PaginationInput
  ): ProfileConnection
  
  # Get segment membership
  segmentMembers(
    segmentId: ID!
    pagination: PaginationInput
  ): ProfileConnection
  
  # Get profile timeline
  profileTimeline(
    personId: ID!
    limit: Int = 50
  ): [TimelineEvent!]!
  
  # Real-time profile stream (WebSocket)
  profileUpdates(
    personIds: [ID!]!
  ): ProfileUpdate!
}

type Profile {
  personId: ID!
  version: Int!
  updatedAt: DateTime!
  
  identifiers: Identifiers!
  attributes: ProfileAttributes
  address: Address
  
  segments: [SegmentMembership!]!
  metrics: ProfileMetrics!
  consent: Consent!
  preferences: Preferences
  timeline(limit: Int): [TimelineEvent!]!
  
  # Computed fields
  lifetimeValue: Float!
  churnRisk: Float!
  engagementScore: Float!
  nextBestAction: NextBestAction
}

type Mutation {
  # Update profile attributes
  updateProfile(
    personId: ID!
    input: ProfileUpdateInput!
  ): Profile!
  
  # Update consent
  updateConsent(
    personId: ID!
    consent: ConsentInput!
  ): Consent!
  
  # Merge profiles (admin only)
  mergeProfiles(
    sourcePersonIds: [ID!]!
    targetPersonId: ID!
    reason: String!
  ): MergeResult!
  
  # Delete profile (GDPR right to erasure)
  deleteProfile(
    personId: ID!
    reason: String!
  ): DeletionResult!
}
```

### 5.5 Caching Strategy

| Layer | Technology | TTL | Use Case |
|-------|-----------|-----|----------|
| **L1: Edge** | Cloudflare Workers KV | 60s | Public segments, campaign config |
| **L2: Application** | Redis Cluster | 5 min | Full profiles, segment memberships |
| **L3: In-Memory** | Caffeine (JVM) | 30s | Hot profiles (frequently accessed) |
| **L4: Persistent** | DynamoDB + DAX | indefinite | Authoritative profile store |

**Cache Invalidation:**
- Event-driven invalidation via Kafka `profile.updates` topic
- Version-based optimistic locking
- Write-through caching for consistency

---

## 6. CRM Integration

### 6.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CRM INTEGRATION LAYER                       │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Salesforce│  │  HubSpot │  │  Zoho    │  │  Custom  │       │
│  │          │  │          │  │  CRM     │  │  CRM     │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │              │
│       ▼              ▼              ▼              ▼              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              UNIFIED CRM ADAPTER LAYER                   │    │
│  │  • Field mapping & transformation                       │    │
│  │  • Rate limiting & backoff                              │    │
│  │  • Conflict resolution                                  │    │
│  │  • Sync orchestration                                   │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   CDP CORE                               │    │
│  │  Profile Store │ Identity Graph │ Consent Manager        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 CRM Adapter Pattern

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class CRMSyncConfig:
    crm_type: str                          # salesforce, hubspot, zoho
    sync_direction: str                    # bidirectional, cdp_to_crm, crm_to_cdp
    sync_frequency: str                    # realtime, hourly, daily
    field_mappings: Dict[str, str]         # cdp_field -> crm_field
    conflict_resolution: str               # cdp_wins, crm_wins, timestamp_wins
    batch_size: int = 100
    rate_limit_rps: int = 10

class CRMAdapter(ABC):
    """Abstract base class for CRM adapters"""
    
    def __init__(self, config: CRMSyncConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit_rps)
    
    @abstractmethod
    async def authenticate(self) -> str:
        """OAuth2 or API key authentication"""
        pass
    
    @abstractmethod
    async def upsert_contact(self, profile: dict) -> str:
        """Create or update a contact in CRM"""
        pass
    
    @abstractmethod
    async def get_contact(self, crm_id: str) -> dict:
        """Fetch contact from CRM"""
        pass
    
    @abstractmethod
    async def search_contacts(self, query: dict) -> List[dict]:
        """Search contacts by criteria"""
        pass
    
    @abstractmethod
    async def get_field_metadata(self) -> dict:
        """Get CRM field definitions for mapping"""
        pass
    
    async def sync_profile(self, person_id: str):
        """Sync a CDP profile to CRM"""
        profile = await self.cdp.get_profile(person_id)
        crm_record = self.transform_to_crm(profile)
        
        # Check for existing contact
        existing = await self.search_contacts({
            'email_hash': profile['identifiers']['emails'][0]['hash']
        })
        
        if existing:
            # Update existing
            crm_id = existing[0]['id']
            await self.upsert_contact(crm_record, crm_id)
        else:
            # Create new
            crm_id = await self.upsert_contact(crm_record)
        
        # Store mapping
        await self.cdp.store_crm_mapping(person_id, self.config.crm_type, crm_id)
        
        return crm_id
    
    def transform_to_crm(self, profile: dict) -> dict:
        """Transform CDP profile to CRM format using field mappings"""
        crm_record = {}
        for cdp_field, crm_field in self.config.field_mappings.items():
            value = self.get_nested_value(profile, cdp_field)
            if value is not None:
                self.set_nested_value(crm_record, crm_field, value)
        return crm_record

class SalesforceAdapter(CRMAdapter):
    """Salesforce-specific adapter"""
    
    def __init__(self, config: CRMSyncConfig):
        super().__init__(config)
        self.api_version = 'v58.0'
        self.base_url = None
        self.access_token = None
    
    async def authenticate(self) -> str:
        # OAuth2 JWT Bearer flow
        auth = SalesforceAuth(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            username=self.config.username,
            private_key=self.config.private_key
        )
        self.access_token = await auth.authenticate()
        self.base_url = f"https://{self.config.instance}.salesforce.com/services/data/{self.api_version}"
        return self.access_token
    
    async def upsert_contact(self, profile: dict, crm_id: Optional[str] = None) -> str:
        await self.rate_limiter.acquire()
        
        sf_record = {
            'FirstName': profile.get('attributes', {}).get('first_name'),
            'LastName': profile.get('attributes', {}).get('last_name'),
            'Email': profile.get('identifiers', {}).get('emails', [{}])[0].get('value'),
            'Phone': profile.get('identifiers', {}).get('phones', [{}])[0].get('value'),
            'MailingCity': profile.get('address', {}).get('city'),
            'MailingState': profile.get('address', {}).get('state'),
            'MailingPostalCode': profile.get('address', {}).get('postal_code'),
            'MailingCountry': profile.get('address', {}).get('country'),
            'LeadSource': 'CDP',
            'Custom_Lifetime_Value__c': profile.get('metrics', {}).get('lifetime_value'),
            'Custom_Engagement_Score__c': profile.get('metrics', {}).get('engagement_score'),
            'Custom_Churn_Risk__c': profile.get('metrics', {}).get('churn_risk_score'),
            'Custom_CDP_Person_ID__c': profile.get('person_id'),
            'Custom_Consent_Marketing__c': profile.get('consent', {}).get('marketing', {}).get('granted'),
            'Custom_Consent_Analytics__c': profile.get('consent', {}).get('analytics', {}).get('granted'),
        }
        
        if crm_id:
            # Update
            response = await self._patch(f/sobjects/Contact/{crm_id}", sf_record)
        else:
            # Create
            response = await self._post('/sobjects/Contact', sf_record)
            crm_id = response['id']
        
        return crm_id

class HubSpotAdapter(CRMAdapter):
    """HubSpot-specific adapter"""
    # Similar implementation for HubSpot API
    pass

class ZohoCRMAdapter(CRMAdapter):
    """Zoho CRM-specific adapter"""
    # Similar implementation for Zoho API
    pass
```

### 6.3 Bidirectional Sync

```
┌──────────┐                    ┌──────────┐
│   CDP    │ ─── Webhook ────→  │   CRM    │
│          │ ←── Polling ─────  │          │
│          │ ─── API Push ───→  │          │
│          │ ←── API Pull ────  │          │
└──────────┘                    └──────────┘
```

**Sync Strategies:**

| Strategy | Direction | Latency | Use Case |
|----------|-----------|---------|----------|
| **Real-time Webhook** | CDP → CRM | < 1s | Profile updates, consent changes |
| **Real-time API** | CRM → CDP | < 1s | New leads, deal updates |
| **Near-real-time** | Bidirectional | 5 min | Batch field sync |
| **Scheduled Batch** | Bidirectional | 24 hr | Full reconciliation |

### 6.4 Field Mapping Configuration

```yaml
# field_mappings.yaml
salesforce:
  contact:
    # CDP Field -> Salesforce Field
    "person_id": "Custom_CDP_Person_ID__c"
    "attributes.first_name": "FirstName"
    "attributes.last_name": "LastName"
    "attributes.email": "Email"
    "attributes.phone": "Phone"
    "address.city": "MailingCity"
    "address.state": "MailingState"
    "address.postal_code": "MailingPostalCode"
    "address.country": "MailingCountry"
    "metrics.lifetime_value": "Custom_Lifetime_Value__c"
    "metrics.engagement_score": "Custom_Engagement_Score__c"
    "metrics.churn_risk_score": "Custom_Churn_Risk__c"
    "consent.marketing.granted": "Custom_Consent_Marketing__c"
    "consent.analytics.granted": "Custom_Consent_Analytics__c"
    "segments": "Custom_Segments__c"  # JSON array
  
  opportunity:
    "person_id": "Custom_CDP_Person_ID__c"
    "deal_value": "Amount"
    "deal_stage": "StageName"
    "expected_close_date": "CloseDate"
    "probability": "Probability"

hubspot:
  contact:
    "person_id": "cdp_person_id"
    "attributes.first_name": "firstname"
    "attributes.last_name": "lastname"
    "attributes.email": "email"
    "attributes.phone": "phone"
    "address.city": "city"
    "address.state": "state"
    "address.postal_code": "zip"
    "address.country": "country"
    "metrics.lifetime_value": "lifetime_value"
    "metrics.engagement_score": "engagement_score"
    "metrics.churn_risk_score": "churn_risk_score"
    "consent.marketing.granted": "marketing_consent"
    "consent.analytics.granted": "analytics_consent"
```

### 6.5 Conflict Resolution

```python
class ConflictResolver:
    def resolve(self, cdp_value, crm_value, cdp_timestamp, crm_timestamp, strategy):
        if strategy == 'cdp_wins':
            return cdp_value
        elif strategy == 'crm_wins':
            return crm_value
        elif strategy == 'timestamp_wins':
            return cdp_value if cdp_timestamp > crm_timestamp else crm_value
        elif strategy == 'merge':
            return self.merge_values(cdp_value, crm_value)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def merge_values(self, cdp_value, crm_value):
        """Merge non-null values from both sources"""
        if cdp_value is None:
            return crm_value
        if crm_value is None:
            return cdp_value
        if isinstance(cdp_value, dict) and isinstance(crm_value, dict):
            merged = crm_value.copy()
            merged.update(cdp_value)
            return merged
        return cdp_value  # Default to CDP for scalar conflicts
```

---

## 7. Data Governance & Privacy

### 7.1 Governance Framework

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA GOVERNANCE FRAMEWORK                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Data       │  │   Data       │  │   Data       │         │
│  │   Quality    │  │   Privacy    │  │   Security   │         │
│  │              │  │              │  │              │         │
│  │ • Completeness│  │ • Consent    │  │ • Encryption │         │
│  │ • Accuracy   │  │ • Retention  │  │ • Access Ctrl│         │
│  │ • Consistency│  │ • Right to   │  │ • Audit Logs │         │
│  │ • Timeliness │  │   erasure    │  │ • Masking    │         │
│  │ • Validity   │  │ • Data       │  │ • Tokenization│        │
│  │ • Uniqueness │  │   minimization│ │ • Key mgmt   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Metadata   │  │   Data       │  │   Compliance │         │
│  │   Management │  │   Lineage    │  │   Reporting  │         │
│  │              │  │              │  │              │         │
│  │ • Data catalog│  │ • Source     │  │ • GDPR       │         │
│  │ • Business   │  │   tracking   │  │ • CCPA       │         │
│  │   glossary   │  │ • Impact     │  │ • LGPD       │         │
│  │ • Tagging    │  │   analysis   │  │ • PIPEDA      │         │
│  │ • Classification│ │ • Transform │  │ • SOC 2      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Consent Management

```python
class ConsentManager:
    """Centralized consent management across all channels"""
    
    CONSENT_TYPES = {
        'marketing': {
            'description': 'Marketing communications',
            'channels': ['email', 'push', 'sms', 'direct_mail'],
            'default': False,
            'required_explicit': True
        },
        'analytics': {
            'description': 'Analytics and measurement',
            'channels': ['web', 'mobile'],
            'default': True,
            'required_explicit': False
        },
        'personalization': {
            'description': 'Personalized experiences',
            'channels': ['web', 'mobile', 'email'],
            'default': True,
            'required_explicit': False
        },
        'data_sharing': {
            'description': 'Data sharing with partners',
            'channels': ['all'],
            'default': False,
            'required_explicit': True
        },
        'ai_processing': {
            'description': 'AI/ML processing of data',
            'channels': ['all'],
            'default': False,
            'required_explicit': True
        }
    }
    
    def record_consent(self, person_id, consent_type, granted, source, metadata=None):
        """Record a consent decision"""
        consent_record = {
            'person_id': person_id,
            'consent_type': consent_type,
            'granted': granted,
            'timestamp': datetime.utcnow().isoformat(),
            'source': source,  # web_form, mobile_app, api, crm
            'metadata': metadata or {},
            'ip_hash': self.hash_ip(metadata.get('ip')),
            'user_agent': metadata.get('user_agent'),
            'version': '1.0'
        }
        
        # Store in consent store
        self.consent_store.append(consent_record)
        
        # Update profile
        self.profile_store.update_consent(person_id, consent_type, consent_record)
        
        # Audit log
        self.audit_log.record('consent_change', consent_record)
        
        # Propagate to CRM
        self.crm_sync.sync_consent(person_id, consent_record)
    
    def check_consent(self, person_id, consent_type, channel=None):
        """Check if consent is granted for a specific purpose"""
        consent = self.consent_store.get_latest(person_id, consent_type)
        
        if not consent:
            return self.CONSENT_TYPES[consent_type]['default']
        
        if channel and consent.get('channels'):
            return consent['granted'] and channel in consent['channels']
        
        return consent['granted']
    
    def enforce_consent(self, event):
        """Enforce consent before processing an event"""
        person_id = event.get('person_id')
        channel = event.get('context', {}).get('channel')
        
        required_consents = ['analytics']  # Minimum required
        
        if event['event_type'] in MARKETING_EVENTS:
            required_consents.append('marketing')
        
        if event['event_type'] in PERSONALIZATION_EVENTS:
            required_consents.append('personalization')
        
        for consent_type in required_consents:
            if not self.check_consent(person_id, consent_type, channel):
                raise ConsentError(
                    f"Missing consent: {consent_type} for person {person_id}"
                )
        
        return True
```

### 7.3 Data Retention Policy

| Data Category | Retention Period | Action After Expiration | Legal Basis |
|---------------|-----------------|------------------------|-------------|
| **Raw events** | 2 years | Anonymize (remove PII) | Legitimate interest |
| **Processed profiles** | 3 years | Delete or anonymize | Consent |
| **Consent records** | 7 years | Archive | Legal obligation |
| **Audit logs** | 7 years | Archive | Legal obligation |
| **CRM sync logs** | 1 year | Delete | Legitimate interest |
| **ML training data** | 5 years | Anonymize | Legitimate interest |
| **Deleted profiles** | 30 days | Permanent delete | GDPR Article 17 |

### 7.4 Privacy Rights Automation

```python
class PrivacyRightsManager:
    """Automate GDPR/CCPA privacy rights requests"""
    
    async def handle_access_request(self, person_id: str):
        """GDPR Article 15: Right of access"""
        # Gather all data about the person
        profile = await self.cdp.get_full_profile(person_id)
        events = await self.warehouse.get_person_events(person_id)
        consents = await self.consent_store.get_all_consents(person_id)
        crm_data = await self.crm_sync.get_all_crm_data(person_id)
        ml_data = await self.feature_store.get_person_features(person_id)
        
        # Compile report
        report = {
            'request_type': 'access',
            'person_id': person_id,
            'generated_at': datetime.utcnow().isoformat(),
            'data_categories': {
                'profile': profile,
                'events': events,
                'consents': consents,
                'crm_data': crm_data,
                'ml_features': ml_data
            },
            'retention_schedule': self.get_retention_schedule(person_id),
            'third_party_sharing': self.get_third_party_sharing(person_id)
        }
        
        # Deliver securely
        await self.secure_deliver(report, person_id)
        
        # Audit
        self.audit_log.record('privacy_access_request', {
            'person_id': person_id,
            'delivered_at': datetime.utcnow().isoformat()
        })
    
    async def handle_deletion_request(self, person_id: str):
        """GDPR Article 17: Right to erasure"""
        # Step 1: Verify identity
        await self.verify_identity(person_id)
        
        # Step 2: Delete from profile store
        await self.profile_store.delete(person_id)
        
        # Step 3: Delete from identity graph
        await self.identity_graph.delete_person(person_id)
        
        # Step 4: Anonymize events in warehouse
        await self.warehouse.anonymize_person_events(person_id)
        
        # Step 5: Delete from feature store
        await self.feature_store.delete_person_features(person_id)
        
        # Step 6: Propagate deletion to CRMs
        await self.crm_sync.delete_from_all_crms(person_id)
        
        # Step 7: Delete from consent store
        await self.consent_store.delete_all_consents(person_id)
        
        # Step 8: Invalidate caches
        await self.cache.invalidate_person(person_id)
        
        # Step 9: Record deletion (minimal audit trail)
        self.audit_log.record('privacy_deletion_request', {
            'person_id_hash': hashlib.sha256(person_id.encode()).hexdigest(),
            'deleted_at': datetime.utcnow().isoformat()
        })
        
        # Step 10: Confirm completion
        return {'status': 'completed', 'person_id_hash': hashlib.sha256(person_id.encode()).hexdigest()}
    
    async def handle_portability_request(self, person_id: str):
        """GDPR Article 20: Right to data portability"""
        data = await self.gather_portable_data(person_id)
        
        # Export in machine-readable format (JSON)
        export = {
            'format': 'JSON',
            'schema_version': '1.0',
            'exported_at': datetime.utcnow().isoformat(),
            'data': data
        }
        
        return export
```

### 7.5 Data Security

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYERS                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  TRANSPORT: TLS 1.3, mTLS for service-to-service        │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  APPLICATION: OAuth 2.0 + OIDC, RBAC, ABAC              │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  DATA: AES-256-GCM at rest, field-level encryption      │    │
│  │  • PII fields: Deterministic encryption (searchable)    │    │
│  │  • Sensitive fields: Randomized encryption              │    │
│  │  • Keys: AWS KMS / HashiCorp Vault with rotation        │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  AUDIT: Immutable audit logs, SIEM integration          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

**Encryption Strategy:**

| Data Type | Encryption | Key Management | Searchable |
|-----------|-----------|----------------|------------|
| Email | AES-256-GCM + HMAC | AWS KMS | Yes (blind index) |
| Phone | AES-256-GCM + HMAC | AWS KMS | Yes (blind index) |
| Name | AES-256-GCM | AWS KMS | No |
| Address | AES-256-GCM | AWS KMS | No |
| DOB | AES-256-GCM | AWS KMS | No |
| Events | AES-256-GCM | AWS KMS | No |
| Consent | AES-256-GCM | AWS KMS | No |

### 7.6 Data Quality Monitoring

```python
class DataQualityMonitor:
    """Continuous data quality monitoring"""
    
    RULES = {
        'completeness': {
            'profile.email': {'threshold': 0.95, 'severity': 'warning'},
            'profile.phone': {'threshold': 0.80, 'severity': 'warning'},
            'event.identifiers': {'threshold': 0.99, 'severity': 'critical'},
        },
        'uniqueness': {
            'profile.email_hash': {'threshold': 1.0, 'severity': 'critical'},
            'event.event_id': {'threshold': 1.0, 'severity': 'critical'},
        },
        'validity': {
            'event.timestamp': {'threshold': 0.99, 'severity': 'critical'},
            'profile.email_format': {'threshold': 0.98, 'severity': 'warning'},
        },
        'timeliness': {
            'event.ingestion_delay': {'threshold': 0.95, 'severity': 'warning'},
            'profile.update_delay': {'threshold': 0.99, 'severity': 'critical'},
        },
        'consistency': {
            'crm.cdp_sync_delay': {'threshold': 0.95, 'severity': 'warning'},
            'warehouse.event_count': {'threshold': 0.99, 'severity': 'critical'},
        }
    }
    
    async def evaluate_quality(self, dataset, rule_type, rule_name):
        rule = self.RULES[rule_type][rule_name]
        score = await self.compute_score(dataset, rule_name)
        
        if score < rule['threshold']:
            await self.alert(
                severity=rule['severity'],
                rule=rule_name,
                score=score,
                threshold=rule['threshold']
            )
        
        return {
            'rule': rule_name,
            'score': score,
            'threshold': rule['threshold'],
            'passed': score >= rule['threshold']
        }
```

---

## 8. Data Flow Diagrams

### 8.1 High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW OVERVIEW                                │
│                                                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │   Web   │  │ Mobile  │  │   CRM   │  │   POS   │  │  Email  │      │
│  │  Site   │  │   App   │  │         │  │         │  │ Platform│      │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘      │
│       │            │            │            │            │             │
│       └────────────┴─────┬──────┴────────────┴────────────┘             │
│                          │                                               │
│                          ▼                                               │
│                 ┌────────────────┐                                       │
│                 │  INGESTION     │                                       │
│                 │  LAYER         │                                       │
│                 │  (Kafka)       │                                       │
│                 └───────┬────────┘                                       │
│                         │                                                │
│          ┌──────────────┼──────────────┐                                │
│          │              │              │                                 │
│          ▼              ▼              ▼                                 │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐                         │
│   │  REAL-TIME │ │   BATCH    │ │  STREAM    │                         │
│   │  PROFILE   │ │   WAREHOUSE│ │  ANALYTICS │                         │
│   │  UPDATES   │ │   (ETL)    │ │  (Flink)   │                         │
│   └─────┬──────┘ └─────┬──────┘ └─────┬──────┘                         │
│         │              │              │                                   │
│         ▼              ▼              ▼                                   │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐                         │
│   │  PROFILE   │ │  WAREHOUSE │ │  REAL-TIME │                         │
│   │  STORE     │ │  (Snowflake)│ │  DASHBOARDS│                         │
│   │  (Redis)   │ │            │ │            │                         │
│   └─────┬──────┘ └─────┬──────┘ └─────┬──────┘                         │
│         │              │              │                                   │
│         └──────────────┼──────────────┘                                  │
│                        │                                                 │
│                        ▼                                                 │
│              ┌─────────────────┐                                         │
│              │  CONSUMPTION    │                                         │
│              │  LAYER          │                                         │
│              │  • AI Agents    │                                         │
│              │  • Marketing    │                                         │
│              │  • Analytics    │                                         │
│              │  • Personalization│                                       │
│              └─────────────────┘                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Event Ingestion Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │     │   SDK    │     │   API    │     │  Kafka   │
│  Action  │ ──→ │  Track   │ ──→ │  Gateway │ ──→ │  Topic   │
│          │     │          │     │          │     │          │
└──────────┘     └──────────┘     └────┬─────┘     └────┬─────┘
                                      │              │
                              ┌───────┴───────┐      │
                              │  Validation   │      │
                              │  • Schema     │      │
                              │  • PII Scan   │      │
                              │  • Consent    │      │
                              │  • Rate Limit │      │
                              └───────────────┘      │
                                                     │
                              ┌──────────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  Consumer    │
                       │  Groups      │
                       │              │
                       │ • Profile    │
                       │   Updater    │
                       │ • Warehouse  │
                       │   Loader     │
                       │ • Analytics  │
                       │   Engine     │
                       │ • ML Feature │
                       │   Computer   │
                       └──────────────┘
```

### 8.3 Identity Resolution Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Event   │     │ Extract  │     │ Determ.  │     │  Prob.   │
│  with    │ ──→ │  Ident.  │ ──→ │  Match   │ ──→ │  Match   │
│  Ident.  │     │          │     │          │     │          │
└──────────┘     └──────────┘     └────┬─────┘     └────┬─────┘
                                      │              │
                                 ┌────┴────┐    ┌────┴────┐
                                 │ Match?  │    │ Score   │
                                 │         │    │ > 0.85? │
                                 └────┬────┘    └────┬────┘
                                      │              │
                              ┌───────┴───────┐ ┌───┴────────┐
                              │ YES: Return   │ │ YES: Merge  │
                              │ Person ID     │ │ & Return   │
                              └───────────────┘ └────────────┘
                                      │              │
                              ┌───────┴───────┐ ┌───┴────────┐
                              │ NO: Check     │ │ NO: Create  │
                              │ Probabilistic │ │ New Profile│
                              └───────────────┘ └────────────┘
```

### 8.4 Profile Update Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Event   │     │  Kafka   │     │  Flink   │     │  Profile │
│  Stream  │ ──→ │  Topic   │ ──→ │  Job     │ ──→ │  Store   │
│          │     │          │     │          │     │  Update  │
└──────────┘     └──────────┘     └────┬─────┘     └────┬─────┘
                                      │              │
                              ┌───────┴───────┐ ┌───┴────────┐
                              │ 1. Resolve ID │ │ 4. Update  │
                              │ 2. Fetch      │ │    Cache   │
                              │    Profile    │ │ 5. Publish │
                              │ 3. Apply      │ │    Update  │
                              │    Event      │ │ 6. Update  │
                              │               │ │    Segments│
                              │               │ │ 7. Compute │
                              │               │ │    Features│
                              └───────────────┘ └────────────┘
```

### 8.5 CRM Sync Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  CDP     │     │  Sync    │     │  CRM     │     │  CRM     │
│  Profile │ ──→ │  Engine  │ ──→ │  Adapter │ ──→ │  System  │
│  Change  │     │          │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │                               │
                      │         ┌──────────┐          │
                      │         │ Conflict │          │
                      │         │Resolver  │          │
                      │         └──────────┘          │
                      │                               │
                      │         ┌──────────┐          │
                      └────────→│  Audit   │←─────────┘
                                │  Log     │
                                └──────────┘
```

### 8.6 Consent Enforcement Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Event   │     │ Consent  │     │  Check   │     │  Route   │
│  with    │ ──→ │  Check   │ ──→ │  Result  │ ──→ │  Decision│
│  Consent │     │          │     │          │     │          │
└──────────┘     └──────────┘     └────┬─────┘     └────┬─────┘
                                      │              │
                              ┌───────┴───────┐ ┌───┴────────┐
                              │ GRANTED:      │ │ DENIED:    │
                              │ Process Event │ │ Reject or  │
                              │               │ │ Anonymize  │
                              └───────────────┘ └────────────┘
```

### 8.7 ML Feature Pipeline Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Event   │     │  Feature │     │  Feature │     │  Model   │
│  Stream  │ ──→ │  Compute │ ──→ │  Store   │ ──→ │  Serving │
│          │     │  (Flink) │     │  (Feast) │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
       │                                               │
       │         ┌──────────┐                          │
       │         │  Batch   │                          │
       └────────→│  Feature │                          │
                 │  Compute │                          │
                 │  (Spark) │                          │
                 └──────────┘                          │
                                                       ▼
                                                ┌──────────┐
                                                │  AI Agent│
                                                │  / MLOps │
                                                └──────────┘
```

---

## 9. Implementation Roadmap

### 9.1 Phase Overview

```
Phase 1 (Months 1-3)     Phase 2 (Months 4-6)     Phase 3 (Months 7-9)     Phase 4 (Months 10-12)
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ FOUNDATION      │      │ CORE PLATFORM   │      │ INTELLIGENCE     │      │ OPTIMIZATION    │
│                 │      │                 │      │                 │      │                 │
│ • Event schema  │ ──→  │ • Identity      │ ──→  │ • ML features   │ ──→  │ • Advanced ML   │
│ • Ingestion     │      │   resolution    │      │ • Real-time     │      │ • Predictive    │
│ • Basic storage │      │ • Profile store │      │   segments      │      │   analytics     │
│ • Consent mgmt  │      │ • Warehouse     │      │ • AI agent      │      │ • Optimization  │
│ • Security      │      │ • CRM sync      │      │   integration   │      │ • Scale         │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
```

### 9.2 Phase 1: Foundation (Months 1-3)

| Week | Deliverable | Owner | Dependencies |
|------|------------|-------|--------------|
| 1-2 | Event schema design & validation | Data Engineering | None |
| 2-3 | Kafka cluster setup & topic design | Infrastructure | None |
| 3-4 | Ingestion API & basic SDK | Engineering | Event schema |
| 4-6 | Raw event storage (S3) | Data Engineering | Kafka |
| 5-6 | Consent management system | Engineering | None |
| 6-8 | Basic profile store (Redis) | Engineering | Ingestion API |
| 8-10 | Data warehouse setup (Snowflake) | Data Engineering | Raw storage |
| 10-12 | Security framework (encryption, IAM) | Security | All above |
| 12 | Phase 1 review & sign-off | All | All above |

**Phase 1 Success Criteria:**
- [ ] Event ingestion handling 10K events/sec
- [ ] Sub-100ms event ingestion latency (p99)
- [ ] Consent management covering all channels
- [ ] Basic profile CRUD operations
- [ ] Data warehouse with raw event storage
- [ ] Encryption at rest and in transit
- [ ] Audit logging for all data access

### 9.3 Phase 2: Core Platform (Months 4-6)

| Week | Deliverable | Owner | Dependencies |
|------|------------|-------|--------------|
| 13-16 | Identity graph implementation | Data Engineering | Profile store |
| 14-18 | Identity resolution engine | Data Engineering | Identity graph |
| 16-18 | Real-time profile updates | Engineering | Kafka, Flink |
| 18-20 | Warehouse ETL pipelines | Data Engineering | Snowflake |
| 20-22 | CRM adapter framework | Engineering | Profile store |
| 22-24 | Salesforce & HubSpot sync | Engineering | CRM adapters |
| 24 | Phase 2 review & sign-off | All | All above |

**Phase 2 Success Criteria:**
- [ ] Identity resolution accuracy > 95%
- [ ] Real-time profile updates < 1 second
- [ ] Bidirectional CRM sync with Salesforce & HubSpot
- [ ] Star schema warehouse with daily ETL
- [ ] Data quality monitoring dashboards
- [ ] 50K events/sec ingestion capacity

### 9.4 Phase 3: Intelligence (Months 7-9)

| Week | Deliverable | Owner | Dependencies |
|------|------------|-------|--------------|
| 25-28 | Feature store implementation | ML Engineering | Warehouse |
| 26-30 | Real-time segmentation engine | Data Engineering | Profile store |
| 28-32 | ML model training pipeline | ML Engineering | Feature store |
| 30-34 | AI agent data access API | Engineering | All above |
| 32-36 | Predictive analytics models | ML Engineering | ML pipeline |
| 36 | Phase 3 review & sign-off | All | All above |

**Phase 3 Success Criteria:**
- [ ] Feature store with 100+ features
- [ ] Real-time segment evaluation < 100ms
- [ ] Churn prediction model with AUC > 0.80
- [ ] Next-best-action recommendation API
- [ ] AI agent profile access API (GraphQL)
- [ ] A/B testing framework integration

### 9.5 Phase 4: Optimization (Months 10-12)

| Week | Deliverable | Owner | Dependencies |
|------|------------|-------|--------------|
| 37-40 | Performance optimization | Engineering | All above |
| 38-42 | Advanced ML models | ML Engineering | ML pipeline |
| 40-44 | Multi-region deployment | Infrastructure | All above |
| 42-46 | Data governance automation | Data Engineering | All above |
| 44-48 | Scale testing & hardening | All | All above |
| 48 | Phase 4 review & sign-off | All | All above |

**Phase 4 Success Criteria:**
- [ ] 100K+ events/sec ingestion capacity
- [ ] Sub-50ms profile API latency (p99)
- [ ] Multi-region active-active deployment
- [ ] Automated data quality remediation
- [ ] Full GDPR/CCPA compliance automation
- [ ] 99.99% platform availability

### 9.6 Resource Requirements

| Role | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Total |
|------|---------|---------|---------|---------|-------|
| **Data Engineers** | 3 | 4 | 3 | 2 | 4 FTE |
| **Software Engineers** | 2 | 3 | 3 | 2 | 3 FTE |
| **ML Engineers** | 0 | 0 | 3 | 2 | 2 FTE |
| **DevOps/SRE** | 1 | 2 | 2 | 2 | 2 FTE |
| **Security Engineer** | 1 | 1 | 1 | 1 | 1 FTE |
| **Product Manager** | 1 | 1 | 1 | 1 | 1 FTE |
| **Data Governance** | 0.5 | 1 | 1 | 1 | 1 FTE |
| **Total** | **8.5** | **12** | **14** | **11** | **14 FTE** |

### 9.7 Technology Stack Summary

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Event Streaming** | Apache Kafka (Redpanda) | High throughput, ecosystem, reliability |
| **Stream Processing** | Apache Flink | Stateful processing, exactly-once, low latency |
| **Profile Store** | Redis Cluster + DynamoDB | Sub-milllex reads, global availability |
| **Identity Graph** | Neo4j | Native graph queries, relationship traversal |
| **Data Warehouse** | Snowflake | Separation of compute/storage, elasticity |
| **Feature Store** | Feast | Open source, real-time + batch features |
| **Orchestration** | Apache Airflow | DAG-based workflows, rich ecosystem |
| **Transformation** | dbt | SQL-based, version control, testing |
| **API Gateway** | Kong / Envoy | Rate limiting, auth, observability |
| **Container Orchestration** | Kubernetes (EKS/GKE) | Industry standard, auto-scaling |
| **CI/CD** | GitHub Actions | Integrated with code repos |
| **Monitoring** | Datadog / Grafana | Full-stack observability |
| **Secrets** | HashiCorp Vault | Dynamic secrets, encryption as a service |

### 9.8 Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Identity resolution accuracy | Medium | High | Probabilistic + deterministic hybrid, continuous model training |
| Data privacy compliance | High | Critical | Privacy by design, automated consent enforcement, regular audits |
| CRM sync conflicts | Medium | Medium | Configurable conflict resolution, audit trail, manual override |
| Scale limitations | Low | High | Cloud-native architecture, horizontal scaling, load testing |
| Data quality degradation | Medium | High | Continuous monitoring, automated alerting, data quality SLAs |
| Vendor lock-in | Medium | Medium | Open source first, multi-cloud capable, abstraction layers |
| Talent acquisition | Medium | High | Competitive compensation, strong documentation, training budget |

### 9.9 Key Performance Indicators

| KPI | Target | Measurement |
|-----|--------|-------------|
| Event ingestion latency (p99) | < 100ms | End-to-end from client to Kafka |
| Profile API latency (p99) | < 50ms | Profile store read latency |
| Identity resolution accuracy | > 95% | Manual audit sampling |
| Data freshness | < 5 minutes | Warehouse data lag |
| CRM sync latency | < 1 minute | Bidirectional sync delay |
| System availability | 99.99% | Uptime excluding planned maintenance |
| Data quality score | > 98% | Automated quality checks |
| Consent compliance | 100% | Audit verification |
| ML model AUC | > 0.80 | Churn prediction model |
| Cost per 1K events | < $0.01 | Infrastructure cost / event volume |

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **CDP** | Customer Data Platform |
| **PII** | Personally Identifiable Information |
| **SCD** | Slowly Changing Dimension |
| **ETL** | Extract, Transform, Load |
| **ELT** | Extract, Load, Transform |
| **RBAC** | Role-Based Access Control |
| **ABAC** | Attribute-Based Access Control |
| **GDPR** | General Data Protection Regulation (EU) |
| **CCPA** | California Consumer Privacy Act |
| **LGPD** | Lei Geral de Proteção de Dados (Brazil) |
| **PIPEDA** | Personal Information Protection and Electronic Documents Act (Canada) |
| **AUC** | Area Under the ROC Curve |
| **Flink** | Apache Flink - stream processing framework |
| **Feast** | Feature store for ML |
| **dbt** | Data build tool |
| **SLA** | Service Level Agreement |

## Appendix B: Reference Architecture Diagrams

### B.1 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │   Web   │  │ Mobile  │  │   CRM   │  │   POS   │  │  Email  │           │
│  │  App    │  │   App   │  │         │  │         │  │ Platform│           │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘           │
│       │            │            │            │            │                  │
│       └────────────┴─────┬──────┴────────────┴────────────┘                  │
│                          │                                                   │
│  ┌───────────────────────┴───────────────────────────────────────────┐      │
│  │                     API GATEWAY (Kong)                             │      │
│  │  Auth │ Rate Limiting │ Validation │ Routing │ Caching            │      │
│  └───────────────────────┬───────────────────────────────────────────┘      │
│                          │                                                   │
│  ┌───────────────────────┴───────────────────────────────────────────┐      │
│  │                     KAFKA CLUSTER                                  │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │      │
│  │  │behavioral│  │transaction│ │ identity │  │engagement│         │      │
│  │  │  topic   │  │  topic   │  │  topic   │  │  topic   │         │      │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │      │
│  └───────────────────────┬───────────────────────────────────────────┘      │
│                          │                                                   │
│       ┌──────────────────┼──────────────────┐                               │
│       │                  │                  │                                │
│       ▼                  ▼                  ▼                                │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                            │
│  │  FLINK   │     │  FLINK   │     │  BATCH   │                            │
│  │  Profile │     │  Feature │     │  ETL     │                            │
│  │  Updater │     │ Computer │     │ (Airflow)│                            │
│  └────┬─────┘     └────┬─────┘     └────┬─────┘                            │
│       │                │                │                                    │
│       ▼                ▼                ▼                                    │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                            │
│  │  REDIS   │     │  FEAST   │     │SNOWFLAKE │                            │
│  │  Cluster │     │  Feature │     │Warehouse │                            │
│  │(Profiles)│     │  Store   │     │          │                            │
│  └────┬─────┘     └──────────┘     └──────────┘                            │
│       │                                                                      │
│       ▼                                                                      │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                            │
│  │  NEO4J   │     │  CRM     │     │  ML      │                            │
│  │  Identity│     │  Sync    │     │  Models  │                            │
│  │  Graph   │     │  Engine  │     │          │                            │
│  └──────────┘     └────┬─────┘     └──────────┘                            │
│                        │                                                     │
│                        ▼                                                     │
│                 ┌──────────┐                                                 │
│                 │   CRM    │                                                 │
│                 │ Systems  │                                                 │
│                 └──────────┘                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### B.2 Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                    CLOUDFLARE CDN                                │
│  DDoS Protection │ WAF │ Edge Caching │ Load Balancing           │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  INGRESS CONTROLLER (NGINX)                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  API     │  │  Stream  │  │  Profile │  │  Admin   │       │
│  │  Service │  │  Process │  │  Service │  │  Service │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Kafka   │  │  Flink   │  │  Airflow │  │  dbt     │       │
│  │  Cluster │  │  Cluster │  │  Worker  │  │  Runner  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                    DATA LAYER                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Redis   │  │  Neo4j   │  │Snowflake │  │  S3/GCS  │       │
│  │  Cluster │  │  Cluster │  │          │  │  Storage │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0
**Last Updated:** 2026-10-01
**Author:** Ahmed Hassan
**Status:** Draft for Review

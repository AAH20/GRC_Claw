# UGC Marketplace API Documentation

> **Version:** 1.0.0 · **Base URL:** `http://localhost:8000/api/v1` · **Format:** JSON

Unified agentic AI platform for content marketplace operations. This document covers every endpoint across all 10 service domains, with request/response examples, authentication, rate limiting, error handling, SDK usage, webhooks, and integration patterns.

---

## Table of Contents

- [Overview](#overview)
- [OpenAPI 3.1 Specification](#openapi-31-specification)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [SDK Usage](#sdk-usage)
- [Webhooks](#webhooks)
- [Integration Guide](#integration-guide)
- [Endpoint Index](#endpoint-index)

---

## Overview

The UGC Marketplace API is a RESTful HTTP API built with FastAPI. It provides a unified interface for content marketplace operations across 10 service domains:

| Domain | Prefix | Endpoints |
|--------|--------|-----------|
| Health | `/api/v1` | 3 |
| Content Moderation | `/api/v1/moderation` | 4 |
| Creator Monetization | `/api/v1/monetization` | 6 |
| Content Discovery | `/api/v1/discovery` | 3 |
| Rights Management | `/api/v1/rights` | 19 |
| Quality Scoring | `/api/v1/quality` | 12 |
| Fraud Detection | `/api/v1/fraud` | 13 |
| Creator Analytics | `/api/v1/analytics` | 17 |
| Licensing Engine | `/api/v1/licensing` | 24 |
| Community Curation | `/api/v1/curation` | 9 |
| Content Marketplace | `/api/v1/marketplace` | 30 |
| **Total** | | **140** |

---

## OpenAPI 3.1 Specification

The full OpenAPI 3.1 spec is available at `openapi.json` in the project root. Below is the complete specification inline.

```yaml
openapi: 3.1.0
info:
  title: UGC Marketplace API
  description: Unified agentic AI platform for content marketplace operations
  version: 1.0.0
  license:
    name: MIT
servers:
  - url: http://localhost:8000/api/v1
    description: Local development server
  - url: https://api.ugc-marketplace.example.com/api/v1
    description: Production server
tags:
  - name: Health
  - name: Moderation
  - name: Monetization
  - name: Discovery
  - name: Rights
  - name: Quality
  - name: Fraud
  - name: Analytics
  - name: Licensing
  - name: Curation
  - name: Marketplace
paths:
  /health:
    get:
      summary: Health check
      operationId: health_check
      tags: [Health]
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
  /health/ready:
    get:
      summary: Readiness check
      operationId: readiness_check
      tags: [Health]
      responses:
        '200':
          description: Service is ready
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
  /health/live:
    get:
      summary: Liveness check
      operationId: liveness_check
      tags: [Health]
      responses:
        '200':
          description: Service is alive
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
  /moderation/moderate/text:
    post:
      summary: Moderate text content
      operationId: moderate_text
      tags: [Moderation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ModerationRequest'
      responses:
        '200':
          description: Moderation result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ModerationResult'
  /moderation/moderate/image:
    post:
      summary: Moderate image content
      operationId: moderate_image
      tags: [Moderation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ModerationRequest'
      responses:
        '200':
          description: Moderation result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ModerationResult'
  /moderation/moderate/video:
    post:
      summary: Moderate video content
      operationId: moderate_video
      tags: [Moderation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ModerationRequest'
      responses:
        '200':
          description: Moderation result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ModerationResult'
  /moderation/moderate/batch:
    post:
      summary: Moderate multiple content items in batch
      operationId: moderate_batch
      tags: [Moderation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BatchModerationRequest'
      responses:
        '200':
          description: Batch moderation result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BatchModerationResult'
  /monetization/metrics:
    post:
      summary: Record a metric data point
      operationId: record_metric
      tags: [Monetization]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, value]
              properties:
                name:
                  type: string
                  minLength: 1
                value:
                  type: number
                label:
                  type: string
      responses:
        '201':
          description: Metric recorded
    get:
      summary: List all available metrics
      operationId: list_metrics
      tags: [Monetization]
      responses:
        '200':
          description: List of metric names
  /monetization/reports:
    post:
      summary: Generate an analytics report
      operationId: generate_report
      tags: [Monetization]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [report_id, creator_id, period_start, period_end]
              properties:
                report_id:
                  type: string
                creator_id:
                  type: string
                period_start:
                  type: string
                  format: date-time
                period_end:
                  type: string
                  format: date-time
      responses:
        '201':
          description: Report generated
        '409':
          description: Report already exists
  /monetization/reports/{report_id}:
    get:
      summary: Get a generated report by ID
      operationId: get_report
      tags: [Monetization]
      parameters:
        - name: report_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: The report object
        '404':
          description: Report not found
  /monetization/forecast:
    post:
      summary: Forecast a metric for future days
      operationId: forecast_metric
      tags: [Monetization]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name]
              properties:
                name:
                  type: string
                days:
                  type: integer
                  minimum: 1
                  maximum: 365
                  default: 30
      responses:
        '200':
          description: Forecast data
  /monetization/revenue/{creator_id}:
    get:
      summary: Get a revenue report for a creator
      operationId: get_revenue_report
      tags: [Monetization]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Revenue report
  /discovery/search:
    get:
      summary: Search content
      operationId: search_content
      tags: [Discovery]
      parameters:
        - name: query
          in: query
          required: true
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: Search results
  /discovery/recommendations/{user_id}:
    get:
      summary: Get personalized recommendations
      operationId: get_recommendations
      tags: [Discovery]
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: Recommendations
  /discovery/trending:
    get:
      summary: Get trending content
      operationId: get_trending
      tags: [Discovery]
      parameters:
        - name: category
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: Trending content
  /rights/licenses:
    post:
      summary: Create a new license
      operationId: create_license
      tags: [Rights]
      responses:
        '201':
          description: License created
    get:
      summary: List all licenses
      operationId: list_licenses
      tags: [Rights]
      responses:
        '200':
          description: List of licenses
  /rights/licenses/{license_id}:
    get:
      summary: Get a license by ID
      operationId: get_license
      tags: [Rights]
      parameters:
        - name: license_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: License object
    delete:
      summary: Revoke a license
      operationId: revoke_license
      tags: [Rights]
      parameters:
        - name: license_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: License revoked
  /rights/detect:
    post:
      summary: Detect license for content
      operationId: detect_license
      tags: [Rights]
      responses:
        '200':
          description: Detection result
  /rights/infringement/report:
    post:
      summary: File a copyright infringement report
      operationId: file_infringement_report
      tags: [Rights]
      responses:
        '201':
          description: Report filed
  /rights/infringement/reports/{content_id}:
    get:
      summary: List infringement reports for content
      operationId: list_infringement_reports
      tags: [Rights]
      parameters:
        - name: content_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: List of infringement reports
  /rights/infringement/detect:
    post:
      summary: Detect potential infringement
      operationId: detect_infringement
      tags: [Rights]
      responses:
        '200':
          description: Infringement detection result
  /rights/infringement/reports/{report_id}/status:
    patch:
      summary: Update infringement report status
      operationId: update_report_status
      tags: [Rights]
      parameters:
        - name: report_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Status updated
  /rights/takedown/request:
    post:
      summary: Submit a takedown request
      operationId: submit_takedown_request
      tags: [Rights]
      responses:
        '201':
          description: Takedown request submitted
  /rights/takedown/{request_id}:
    get:
      summary: Get a takedown request
      operationId: get_takedown_request
      tags: [Rights]
      parameters:
        - name: request_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Takedown request
  /rights/takedown/{request_id}/process:
    post:
      summary: Process a takedown request
      operationId: process_takedown_request
      tags: [Rights]
      parameters:
        - name: request_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Takedown processed
  /rights/takedown:
    get:
      summary: List all takedown requests
      operationId: list_takedown_requests
      tags: [Rights]
      responses:
        '200':
          description: List of takedown requests
  /rights/usage/record:
    post:
      summary: Record content usage
      operationId: record_usage
      tags: [Rights]
      responses:
        '201':
          description: Usage recorded
  /rights/usage/summary/{content_id}:
    get:
      summary: Get usage summary for content
      operationId: get_usage_summary
      tags: [Rights]
      parameters:
        - name: content_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Usage summary
  /rights/usage/records/{content_id}:
    get:
      summary: List usage records for content
      operationId: list_usage_records
      tags: [Rights]
      parameters:
        - name: content_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: List of usage records
  /rights/validate:
    post:
      summary: Validate content usage rights
      operationId: validate_rights
      tags: [Rights]
      responses:
        '201':
          description: Validation result
  /rights/validations/{validation_id}:
    get:
      summary: Get a rights validation
      operationId: get_validation
      tags: [Rights]
      parameters:
        - name: validation_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Validation object
  /rights/validations/content/{content_id}:
    get:
      summary: List validations for content
      operationId: list_validations
      tags: [Rights]
      parameters:
        - name: content_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: List of validations
  /quality/health:
    get:
      summary: Quality service health check
      tags: [Quality]
      responses:
        '200':
          description: Service is healthy
  /quality/metrics:
    get:
      summary: Prometheus metrics endpoint
      tags: [Quality]
      responses:
        '200':
          description: Metrics data
  /quality/score:
    post:
      summary: Score content quality across all dimensions
      operationId: score_content
      tags: [Quality]
      parameters:
        - name: content
          in: query
          required: true
          schema:
            type: string
        - name: content_type
          in: query
          schema:
            $ref: '#/components/schemas/ContentType'
            default: text
      responses:
        '200':
          description: Quality scores
  /quality/score/readability:
    post:
      summary: Score content readability
      operationId: score_readability
      tags: [Quality]
      parameters:
        - name: content
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Readability score
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DimensionScore'
  /quality/score/originality:
    post:
      summary: Score content originality
      operationId: score_originality
      tags: [Quality]
      parameters:
        - name: content
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Originality score
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DimensionScore'
  /quality/score/engagement:
    post:
      summary: Score content engagement potential
      operationId: score_engagement
      tags: [Quality]
      parameters:
        - name: content
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Engagement score
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DimensionScore'
  /quality/score/seo:
    post:
      summary: Score content SEO optimization
      operationId: score_seo
      tags: [Quality]
      parameters:
        - name: content
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: SEO score
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DimensionScore'
  /quality/improvements:
    post:
      summary: Get content improvement suggestions
      operationId: get_improvements
      tags: [Quality]
      parameters:
        - name: content
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Improvement suggestions
  /quality/benchmark:
    post:
      summary: Compare content against benchmarks
      operationId: compare_benchmark
      tags: [Quality]
      parameters:
        - name: content
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Benchmark comparison
  /quality/batch:
    post:
      summary: Score multiple content items
      operationId: batch_score
      tags: [Quality]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: array
              items:
                type: string
      responses:
        '200':
          description: List of scores
  /quality/dimensions:
    get:
      summary: List available scoring dimensions
      operationId: list_dimensions
      tags: [Quality]
      responses:
        '200':
          description: List of dimensions
  /quality/benchmarks:
    get:
      summary: List available benchmarks
      operationId: list_benchmarks
      tags: [Quality]
      responses:
        '200':
          description: List of benchmarks
  /fraud/analyze:
    post:
      summary: Analyze a transaction for fraud
      operationId: analyze_transaction
      tags: [Fraud]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Fraud analysis result
  /fraud/analyze/batch:
    post:
      summary: Analyze a batch of transactions for fraud
      operationId: analyze_batch
      tags: [Fraud]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                transactions:
                  type: array
                  items:
                    type: object
      responses:
        '200':
          description: Batch analysis result
  /fraud/patterns/detect:
    post:
      summary: Detect fraud patterns in a transaction
      operationId: detect_patterns
      tags: [Fraud]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Detected patterns
  /fraud/anomalies/detect:
    post:
      summary: Detect anomalies in a transaction
      operationId: detect_anomalies
      tags: [Fraud]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Detected anomalies
  /fraud/risk/score:
    post:
      summary: Score risk for a transaction
      operationId: score_risk
      tags: [Fraud]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Risk score
  /fraud/accounts/analyze:
    post:
      summary: Analyze an account for fraud risk
      operationId: analyze_account
      tags: [Fraud]
      parameters:
        - name: account_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Account risk analysis
  /fraud/health:
    get:
      summary: Fraud service health check
      tags: [Fraud]
      responses:
        '200':
          description: Service is healthy
  /fraud/ready:
    get:
      summary: Fraud service readiness check
      tags: [Fraud]
      responses:
        '200':
          description: Service is ready
  /fraud/monitoring/start:
    post:
      summary: Start monitoring transactions for an account
      operationId: start_monitoring
      tags: [Fraud]
      parameters:
        - name: account_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Monitoring started
  /fraud/monitoring/stop:
    post:
      summary: Stop a monitoring session
      operationId: stop_monitoring
      tags: [Fraud]
      parameters:
        - name: session_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Monitoring stopped
  /fraud/agents/status:
    get:
      summary: Get status of all fraud detection agents
      operationId: get_agents_status
      tags: [Fraud]
      responses:
        '200':
          description: Agent statuses
  /fraud/reports/{report_id}:
    get:
      summary: Get a fraud report by ID
      operationId: get_fraud_report
      tags: [Fraud]
      parameters:
        - name: report_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Fraud report
  /fraud/reports:
    get:
      summary: List all fraud reports
      operationId: list_fraud_reports
      tags: [Fraud]
      responses:
        '200':
          description: List of fraud reports
  /analytics/health:
    get:
      summary: Analytics service health check
      tags: [Analytics]
      responses:
        '200':
          description: Service is healthy
  /analytics/ready:
    get:
      summary: Analytics service readiness check
      tags: [Analytics]
      responses:
        '200':
          description: Service is ready
  /analytics/growth/predict:
    post:
      summary: Predict growth for a creator
      operationId: predict_growth
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Growth prediction
  /analytics/growth/{creator_id}:
    get:
      summary: Get growth prediction for a creator
      operationId: get_growth_prediction
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Growth prediction
  /analytics/growth/{creator_id}/scenarios:
    get:
      summary: Get growth scenarios for a creator
      operationId: get_growth_scenarios
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Growth scenarios
  /analytics/content/analyze:
    post:
      summary: Analyze content performance
      operationId: analyze_content
      tags: [Analytics]
      parameters:
        - name: content_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Content performance analysis
  /analytics/content/{content_id}:
    get:
      summary: Get content performance
      operationId: get_content_performance
      tags: [Analytics]
      parameters:
        - name: content_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Content performance
  /analytics/content/creator/{creator_id}:
    get:
      summary: Get content performance for a creator
      operationId: get_creator_content
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Creator content performance
  /analytics/audience/analyze:
    post:
      summary: Analyze audience for a creator
      operationId: analyze_audience
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Audience analysis
  /analytics/audience/{creator_id}:
    get:
      summary: Get audience analysis for a creator
      operationId: get_audience
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Audience analysis
  /analytics/audience/{creator_id}/segments:
    get:
      summary: Get audience segments for a creator
      operationId: get_audience_segments
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Audience segments
  /analytics/revenue/report:
    post:
      summary: Generate revenue report for a creator
      operationId: generate_revenue_report
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Revenue report
  /analytics/revenue/{creator_id}:
    get:
      summary: Get revenue report for a creator
      operationId: get_revenue_report
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Revenue report
  /analytics/revenue/{creator_id}/breakdown:
    get:
      summary: Get revenue breakdown for a creator
      operationId: get_revenue_breakdown
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Revenue breakdown
  /analytics/engagement/report:
    post:
      summary: Generate engagement report for a creator
      operationId: generate_engagement_report
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Engagement report
  /analytics/engagement/{creator_id}:
    get:
      summary: Get engagement report for a creator
      operationId: get_engagement_report
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Engagement report
  /analytics/engagement/{creator_id}/metrics:
    get:
      summary: Get engagement metrics for a creator
      operationId: get_engagement_metrics
      tags: [Analytics]
      parameters:
        - name: creator_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Engagement metrics
  /licensing/health:
    get:
      summary: Licensing service health check
      tags: [Licensing]
      responses:
        '200':
          description: Service is healthy
  /licensing/ready:
    get:
      summary: Licensing service readiness check
      tags: [Licensing]
      responses:
        '200':
          description: Service is ready
  /licensing/live:
    get:
      summary: Licensing service liveness check
      tags: [Licensing]
      responses:
        '200':
          description: Service is alive
  /licensing/licenses:
    post:
      summary: Create a new license
      operationId: create_license
      tags: [Licensing]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '201':
          description: License created
    get:
      summary: List all licenses
      operationId: list_licenses
      tags: [Licensing]
      responses:
        '200':
          description: List of licenses
  /licensing/licenses/{license_id}:
    get:
      summary: Get a license by ID
      operationId: get_license
      tags: [Licensing]
      parameters:
        - name: license_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: License object
    patch:
      summary: Update a license
      operationId: update_license
      tags: [Licensing]
      parameters:
        - name: license_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: License updated
    delete:
      summary: Delete a license
      operationId: delete_license
      tags: [Licensing]
      parameters:
        - name: license_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: License deleted
  /licensing/licenses/{license_id}/activate:
    post:
      summary: Activate a license
      operationId: activate_license
      tags: [Licensing]
      parameters:
        - name: license_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: License activated
  /licensing/licenses/{license_id}/revoke:
    post:
      summary: Revoke a license
      operationId: revoke_license
      tags: [Licensing]
      parameters:
        - name: license_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: License revoked
  /licensing/negotiations:
    post:
      summary: Create a new negotiation
      operationId: create_negotiation
      tags: [Licensing]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '201':
          description: Negotiation created
  /licensing/negotiations/{negotiation_id}:
    get:
      summary: Get a negotiation by ID
      operationId: get_negotiation
      tags: [Licensing]
      parameters:
        - name: negotiation_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Negotiation object
  /licensing/negotiations/{negotiation_id}/counter:
    post:
      summary: Submit a counter proposal
      operationId: submit_counter_proposal
      tags: [Licensing]
      parameters:
        - name: negotiation_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Counter proposal submitted
  /licensing/negotiations/{negotiation_id}/accept:
    post:
      summary: Accept a proposal
      operationId: accept_proposal
      tags: [Licensing]
      parameters:
        - name: negotiation_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Proposal accepted
  /licensing/negotiations/{negotiation_id}/reject:
    post:
      summary: Reject a proposal
      operationId: reject_proposal
      tags: [Licensing]
      parameters:
        - name: negotiation_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Proposal rejected
  /licensing/compliance/check:
    post:
      summary: Run a compliance check
      operationId: run_compliance_check
      tags: [Licensing]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '201':
          description: Compliance check result
  /licensing/compliance/reports:
    get:
      summary: List compliance reports
      operationId: list_compliance_reports
      tags: [Licensing]
      responses:
        '200':
          description: List of compliance reports
  /licensing/compliance/reports/{report_id}:
    get:
      summary: Get a compliance report
      operationId: get_compliance_report
      tags: [Licensing]
      parameters:
        - name: report_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Compliance report
  /licensing/compliance/licenses/{license_id}:
    get:
      summary: Get compliance reports for a license
      operationId: get_license_compliance_reports
      tags: [Licensing]
      parameters:
        - name: license_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: List of compliance reports
  /licensing/royalties/calculate:
    post:
      summary: Calculate royalties
      operationId: calculate_royalties
      tags: [Licensing]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '201':
          description: Royalty calculation result
  /licensing/royalties/{calculation_id}:
    get:
      summary: Get a royalty calculation
      operationId: get_calculation
      tags: [Licensing]
      parameters:
        - name: calculation_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Royalty calculation
  /licensing/royalties/license/{license_id}:
    get:
      summary: Get royalty calculations for a license
      operationId: get_license_calculations
      tags: [Licensing]
      parameters:
        - name: license_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: List of royalty calculations
  /licensing/contracts/analyze:
    post:
      summary: Analyze a contract
      operationId: analyze_contract
      tags: [Licensing]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '201':
          description: Contract analysis result
  /licensing/contracts/{analysis_id}:
    get:
      summary: Get a contract analysis
      operationId: get_analysis
      tags: [Licensing]
      parameters:
        - name: analysis_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Contract analysis
  /curation/health:
    get:
      summary: Curation service health check
      tags: [Curation]
      responses:
        '200':
          description: Service is healthy
  /curation/agents:
    get:
      summary: List available curation agents
      operationId: list_agents
      tags: [Curation]
      responses:
        '200':
          description: List of agents
  /curation/curate:
    post:
      summary: Curate content for a community feed
      operationId: curate_content
      tags: [Curation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Curation result
  /curation/rank:
    post:
      summary: Rank content items
      operationId: rank_content
      tags: [Curation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Ranked content
  /curation/trends:
    post:
      summary: Surface trending content
      operationId: surface_trends
      tags: [Curation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Trending content
  /curation/filter:
    post:
      summary: Filter content by quality
      operationId: filter_quality
      tags: [Curation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Quality assessments
  /curation/cluster:
    post:
      summary: Cluster content by topic
      operationId: cluster_topics
      tags: [Curation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Topic clusters
  /curation/explain:
    post:
      summary: Explain curation decisions
      operationId: explain_curation
      tags: [Curation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Curation explanations
  /curation/metrics:
    get:
      summary: Get curation metrics
      operationId: get_curation_metrics
      tags: [Curation]
      responses:
        '200':
          description: Curation metrics
  /marketplace/listings:
    post:
      summary: Create a new listing
      operationId: create_listing
      tags: [Marketplace]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '201':
          description: Listing created
    get:
      summary: List all listings
      operationId: list_listings
      tags: [Marketplace]
      responses:
        '200':
          description: List of listings
  /marketplace/listings/{listing_id}:
    get:
      summary: Get a listing by ID
      operationId: get_listing
      tags: [Marketplace]
      parameters:
        - name: listing_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Listing object
    put:
      summary: Update a listing
      operationId: update_listing
      tags: [Marketplace]
      parameters:
        - name: listing_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Listing updated
    delete:
      summary: Delete a listing
      operationId: delete_listing
      tags: [Marketplace]
      parameters:
        - name: listing_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Listing deleted
  /marketplace/listings/{listing_id}/categorize:
    post:
      summary: Categorize a listing
      operationId: categorize_listing
      tags: [Marketplace]
      parameters:
        - name: listing_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Listing categorized
  /marketplace/listings/{listing_id}/moderate:
    post:
      summary: Moderate a listing
      operationId: moderate_listing
      tags: [Marketplace]
      parameters:
        - name: listing_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Listing moderated
  /marketplace/transactions:
    post:
      summary: Create a new transaction
      operationId: create_transaction
      tags: [Marketplace]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '201':
          description: Transaction created
    get:
      summary: List all transactions
      operationId: list_transactions
      tags: [Marketplace]
      responses:
        '200':
          description: List of transactions
  /marketplace/transactions/{transaction_id}:
    get:
      summary: Get a transaction by ID
      operationId: get_transaction
      tags: [Marketplace]
      parameters:
        - name: transaction_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Transaction object
  /marketplace/transactions/{transaction_id}/process:
    post:
      summary: Process a transaction
      operationId: process_transaction
      tags: [Marketplace]
      parameters:
        - name: transaction_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Transaction processing
  /marketplace/transactions/{transaction_id}/complete:
    post:
      summary: Complete a transaction
      operationId: complete_transaction
      tags: [Marketplace]
      parameters:
        - name: transaction_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Transaction completed
  /marketplace/transactions/{transaction_id}/refund:
    post:
      summary: Refund a transaction
      operationId: refund_transaction
      tags: [Marketplace]
      parameters:
        - name: transaction_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Transaction refunded
  /marketplace/transactions/stats/summary:
    get:
      summary: Get transaction statistics
      operationId: get_transaction_stats
      tags: [Marketplace]
      responses:
        '200':
          description: Transaction statistics
  /marketplace/trust:
    post:
      summary: Create a trust score
      operationId: create_trust_score
      tags: [Marketplace]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '201':
          description: Trust score created
  /marketplace/trust/{user_id}:
    get:
      summary: Get trust score for a user
      operationId: get_trust_score
      tags: [Marketplace]
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Trust score
  /marketplace/trust/{user_id}/update:
    post:
      summary: Update trust score for a user
      operationId: update_trust_score
      tags: [Marketplace]
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Trust score updated
  /marketplace/trust/{user_id}/verify:
    post:
      summary: Verify a user
      operationId: verify_user
      tags: [Marketplace]
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User verification result
  /marketplace/trust/{user_id}/behavior:
    get:
      summary: Analyze user behavior
      operationId: analyze_user_behavior
      tags: [Marketplace]
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User behavior analysis
  /marketplace/trust/leaderboard/top:
    get:
      summary: Get trust leaderboard
      operationId: get_trust_leaderboard
      tags: [Marketplace]
      responses:
        '200':
          description: Trust leaderboard
  /marketplace/pricing:
    post:
      summary: Create a pricing entry
      operationId: create_pricing
      tags: [Marketplace]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '201':
          description: Pricing created
  /marketplace/pricing/{pricing_id}:
    get:
      summary: Get pricing by ID
      operationId: get_pricing
      tags: [Marketplace]
      parameters:
        - name: pricing_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Pricing object
    put:
      summary: Update pricing
      operationId: update_pricing
      tags: [Marketplace]
      parameters:
        - name: pricing_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Pricing updated
  /marketplace/pricing/{pricing_id}/optimize:
    post:
      summary: Optimize pricing
      operationId: optimize_pricing
      tags: [Marketplace]
      parameters:
        - name: pricing_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Pricing optimized
  /marketplace/pricing/listing/{listing_id}:
    get:
      summary: Get pricing for a listing
      operationId: get_pricing_for_listing
      tags: [Marketplace]
      parameters:
        - name: listing_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Pricing for listing
  /marketplace/pricing/bulk-optimize:
    post:
      summary: Bulk optimize pricing
      operationId: bulk_optimize_pricing
      tags: [Marketplace]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Bulk optimization results
  /marketplace/analytics/report:
    get:
      summary: Get marketplace analytics report
      operationId: get_analytics_report
      tags: [Marketplace]
      responses:
        '200':
          description: Analytics report
  /marketplace/analytics/insights:
    get:
      summary: Get marketplace insights
      operationId: get_marketplace_insights
      tags: [Marketplace]
      responses:
        '200':
          description: Marketplace insights
  /marketplace/analytics/compare:
    get:
      summary: Compare time periods
      operationId: compare_periods
      tags: [Marketplace]
      responses:
        '200':
          description: Period comparison
  /marketplace/analytics/demand-prediction/{category}:
    get:
      summary: Predict demand for a category
      operationId: predict_demand
      tags: [Marketplace]
      parameters:
        - name: category
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Demand prediction
components:
  schemas:
    HealthResponse:
      type: object
      required: [status, version]
      properties:
        status:
          type: string
        version:
          type: string
        timestamp:
          type: string
          format: date-time
    ContentType:
      type: string
      enum: [text, image, video]
    ModerationAction:
      type: string
      enum: [allow, flag, block, escalate]
    PolicySeverity:
      type: string
      enum: [low, medium, high, critical]
    AppealStatus:
      type: string
      enum: [pending, under_review, approved, rejected, escalated]
    ModerationRequest:
      type: object
      required: [content, content_type]
      properties:
        content:
          type: string
          minLength: 1
          maxLength: 100000
        content_type:
          $ref: '#/components/schemas/ContentType'
        user_id:
          type: string
        metadata:
          type: object
        callback_url:
          type: string
    ModerationResult:
      type: object
      properties:
        id:
          type: string
          format: uuid
        request_id:
          type: string
          format: uuid
        content_type:
          $ref: '#/components/schemas/ContentType'
        action:
          $ref: '#/components/schemas/ModerationAction'
        confidence:
          type: number
          minimum: 0
          maximum: 1
        categories:
          type: array
          items:
            type: string
        reasons:
          type: array
          items:
            type: string
        policy_violations:
          type: array
          items:
            type: string
        processing_time_ms:
          type: number
        created_at:
          type: string
          format: date-time
        agent_trace:
          type: object
    BatchModerationRequest:
      type: object
      required: [items]
      properties:
        items:
          type: array
          minItems: 1
          maxItems: 100
          items:
            $ref: '#/components/schemas/ModerationRequest'
        priority:
          type: string
          enum: [low, normal, high]
          default: normal
    BatchModerationResult:
      type: object
      properties:
        batch_id:
          type: string
          format: uuid
        results:
          type: array
          items:
            $ref: '#/components/schemas/ModerationResult'
        total_processed:
          type: integer
        total_flagged:
          type: integer
        total_blocked:
          type: integer
    PolicyRule:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
          minLength: 1
          maxLength: 200
        description:
          type: string
        pattern:
          type: string
          minLength: 1
        severity:
          $ref: '#/components/schemas/PolicySeverity'
        action:
          $ref: '#/components/schemas/ModerationAction'
        enabled:
          type: boolean
          default: true
    Policy:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
          minLength: 1
          maxLength: 200
        description:
          type: string
        rules:
          type: array
          items:
            $ref: '#/components/schemas/PolicyRule'
        content_types:
          type: array
          items:
            $ref: '#/components/schemas/ContentType'
        enabled:
          type: boolean
          default: true
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
    AppealSubmission:
      type: object
      required: [moderation_result_id, user_id, reason]
      properties:
        moderation_result_id:
          type: string
          format: uuid
        user_id:
          type: string
          minLength: 1
        reason:
          type: string
          minLength: 10
          maxLength: 5000
        evidence:
          type: object
    Appeal:
      type: object
      properties:
        id:
          type: string
          format: uuid
        moderation_result_id:
          type: string
          format: uuid
        user_id:
          type: string
        reason:
          type: string
        evidence:
          type: object
        status:
          $ref: '#/components/schemas/AppealStatus'
        reviewer_notes:
          type: string
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
        resolved_at:
          type: string
          format: date-time
    ScoreDimension:
      type: string
      enum: [readability, originality, engagement, seo]
    ScoreLevel:
      type: string
      enum: [low, medium, high]
    DimensionScore:
      type: object
      properties:
        dimension:
          $ref: '#/components/schemas/ScoreDimension'
        score:
          type: number
          minimum: 0
          maximum: 1
        level:
          $ref: '#/components/schemas/ScoreLevel'
    MetricRecordRequest:
      type: object
      required: [name, value]
      properties:
        name:
          type: string
          minLength: 1
        value:
          type: number
        label:
          type: string
    ReportRequest:
      type: object
      required: [report_id, creator_id, period_start, period_end]
      properties:
        report_id:
          type: string
        creator_id:
          type: string
        period_start:
          type: string
          format: date-time
        period_end:
          type: string
          format: date-time
    ForecastRequest:
      type: object
      required: [name]
      properties:
        name:
          type: string
        days:
          type: integer
          minimum: 1
          maximum: 365
          default: 30
    RevenueReportResponse:
      type: object
      properties:
        report_id:
          type: string
        creator_id:
          type: string
        period_start:
          type: string
        period_end:
          type: string
        total_revenue:
          type: string
        subscription_revenue:
          type: string
        tip_revenue:
          type: string
        merchandise_revenue:
          type: string
        sponsorship_revenue:
          type: string
        other_revenue:
          type: string
        subscriber_count:
          type: integer
        active_subscribers:
          type: integer
        churned_subscribers:
          type: integer
        currency:
          type: string
        insights:
          type: array
          items:
            type: string
        generated_at:
          type: string
    User:
      type: object
      required: [id, username, email, created_at, updated_at]
      properties:
        id:
          type: string
        username:
          type: string
        email:
          type: string
        avatar_url:
          type: string
        bio:
          type: string
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
    Category:
      type: object
      required: [id, name, slug]
      properties:
        id:
          type: string
        name:
          type: string
        slug:
          type: string
        description:
          type: string
        parent_id:
          type: string
    Product:
      type: object
      required: [id, seller_id, title, description, price, category_id, created_at, updated_at]
      properties:
        id:
          type: string
        seller_id:
          type: string
        title:
          type: string
        description:
          type: string
        price:
          type: number
          minimum: 0
        currency:
          type: string
          default: USD
        category_id:
          type: string
        images:
          type: array
          items:
            type: string
        tags:
          type: array
          items:
            type: string
        status:
          type: string
          default: active
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
    Order:
      type: object
      required: [id, buyer_id, seller_id, product_id, total_amount, created_at, updated_at]
      properties:
        id:
          type: string
        buyer_id:
          type: string
        seller_id:
          type: string
        product_id:
          type: string
        quantity:
          type: integer
          minimum: 1
          default: 1
        total_amount:
          type: number
          minimum: 0
        currency:
          type: string
          default: USD
        status:
          type: string
          default: pending
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
    Review:
      type: object
      required: [id, product_id, reviewer_id, rating, body, created_at, updated_at]
      properties:
        id:
          type: string
        product_id:
          type: string
        reviewer_id:
          type: string
        rating:
          type: integer
          minimum: 1
          maximum: 5
        title:
          type: string
        body:
          type: string
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
    PaginatedResponse:
      type: object
      properties:
        items:
          type: array
        total:
          type: integer
          minimum: 0
        page:
          type: integer
          minimum: 1
        per_page:
          type: integer
          minimum: 1
        has_next:
          type: boolean
        has_prev:
          type: boolean
    CreateOrderRequest:
      type: object
      required: [product_id]
      properties:
        product_id:
          type: string
        quantity:
          type: integer
          minimum: 1
          default: 1
    CreateReviewRequest:
      type: object
      required: [product_id, rating, body]
      properties:
        product_id:
          type: string
        rating:
          type: integer
          minimum: 1
          maximum: 5
        title:
          type: string
        body:
          type: string
          minLength: 1
    UpdateProductRequest:
      type: object
      properties:
        title:
          type: string
        description:
          type: string
        price:
          type: number
          minimum: 0
        category_id:
          type: string
        images:
          type: array
          items:
            type: string
        tags:
          type: array
          items:
            type: string
        status:
          type: string
    TokenResponse:
      type: object
      required: [access_token, expires_in]
      properties:
        access_token:
          type: string
        token_type:
          type: string
          default: Bearer
        expires_in:
          type: integer
        refresh_token:
          type: string
```

---

## Authentication

The UGC Marketplace API supports two authentication methods:

### 1. API Key (Current Default)

Pass your API key via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/health
```

Or as a query parameter:

```bash
curl "http://localhost:8000/api/v1/health?api_key=your-api-key"
```

### 2. OAuth2 Client Credentials (SDK)

The Python SDK uses OAuth2 client credentials flow. Provide `client_id` and `client_secret`:

```python
from ugc_marketplace import UGCMarketplaceClient

client = UGCMarketplaceClient(
    base_url="https://api.ugc-marketplace.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
)
```

The SDK automatically:
- Obtains an access token via `POST /v1/auth/token`
- Refreshes the token before expiry (60-second buffer)
- Includes `Authorization: Bearer <token>` on every request
- Falls back to re-authentication if refresh fails

### Token Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

### Authentication Errors

| Status | Error | Description |
|--------|-------|-------------|
| 401 | `UGCAuthenticationError` | Missing or invalid credentials |
| 403 | Forbidden | Insufficient permissions |

---

## Rate Limiting

The API enforces rate limiting to ensure fair usage and service stability.

### Limits

| Tier | Rate Limit | Burst |
|------|-----------|-------|
| API endpoints | 10 requests/second | 20 |
| General endpoints | 30 requests/second | 50 |

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1705312800
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in the window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

### Handling Rate Limits

When you receive a `429 Too Many Requests` response:

1. **Read the `Retry-After` header** — seconds to wait before retrying
2. **Wait the specified duration**
3. **Retry the request**

```python
import time
import httpx

response = httpx.get("http://localhost:8000/api/v1/discovery/search?query=python")
if response.status_code == 429:
    retry_after = int(response.headers.get("Retry-After", 1))
    time.sleep(retry_after)
    response = httpx.get("http://localhost:8000/api/v1/discovery/search?query=python")
```

The Python SDK handles this automatically — it reads `Retry-After` and retries with exponential backoff.

---

## Error Handling

All endpoints return standard HTTP error responses with a consistent JSON structure:

```json
{
  "detail": "Error description"
}
```

### Error Response Format

| Status Code | Description | SDK Exception |
|-------------|-------------|---------------|
| 400 | Bad Request — Invalid input | `UGCValidationError` |
| 401 | Unauthorized — Missing or invalid API key | `UGCAuthenticationError` |
| 403 | Forbidden — Insufficient permissions | `UGCMarketplaceError` |
| 404 | Not Found — Resource does not exist | `UGCNotFoundError` |
| 409 | Conflict — Resource already exists | `UGCMarketplaceError` |
| 422 | Validation Error — Invalid request body | `UGCValidationError` |
| 429 | Too Many Requests — Rate limit exceeded | `UGCRateLimitError` |
| 500 | Internal Server Error | `UGCServerError` |

### Validation Error Format

For `422` responses, the error body includes field-level details:

```json
{
  "detail": [
    {
      "loc": ["body", "content"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### SDK Error Handling

```python
from ugc_marketplace import (
    UGCMarketplaceClient,
    UGCAuthenticationError,
    UGCNotFoundError,
    UGCRateLimitError,
    UGCValidationError,
    UGCServerError,
    UGCMarketplaceError,
)

client = UGCMarketplaceClient(
    base_url="https://api.ugc-marketplace.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
)

try:
    product = client.get_product("prod_nonexistent")
except UGCNotFoundError:
    print("Product not found")
except UGCAuthenticationError:
    print("Authentication failed — check your credentials")
except UGCRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except UGCValidationError as e:
    print(f"Validation failed: {e.errors}")
except UGCServerError:
    print("Server error — please try again later")
except UGCMarketplaceError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
```

### Exception Hierarchy

```
UGCMarketplaceError (base)
├── UGCAuthenticationError (401)
├── UGCNotFoundError (404)
├── UGCRateLimitError (429)
│   └── retry_after: int | None
├── UGCValidationError (422)
│   └── errors: dict
└── UGCServerError (5xx)
```

---

## SDK Usage

### Installation

```bash
pip install ugc-marketplace-sdk
```

Or from source:

```bash
cd ugc-marketplace/sdk
pip install -e .
```

### Quick Start

```python
from ugc_marketplace import UGCMarketplaceClient

# Initialize with OAuth2 credentials
client = UGCMarketplaceClient(
    base_url="https://api.ugc-marketplace.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
)

# List products
products = client.list_products(page=1, per_page=20)
for product in products.items:
    print(f"{product.title} — ${product.price}")

# Get a specific product
product = client.get_product("prod_123")
print(product.description)

# Create an order
from ugc_marketplace import CreateOrderRequest
order = client.create_order(CreateOrderRequest(product_id="prod_123", quantity=2))
print(f"Order created: {order.id}")
```

### Context Manager (Recommended)

```python
from ugc_marketplace import UGCMarketplaceClient

with UGCMarketplaceClient(
    base_url="https://api.ugc-marketplace.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
) as client:
    user = client.get_current_user()
    print(f"Logged in as {user.username}")
```

### Users

```python
# Get current user profile
me = client.get_current_user()
print(me.email)

# Get a specific user
user = client.get_user("user_456")
print(user.bio)
```

### Categories

```python
# List all categories
categories = client.list_categories(page=1, per_page=50)
for cat in categories.items:
    print(f"{cat.name} ({cat.slug})")

# Get a specific category
category = client.get_category("cat_789")
```

### Products

```python
# List products with filters
products = client.list_products(
    page=1,
    per_page=20,
    category_id="cat_electronics",
    min_price=10.0,
    max_price=500.0,
    search="wireless headphones",
)

# Check pagination
print(f"Page {products.page}, showing {len(products.items)} of {products.total}")
if products.has_next:
    next_page = client.list_products(page=2, per_page=20)

# Get a single product
product = client.get_product("prod_abc123")

# Create a new product
from ugc_marketplace import Product
from datetime import datetime

new_product = Product(
    seller_id="user_456",
    title="Handmade Leather Wallet",
    description="Premium full-grain leather wallet",
    price=49.99,
    category_id="cat_accessories",
    images=["https://example.com/wallet1.jpg"],
    tags=["leather", "handmade", "accessories"],
    created_at=datetime.now(),
    updated_at=datetime.now(),
)
created = client.create_product(new_product)

# Update a product
from ugc_marketplace import UpdateProductRequest
updated = client.update_product(
    "prod_abc123",
    UpdateProductRequest(price=39.99, status="active"),
)

# Delete a product
client.delete_product("prod_abc123")
```

### Orders

```python
# List orders
orders = client.list_orders(page=1, per_page=20, status="pending")

# Get a specific order
order = client.get_order("order_xyz789")

# Create an order
from ugc_marketplace import CreateOrderRequest
order = client.create_order(CreateOrderRequest(product_id="prod_abc123", quantity=1))

# Cancel an order
cancelled = client.cancel_order("order_xyz789")
```

### Reviews

```python
# List reviews for a product
reviews = client.list_reviews(product_id="prod_abc123", page=1, per_page=10)
avg_rating = sum(r.rating for r in reviews.items) / len(reviews.items) if reviews.items else 0

# Get a specific review
review = client.get_review("rev_111")

# Create a review
from ugc_marketplace import CreateReviewRequest
review = client.create_review(
    CreateReviewRequest(
        product_id="prod_abc123",
        rating=5,
        title="Excellent quality",
        body="Exceeded my expectations. Highly recommended!",
    )
)

# Delete a review
client.delete_review("rev_111")
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | `https://api.ugc-marketplace.example.com` | API base URL |
| `client_id` | `None` | OAuth2 client ID |
| `client_secret` | `None` | OAuth2 client secret |
| `access_token` | `None` | Pre-existing access token |
| `timeout` | `30.0` | Request timeout in seconds |
| `max_retries` | `3` | Maximum retry attempts |
| `retry_delay` | `1.0` | Initial retry delay (exponential backoff) |

### Raw HTTP Examples

#### cURL

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Moderate text
curl -X POST http://localhost:8000/api/v1/moderation/moderate/text \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello world", "content_type": "text"}'

# Search content
curl "http://localhost:8000/api/v1/discovery/search?query=python&limit=5"

# Create a listing
curl -X POST http://localhost:8000/api/v1/marketplace/listings \
  -H "Content-Type: application/json" \
  -d '{"title": "Digital Art Pack", "price": 29.99, "category": "digital-art"}'
```

#### JavaScript

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

#### Python (httpx)

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

---

## Webhooks

The UGC Marketplace API supports webhook callbacks for asynchronous operations, primarily for content moderation results.

### Moderation Result Webhook

When you submit content for moderation with a `callback_url`, the API will POST the moderation result to your endpoint once processing is complete.

#### Request

Include `callback_url` in your moderation request:

```json
{
  "content": "Text to analyze",
  "content_type": "text",
  "user_id": "user-123",
  "callback_url": "https://your-app.com/webhooks/moderation"
}
```

#### Webhook Payload

Your endpoint will receive a `POST` with the full `ModerationResult`:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "content_type": "text",
  "action": "flag",
  "confidence": 0.85,
  "categories": ["spam"],
  "reasons": ["matched pattern: promotional content"],
  "policy_violations": ["spam_policy"],
  "processing_time_ms": 45.2,
  "created_at": "2024-01-15T10:30:00.000000",
  "agent_trace": {
    "text_moderation": {"score": 0.85},
    "policy_enforcement": {"matched": ["spam_policy"]}
  }
}
```

#### Webhook Headers

```
Content-Type: application/json
X-UGC-Event: moderation.completed
X-UGC-Delivery: 550e8400-e29b-41d4-a716-446655440000
```

#### Handling Webhooks

```python
from fastapi import FastAPI, Request
from ugc_marketplace.models import ModerationResult

app = FastAPI()

@app.post("/webhooks/moderation")
async def handle_moderation_webhook(request: Request):
    payload = await request.json()
    result = ModerationResult.model_validate(payload)

    if result.action == "block":
        # Remove content immediately
        await remove_content(result.request_id)
    elif result.action == "flag":
        # Queue for human review
        await queue_for_review(result.request_id)
    elif result.action == "escalate":
        # Notify moderators
        await notify_moderators(result)

    return {"received": True}
```

#### Webhook Delivery Behavior

- **Timeout:** 10 seconds
- **Retries:** Failed deliveries are logged but not retried automatically
- **Success:** HTTP 2xx response
- **Failure:** Non-2xx response or timeout — logged as warning

#### Webhook Client (Server-Side)

The `WebhookClient` in `integrations/content_moderation/webhook.py` handles delivery:

```python
from ugc_marketplace.integrations.content_moderation.webhook import WebhookClient
from ugc_marketplace.models import ModerationResult

client = WebhookClient(timeout=10.0)
success = await client.send_result(
    url="https://your-app.com/webhooks/moderation",
    result=moderation_result,
)
```

---

## Integration Guide

### Architecture Overview

The UGC Marketplace API follows a modular monolith pattern with 10 service domains, each backed by dedicated AI agents:

```
┌─────────────────────────────────────────────────────┐
│                   API Gateway                        │
│              (FastAPI + Uvicorn)                     │
├─────────┬─────────┬─────────┬─────────┬─────────────┤
│Moderation│Monetize │Discovery│  Rights │   Quality   │
├─────────┼─────────┼─────────┼─────────┼─────────────┤
│  Fraud  │Analytics│Licensing│Curation │ Marketplace │
├─────────┴─────────┴─────────┴─────────┴─────────────┤
│              AI Agent Layer                          │
│  (LangChain + OpenAI + DeepAgents)                  │
├─────────────────────────────────────────────────────┤
│              Infrastructure                          │
│  PostgreSQL │ Redis │ Kafka │ Prometheus            │
└─────────────────────────────────────────────────────┘
```

### Integration Patterns

#### 1. Content Moderation Pipeline

```python
import httpx

async def moderate_content_pipeline(content: str, content_type: str, user_id: str):
    """Full moderation pipeline with webhook callback."""
    async with httpx.AsyncClient() as client:
        # Step 1: Submit for moderation
        response = await client.post(
            "http://localhost:8000/api/v1/moderation/moderate/text",
            json={
                "content": content,
                "content_type": content_type,
                "user_id": user_id,
                "callback_url": "https://your-app.com/webhooks/moderation",
            }
        )
        result = response.json()

        # Step 2: Handle immediate result
        if result["action"] == "block":
            return {"status": "blocked", "reasons": result["reasons"]}
        elif result["action"] == "flag":
            return {"status": "flagged", "review_required": True}
        else:
            return {"status": "allowed", "confidence": result["confidence"]}
```

#### 2. Marketplace Transaction Flow

```python
import httpx

async def purchase_flow(product_id: str, buyer_id: str, quantity: int = 1):
    """Complete purchase flow with fraud check and trust scoring."""
    async with httpx.AsyncClient() as client:
        base = "http://localhost:8000/api/v1"

        # Step 1: Get product details
        product = (await client.get(f"{base}/marketplace/listings/{product_id}")).json()

        # Step 2: Check buyer trust score
        trust = (await client.get(f"{base}/marketplace/trust/{buyer_id}")).json()

        # Step 3: Create transaction
        txn = (await client.post(
            f"{base}/marketplace/transactions",
            json={"product_id": product_id, "quantity": quantity, "buyer_id": buyer_id}
        )).json()

        # Step 4: Process transaction
        processed = (await client.post(
            f"{base}/marketplace/transactions/{txn['transaction_id']}/process"
        )).json()

        # Step 5: Complete transaction
        completed = (await client.post(
            f"{base}/marketplace/transactions/{txn['transaction_id']}/complete"
        )).json()

        return completed
```

#### 3. Creator Analytics Dashboard

```python
import httpx

async def get_creator_dashboard(creator_id: str):
    """Aggregate all creator metrics into a single dashboard."""
    async with httpx.AsyncClient() as client:
        base = "http://localhost:8000/api/v1"

        # Fetch all metrics in parallel
        growth, audience, revenue, engagement = await asyncio.gather(
            client.get(f"{base}/analytics/growth/{creator_id}"),
            client.get(f"{base}/analytics/audience/{creator_id}"),
            client.get(f"{base}/analytics/revenue/{creator_id}"),
            client.get(f"{base}/analytics/engagement/{creator_id}"),
        )

        return {
            "creator_id": creator_id,
            "growth": growth.json(),
            "audience": audience.json(),
            "revenue": revenue.json(),
            "engagement": engagement.json(),
        }
```

#### 4. Fraud Detection Integration

```python
import httpx

async def fraud_check_transaction(transaction: dict):
    """Analyze transaction for fraud before processing."""
    async with httpx.AsyncClient() as client:
        base = "http://localhost:8000/api/v1"

        # Step 1: Analyze transaction
        analysis = (await client.post(
            f"{base}/fraud/analyze",
            json=transaction
        )).json()

        # Step 2: Check risk score
        risk = (await client.post(
            f"{base}/fraud/risk/score",
            json=transaction
        )).json()

        # Step 3: Detect patterns
        patterns = (await client.post(
            f"{base}/fraud/patterns/detect",
            json=transaction
        )).json()

        # Step 4: Make decision
        if analysis["risk_score"] > 0.8 or risk["overall_score"] > 0.8:
            return {"approved": False, "reason": "high_risk", "risk_score": analysis["risk_score"]}

        return {"approved": True, "risk_score": analysis["risk_score"]}
```

#### 5. Rights Management Workflow

```python
import httpx

async def license_content_workflow(content_id: str, licensor: str, licensee: str):
    """Full rights management workflow."""
    async with httpx.AsyncClient() as client:
        base = "http://localhost:8000/api/v1"

        # Step 1: Create license
        license_resp = (await client.post(
            f"{base}/licensing/licenses",
            json={
                "licensor": licensor,
                "licensee": licensee,
                "content_id": content_id,
                "terms": {"type": "non-exclusive", "duration": "1 year"}
            }
        )).json()

        license_id = license_resp["license_id"]

        # Step 2: Activate license
        activated = (await client.post(
            f"{base}/licensing/licenses/{license_id}/activate"
        )).json()

        # Step 3: Run compliance check
        compliance = (await client.post(
            f"{base}/licensing/compliance/check",
            json={"license_id": license_id}
        )).json()

        # Step 4: Calculate royalties
        royalties = (await client.post(
            f"{base}/licensing/royalties/calculate",
            json={"license_id": license_id}
        )).json()

        return {
            "license_id": license_id,
            "status": activated["status"],
            "compliant": compliance["compliant"],
            "royalty": royalties["total_royalty"],
        }
```

### Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment (development/production) |
| `API_PREFIX` | `/api/v1` | API route prefix |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka brokers |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `SECRET_KEY` | `change-me-in-production` | Application secret |
| `DEFAULT_CONFIDENCE_THRESHOLD` | `0.7` | Moderation confidence threshold |
| `MAX_CONTENT_SIZE_MB` | `50` | Maximum content size in MB |

### Deployment

#### Docker

```bash
docker-compose up -d
```

#### Kubernetes

```bash
kubectl apply -k k8s/overlays/development/
```

#### Health Checks

```bash
# Liveness
curl http://localhost:8000/api/v1/health/live

# Readiness
curl http://localhost:8000/api/v1/health/ready

# Full health
curl http://localhost:8000/api/v1/health
```

### Interactive Documentation

When the server is running:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

## Endpoint Index

### Health (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/health/ready` | Readiness check |
| GET | `/api/v1/health/live` | Liveness check |

### Content Moderation (4)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/moderation/moderate/text` | Moderate text content |
| POST | `/api/v1/moderation/moderate/image` | Moderate image content |
| POST | `/api/v1/moderation/moderate/video` | Moderate video content |
| POST | `/api/v1/moderation/moderate/batch` | Batch moderation |

### Creator Monetization (6)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/monetization/metrics` | Record a metric |
| GET | `/api/v1/monetization/metrics` | List metrics |
| POST | `/api/v1/monetization/reports` | Generate report |
| GET | `/api/v1/monetization/reports/{report_id}` | Get report |
| POST | `/api/v1/monetization/forecast` | Forecast metric |
| GET | `/api/v1/monetization/revenue/{creator_id}` | Revenue report |

### Content Discovery (3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/discovery/search` | Search content |
| GET | `/api/v1/discovery/recommendations/{user_id}` | Get recommendations |
| GET | `/api/v1/discovery/trending` | Get trending |

### Rights Management (19)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/rights/licenses` | Create license |
| GET | `/api/v1/rights/licenses` | List licenses |
| GET | `/api/v1/rights/licenses/{license_id}` | Get license |
| DELETE | `/api/v1/rights/licenses/{license_id}` | Revoke license |
| POST | `/api/v1/rights/detect` | Detect license |
| POST | `/api/v1/rights/infringement/report` | File infringement report |
| GET | `/api/v1/rights/infringement/reports/{content_id}` | List infringement reports |
| POST | `/api/v1/rights/infringement/detect` | Detect infringement |
| PATCH | `/api/v1/rights/infringement/reports/{report_id}/status` | Update report status |
| POST | `/api/v1/rights/takedown/request` | Submit takedown request |
| GET | `/api/v1/rights/takedown/{request_id}` | Get takedown request |
| POST | `/api/v1/rights/takedown/{request_id}/process` | Process takedown |
| GET | `/api/v1/rights/takedown` | List takedown requests |
| POST | `/api/v1/rights/usage/record` | Record usage |
| GET | `/api/v1/rights/usage/summary/{content_id}` | Usage summary |
| GET | `/api/v1/rights/usage/records/{content_id}` | Usage records |
| POST | `/api/v1/rights/validate` | Validate rights |
| GET | `/api/v1/rights/validations/{validation_id}` | Get validation |
| GET | `/api/v1/rights/validations/content/{content_id}` | List validations |

### Quality Scoring (12)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/quality/health` | Health check |
| GET | `/api/v1/quality/metrics` | Prometheus metrics |
| POST | `/api/v1/quality/score` | Score content |
| POST | `/api/v1/quality/score/readability` | Score readability |
| POST | `/api/v1/quality/score/originality` | Score originality |
| POST | `/api/v1/quality/score/engagement` | Score engagement |
| POST | `/api/v1/quality/score/seo` | Score SEO |
| POST | `/api/v1/quality/improvements` | Get improvements |
| POST | `/api/v1/quality/benchmark` | Compare benchmark |
| POST | `/api/v1/quality/batch` | Batch score |
| GET | `/api/v1/quality/dimensions` | List dimensions |
| GET | `/api/v1/quality/benchmarks` | List benchmarks |

### Fraud Detection (13)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/fraud/analyze` | Analyze transaction |
| POST | `/api/v1/fraud/analyze/batch` | Batch analyze |
| POST | `/api/v1/fraud/patterns/detect` | Detect patterns |
| POST | `/api/v1/fraud/anomalies/detect` | Detect anomalies |
| POST | `/api/v1/fraud/risk/score` | Score risk |
| POST | `/api/v1/fraud/accounts/analyze` | Analyze account |
| GET | `/api/v1/fraud/health` | Health check |
| GET | `/api/v1/fraud/ready` | Readiness check |
| POST | `/api/v1/fraud/monitoring/start` | Start monitoring |
| POST | `/api/v1/fraud/monitoring/stop` | Stop monitoring |
| GET | `/api/v1/fraud/agents/status` | Agent statuses |
| GET | `/api/v1/fraud/reports/{report_id}` | Get report |
| GET | `/api/v1/fraud/reports` | List reports |

### Creator Analytics (17)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/analytics/health` | Health check |
| GET | `/api/v1/analytics/ready` | Readiness check |
| POST | `/api/v1/analytics/growth/predict` | Predict growth |
| GET | `/api/v1/analytics/growth/{creator_id}` | Get growth prediction |
| GET | `/api/v1/analytics/growth/{creator_id}/scenarios` | Growth scenarios |
| POST | `/api/v1/analytics/content/analyze` | Analyze content |
| GET | `/api/v1/analytics/content/{content_id}` | Content performance |
| GET | `/api/v1/analytics/content/creator/{creator_id}` | Creator content |
| POST | `/api/v1/analytics/audience/analyze` | Analyze audience |
| GET | `/api/v1/analytics/audience/{creator_id}` | Audience analysis |
| GET | `/api/v1/analytics/audience/{creator_id}/segments` | Audience segments |
| POST | `/api/v1/analytics/revenue/report` | Generate revenue report |
| GET | `/api/v1/analytics/revenue/{creator_id}` | Revenue report |
| GET | `/api/v1/analytics/revenue/{creator_id}/breakdown` | Revenue breakdown |
| POST | `/api/v1/analytics/engagement/report` | Generate engagement report |
| GET | `/api/v1/analytics/engagement/{creator_id}` | Engagement report |
| GET | `/api/v1/analytics/engagement/{creator_id}/metrics` | Engagement metrics |

### Licensing Engine (24)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/licensing/health` | Health check |
| GET | `/api/v1/licensing/ready` | Readiness check |
| GET | `/api/v1/licensing/live` | Liveness check |
| POST | `/api/v1/licensing/licenses` | Create license |
| GET | `/api/v1/licensing/licenses` | List licenses |
| GET | `/api/v1/licensing/licenses/{license_id}` | Get license |
| PATCH | `/api/v1/licensing/licenses/{license_id}` | Update license |
| DELETE | `/api/v1/licensing/licenses/{license_id}` | Delete license |
| POST | `/api/v1/licensing/licenses/{license_id}/activate` | Activate license |
| POST | `/api/v1/licensing/licenses/{license_id}/revoke` | Revoke license |
| POST | `/api/v1/licensing/negotiations` | Create negotiation |
| GET | `/api/v1/licensing/negotiations/{negotiation_id}` | Get negotiation |
| POST | `/api/v1/licensing/negotiations/{negotiation_id}/counter` | Counter proposal |
| POST | `/api/v1/licensing/negotiations/{negotiation_id}/accept` | Accept proposal |
| POST | `/api/v1/licensing/negotiations/{negotiation_id}/reject` | Reject proposal |
| POST | `/api/v1/licensing/compliance/check` | Compliance check |
| GET | `/api/v1/licensing/compliance/reports` | List compliance reports |
| GET | `/api/v1/licensing/compliance/reports/{report_id}` | Get compliance report |
| GET | `/api/v1/licensing/compliance/licenses/{license_id}` | License compliance |
| POST | `/api/v1/licensing/royalties/calculate` | Calculate royalties |
| GET | `/api/v1/licensing/royalties/{calculation_id}` | Get calculation |
| GET | `/api/v1/licensing/royalties/license/{license_id}` | License royalties |
| POST | `/api/v1/licensing/contracts/analyze` | Analyze contract |
| GET | `/api/v1/licensing/contracts/{analysis_id}` | Get analysis |

### Community Curation (9)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/curation/health` | Health check |
| GET | `/api/v1/curation/agents` | List agents |
| POST | `/api/v1/curation/curate` | Curate content |
| POST | `/api/v1/curation/rank` | Rank content |
| POST | `/api/v1/curation/trends` | Surface trends |
| POST | `/api/v1/curation/filter` | Filter by quality |
| POST | `/api/v1/curation/cluster` | Cluster topics |
| POST | `/api/v1/curation/explain` | Explain curation |
| GET | `/api/v1/curation/metrics` | Curation metrics |

### Content Marketplace (30)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/marketplace/listings` | Create listing |
| GET | `/api/v1/marketplace/listings` | List listings |
| GET | `/api/v1/marketplace/listings/{listing_id}` | Get listing |
| PUT | `/api/v1/marketplace/listings/{listing_id}` | Update listing |
| DELETE | `/api/v1/marketplace/listings/{listing_id}` | Delete listing |
| POST | `/api/v1/marketplace/listings/{listing_id}/categorize` | Categorize listing |
| POST | `/api/v1/marketplace/listings/{listing_id}/moderate` | Moderate listing |
| POST | `/api/v1/marketplace/transactions` | Create transaction |
| GET | `/api/v1/marketplace/transactions` | List transactions |
| GET | `/api/v1/marketplace/transactions/{transaction_id}` | Get transaction |
| POST | `/api/v1/marketplace/transactions/{transaction_id}/process` | Process transaction |
| POST | `/api/v1/marketplace/transactions/{transaction_id}/complete` | Complete transaction |
| POST | `/api/v1/marketplace/transactions/{transaction_id}/refund` | Refund transaction |
| GET | `/api/v1/marketplace/transactions/stats/summary` | Transaction stats |
| POST | `/api/v1/marketplace/trust` | Create trust score |
| GET | `/api/v1/marketplace/trust/{user_id}` | Get trust score |
| POST | `/api/v1/marketplace/trust/{user_id}/update` | Update trust score |
| POST | `/api/v1/marketplace/trust/{user_id}/verify` | Verify user |
| GET | `/api/v1/marketplace/trust/{user_id}/behavior` | User behavior |
| GET | `/api/v1/marketplace/trust/leaderboard/top` | Trust leaderboard |
| POST | `/api/v1/marketplace/pricing` | Create pricing |
| GET | `/api/v1/marketplace/pricing/{pricing_id}` | Get pricing |
| PUT | `/api/v1/marketplace/pricing/{pricing_id}` | Update pricing |
| POST | `/api/v1/marketplace/pricing/{pricing_id}/optimize` | Optimize pricing |
| GET | `/api/v1/marketplace/pricing/listing/{listing_id}` | Listing pricing |
| POST | `/api/v1/marketplace/pricing/bulk-optimize` | Bulk optimize |
| GET | `/api/v1/marketplace/analytics/report` | Analytics report |
| GET | `/api/v1/marketplace/analytics/insights` | Marketplace insights |
| GET | `/api/v1/marketplace/analytics/compare` | Compare periods |
| GET | `/api/v1/marketplace/analytics/demand-prediction/{category}` | Demand prediction |

---

**Total: 140 endpoints across 11 service domains**

---

*Generated from source code analysis of ugc-marketplace v1.0.0*

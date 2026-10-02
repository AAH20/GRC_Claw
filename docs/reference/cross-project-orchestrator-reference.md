# Cross-Project Orchestrator API Reference

> Last updated: 2026-10-02 | Base URL: `http://localhost:8000`

Unified orchestration layer for multi-project agentic AI marketing systems. Project discovery, dependency resolution, resource allocation, health monitoring, and cost optimization.

---

## Table of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
  - [GET /health](#get-health)
  - [GET /metrics](#get-metrics)
  - [GET /api/v1/agents/{agent_id}/status](#get-apiv1agentsagent_idstatus)
  - [Projects](#projects)
    - [GET /api/v1/projects](#get-apiv1projects)
    - [POST /api/v1/projects](#post-apiv1projects)
    - [GET /api/v1/projects/{project_id}](#get-apiv1projectsproject_id)
    - [POST /api/v1/projects/scan](#post-apiv1projectsscan)
  - [Dependencies](#dependencies)
    - [GET /api/v1/dependencies](#get-apiv1dependencies)
    - [POST /api/v1/dependencies/resolve](#post-apiv1dependenciesresolve)
    - [POST /api/v1/dependencies/edges](#post-apiv1dependenciesedges)
    - [DELETE /api/v1/dependencies/edges/{source}/{target}](#delete-apiv1dependenciesedgessourcetarget)
    - [GET /api/v1/dependencies/topology](#get-apiv1dependenciestopology)
    - [GET /api/v1/dependencies/dependents/{project_id}](#get-apiv1dependenciesdependentsproject_id)
- [Data Models](#data-models)
- [Error Codes](#error-codes)
- [Authentication](#authentication)

---

## Overview

The Cross-Project Orchestrator API provides programmatic access to unified orchestration of multi-project agentic AI marketing systems. It manages project discovery, dependency resolution, resource allocation, health monitoring, and cost optimization across all GRC_Claw projects.

**Base Path:** `/api/v1`

**Technology:** FastAPI with Pydantic v2 models, structured logging via structlog, Prometheus metrics, CORS middleware, and background agent loops.

---

## Endpoints

### GET /health

Health check endpoint for load balancers and monitoring.

**Response (200):**

```json
{
  "status": "healthy",
  "service": "cross-project-orchestrator"
}
```

---

### GET /metrics

Prometheus metrics endpoint for monitoring.

**Response (200):**

```
# HELP orchestrator_requests_total Total HTTP requests
# TYPE orchestrator_requests_total counter
orchestrator_requests_total{endpoint="/health",method="GET",status="200"} 42.0
# HELP orchestrator_request_duration_seconds HTTP request latency in seconds
# TYPE orchestrator_request_duration_seconds histogram
orchestrator_request_duration_seconds_bucket{endpoint="/health",le="0.005",method="GET"} 42.0
```

---

### GET /api/v1/agents/{agent_id}/status

Get the status of a specific orchestrator agent.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | Yes | Agent identifier |

**Valid Agent IDs:**

| Agent ID | Description |
|----------|-------------|
| `project_discovery` | Discovers and catalogs projects |
| `dependency_resolution` | Resolves inter-project dependencies |
| `resource_allocation` | Allocates resources across projects |
| `health_monitoring` | Monitors project health |
| `cost_optimization` | Optimizes infrastructure costs |

**Response (200):**

```json
{
  "agent_id": "project_discovery",
  "running": true
}
```

---

## Projects

### GET /api/v1/projects

List all discovered projects with optional filtering.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `language` | string | No | Filter by programming language |
| `project_type` | string | No | Filter by project type |

**Response (200):**

```json
{
  "projects": [
    {
      "project_id": "real-estate-marketing",
      "name": "Real Estate Marketing",
      "path": "/Users/ahmedhassan/GRC_Claw/projects/real-estate-marketing",
      "project_type": "marketing",
      "language": "python",
      "dependencies": [],
      "metadata": {},
      "discovered_at": "2026-10-02T12:00:00+00:00",
      "last_scanned": "2026-10-02T12:00:00+00:00"
    }
  ],
  "total": 1
}
```

---

### POST /api/v1/projects

Register a new project manually.

**Request Body:**

```json
{
  "name": "New Marketing Project",
  "path": "/Users/ahmedhassan/GRC_Claw/projects/new-project",
  "type": "marketing",
  "language": "python",
  "dependencies": ["campaign-optimizer"],
  "metadata": {
    "team": "marketing",
    "priority": "high"
  }
}
```

**Response (200):**

```json
{
  "project_id": "manual:New Marketing Project",
  "name": "New Marketing Project",
  "path": "/Users/ahmedhassan/GRC_Claw/projects/new-project",
  "project_type": "marketing",
  "language": "python",
  "dependencies": ["campaign-optimizer"],
  "metadata": {
    "team": "marketing",
    "priority": "high"
  },
  "discovered_at": "2026-10-02T12:00:00+00:00",
  "last_scanned": null
}
```

---

### GET /api/v1/projects/{project_id}

Get a specific project by ID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |

**Response (200):**

```json
{
  "project_id": "real-estate-marketing",
  "name": "Real Estate Marketing",
  "path": "/Users/ahmedhassan/GRC_Claw/projects/real-estate-marketing",
  "project_type": "marketing",
  "language": "python",
  "dependencies": [],
  "metadata": {},
  "discovered_at": "2026-10-02T12:00:00+00:00",
  "last_scanned": "2026-10-02T12:00:00+00:00"
}
```

---

### POST /api/v1/projects/scan

Trigger an immediate project discovery scan.

**Response (200):**

```json
{
  "discovered": 5,
  "projects": [
    {
      "project_id": "new-project-1",
      "name": "New Project 1",
      "path": "/Users/ahmedhassan/GRC_Claw/projects/new-project-1",
      "project_type": "marketing",
      "language": "python",
      "dependencies": [],
      "metadata": {},
      "discovered_at": "2026-10-02T12:00:00+00:00",
      "last_scanned": "2026-10-02T12:00:00+00:00"
    }
  ]
}
```

---

## Dependencies

### GET /api/v1/dependencies

List all known dependency edges.

**Response (200):**

```json
{
  "edges": [
    {
      "source": "real-estate-marketing",
      "target": "campaign-optimizer",
      "version_constraint": ">=1.0.0"
    }
  ],
  "total": 1
}
```

---

### POST /api/v1/dependencies/resolve

Resolve dependencies starting from a root project.

**Request Body:**

```json
{
  "root": "real-estate-marketing"
}
```

**Response (200):**

```json
{
  "resolved": {
    "real-estate-marketing": "1.0.0",
    "campaign-optimizer": "2.1.0"
  },
  "conflicts": [],
  "unresolved": [],
  "graph": {
    "real-estate-marketing": ["campaign-optimizer"]
  }
}
```

---

### POST /api/v1/dependencies/edges

Add a dependency edge.

**Request Body:**

```json
{
  "source": "real-estate-marketing",
  "target": "email-marketing",
  "version_constraint": ">=1.0.0"
}
```

**Response (200):**

```json
{
  "status": "added",
  "edge": {
    "source": "real-estate-marketing",
    "target": "email-marketing"
  }
}
```

---

### DELETE /api/v1/dependencies/edges/{source}/{target}

Remove a dependency edge.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source` | string | Yes | Source project ID |
| `target` | string | Yes | Target project ID |

**Response (200):**

```json
{
  "status": "removed"
}
```

---

### GET /api/v1/dependencies/topology

Get the topological ordering of the dependency graph.

**Response (200):**

```json
{
  "order": [
    "campaign-optimizer",
    "real-estate-marketing"
  ]
}
```

---

### GET /api/v1/dependencies/dependents/{project_id}

Get all projects that depend on the given project.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | Yes | Project identifier |

**Response (200):**

```json
{
  "project_id": "campaign-optimizer",
  "dependents": [
    "real-estate-marketing",
    "email-marketing"
  ]
}
```

---

## Data Models

### DiscoveredProject

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | string | Unique project identifier |
| `name` | string | Project name |
| `path` | string | Filesystem path to project |
| `project_type` | string | Project type (default: unknown) |
| `language` | string | Primary language (default: unknown) |
| `dependencies` | list[string] | List of dependency project IDs |
| `metadata` | dict | Arbitrary metadata |
| `discovered_at` | datetime | Discovery timestamp |
| `last_scanned` | datetime | Last scan timestamp (optional) |

### DependencyEdge

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Source project ID |
| `target` | string | Target project ID |
| `version_constraint` | string | Version constraint (default: *) |

### ResolutionResult

| Field | Type | Description |
|-------|------|-------------|
| `resolved` | dict | Map of project ID to resolved version |
| `conflicts` | list | List of version conflicts |
| `unresolved` | list | List of unresolved dependencies |
| `graph` | dict | Adjacency list representation |

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid authentication |
| `AUTHORIZATION_DENIED` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist |
| `CONFLICT` | 409 | Resource conflict (e.g., circular dependency) |
| `UNPROCESSABLE_ENTITY` | 422 | Business logic validation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Response Format

```json
{
  "detail": "Project not found: unknown-project"
}
```

---

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <token>
```

CORS is configured to allow all origins. In production, restrict to configured origins only.

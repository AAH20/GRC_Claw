# GRC_Claw API Versioning & Deprecation Automation
# =================================================
#
# This document defines the automated versioning and deprecation system
# for the GRC_Claw API. It covers:
# - Version lifecycle management
# - Automated deprecation detection
# - Breaking change detection
# - Migration automation
# - Client notification system
#
# The system is implemented as a CI/CD pipeline that runs on every API
# spec change.

---

## 1. Version Lifecycle

### 1.1 Version Stages

```
Alpha → Beta → GA → Deprecated → Sunset
  │       │      │        │          │
  │       │      │        │          └─ Endpoint removed (410 Gone)
  │       │      │        └─ 6 months notice, still functional
  │       │      └─ Stable, no breaking changes
  │       └─ Public testing, minor breaking changes allowed
  └─ Internal testing, breaking changes allowed
```

### 1.2 Stage Durations

| Stage | Minimum Duration | Maximum Duration | Breaking Changes |
|-------|-----------------|-----------------|------------------|
| Alpha | 1 month | 3 months | Allowed |
| Beta | 1 month | 3 months | Minor only |
| GA | 12 months | Indefinite | Not allowed |
| Deprecated | 6 months | 12 months | N/A |
| Sunset | — | — | Endpoint removed |

### 1.3 Version Format

```
v{major}.{minor}

Examples:
  v1.0    — Initial GA release
  v1.1    — Minor update (additive changes)
  v1.2    — Minor update
  v2.0    — Major update (breaking changes)
```

---

## 2. Automated Deprecation Detection

### 2.1 Detection Pipeline

```yaml
# .github/workflows/api-versioning.yml
name: API Versioning & Deprecation

on:
  push:
    paths:
      - 'grc-claw-api-spec.md'
      - 'grc-claw-openapi.yaml'
      - 'grc-claw-sdk-python/**'
      - 'grc-claw-sdk-typescript/**'
  pull_request:
    paths:
      - 'grc-claw-api-spec.md'
      - 'grc-claw-openapi.yaml'

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Detect API changes
        id: changes
        run: |
          # Compare OpenAPI specs
          git diff HEAD~1 -- grc-claw-openapi.yaml > api-diff.txt

          # Run change detection
          python scripts/detect_api_changes.py \
            --old-spec grc-claw-openapi.yaml \
            --new-spec grc-claw-openapi.yaml \
            --output changes.json

          echo "changes=$(cat changes.json)" >> $GITHUB_OUTPUT

      - name: Check for breaking changes
        run: |
          python scripts/check_breaking_changes.py \
            --changes changes.json \
            --output breaking-changes.json

      - name: Update version metadata
        run: |
          python scripts/update_version.py \
            --changes changes.json \
            --breaking-changes breaking-changes.json

      - name: Generate deprecation notices
        run: |
          python scripts/generate_deprecations.py \
            --spec grc-claw-openapi.yaml \
            --output deprecations.md

      - name: Create migration guide
        if: steps.changes.outputs.breaking == 'true'
        run: |
          python scripts/generate_migration_guide.py \
            --old-version ${{ steps.changes.outputs.old_version }} \
            --new-version ${{ steps.changes.outputs.new_version }} \
            --output migration-guide.md

      - name: Notify subscribers
        run: |
          python scripts/notify_subscribers.py \
            --deprecations deprecations.md \
            --webhook-url ${{ secrets.DEPRECATION_WEBHOOK_URL }}
```

### 2.2 Change Detection Script

```python
#!/usr/bin/env python3
"""
detect_api_changes.py — Detect API changes between spec versions.

Usage:
    python detect_api_changes.py --old-spec old.yaml --new-spec new.yaml --output changes.json
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional
import yaml


class ChangeType(Enum):
    # Breaking changes
    ENDPOINT_REMOVED = "endpoint_removed"
    FIELD_REMOVED = "field_removed"
    FIELD_TYPE_CHANGED = "field_type_changed"
    FIELD_RENAMED = "field_renamed"
    ENUM_VALUE_REMOVED = "enum_value_removed"
    ERROR_CODE_CHANGED = "error_code_changed"
    AUTH_REQUIRED = "auth_required"

    # Additive changes (non-breaking)
    ENDPOINT_ADDED = "endpoint_added"
    FIELD_ADDED = "field_added"
    ENUM_VALUE_ADDED = "enum_value_added"
    OPTIONAL_FIELD_ADDED = "optional_field_added"

    # Deprecation
    ENDPOINT_DEPRECATED = "endpoint_deprecated"
    FIELD_DEPRECATED = "field_deprecated"


@dataclass
class APIChange:
    change_type: str
    path: str
    description: str
    breaking: bool
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    migration_hint: Optional[str] None


def load_spec(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def extract_endpoints(spec: dict) -> dict:
    """Extract all endpoints from OpenAPI spec."""
    endpoints = {}
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method in ("get", "post", "put", "delete", "patch"):
                key = f"{method.upper()} {path}"
                endpoints[key] = {
                    "summary": details.get("summary", ""),
                    "operation_id": details.get("operationId", ""),
                    "deprecated": details.get("deprecated", False),
                    "parameters": details.get("parameters", []),
                    "request_body": details.get("requestBody", {}),
                    "responses": details.get("responses", {}),
                }
    return endpoints


def extract_schemas(spec: dict) -> dict:
    """Extract all schemas from OpenAPI spec."""
    return spec.get("components", {}).get("schemas", {})


def compare_endpoints(old: dict, new: dict) -> List[APIChange]:
    """Compare endpoints between two spec versions."""
    changes = []

    # Check for removed endpoints
    for key in old:
        if key not in new:
            changes.append(APIChange(
                change_type=ChangeType.ENDPOINT_REMOVED.value,
                path=key,
                description=f"Endpoint {key} was removed",
                breaking=True,
                old_value=old[key]["summary"],
            ))

    # Check for added endpoints
    for key in new:
        if key not in old:
            changes.append(APIChange(
                change_type=ChangeType.ENDPOINT_ADDED.value,
                path=key,
                description=f"Endpoint {key} was added",
                breaking=False,
                new_value=new[key]["summary"],
            ))

    # Check for modified endpoints
    for key in old:
        if key in new:
            old_ep = old[key]
            new_ep = new[key]

            # Check deprecation
            if not old_ep.get("deprecated") and new_ep.get("deprecated"):
                changes.append(APIChange(
                    change_type=ChangeType.ENDPOINT_DEPRECATED.value,
                    path=key,
                    description=f"Endpoint {key} was deprecated",
                    breaking=False,
                    migration_hint="Check deprecation header for replacement",
                ))

            # Check for removed parameters
            old_params = {p["name"] for p in old_ep.get("parameters", [])}
            new_params = {p["name"] for p in new_ep.get("parameters", [])}
            for param in old_params - new_params:
                changes.append(APIChange(
                    change_type=ChangeType.FIELD_REMOVED.value,
                    path=f"{key} (parameter: {param})",
                    description=f"Parameter '{param}' was removed from {key}",
                    breaking=True,
                    old_value=param,
                ))

            # Check for removed request body fields
            old_body = old_ep.get("request_body", {})
            new_body = new_ep.get("request_body", {})
            # ... deep comparison of request body schemas

    return changes


def compare_schemas(old: dict, new: dict) -> List[APIChange]:
    """Compare schemas between two spec versions."""
    changes = []

    for schema_name in old:
        if schema_name not in new:
            changes.append(APIChange(
                change_type=ChangeType.FIELD_REMOVED.value,
                path=f"schema:{schema_name}",
                description=f"Schema '{schema_name}' was removed",
                breaking=True,
            ))
            continue

        old_schema = old[schema_name]
        new_schema = new[schema_name]

        # Check for removed fields
        old_fields = set(old_schema.get("properties", {}).keys())
        new_fields = set(new_schema.get("properties", {}).keys())

        for field in old_fields - new_fields:
            changes.append(APIChange(
                change_type=ChangeType.FIELD_REMOVED.value,
                path=f"schema:{schema_name}.{field}",
                description=f"Field '{field}' was removed from {schema_name}",
                breaking=True,
                old_value=old_schema["properties"][field].get("type", "unknown"),
            ))

        # Check for type changes
        for field in old_fields & new_fields:
            old_type = old_schema["properties"][field].get("type")
            new_type = new_schema["properties"][field].get("type")
            if old_type != new_type:
                changes.append(APIChange(
                    change_type=ChangeType.FIELD_TYPE_CHANGED.value,
                    path=f"schema:{schema_name}.{field}",
                    description=f"Field '{field}' type changed from {old_type} to {new_type}",
                    breaking=True,
                    old_value=old_type,
                    new_value=new_type,
                ))

        # Check for new fields (non-breaking)
        for field in new_fields - old_fields:
            changes.append(APIChange(
                change_type=ChangeType.FIELD_ADDED.value,
                path=f"schema:{schema_name}.{field}",
                description=f"Field '{field}' was added to {schema_name}",
                breaking=False,
                new_value=new_schema["properties"][field].get("type", "unknown"),
            ))

    return changes


def main():
    parser = argparse.ArgumentParser(description="Detect API changes")
    parser.add_argument("--old-spec", required=True)
    parser.add_argument("--new-spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    old_spec = load_spec(args.old_spec)
    new_spec = load_spec(args.new_spec)

    old_endpoints = extract_endpoints(old_spec)
    new_endpoints = extract_endpoints(new_spec)
    old_schemas = extract_schemas(old_spec)
    new_schemas = extract_schemas(new_spec)

    changes = []
    changes.extend(compare_endpoints(old_endpoints, new_endpoints))
    changes.extend(compare_schemas(old_schemas, new_schemas))

    output = {
        "total_changes": len(changes),
        "breaking_changes": sum(1 for c in changes if c.breaking),
        "additive_changes": sum(1 for c in changes if not c.breaking),
        "changes": [asdict(c) for c in changes],
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Detected {output['total_changes']} changes")
    print(f"  Breaking: {output['breaking_changes']}")
    print(f"  Additive: {output['additive_changes']}")

    if output["breaking_changes"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 2.3 Breaking Change Checker

```python
#!/usr/bin/env python3
"""
check_breaking_changes.py — Check for breaking changes and determine version bump.

Usage:
    python check_breaking_changes.py --changes changes.json --output version-bump.json
"""

import argparse
import json
from dataclasses import dataclass
from enum import Enum


class VersionBump(Enum):
    MAJOR = "major"    # Breaking changes
    MINOR = "minor"    # Additive changes
    PATCH = "patch"    # Documentation, bug fixes


@dataclass
class VersionDecision:
    bump_type: str
    current_version: str
    new_version: str
    reason: str
    breaking_changes: list
    migration_required: bool


def parse_version(version: str) -> tuple:
    """Parse version string into (major, minor, patch)."""
    parts = version.lstrip("v").split(".")
    return tuple(int(p) for p in parts)


def format_version(major: int, minor: int, patch: int = 0) -> str:
    """Format version tuple into string."""
    return f"v{major}.{minor}.{patch}"


def determine_bump(changes: dict, current_version: str) -> VersionDecision:
    """Determine version bump based on changes."""
    breaking = [c for c in changes["changes"] if c["breaking"]]
    additive = [c for c in changes["changes"] if not c["breaking"]]

    major, minor, patch = parse_version(current_version)

    if breaking:
        # Major version bump
        new_version = format_version(major + 1, 0, 0)
        return VersionDecision(
            bump_type=VersionBump.MAJOR.value,
            current_version=current_version,
            new_version=new_version,
            reason=f"{len(breaking)} breaking changes detected",
            breaking_changes=breaking,
            migration_required=True,
        )
    elif additive:
        # Minor version bump
        new_version = format_version(major, minor + 1, 0)
        return VersionDecision(
            bump_type=VersionBump.MINOR.value,
            current_version=current_version,
            new_version=new_version,
            reason=f"{len(additive)} additive changes detected",
            breaking_changes=[],
            migration_required=False,
        )
    else:
        # Patch version bump
        new_version = format_version(major, minor, patch + 1)
        return VersionDecision(
            bump_type=VersionBump.PATCH.value,
            current_version=current_version,
            new_version=new_version,
            reason="No functional changes",
            breaking_changes=[],
            migration_required=False,
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--changes", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--current-version", default="v1.0")
    args = parser.parse_args()

    with open(args.changes) as f:
        changes = json.load(f)

    decision = determine_bump(changes, args.current_version)

    output = {
        "bump_type": decision.bump_type,
        "current_version": decision.current_version,
        "new_version": decision.new_version,
        "reason": decision.reason,
        "migration_required": decision.migration_required,
        "breaking_changes": decision.breaking_changes,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Version bump: {decision.current_version} → {decision.new_version}")
    print(f"Reason: {decision.reason}")
    print(f"Migration required: {decision.migration_required}")


if __name__ == "__main__":
    main()
```

---

## 3. Deprecation Automation

### 3.1 Deprecation Notice Generator

```python
#!/usr/bin/env python3
"""
generate_deprecations.py — Generate deprecation notices from OpenAPI spec.

Scans the OpenAPI spec for deprecated endpoints and fields, then generates:
- Deprecation timeline
- Migration instructions
- Webhook notification payload
- Email notification content
"""

import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import yaml


DEPRECATION_PERIOD_DAYS = 180  # 6 months


def find_deprecated_endpoints(spec: dict) -> List[Dict[str, Any]]:
    """Find all deprecated endpoints in the spec."""
    deprecated = []

    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method not in ("get", "post", "put", "delete", "patch"):
                continue

            if details.get("deprecated"):
                deprecated.append({
                    "type": "endpoint",
                    "method": method.upper(),
                    "path": path,
                    "operation_id": details.get("operationId", ""),
                    "summary": details.get("summary", ""),
                    "deprecation_date": details.get("x-deprecation-date", ""),
                    "sunset_date": details.get("x-sunset-date", ""),
                    "replacement": details.get("x-replacement", ""),
                })

    return deprecated


def find_deprecated_fields(spec: dict) -> List[Dict[str, Any]]:
    """Find all deprecated fields in the spec."""
    deprecated = []

    for schema_name, schema in spec.get("components", {}).get("schemas", {}).items():
        for field_name, field in schema.get("properties", {}).items():
            if field.get("deprecated"):
                deprecated.append({
                    "type": "field",
                    "schema": schema_name,
                    "field": field_name,
                    "deprecation_date": field.get("x-deprecation-date", ""),
                    "sunset_date": field.get("x-sunset-date", ""),
                    "replacement": field.get("x-replacement", ""),
                })

    return deprecated


def generate_timeline(deprecated_items: List[Dict]) -> Dict[str, Any]:
    """Generate deprecation timeline."""
    today = datetime.utcnow()
    sunset = today + timedelta(days=DEPRECATION_PERIOD_DAYS)

    timeline = {
        "announcement_date": today.isoformat() + "Z",
        "deprecation_date": today.isoformat() + "Z",
        "sunset_date": sunset.isoformat() + "Z",
        "total_days": DEPRECATION_PERIOD_DAYS,
        "milestones": [
            {
                "date": today.isoformat() + "Z",
                "event": "Deprecation announced",
                "description": "Deprecation notice sent to all subscribers",
            },
            {
                "date": (today + timedelta(days=30)).isoformat() + "Z",
                "event": "30-day warning",
                "description": "First warning: 30 days until deprecation",
            },
            {
                "date": (today + timedelta(days=90)).isoformat() + "Z",
                "event": "90-day warning",
                "description": "Second warning: 90 days until deprecation",
            },
            {
                "date": (today + timedelta(days=150)).isoformat() + "Z",
                "event": "150-day warning",
                "description": "Final warning: 30 days until sunset",
            },
            {
                "date": sunset.isoformat() + "Z",
                "event": "Sunset",
                "description": "Endpoint/field removed, returns 410 Gone",
            },
        ],
    }

    return timeline


def generate_webhook_payload(deprecated_items: List[Dict], timeline: Dict) -> Dict:
    """Generate webhook payload for deprecation notification."""
    return {
        "webhook_id": f"wh-dep-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "event_type": "api.version_deprecated",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "deprecated_items": deprecated_items,
            "timeline": timeline,
            "total_deprecations": len(deprecated_items),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.spec) as f:
        spec = yaml.safe_load(f)

    deprecated_endpoints = find_deprecated_endpoints(spec)
    deprecated_fields = find_deprecated_fields(spec)
    all_deprecated = deprecated_endpoints + deprecated_fields

    timeline = generate_timeline(all_deprecated)
    webhook_payload = generate_webhook_payload(all_deprecated, timeline)

    output = {
        "deprecated_endpoints": deprecated_endpoints,
        "deprecated_fields": deprecated_fields,
        "timeline": timeline,
        "webhook_payload": webhook_payload,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Found {len(deprecated_endpoints)} deprecated endpoints")
    print(f"Found {len(deprecated_fields)} deprecated fields")
    print(f"Sunset date: {timeline['sunset_date']}")


if __name__ == "__main__":
    main()
```

### 3.2 Subscriber Notification System

```python
#!/usr/bin/env python3
"""
notify_subscribers.py — Notify webhook subscribers of deprecations.

Sends deprecation notices to all registered webhook subscribers
that are subscribed to the 'api.version_deprecated' event.
"""

import argparse
import hashlib
import hmac
import json
import time
from typing import List, Dict, Any

import httpx


WEBHOOK_EVENTS = [
    "api.version_deprecated",
    "api.endpoint_removed",
    "api.breaking_change",
]


def sign_payload(payload: str, secret: str) -> str:
    """Sign webhook payload with HMAC-SHA256."""
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def send_webhook(url: str, payload: Dict, secret: str) -> bool:
    """Send webhook to subscriber."""
    payload_str = json.dumps(payload)
    signature = sign_payload(payload_str, secret)

    headers = {
        "Content-Type": "application/json",
        "X-GRC-Signature": signature,
        "X-GRC-Event-Type": payload.get("event_type", ""),
        "X-GRC-Event-ID": payload.get("event_id", ""),
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send webhook to {url}: {e}")
        return False


def notify_subscribers(deprecations: Dict, subscribers: List[Dict]) -> Dict[str, Any]:
    """Notify all subscribers of deprecations."""
    results = {
        "total_subscribers": len(subscribers),
        "successful": 0,
        "failed": 0,
        "details": [],
    }

    for sub in subscribers:
        if "api.version_deprecated" not in sub.get("events", []):
            continue

        success = send_webhook(
            sub["url"],
            deprecations["webhook_payload"],
            sub["secret"],
        )

        results["details"].append({
            "subscription_id": sub["subscription_id"],
            "url": sub["url"],
            "success": success,
        })

        if success:
            results["successful"] += 1
        else:
            results["failed"] += 1

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deprecations", required=True)
    parser.add_argument("--subscribers", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.deprecations) as f:
        deprecations = json.load(f)

    with open(args.subscribers) as f:
        subscribers = json.load(f)

    results = notify_subscribers(deprecations, subscribers)

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Notified {results['successful']}/{results['total_subscribers']} subscribers")
    print(f"Failed: {results['failed']}")


if __name__ == "__main__":
    main()
```

---

## 4. Migration Guide Generator

### 4.1 Automated Migration Guide

```python
#!/usr/bin/env python3
"""
generate_migration_guide.py — Generate migration guide for breaking changes.

Usage:
    python generate_migration_guide.py \
        --old-version v1.0 \
        --new-version v2.0 \
        --changes changes.json \
        --output migration-guide.md
"""

import argparse
import json
from typing import List, Dict, Any


MIGRATION_TEMPLATES = {
    "endpoint_removed": """
### {description}

**Breaking Change:** Endpoint `{path}` has been removed.

**Migration:**
{replacement}

**Before:**
```{language}
{old_code}
```

**After:**
```{language}
{new_code}
```
""",
    "field_removed": """
### {description}

**Breaking Change:** Field `{field}` has been removed from `{schema}`.

**Migration:**
{replacement}
""",
    "field_type_changed": """
### {description}

**Breaking Change:** Field `{field}` type changed from `{old_type}` to `{new_type}`.

**Migration:**
Update your code to handle the new type.
""",
    "field_renamed": """
### {description}

**Breaking Change:** Field `{old_name}` has been renamed to `{new_name}`.

**Migration:**
Update all references from `{old_name}` to `{new_name}`.
""",
}


def generate_migration_guide(
    old_version: str,
    new_version: str,
    changes: List[Dict[str, Any]],
) -> str:
    """Generate markdown migration guide."""
    breaking = [c for c in changes if c["breaking"]]

    guide = f"""# Migration Guide: {old_version} → {new_version}

## Overview

This guide helps you migrate from {old_version} to {new_version}.

**Total breaking changes:** {len(breaking)}

## Timeline

| Date | Milestone |
|------|-----------|
| {old_version} | Current version |
| T+30 days | Deprecation notices sent |
| T+90 days | Migration deadline |
| T+180 days | {old_version} sunset |

## Breaking Changes

"""

    for change in breaking:
        template = MIGRATION_TEMPLATES.get(change["change_type"], "")
        if template:
            guide += template.format(
                description=change["description"],
                path=change.get("path", ""),
                field=change.get("path", "").split(".")[-1],
                schema=change.get("path", "").split(".")[0],
                old_type=change.get("old_value", ""),
                new_type=change.get("new_value", ""),
                old_name=change.get("old_value", ""),
                new_name=change.get("new_value", ""),
                replacement=change.get("migration_hint", "See API reference for replacement"),
                language="python",
                old_code="# TODO: Add old code example",
                new_code="# TODO: Add new code example",
            )

    guide += """
## SDK Updates

Update your SDK to the latest version:

```bash
# Python
pip install --upgrade grc-claw-sdk

# TypeScript
npm update @grc-claw/sdk

# Go
go get -u github.com/grc-claw/sdk-go
```

## Testing

1. Update your SDK to the latest version
2. Run your test suite against the staging environment
3. Fix any breaking changes identified in this guide
4. Deploy to production after validation

## Support

- [Developer Portal](https://portal.grc-claw.io)
- [GitHub Issues](https://github.com/grc-claw/grc-claw/issues)
- [Community Discord](https://discord.gg/grc-claw)
"""

    return guide


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-version", required=True)
    parser.add_argument("--new-version", required=True)
    parser.add_argument("--changes", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.changes) as f:
        changes_data = json.load(f)

    guide = generate_migration_guide(
        args.old_version,
        args.new_version,
        changes_data["changes"],
    )

    with open(args.output, "w") as f:
        f.write(guide)

    print(f"Migration guide written to {args.output}")


if __name__ == "__main__":
    main()
```

---

## 5. Version Metadata Schema

### 5.1 Version Metadata File

```yaml
# version-metadata.yaml
# This file is auto-generated by the versioning pipeline.

version: v1.2
status: ga
release_date: "2026-10-01"
sunset_date: null

# Version history
history:
  - version: v1.0
    status: deprecated
    release_date: "2026-04-01"
    sunset_date: "2026-10-01"
    deprecation_date: "2026-04-01"
    changes:
      - type: initial_release
        description: "Initial GA release"

  - version: v1.1
    status: ga
    release_date: "2026-07-01"
    sunset_date: null
    changes:
      - type: additive
        description: "Added policy dependency graph endpoint"
      - type: additive
        description: "Added compliance crosswalk query"
      - type: additive
        description: "Added agent trust score endpoint"

  - version: v1.2
    status: ga
    release_date: "2026-10-01"
    sunset_date: null
    changes:
      - type: additive
        description: "Added batch enforcement decisions"
      - type: additive
        description: "Added evidence export packages"
      - type: additive
        description: "Added GraphQL subscriptions"
      - type: deprecation
        description: "Deprecated v1.0 /v1.0/policies/{id}/activate endpoint"
        replacement: "Use POST /v1.2/policies/{id}/activate"

# Deprecation schedule
deprecations:
  - endpoint: "POST /v1.0/policies/{id}/activate"
    deprecated_in: v1.2
    sunset_date: "2027-04-01"
    replacement: "POST /v1.2/policies/{id}/activate"
    migration: "Update URL path from v1.0 to v1.2"

  - field: "Policy.policy_key"
    deprecated_in: v1.2
    sunset_date: "2027-04-01"
    replacement: "Policy.policyKey"
    migration: "Use camelCase field name"

# Compatibility matrix
compatibility:
  sdk_versions:
    python: ">=1.0.0"
    typescript: ">=1.0.0"
    go: ">=1.0.0"
    java: ">=1.0.0"
    rust: ">=1.0.0"

  minimum_api_version: v1.0
  recommended_api_version: v1.2
```

### 5.2 Version Header

All API responses include version information:

```http
HTTP/1.1 200 OK
X-API-Version: v1.2
X-API-Deprecated: false
X-API-Sunset-Date: (only if deprecated)
Content-Type: application/json
```

---

## 6. CI/CD Pipeline

### 6.1 Pipeline Stages

```yaml
# .github/workflows/api-versioning.yml (complete)

name: API Versioning & Deprecation

on:
  push:
    branches: [main]
    paths:
      - 'grc-claw-api-spec.md'
      - 'grc-claw-openapi.yaml'
      - 'grc-claw-sdk-python/**'
      - 'grc-claw-sdk-typescript/**'

jobs:
  # Stage 1: Detect changes
  detect:
    runs-on: ubuntu-latest
    outputs:
      changes: ${{ steps.detect.outputs.changes }}
      breaking: ${{ steps.detect.outputs.breaking }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Detect API changes
        id: detect
        run: |
          python scripts/detect_api_changes.py \
            --old-spec grc-claw-openapi.yaml \
            --new-spec grc-claw-openapi.yaml \
            --output changes.json

          echo "changes=$(cat changes.json)" >> $GITHUB_OUTPUT
          echo "breaking=$(jq -r '.breaking_changes > 0' changes.json)" >> $GITHUB_OUTPUT

  # Stage 2: Determine version bump
  version:
    needs: detect
    runs-on: ubuntu-latest
    outputs:
      new_version: ${{ steps.version.outputs.new_version }}
      bump_type: ${{ steps.version.outputs.bump_type }}
    steps:
      - uses: actions/checkout@v4

      - name: Determine version bump
        id: version
        run: |
          python scripts/check_breaking_changes.py \
            --changes changes.json \
            --current-version $(cat VERSION) \
            --output version.json

          echo "new_version=$(jq -r '.new_version' version.json)" >> $GITHUB_OUTPUT
          echo "bump_type=$(jq -r '.bump_type' version.json)" >> $GITHUB_OUTPUT

      - name: Update VERSION file
        run: |
          echo "${{ steps.version.outputs.new_version }}" > VERSION

  # Stage 3: Generate deprecation notices
  deprecate:
    needs: [detect, version]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate deprecation notices
        run: |
          python scripts/generate_deprecations.py \
            --spec grc-claw-openapi.yaml \
            --output deprecations.json

      - name: Upload deprecation artifact
        uses: actions/upload-artifact@v4
        with:
          name: deprecations
          path: deprecations.json

  # Stage 4: Generate migration guide (only for major versions)
  migrate:
    needs: [detect, version]
    if: needs.version.outputs.bump_type == 'major'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate migration guide
        run: |
          python scripts/generate_migration_guide.py \
            --old-version $(cat VERSION~1) \
            --new-version ${{ needs.version.outputs.new_version }} \
            --changes changes.json \
            --output migration-guide.md

      - name: Upload migration guide
        uses: actions/upload-artifact@v4
        with:
          name: migration-guide
          path: migration-guide.md

  # Stage 5: Notify subscribers
  notify:
    needs: [deprecate, version]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Notify webhook subscribers
        run: |
          python scripts/notify_subscribers.py \
            --deprecations deprecations.json \
            --subscribers subscribers.json \
            --output notification-results.json

      - name: Send email notifications
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 587
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: "GRC_Claw API ${{ needs.version.outputs.new_version }} Released"
          to: api-subscribers@grc-claw.io
          from: api@grc-claw.io
          html_body: |
            <h1>GRC_Claw API ${{ needs.version.outputs.new_version }}</h1>
            <p>New version released with ${{ needs.detect.outputs.changes }} changes.</p>
            <p>See the <a href="https://portal.grc-claw.io/migration">migration guide</a> for details.</p>

  # Stage 6: Update documentation
  docs:
    needs: [version, deprecate]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update version metadata
        run: |
          python scripts/update_version_metadata.py \
            --version ${{ needs.version.outputs.new_version }} \
            --deprecations deprecations.json \
            --output version-metadata.yaml

      - name: Commit changes
        run: |
          git config user.name "GRC_Claw Bot"
          git config user.email "bot@grc-claw.io"
          git add VERSION version-metadata.yaml
          git commit -m "chore: release ${{ needs.version.outputs.new_version }}"
          git push

  # Stage 7: Create GitHub release
  release:
    needs: [version, docs]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ needs.version.outputs.new_version }}
          name: "GRC_Claw API ${{ needs.version.outputs.new_version }}"
          body: |
            ## Changes
            ${{ needs.detect.outputs.changes }}

            ## Migration
            See the [migration guide](https://portal.grc-claw.io/migration) for breaking changes.
          draft: false
          prerelease: false
```

---

## 7. Deprecation Headers

### 7.1 HTTP Headers

All deprecated endpoints include these headers:

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Apr 2027 00:00:00 GMT
Link: <https://api.grc-claw.io/v1.2/policies/{id}/activate>; rel="successor-version"
X-API-Deprecated: true
X-API-Sunset-Date: 2027-04-01
X-API-Replacement: POST /v1.2/policies/{id}/activate
```

### 7.2 SDK Deprecation Warnings

```python
import warnings
from grc_claw import GRCClawClient

client = GRCClawClient(api_key="...", tenant_id="...")

# This will emit a DeprecationWarning
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    response = client._request("POST", "/v1.0/policies/pol-001/activate")
    # DeprecationWarning: Endpoint POST /v1.0/policies/{id}/activate is deprecated.
    # Use POST /v1.2/policies/{id}/activate instead.
    # Sunset date: 2027-04-01
```

---

## 8. Monitoring & Alerting

### 8.1 Deprecation Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `api_deprecated_endpoint_calls` | Calls to deprecated endpoints | > 1000/day |
| `api_sunset_endpoint_calls` | Calls to sunset endpoints | > 0 |
| `api_version_adoption` | % clients on latest version | < 80% |
| `api_deprecation_notice_delivery` | Successful deprecation notices | < 99% |

### 8.2 Alerts

```yaml
# alerts/deprecation-alerts.yml
groups:
  - name: api-deprecation
    rules:
      - alert: DeprecatedEndpointHighUsage
        expr: rate(api_deprecated_endpoint_calls[1d]) > 1000
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "High usage of deprecated endpoint {{ $labels.endpoint }}"
          description: "Endpoint {{ $labels.endpoint }} has {{ $value }} calls/day"

      - alert: SunsetEndpointCalled
        expr: rate(api_sunset_endpoint_calls[1h]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Sunset endpoint {{ $labels.endpoint }} is being called"
          description: "Endpoint {{ $labels.endpoint }} was sunset and should not be called"

      - alert: LowVersionAdoption
        expr: api_version_adoption < 0.8
        for: 7d
        labels:
          severity: warning
        annotations:
          summary: "Low adoption of latest API version"
          description: "Only {{ $value }}% of clients are on the latest version"
```

---

## 9. Automation Scripts Summary

| Script | Purpose | Trigger |
|--------|---------|---------|
| `detect_api_changes.py` | Detect changes between spec versions | Every PR |
| `check_breaking_changes.py` | Determine version bump type | Every PR |
| `generate_deprecations.py` | Generate deprecation notices | Every release |
| `notify_subscribers.py` | Notify webhook subscribers | Every release |
| `generate_migration_guide.py` | Generate migration guide | Major releases |
| `update_version_metadata.py` | Update version metadata | Every release |
| `update_version.py` | Update VERSION file | Every release |

---

*End of Versioning & Deprecation Automation Specification*

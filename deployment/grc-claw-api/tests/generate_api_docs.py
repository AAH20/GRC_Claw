#!/usr/bin/env python3
"""
API Documentation Generator for GRC_Claw.

Generates comprehensive markdown documentation from the OpenAPI spec.
Can also generate documentation from route introspection.

Usage:
    python generate_api_docs.py [--openapi /path/to/openapi.json] [--output docs/api_reference.md]
    python generate_api_docs.py --introspect --output docs/api_reference.md
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ===========================================================================
# OpenAPI-based Documentation Generator
# ===========================================================================

def load_openapi_spec(path: str) -> Dict[str, Any]:
    """Load OpenAPI spec from JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def extract_parameters(parameters: List[Dict[str, Any]]) -> str:
    """Extract parameter documentation from OpenAPI spec."""
    if not parameters:
        return ""

    lines = ["#### Parameters", ""]
    lines.append("| Name | In | Type | Required | Description |")
    lines.append("|------|-----|------|----------|-------------|")

    for param in parameters:
        name = param.get("name", "")
        location = param.get("in", "")
        schema = param.get("schema", {})
        param_type = schema.get("type", "string")
        required = "Yes" if param.get("required", False) else "No"
        description = param.get("description", "").replace("|", "\\|")
        lines.append(f"| `{name}` | {location} | {param_type} | {required} | {description} |")

    lines.append("")
    return "\n".join(lines)


def extract_request_body(request_body: Optional[Dict[str, Any]]) -> str:
    """Extract request body documentation."""
    if not request_body:
        return ""

    lines = ["#### Request Body", ""]
    content = request_body.get("content", {})

    for media_type, media_obj in content.items():
        lines.append(f"**Content-Type:** `{media_type}`")
        lines.append("")

        schema = media_obj.get("schema", {})
        ref = schema.get("$ref", "")

        if ref:
            # Extract model name from reference
            model_name = ref.split("/")[-1]
            lines.append(f"**Schema:** `{model_name}`")
            lines.append("")

        example = media_obj.get("example")
        if example:
            lines.append("**Example:**")
            lines.append("```json")
            lines.append(json.dumps(example, indent=2))
            lines.append("```")
            lines.append("")

    return "\n".join(lines)


def extract_responses(responses: Dict[str, Any]) -> str:
    """Extract response documentation."""
    lines = ["#### Responses", ""]

    for status_code, response_obj in responses.items():
        description = response_obj.get("description", "")
        lines.append(f"**{status_code}** - {description}")
        lines.append("")

        content = response_obj.get("content", {})
        for media_type, media_obj in content.items():
            example = media_obj.get("example")
            if example:
                lines.append(f"```json")
                lines.append(json.dumps(example, indent=2))
                lines.append("```")
                lines.append("")

    return "\n".join(lines)


def generate_endpoint_doc(
    method: str,
    path: str,
    operation: Dict[str, Any],
    base_path: str = "",
) -> str:
    """Generate documentation for a single endpoint."""
    summary = operation.get("summary", "")
    description = operation.get("description", "")
    tags = operation.get("tags", [])
    parameters = operation.get("parameters", [])
    request_body = operation.get("requestBody")
    responses = operation.get("responses", {})
    operation_id = operation.get("operationId", "")

    lines = []

    # Header
    lines.append(f"### {summary}")
    lines.append("")

    # Method and path
    full_path = f"{base_path}{path}" if base_path else path
    lines.append(f"`{method.upper()} {full_path}`")
    lines.append("")

    # Tags
    if tags:
        lines.append(f"**Tags:** {', '.join(tags)}")
        lines.append("")

    # Description
    if description:
        lines.append(description)
        lines.append("")

    # Operation ID
    if operation_id:
        lines.append(f"**Operation ID:** `{operation_id}`")
        lines.append("")

    # Parameters
    param_doc = extract_parameters(parameters)
    if param_doc:
        lines.append(param_doc)

    # Request Body
    body_doc = extract_request_body(request_body)
    if body_doc:
        lines.append(body_doc)

    # Responses
    response_doc = extract_responses(responses)
    if response_doc:
        lines.append(response_doc)

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def generate_openapi_docs(spec: Dict[str, Any], title: str = "API Reference") -> str:
    """Generate full markdown documentation from OpenAPI spec."""
    info = spec.get("info", {})
    api_title = info.get("title", title)
    api_version = info.get("version", "1.0.0")
    api_description = info.get("description", "")
    servers = spec.get("servers", [])
    paths = spec.get("paths", {})

    lines = []

    # Header
    lines.append(f"# {api_title}")
    lines.append("")
    lines.append(f"**Version:** {api_version}")
    lines.append("")

    if api_description:
        lines.append(api_description)
        lines.append("")

    # Servers
    if servers:
        lines.append("## Servers")
        lines.append("")
        for server in servers:
            url = server.get("url", "")
            desc = server.get("description", "")
            lines.append(f"- `{url}` - {desc}")
        lines.append("")

    # Group endpoints by tag
    tagged_endpoints: Dict[str, List[Tuple[str, str, Dict[str, Any]]]] = {}

    for path, path_obj in paths.items():
        for method, operation in path_obj.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue

            tags = operation.get("tags", ["Other"])
            for tag in tags:
                if tag not in tagged_endpoints:
                    tagged_endpoints[tag] = []
                tagged_endpoints[tag].append((method, path, operation))

    # Generate documentation for each tag group
    for tag, endpoints in sorted(tagged_endpoints.items()):
        lines.append(f"## {tag}")
        lines.append("")

        for method, path, operation in sorted(endpoints, key=lambda x: (x[1], x[0])):
            endpoint_doc = generate_endpoint_doc(method, path, operation)
            lines.append(endpoint_doc)

    return "\n".join(lines)


# ===========================================================================
# Route Introspection-based Documentation Generator
# ===========================================================================

def generate_introspection_docs(app_path: str, output_path: str) -> str:
    """Generate documentation by introspecting FastAPI routes."""
    # This would import the FastAPI app and extract route info
    # For now, we generate from the known route structure

    routes = [
        # (method, path, summary, description, tag)
        ("GET", "/health", "Health Check", "Health check endpoint", "System"),
        ("GET", "/ready", "Readiness Check", "Readiness check endpoint", "System"),
        ("GET", "/metrics", "Prometheus Metrics", "Prometheus metrics endpoint", "System"),

        ("GET", "/v1.0/agents", "List Agents", "List agents with filtering and pagination", "Agents"),
        ("POST", "/v1.0/agents", "Register Agent", "Register a new agent", "Agents"),
        ("GET", "/v1.0/agents/{agent_id}", "Get Agent", "Get an agent by ID", "Agents"),
        ("PUT", "/v1.0/agents/{agent_id}", "Update Agent", "Update an agent", "Agents"),
        ("POST", "/v1.0/agents/{agent_id}/trust-score", "Update Trust Score", "Update agent trust score", "Agents"),
        ("POST", "/v1.0/agents/{agent_id}/policy-bindings", "Bind Policies", "Bind policies to an agent", "Agents"),

        ("GET", "/v1.0/policies", "List Policies", "List policies with filtering and pagination", "Policies"),
        ("POST", "/v1.0/policies", "Create Policy", "Create a new policy", "Policies"),
        ("GET", "/v1.0/policies/{policy_id}", "Get Policy", "Get a policy by ID", "Policies"),
        ("PUT", "/v1.0/policies/{policy_id}", "Update Policy", "Update a policy (creates new version)", "Policies"),
        ("DELETE", "/v1.0/policies/{policy_id}", "Delete Policy", "Delete a policy", "Policies"),
        ("POST", "/v1.0/policies/{policy_id}/compile", "Compile Policy", "Compile Cedar policy to Rego", "Policies"),
        ("POST", "/v1.0/policies/{policy_id}/dry-run", "Dry-Run Policy", "Dry-run policy against test inputs", "Policies"),
        ("GET", "/v1.0/policies/{policy_id}/versions", "Get Policy Versions", "Get policy version history", "Policies"),
        ("GET", "/v1.0/policies/{policy_id}/dependencies", "Get Policy Dependencies", "Get policy dependency graph", "Policies"),

        ("GET", "/v1.0/evidence", "Search Evidence", "Search evidence with filtering and pagination", "Evidence"),
        ("POST", "/v1.0/evidence", "Submit Evidence", "Submit new evidence", "Evidence"),
        ("GET", "/v1.0/evidence/{evidence_id}", "Get Evidence", "Get evidence by ID", "Evidence"),
        ("POST", "/v1.0/evidence/{evidence_id}/verify", "Verify Evidence", "Verify evidence integrity", "Evidence"),
        ("POST", "/v1.0/evidence/export", "Export Evidence Package", "Export evidence package (async)", "Evidence"),
        ("GET", "/v1.0/evidence/export/{package_id}", "Get Export Package", "Get export package status", "Evidence"),

        ("POST", "/v1.0/enforcement/decide", "Request Decision", "Request a single enforcement decision", "Enforcement"),
        ("POST", "/v1.0/enforcement/decide-batch", "Batch Decide", "Request batch enforcement decisions", "Enforcement"),
        ("GET", "/v1.0/enforcement/decisions/{decision_id}", "Get Decision", "Get an enforcement decision by ID", "Enforcement"),
        ("GET", "/v1.0/enforcement/decisions", "List Decisions", "List enforcement decisions with filtering", "Enforcement"),

        ("GET", "/v1.0/assessments", "List Assessments", "List assessments with filtering and pagination", "Assessments"),
        ("POST", "/v1.0/assessments", "Create Assessment", "Create a new assessment", "Assessments"),
        ("GET", "/v1.0/assessments/{assessment_id}", "Get Assessment", "Get an assessment by ID", "Assessments"),
        ("PUT", "/v1.0/assessments/{assessment_id}", "Update Assessment", "Update an assessment", "Assessments"),
        ("POST", "/v1.0/assessments/{assessment_id}/findings", "Add Finding", "Add a finding to an assessment", "Assessments"),
        ("POST", "/v1.0/assessments/{assessment_id}/report", "Generate Report", "Generate an assessment report (async)", "Assessments"),

        ("GET", "/v1.0/compliance/frameworks", "List Frameworks", "List compliance frameworks", "Compliance"),
        ("GET", "/v1.0/compliance/frameworks/{framework_id}/controls", "List Controls", "List controls for a framework", "Compliance"),
        ("GET", "/v1.0/compliance/posture", "Get Compliance Posture", "Get compliance posture", "Compliance"),
        ("POST", "/v1.0/compliance/mappings", "Create Mapping", "Create a compliance mapping", "Compliance"),
        ("POST", "/v1.0/compliance/reports", "Generate Report", "Generate a compliance report (async)", "Compliance"),
        ("GET", "/v1.0/compliance/crosswalk", "Get Crosswalk", "Get cross-framework control mapping", "Compliance"),

        ("GET", "/v1.0/audit", "Query Audit Trail", "Query audit trail with filtering", "Audit"),
        ("POST", "/v1.0/audit/verify", "Verify Audit Chain", "Verify audit chain integrity", "Audit"),

        ("GET", "/v1.0/webhooks/subscriptions", "List Subscriptions", "List webhook subscriptions", "Webhooks"),
        ("POST", "/v1.0/webhooks/subscriptions", "Create Subscription", "Create a webhook subscription", "Webhooks"),
        ("GET", "/v1.0/webhooks/subscriptions/{subscription_id}", "Get Subscription", "Get a webhook subscription by ID", "Webhooks"),
        ("PUT", "/v1.0/webhooks/subscriptions/{subscription_id}", "Update Subscription", "Update a webhook subscription", "Webhooks"),
        ("DELETE", "/v1.0/webhooks/subscriptions/{subscription_id}", "Delete Subscription", "Delete a webhook subscription", "Webhooks"),
        ("POST", "/v1.0/webhooks/subscriptions/{subscription_id}/test", "Test Subscription", "Send a test event to the subscription", "Webhooks"),
        ("GET", "/v1.0/webhooks/subscriptions/{subscription_id}/deliveries", "Get Delivery History", "Get webhook delivery history", "Webhooks"),

        ("GET", "/v1.0/composed/dashboard", "Dashboard Overview", "Get aggregated dashboard overview", "Composed"),
        ("GET", "/v1.0/composed/agents/{agent_id}/360", "Agent 360", "Get 360-degree view of an agent", "Composed"),
        ("GET", "/v1.0/composed/compliance-report", "Compliance Report", "Get aggregated compliance report across frameworks", "Composed"),
        ("GET", "/v1.0/composed/executive-summary", "Executive Summary", "Get high-level executive summary", "Composed"),

        ("POST", "/v1.0/graphql", "GraphQL Query", "GraphQL query endpoint", "GraphQL"),
    ]

    lines = []
    lines.append("# GRC_Claw API Reference")
    lines.append("")
    lines.append(f"**Version:** 1.0.0")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    lines.append("Governance, Risk, and Compliance platform for agentic AI")
    lines.append("")

    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")

    current_tag = None
    for method, path, summary, description, tag in routes:
        if tag != current_tag:
            lines.append(f"- [{tag}](#{tag.lower()})")
            current_tag = tag

    lines.append("")

    # Group by tag
    tagged: Dict[str, List[Tuple[str, str, str, str]]] = {}
    for method, path, summary, description, tag in routes:
        if tag not in tagged:
            tagged[tag] = []
        tagged[tag].append((method, path, summary, description))

    for tag, endpoints in tagged.items():
        lines.append(f"## {tag}")
        lines.append("")

        for method, path, summary, description in endpoints:
            lines.append(f"### {summary}")
            lines.append("")
            lines.append(f"`{method} {path}`")
            lines.append("")
            lines.append(description)
            lines.append("")

            # Add parameter table for path parameters
            if "{" in path:
                lines.append("**Path Parameters:**")
                lines.append("")
                lines.append("| Name | Type | Description |")
                lines.append("|------|------|-------------|")

                import re
                params = re.findall(r"\{(\w+)\}", path)
                for param in params:
                    param_type = "string"
                    if param.endswith("_id"):
                        param_type = "string (ID)"
                    lines.append(f"| `{param}` | {param_type} | The {param.replace('_', ' ')} |")

                lines.append("")

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate GRC_Claw API documentation")
    parser.add_argument(
        "--openapi",
        type=str,
        help="Path to OpenAPI JSON spec file",
    )
    parser.add_argument(
        "--introspect",
        action="store_true",
        help="Generate docs from route introspection instead of OpenAPI spec",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/api_reference.md",
        help="Output markdown file path",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="GRC_Claw API Reference",
        help="Documentation title",
    )

    args = parser.parse_args()

    markdown = ""

    if args.openapi:
        if not os.path.exists(args.openapi):
            print(f"Error: OpenAPI spec not found at {args.openapi}", file=sys.stderr)
            sys.exit(1)

        spec = load_openapi_spec(args.openapi)
        markdown = generate_openapi_docs(spec, args.title)
        print(f"Generated documentation from OpenAPI spec: {args.openapi}")
    elif args.introspect:
        markdown = generate_introspection_docs("", args.output)
        print(f"Generated documentation from route introspection")
    else:
        # Default: try to find OpenAPI spec, fall back to introspection
        openapi_path = os.path.join(os.path.dirname(__file__), "..", "openapi.json")
        if os.path.exists(openapi_path):
            spec = load_openapi_spec(openapi_path)
            markdown = generate_openapi_docs(spec, args.title)
            print(f"Generated documentation from OpenAPI spec: {openapi_path}")
        else:
            markdown = generate_introspection_docs("", args.output)
            print("Generated documentation from route introspection (no OpenAPI spec found)")

    # Write output
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w") as f:
        f.write(markdown)

    print(f"Documentation written to: {args.output}")
    print(f"Total lines: {len(markdown.splitlines())}")


if __name__ == "__main__":
    main()

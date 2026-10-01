#!/usr/bin/env python3
"""
K8s Drift Detection Script for GRC_Claw
Compares desired state (manifests) against live cluster state.
Detects configuration drift, missing resources, and unauthorized changes.
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

DEPLOYMENT_ROOT = Path(__file__).resolve().parent.parent / "deployment" / "grc-claw-deployment"


@dataclass
class DriftResult:
    resource: str
    namespace: str
    name: str
    kind: str
    drift_type: str  # "missing", "extra", "modified", "orphaned"
    details: dict[str, Any] = field(default_factory=dict)
    severity: str = "warning"  # "info", "warning", "critical"


def run_kubectl(args: list[str], timeout: int = 30) -> tuple[bool, str, str]:
    """Run kubectl command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["kubectl"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except FileNotFoundError:
        return False, "", "kubectl not found"
    except subprocess.TimeoutExpired:
        return False, "", "kubectl timed out"


def get_live_resources(namespace: str = "default") -> dict[str, list[dict]]:
    """Fetch all live resources from the cluster."""
    resources = {}
    resource_types = [
        "deployments", "statefulsets", "daemonsets", "services",
        "configmaps", "secrets", "serviceaccounts", "ingresses",
        "networkpolicies", "poddisruptionbudgets", "hpa",
        "cronjobs", "jobs", "persistentvolumeclaims",
    ]

    for rtype in resource_types:
        success, stdout, _ = run_kubectl([
            "get", rtype, "-n", namespace, "-o", "json"
        ])
        if success:
            try:
                data = json.loads(stdout)
                resources[rtype] = data.get("items", [])
            except json.JSONDecodeError:
                resources[rtype] = []
        else:
            resources[rtype] = []

    return resources


def parse_manifests(root: Path) -> list[dict]:
    """Parse all manifests and return list of resource dicts."""
    resources = []
    for ext in ("*.yaml", "*.yml"):
        for manifest in sorted(root.rglob(ext)):
            try:
                with open(manifest) as f:
                    for doc in yaml.safe_load_all(f):
                        if doc and isinstance(doc, dict) and "kind" in doc:
                            doc["_source_file"] = str(manifest.relative_to(root))
                            resources.append(doc)
            except yaml.YAMLError:
                continue
    return resources


def resource_key(kind: str, namespace: str, name: str) -> str:
    """Generate unique key for a resource."""
    return f"{kind}/{namespace}/{name}"


def compare_resources(
    desired: list[dict],
    live: dict[str, list[dict]],
    namespace: str = "default"
) -> list[DriftResult]:
    """Compare desired vs live state and detect drift."""
    drifts = []

    # Build live resource index
    live_index: dict[str, dict] = {}
    for rtype, items in live.items():
        for item in items:
            kind = item.get("kind", "").lower()
            meta = item.get("metadata", {})
            ns = meta.get("namespace", "default")
            name = meta.get("name", "")
            key = resource_key(kind, ns, name)
            live_index[key] = item

    # Build desired resource index
    desired_index: dict[str, dict] = {}
    for item in desired:
        kind = item.get("kind", "").lower()
        meta = item.get("metadata", {})
        ns = meta.get("namespace", namespace)
        name = meta.get("name", "")
        key = resource_key(kind, ns, name)
        desired_index[key] = item

    # Check for missing resources (in desired but not in live)
    for key, desired_item in desired_index.items():
        if key not in live_index:
            kind = desired_item.get("kind", "Unknown")
            meta = desired_item.get("metadata", {})
            drifts.append(DriftResult(
                resource=key,
                namespace=meta.get("namespace", namespace),
                name=meta.get("name", "unknown"),
                kind=kind,
                drift_type="missing",
                details={"source_file": desired_item.get("_source_file", "unknown")},
                severity="critical"
            ))
        else:
            # Compare specs for modifications
            live_item = live_index[key]
            diffs = compare_specs(desired_item, live_item, kind)
            if diffs:
                meta = desired_item.get("metadata", {})
                drifts.append(DriftResult(
                    resource=key,
                    namespace=meta.get("namespace", namespace),
                    name=meta.get("name", "unknown"),
                    kind=desired_item.get("kind", "Unknown"),
                    drift_type="modified",
                    details={"differences": diffs},
                    severity="warning"
                ))

    # Check for extra/orphaned resources (in live but not in desired)
    for key, live_item in live_index.items():
        if key not in desired_index:
            kind = live_item.get("kind", "Unknown")
            meta = live_item.get("metadata", {})
            # Skip system resources
            if meta.get("namespace") in ("kube-system", "kube-public", "kube-node-lease"):
                continue
            drifts.append(DriftResult(
                resource=key,
                namespace=meta.get("namespace", "default"),
                name=meta.get("name", "unknown"),
                kind=kind,
                drift_type="orphaned",
                details={},
                severity="info"
            ))

    return drifts


def compare_specs(desired: dict, live: dict, kind: str) -> list[dict]:
    """Compare desired vs live spec, returning list of differences."""
    diffs = []

    # Map kind to the correct spec path
    spec_paths = {
        "deployment": ("spec",),
        "statefulset": ("spec",),
        "daemonset": ("spec",),
        "service": ("spec",),
        "configmap": ("data",),
        "secret": ("data",),
    }

    path = spec_paths.get(kind.lower(), ("spec",))
    desired_spec = desired
    live_spec = live
    for key in path:
        desired_spec = desired_spec.get(key, {}) if isinstance(desired_spec, dict) else {}
        live_spec = live_spec.get(key, {}) if isinstance(live_spec, dict) else {}

    # Compare replicas for scalable resources
    if kind.lower() in ("deployment", "statefulset"):
        desired_replicas = desired_spec.get("replicas")
        live_replicas = live_spec.get("replicas")
        if desired_replicas and live_replicas and desired_replicas != live_replicas:
            diffs.append({
                "field": "spec.replicas",
                "desired": desired_replicas,
                "live": live_replicas
            })

    # Compare containers/images
    if kind.lower() in ("deployment", "statefulset", "daemonset"):
        desired_containers = get_containers(desired_spec)
        live_containers = get_containers(live_spec)
        for dc in desired_containers:
            for lc in live_containers:
                if dc.get("name") == lc.get("name"):
                    if dc.get("image") != lc.get("image"):
                        diffs.append({
                            "field": f"spec.template.spec.containers[{dc['name']}].image",
                            "desired": dc.get("image"),
                            "live": lc.get("image")
                        })

    return diffs


def get_containers(spec: dict) -> list[dict]:
    """Extract containers from a workload spec."""
    template = spec.get("template", {})
    pod_spec = template.get("spec", {})
    return pod_spec.get("containers", [])


def generate_report(drifts: list[DriftResult], output_format: str = "text") -> str:
    """Generate drift detection report."""
    if output_format == "json":
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_drifts": len(drifts),
                "critical": sum(1 for d in drifts if d.severity == "critical"),
                "warning": sum(1 for d in drifts if d.severity == "warning"),
                "info": sum(1 for d in drifts if d.severity == "info"),
            },
            "drifts": [
                {
                    "resource": d.resource,
                    "namespace": d.namespace,
                    "name": d.name,
                    "kind": d.kind,
                    "drift_type": d.drift_type,
                    "severity": d.severity,
                    "details": d.details,
                }
                for d in drifts
            ]
        }
        return json.dumps(report, indent=2)

    lines = [
        "=" * 70,
        "GRC_Claw K8s Drift Detection Report",
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
        "=" * 70,
        f"Total drifts:  {len(drifts)}",
        f"  Critical:     {sum(1 for d in drifts if d.severity == 'critical')}",
        f"  Warning:      {sum(1 for d in drifts if d.severity == 'warning')}",
        f"  Info:         {sum(1 for d in drifts if d.severity == 'info')}",
        "-" * 70,
    ]

    for d in drifts:
        icon = {"critical": "!!!", "warning": " ! ", "info": " i "}[d.severity]
        lines.append(f"[{icon}] {d.drift_type.upper()}: {d.kind}/{d.namespace}/{d.name}")
        if d.details:
            for key, val in d.details.items():
                if key == "differences":
                    for diff in val:
                        lines.append(f"       {diff['field']}: desired={diff['desired']}, live={diff['live']}")
                else:
                    lines.append(f"       {key}: {val}")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Detect K8s configuration drift")
    parser.add_argument("--namespace", "-n", default="default", help="Namespace to check")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--manifest-path", type=str, default=None, help="Path to manifests")
    parser.add_argument("--exclude-ns", nargs="*", default=["kube-system", "kube-public"],
                        help="Namespaces to exclude")
    args = parser.parse_args()

    manifest_path = Path(args.manifest_path) if args.manifest_path else DEPLOYMENT_ROOT

    if not manifest_path.exists():
        print(f"ERROR: Manifest path not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    desired = parse_manifests(manifest_path)
    live = get_live_resources(args.namespace)
    drifts = compare_resources(desired, live, args.namespace)

    report = generate_report(drifts, args.format)
    print(report)

    # Exit with error code if critical drifts found
    if any(d.severity == "critical" for d in drifts):
        sys.exit(2)
    elif any(d.severity == "warning" for d in drifts):
        sys.exit(1)


if __name__ == "__main__":
    main()

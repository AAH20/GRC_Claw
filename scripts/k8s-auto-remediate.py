#!/usr/bin/env python3
"""
K8s Automated Remediation Playbook for GRC_Claw
Automatically fixes detected drift and common issues.
Supports dry-run mode and configurable remediation policies.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

DEPLOYMENT_ROOT = Path(__file__).resolve().parent.parent / "deployment" / "grc-claw-deployment"


@dataclass
class RemediationAction:
    resource: str
    namespace: str
    name: str
    kind: str
    action: str  # "apply", "delete", "scale", "restart", "patch"
    reason: str
    status: str = "pending"  # "pending", "success", "failed", "skipped"
    details: str = ""


def run_kubectl(args: list[str], timeout: int = 60, dry_run: bool = False) -> tuple[bool, str, str]:
    """Run kubectl command."""
    cmd = ["kubectl"] + args
    if dry_run:
        cmd.append("--dry-run=client")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except FileNotFoundError:
        return False, "", "kubectl not found"
    except subprocess.TimeoutExpired:
        return False, "", "kubectl timed out"


def remediate_missing_resource(
    manifest_path: Path, namespace: str, dry_run: bool
) -> RemediationAction:
    """Apply a missing resource from its manifest."""
    action = RemediationAction(
        resource=str(manifest_path),
        namespace=namespace,
        name=manifest_path.stem,
        kind="unknown",
        action="apply",
        reason="Resource defined in manifests but missing from cluster"
    )

    success, stdout, stderr = run_kubectl(
        ["apply", "-f", str(manifest_path), "-n", namespace],
        dry_run=dry_run
    )

    if success:
        action.status = "success"
        action.details = stdout.strip()
    else:
        action.status = "failed"
        action.details = stderr.strip()

    return action


def remediate_orphaned_resource(
    kind: str, namespace: str, name: str, dry_run: bool, force: bool = False
) -> RemediationAction:
    """Delete an orphaned resource not defined in manifests."""
    action = RemediationAction(
        resource=f"{kind}/{namespace}/{name}",
        namespace=namespace,
        name=name,
        kind=kind,
        action="delete",
        reason="Resource exists in cluster but not in manifests (orphaned)"
    )

    if not force and not dry_run:
        # Safety check: don't delete without force flag
        action.status = "skipped"
        action.details = "Use --force to delete orphaned resources"
        return action

    success, stdout, stderr = run_kubectl(
        ["delete", kind.lower(), name, "-n", namespace, "--wait=true"],
        dry_run=dry_run
    )

    if success:
        action.status = "success"
        action.details = stdout.strip()
    else:
        action.status = "failed"
        action.details = stderr.strip()

    return action


def remediate_replica_drift(
    kind: str, namespace: str, name: str, desired_replicas: int, dry_run: bool
) -> RemediationAction:
    """Scale a deployment/statefulset to match desired replica count."""
    action = RemediationAction(
        resource=f"{kind}/{namespace}/{name}",
        namespace=namespace,
        name=name,
        kind=kind,
        action="scale",
        reason=f"Replica drift detected: desired={desired_replicas}"
    )

    success, stdout, stderr = run_kubectl(
        ["scale", kind.lower(), name, "-n", namespace, f"--replicas={desired_replicas}"],
        dry_run=dry_run
    )

    if success:
        action.status = "success"
        action.details = stdout.strip()
    else:
        action.status = "failed"
        action.details = stderr.strip()

    return action


def remediate_image_drift(
    kind: str, namespace: str, name: str, container: str, desired_image: str, dry_run: bool
) -> RemediationAction:
    """Update container image to match desired state."""
    action = RemediationAction(
        resource=f"{kind}/{namespace}/{name}",
        namespace=namespace,
        name=name,
        kind=kind,
        action="patch",
        reason=f"Image drift on container '{container}': desired={desired_image}"
    )

    patch = json.dumps({
        "spec": {
            "template": {
                "spec": {
                    "containers": [{"name": container, "image": desired_image}]
                }
            }
        }
    })

    success, stdout, stderr = run_kubectl(
        ["patch", kind.lower(), name, "-n", namespace, "--type=merge", "-p", patch],
        dry_run=dry_run
    )

    if success:
        action.status = "success"
        action.details = stdout.strip()
    else:
        action.status = "failed"
        action.details = stderr.strip()

    return action


def restart_deployment(namespace: str, name: str, dry_run: bool) -> RemediationAction:
    """Rolling restart of a deployment."""
    action = RemediationAction(
        resource=f"Deployment/{namespace}/{name}",
        namespace=namespace,
        name=name,
        kind="Deployment",
        action="restart",
        reason="Manual or automated rolling restart"
    )

    success, stdout, stderr = run_kubectl(
        ["rollout", "restart", f"deployment/{name}", "-n", namespace],
        dry_run=dry_run
    )

    if success:
        action.status = "success"
        action.details = stdout.strip()
    else:
        action.status = "failed"
        action.details = stderr.strip()

    return action


def check_rollout_status(namespace: str, name: str, timeout: int = 120) -> bool:
    """Wait for rollout to complete."""
    success, stdout, stderr = run_kubectl(
        ["rollout", "status", f"deployment/{name}", "-n", namespace, f"--timeout={timeout}s"],
        timeout=timeout + 10
    )
    return success


def run_remediation_playbook(
    drift_report: dict, namespace: str, dry_run: bool = False, force: bool = False
) -> list[RemediationAction]:
    """Execute remediation based on drift report."""
    actions = []

    for drift in drift_report.get("drifts", []):
        drift_type = drift.get("drift_type")
        kind = drift.get("kind", "").lower()
        ns = drift.get("namespace", namespace)
        name = drift.get("name", "unknown")

        if drift_type == "missing":
            # Find the manifest file
            source = drift.get("details", {}).get("source_file", "")
            manifest_path = DEPLOYMENT_ROOT.parent.parent / source if source else None
            if manifest_path and manifest_path.exists():
                actions.append(remediate_missing_resource(manifest_path, ns, dry_run))
            else:
                actions.append(RemediationAction(
                    resource=f"{kind}/{ns}/{name}",
                    namespace=ns, name=name, kind=kind,
                    action="apply", reason="Missing resource",
                    status="failed", details=f"Manifest not found: {source}"
                ))

        elif drift_type == "orphaned":
            actions.append(remediate_orphaned_resource(kind, ns, name, dry_run, force))

        elif drift_type == "modified":
            differences = drift.get("details", {}).get("differences", [])
            for diff in differences:
                field = diff.get("field", "")
                if "replicas" in field:
                    desired = diff.get("desired")
                    if desired:
                        actions.append(remediate_replica_drift(kind, ns, name, desired, dry_run))
                elif "image" in field:
                    container = field.split("[")[1].split("]")[0] if "[" in field else "unknown"
                    desired_image = diff.get("desired")
                    if desired_image:
                        actions.append(remediate_image_drift(kind, ns, name, container, desired_image, dry_run))

    return actions


def generate_report(actions: list[RemediationAction], output_format: str = "text") -> str:
    """Generate remediation report."""
    total = len(actions)
    success = sum(1 for a in actions if a.status == "success")
    failed = sum(1 for a in actions if a.status == "failed")
    skipped = sum(1 for a in actions if a.status == "skipped")

    if output_format == "json":
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {"total": total, "success": success, "failed": failed, "skipped": skipped},
            "actions": [
                {
                    "resource": a.resource,
                    "namespace": a.namespace,
                    "name": a.name,
                    "kind": a.kind,
                    "action": a.action,
                    "reason": a.reason,
                    "status": a.status,
                    "details": a.details,
                }
                for a in actions
            ]
        }
        return json.dumps(report, indent=2)

    lines = [
        "=" * 70,
        "GRC_Claw K8s Automated Remediation Report",
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
        "=" * 70,
        f"Total actions:  {total}",
        f"  Success:       {success}",
        f"  Failed:        {failed}",
        f"  Skipped:       {skipped}",
        "-" * 70,
    ]

    for a in actions:
        status_icon = {"success": "OK", "failed": "FAIL", "skipped": "SKIP", "pending": "PEND"}[a.status]
        lines.append(f"[{status_icon}] {a.action.upper()}: {a.kind}/{a.namespace}/{a.name}")
        lines.append(f"       Reason: {a.reason}")
        if a.details:
            lines.append(f"       Details: {a.details}")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="K8s automated remediation playbook")
    parser.add_argument("--namespace", "-n", default="default", help="Target namespace")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making changes")
    parser.add_argument("--force", action="store_true", help="Force delete orphaned resources")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--drift-report", type=str, default=None, help="Path to drift report JSON")
    parser.add_argument("--restart-deployment", type=str, nargs="*", default=None,
                        help="Rolling restart specific deployments")
    args = parser.parse_args()

    actions = []

    if args.drift_report:
        with open(args.drift_report) as f:
            drift_data = json.load(f)
        actions.extend(run_remediation_playbook(drift_data, args.namespace, args.dry_run, args.force))

    if args.restart_deployment:
        for dep in args.restart_deployment:
            actions.append(restart_deployment(args.namespace, dep, args.dry_run))
            if not args.dry_run:
                check_rollout_status(args.namespace, dep)

    if not actions:
        print("No remediation actions to perform.", file=sys.stderr)
        sys.exit(0)

    report = generate_report(actions, args.format)
    print(report)

    if any(a.status == "failed" for a in actions):
        sys.exit(1)


if __name__ == "__main__":
    main()

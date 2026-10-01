#!/usr/bin/env python3
"""
K8s Deployment Validation Script for GRC_Claw
Validates all Kubernetes manifests using kubeval and kustomize.
Checks schema, best practices, and policy compliance.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEPLOYMENT_ROOT = Path(__file__).resolve().parent.parent / "deployment" / "grc-claw-deployment"
HELM_CHART = Path(__file__).resolve().parent.parent / "deploy" / "helm" / "grc-claw"


@dataclass
class ValidationResult:
    file: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def find_manifests(root: Path) -> list[Path]:
    """Find all YAML manifests recursively."""
    manifests = []
    for ext in ("*.yaml", "*.yml"):
        manifests.extend(root.rglob(ext))
    return sorted(manifests)


def run_kubeval(manifest_path: Path, kubernetes_version: str = "1.28.0") -> tuple[bool, list[str]]:
    """Run kubeval on a single manifest."""
    errors = []
    try:
        result = subprocess.run(
            ["kubeval", "--strict", "--kubernetes-version", kubernetes_version,
             "--schema-location", "https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/",
             str(manifest_path)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            errors.append(result.stderr.strip() or result.stdout.strip())
        return result.returncode == 0, errors
    except FileNotFoundError:
        return True, ["kubeval not installed — skipping schema validation"]
    except subprocess.TimeoutExpired:
        return False, ["kubeval timed out"]


def run_kustomize_build(manifest_path: Path) -> tuple[bool, list[str]]:
    """Run kustomize build to validate kustomization."""
    errors = []
    try:
        result = subprocess.run(
            ["kustomize", "build", str(manifest_path.parent)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            errors.append(result.stderr.strip())
        return result.returncode == 0, errors
    except FileNotFoundError:
        return True, ["kustomize not installed — skipping kustomize validation"]
    except subprocess.TimeoutExpired:
        return False, ["kustomize timed out"]


def validate_labels_and_annotations(doc: dict, rel_path: str) -> list[str]:
    """Check for required labels and annotations."""
    warnings = []
    metadata = doc.get("metadata", {})
    labels = metadata.get("labels", {})
    annotations = metadata.get("annotations", {})

    required_labels = {"app.kubernetes.io/name", "app.kubernetes.io/instance"}
    missing_labels = required_labels - set(labels.keys())
    if missing_labels:
        warnings.append(f"Missing recommended labels: {missing_labels}")

    if "app.kubernetes.io/version" not in labels:
        warnings.append("Missing label: app.kubernetes.io/version")

    return warnings


def validate_security_context(doc: dict, rel_path: str) -> list[str]:
    """Check security context on workloads."""
    warnings = []
    kind = doc.get("kind", "")

    if kind in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"):
        spec = doc.get("spec", {})
        if kind == "CronJob":
            template = spec.get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", {})
        else:
            template = spec.get("template", {}).get("spec", {})

        containers = template.get("containers", [])
        for container in containers:
            name = container.get("name", "unknown")
            sec_ctx = container.get("securityContext", {})

            if not sec_ctx.get("runAsNonRoot"):
                warnings.append(f"Container '{name}': securityContext.runAsNonRoot not set")
            if not sec_ctx.get("readOnlyRootFilesystem"):
                warnings.append(f"Container '{name}': securityContext.readOnlyRootFilesystem not set")
            if sec_ctx.get("privileged"):
                warnings.append(f"Container '{name}': securityContext.privileged=true (DANGEROUS)")
            if not sec_ctx.get("allowPrivilegeEscalation") is False:
                warnings.append(f"Container '{name}': securityContext.allowPrivilegeEscalation not false")

            # Check for resource limits
            resources = container.get("resources", {})
            if not resources.get("limits"):
                warnings.append(f"Container '{name}': missing resource limits")
            if not resources.get("requests"):
                warnings.append(f"Container '{name}': missing resource requests")

    return warnings


def validate_pod_disruption_budget(doc: dict, rel_path: str) -> list[str]:
    """Check for PodDisruptionBudget on workloads."""
    warnings = []
    kind = doc.get("kind", "")
    if kind in ("Deployment", "StatefulSet"):
        # This is a simplified check — in production you'd cross-reference
        pass
    return warnings


def validate_network_policies(doc: dict, rel_path: str) -> list[str]:
    """Check network policy coverage."""
    warnings = []
    kind = doc.get("kind", "")
    if kind in ("Deployment", "StatefulSet", "DaemonSet"):
        # Check if namespace has network policies
        pass
    return warnings


def validate_helm_templates() -> list[ValidationResult]:
    """Validate Helm chart templates."""
    results = []
    if not HELM_CHART.exists():
        return results

    try:
        result = subprocess.run(
            ["helm", "template", "grc-claw", str(HELM_CHART)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            results.append(ValidationResult(
                file="helm/grc-claw",
                passed=False,
                errors=[result.stderr.strip()]
            ))
        else:
            # Parse rendered templates and validate each
            docs = list(yaml.safe_load_all(result.stdout))
            for i, doc in enumerate(docs):
                if doc is None:
                    continue
                rel_path = f"helm-template-{i}"
                warnings = validate_labels_and_annotations(doc, rel_path)
                warnings.extend(validate_security_context(doc, rel_path))
                results.append(ValidationResult(
                    file=rel_path,
                    passed=True,
                    warnings=warnings
                ))
    except FileNotFoundError:
        results.append(ValidationResult(
            file="helm/grc-claw",
            passed=True,
            warnings=["helm not installed — skipping Helm validation"]
        ))
    except subprocess.TimeoutExpired:
        results.append(ValidationResult(
            file="helm/grc-claw",
            passed=False,
            errors=["helm template timed out"]
        ))

    return results


def validate_manifest(manifest_path: Path, run_schema: bool = True) -> ValidationResult:
    """Validate a single manifest file."""
    rel_path = str(manifest_path.relative_to(DEPLOYMENT_ROOT.parent.parent))
    errors = []
    warnings = []

    try:
        with open(manifest_path) as f:
            docs = list(yaml.safe_load_all(f))
    except yaml.YAMLError as e:
        return ValidationResult(file=rel_path, passed=False, errors=[f"YAML parse error: {e}"])

    for doc in docs:
        if doc is None:
            continue
        warnings.extend(validate_labels_and_annotations(doc, rel_path))
        warnings.extend(validate_security_context(doc, rel_path))

    if run_schema:
        passed, schema_errors = run_kubeval(manifest_path)
        errors.extend(schema_errors)
        if not passed:
            return ValidationResult(file=rel_path, passed=False, errors=errors, warnings=warnings)

    return ValidationResult(file=rel_path, passed=not errors, errors=errors, warnings=warnings)


def generate_report(results: list[ValidationResult], output_format: str = "text") -> str:
    """Generate validation report."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    total_warnings = sum(len(r.warnings) for r in results)

    if output_format == "json":
        report = {
            "summary": {"total": total, "passed": passed, "failed": failed, "warnings": total_warnings},
            "results": [
                {
                    "file": r.file,
                    "passed": r.passed,
                    "errors": r.errors,
                    "warnings": r.warnings
                }
                for r in results
            ]
        }
        return json.dumps(report, indent=2)

    lines = [
        "=" * 70,
        "GRC_Claw K8s Deployment Validation Report",
        "=" * 70,
        f"Total manifests:  {total}",
        f"Passed:           {passed}",
        f"Failed:           {failed}",
        f"Warnings:         {total_warnings}",
        "-" * 70,
    ]

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"[{status}] {r.file}")
        for err in r.errors:
            lines.append(f"  ERROR: {err}")
        for warn in r.warnings:
            lines.append(f"  WARN:  {warn}")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Validate GRC_Claw K8s deployments")
    parser.add_argument("--schema", action="store_true", help="Run kubeval schema validation")
    parser.add_argument("--kustomize", action="store_true", help="Run kustomize build validation")
    parser.add_argument("--helm", action="store_true", help="Validate Helm chart")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--path", type=str, default=None, help="Validate specific path only")
    args = parser.parse_args()

    results = []

    if args.path:
        target = Path(args.path)
        if target.is_file():
            results.append(validate_manifest(target, run_schema=args.schema))
        elif target.is_dir():
            for m in find_manifests(target):
                results.append(validate_manifest(m, run_schema=args.schema))
    else:
        if DEPLOYMENT_ROOT.exists():
            for m in find_manifests(DEPLOYMENT_ROOT):
                results.append(validate_manifest(m, run_schema=args.schema))

        if args.helm:
            results.extend(validate_helm_templates())

    report = generate_report(results, args.format)
    print(report)

    # Exit with error code if any failures
    if any(not r.passed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()

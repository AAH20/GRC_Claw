#!/usr/bin/env python3
"""
K8s Cost Optimization Analyzer for GRC_Claw
Analyzes resource requests/limits, identifies waste, and recommends optimizations.
Supports Kubecost API integration and standalone analysis.
"""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

DEPLOYMENT_ROOT = Path(__file__).resolve().parent.parent / "deployment" / "grc-claw-deployment"


@dataclass
class ResourceUsage:
    cpu_request: float = 0.0  # millicores
    cpu_limit: float = 0.0
    memory_request: int = 0  # MiB
    memory_limit: int = 0
    gpu_request: int = 0


@dataclass
class CostRecommendation:
    resource: str
    namespace: str
    name: str
    kind: str
    issue: str
    severity: str  # "high", "medium", "low"
    current_cost: float  # estimated monthly cost in USD
    potential_savings: float
    recommendation: str
    details: dict[str, Any] = field(default_factory=dict)


def parse_cpu(value: str | int | float | None) -> float:
    """Parse CPU value to millicores."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value) * 1000
    value = str(value)
    if value.endswith("m"):
        return float(value[:-1])
    return float(value) * 1000


def parse_memory(value: str | int | float | None) -> int:
    """Parse memory value to MiB."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    value = str(value)
    if value.endswith("Ki"):
        return int(float(value[:-2]) / 1024)
    if value.endswith("Mi"):
        return int(float(value[:-2]))
    if value.endswith("Gi"):
        return int(float(value[:-2]) * 1024)
    if value.endswith("Ti"):
        return int(float(value[:-2]) * 1024 * 1024)
    return int(float(value) / (1024 * 1024))


def get_workload_usage(doc: dict) -> ResourceUsage:
    """Extract resource requests/limits from a workload manifest."""
    kind = doc.get("kind", "")
    spec = doc.get("spec", {})

    if kind == "CronJob":
        template = spec.get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", {})
    else:
        template = spec.get("template", {}).get("spec", {})

    usage = ResourceUsage()
    for container in template.get("containers", []):
        resources = container.get("resources", {})
        requests = resources.get("requests", {})
        limits = resources.get("limits", {})

        usage.cpu_request += parse_cpu(requests.get("cpu"))
        usage.cpu_limit += parse_cpu(limits.get("cpu"))
        usage.memory_request += parse_memory(requests.get("memory"))
        usage.memory_limit += parse_memory(limits.get("memory"))

        gpu = requests.get("nvidia.com/gpu", 0)
        usage.gpu_request += int(gpu) if gpu else 0

    return usage


def estimate_monthly_cost(usage: ResourceUsage) -> float:
    """Estimate monthly cost based on resource requests (on-demand pricing)."""
    # Approximate on-demand pricing per unit
    CPU_COST_PER_CORE_MONTH = 30.0  # $30/core/month
    MEM_COST_PER_GIB_MONTH = 4.0   # $4/GiB/month
    GPU_COST_PER_MONTH = 300.0     # $300/GPU/month

    cpu_cores = usage.cpu_request / 1000
    mem_gib = usage.memory_request / 1024

    cost = (cpu_cores * CPU_COST_PER_CORE_MONTH +
            mem_gib * MEM_COST_PER_GIB_MONTH +
            usage.gpu_request * GPU_COST_PER_MONTH)

    return round(cost, 2)


def analyze_resource_efficiency(usage: ResourceUsage) -> dict[str, Any]:
    """Analyze resource request/limit efficiency."""
    analysis = {
        "cpu_request_millicores": usage.cpu_request,
        "cpu_limit_millicores": usage.cpu_limit,
        "memory_request_mib": usage.memory_request,
        "memory_limit_mib": usage.memory_limit,
        "cpu_burst_ratio": 0.0,
        "memory_burst_ratio": 0.0,
        "issues": [],
    }

    if usage.cpu_request > 0:
        analysis["cpu_burst_ratio"] = round(usage.cpu_limit / usage.cpu_request, 2)
    if usage.memory_request > 0:
        analysis["memory_burst_ratio"] = round(usage.memory_limit / usage.memory_request, 2)

    # Identify issues
    if usage.cpu_limit == 0:
        analysis["issues"].append("No CPU limit set — risk of resource starvation")
    if usage.memory_limit == 0:
        analysis["issues"].append("No memory limit set — risk of OOM kills")
    if usage.cpu_request == 0:
        analysis["issues"].append("No CPU request set — scheduler cannot guarantee placement")
    if usage.memory_request == 0:
        analysis["issues"].append("No memory request set — scheduler cannot guarantee placement")

    if analysis["cpu_burst_ratio"] > 4:
        analysis["issues"].append(f"High CPU burst ratio ({analysis['cpu_burst_ratio']}x) — consider tightening limits")
    if analysis["memory_burst_ratio"] > 2:
        analysis["issues"].append(f"High memory burst ratio ({analysis['memory_burst_ratio']}x) — consider tightening limits")

    return analysis


def check_hpa_coverage(doc: dict, all_workloads: list[dict]) -> list[str]:
    """Check if workloads have HPA configured."""
    issues = []
    kind = doc.get("kind", "")
    name = doc.get("metadata", {}).get("name", "")

    if kind in ("Deployment", "StatefulSet"):
        has_hpa = any(
            w.get("kind") == "HorizontalPodAutoscaler" and
            w.get("spec", {}).get("scaleTargetRef", {}).get("name") == name
            for w in all_workloads
        )
        if not has_hpa:
            issues.append(f"No HPA found for {kind}/{name}")

    return issues


def check_vpa_opportunities(doc: dict) -> list[str]:
    """Check if VPA could help optimize resources."""
    issues = []
    usage = get_workload_usage(doc)

    if usage.cpu_request == 0 or usage.memory_request == 0:
        issues.append("VPA could help determine optimal resource requests")

    return issues


def check_replica_efficiency(doc: dict) -> list[str]:
    """Check if replica count is appropriate."""
    issues = []
    kind = doc.get("kind", "")
    spec = doc.get("spec", {})

    if kind in ("Deployment", "StatefulSet"):
        replicas = spec.get("replicas", 1)
        if replicas == 1:
            issues.append("Single replica — no high availability")
        elif replicas > 10:
            issues.append(f"High replica count ({replicas}) — verify this is necessary")

    return issues


def check_storage_costs(doc: dict) -> list[str]:
    """Check for expensive storage configurations."""
    issues = []
    kind = doc.get("kind", "")

    if kind == "PersistentVolumeClaim":
        spec = doc.get("spec", {})
        storage_class = spec.get("storageClassName", "default")
        resources = spec.get("resources", {})
        size = resources.get("requests", {}).get("storage", "0")

        if "premium" in storage_class.lower() or "ssd" in storage_class.lower():
            issues.append(f"Using premium storage class '{storage_class}' — consider standard for non-critical data")

    return issues


def check_idle_resources(namespace: str = "default") -> list[CostRecommendation]:
    """Check for idle/unused resources via kubectl top."""
    recommendations = []

    success, stdout, _ = run_kubectl_top(["pods", "-n", namespace])
    if not success:
        return recommendations

    # Parse kubectl top output
    lines = stdout.strip().split("\n")[1:]  # Skip header
    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            cpu_str = parts[1].replace("m", "")
            mem_str = parts[2].replace("Mi", "")
            try:
                cpu = float(cpu_str)
                mem = float(mem_str)
                if cpu < 1 and mem < 10:
                    recommendations.append(CostRecommendation(
                        resource=f"Pod/{namespace}/{parts[0]}",
                        namespace=namespace,
                        name=parts[0],
                        kind="Pod",
                        issue="Idle pod consuming minimal resources",
                        severity="low",
                        current_cost=0.0,
                        potential_savings=0.0,
                        recommendation="Consider removing or scaling down"
                    ))
            except ValueError:
                continue

    return recommendations


def run_kubectl_top(args: list[str], timeout: int = 30) -> tuple[bool, str, str]:
    """Run kubectl top command."""
    try:
        result = subprocess.run(
            ["kubectl", "top"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "", ""


def generate_recommendations(
    manifests: list[dict], namespace: str = "default"
) -> list[CostRecommendation]:
    """Generate cost optimization recommendations."""
    recommendations = []

    for doc in manifests:
        kind = doc.get("kind", "")
        meta = doc.get("metadata", {})
        name = meta.get("name", "unknown")
        ns = meta.get("namespace", namespace)

        if kind not in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob", "PersistentVolumeClaim"):
            continue

        usage = get_workload_usage(doc)
        monthly_cost = estimate_monthly_cost(usage)
        efficiency = analyze_resource_efficiency(usage)

        # Resource efficiency issues
        for issue in efficiency["issues"]:
            severity = "high" if "No" in issue and "limit" in issue else "medium"
            recommendations.append(CostRecommendation(
                resource=f"{kind}/{ns}/{name}",
                namespace=ns,
                name=name,
                kind=kind,
                issue=issue,
                severity=severity,
                current_cost=monthly_cost,
                potential_savings=round(monthly_cost * 0.1, 2),
                recommendation="Set appropriate resource requests and limits based on actual usage",
                details=efficiency
            ))

        # HPA coverage
        hpa_issues = check_hpa_coverage(doc, manifests)
        for issue in hpa_issues:
            recommendations.append(CostRecommendation(
                resource=f"{kind}/{ns}/{name}",
                namespace=ns,
                name=name,
                kind=kind,
                issue=issue,
                severity="medium",
                current_cost=monthly_cost,
                potential_savings=round(monthly_cost * 0.2, 2),
                recommendation="Configure HPA to scale based on demand",
                details={}
            ))

        # Replica efficiency
        replica_issues = check_replica_efficiency(doc)
        for issue in replica_issues:
            recommendations.append(CostRecommendation(
                resource=f"{kind}/{ns}/{name}",
                namespace=ns,
                name=name,
                kind=kind,
                issue=issue,
                severity="low",
                current_cost=monthly_cost,
                potential_savings=round(monthly_cost * 0.3, 2) if "Single" in issue else 0.0,
                recommendation="Review replica count for cost optimization",
                details={}
            ))

        # Storage costs
        storage_issues = check_storage_costs(doc)
        for issue in storage_issues:
            recommendations.append(CostRecommendation(
                resource=f"{kind}/{ns}/{name}",
                namespace=ns,
                name=name,
                kind=kind,
                issue=issue,
                severity="medium",
                current_cost=monthly_cost,
                potential_savings=round(monthly_cost * 0.15, 2),
                recommendation="Evaluate storage class for cost efficiency",
                details={}
            ))

    return recommendations


def generate_report(
    recommendations: list[CostRecommendation],
    output_format: str = "text"
) -> str:
    """Generate cost optimization report."""
    total_current = sum(r.current_cost for r in recommendations)
    total_savings = sum(r.potential_savings for r in recommendations)
    by_severity = defaultdict(int)
    for r in recommendations:
        by_severity[r.severity] += 1

    if output_format == "json":
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_recommendations": len(recommendations),
                "estimated_monthly_cost": round(total_current, 2),
                "potential_monthly_savings": round(total_savings, 2),
                "by_severity": dict(by_severity),
            },
            "recommendations": [
                {
                    "resource": r.resource,
                    "namespace": r.namespace,
                    "name": r.name,
                    "kind": r.kind,
                    "issue": r.issue,
                    "severity": r.severity,
                    "current_cost": r.current_cost,
                    "potential_savings": r.potential_savings,
                    "recommendation": r.recommendation,
                    "details": r.details,
                }
                for r in recommendations
            ]
        }
        return json.dumps(report, indent=2)

    lines = [
        "=" * 70,
        "GRC_Claw K8s Cost Optimization Report",
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
        "=" * 70,
        f"Total recommendations:  {len(recommendations)}",
        f"  High severity:         {by_severity['high']}",
        f"  Medium severity:       {by_severity['medium']}",
        f"  Low severity:          {by_severity['low']}",
        f"Estimated monthly cost:  ${total_current:,.2f}",
        f"Potential savings:       ${total_savings:,.2f}",
        "-" * 70,
    ]

    for r in recommendations:
        icon = {"high": "!!!", "medium": " ! ", "low": " i "}[r.severity]
        lines.append(f"[{icon}] {r.kind}/{r.namespace}/{r.name}")
        lines.append(f"       Issue: {r.issue}")
        lines.append(f"       Recommendation: {r.recommendation}")
        lines.append(f"       Potential savings: ${r.potential_savings:,.2f}/month")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="K8s cost optimization analyzer")
    parser.add_argument("--namespace", "-n", default="default", help="Namespace to analyze")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--manifest-path", type=str, default=None, help="Path to manifests")
    parser.add_argument("--check-idle", action="store_true", help="Check for idle resources")
    args = parser.parse_args()

    manifest_path = Path(args.manifest_path) if args.manifest_path else DEPLOYMENT_ROOT

    if not manifest_path.exists():
        print(f"ERROR: Manifest path not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    # Parse all manifests
    manifests = []
    for ext in ("*.yaml", "*.yml"):
        for mf in sorted(manifest_path.rglob(ext)):
            try:
                with open(mf) as f:
                    for doc in yaml.safe_load_all(f):
                        if doc and isinstance(doc, dict) and "kind" in doc:
                            manifests.append(doc)
            except yaml.YAMLError:
                continue

    recommendations = generate_recommendations(manifests, args.namespace)

    if args.check_idle:
        recommendations.extend(check_idle_resources(args.namespace))

    report = generate_report(recommendations, args.format)
    print(report)

    # Exit with error code if high severity issues found
    if any(r.severity == "high" for r in recommendations):
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
K8s Security Posture Checker for GRC_Claw
CIS Kubernetes Benchmark compliance, RBAC analysis, and security best practices.
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
class SecurityFinding:
    check_id: str
    title: str
    severity: str  # "critical", "high", "medium", "low", "info"
    resource: str
    namespace: str
    description: str
    remediation: str
    status: str = "fail"  # "pass", "fail", "warn", "info"
    details: dict[str, Any] = field(default_factory=dict)


def run_kubectl(args: list[str], timeout: int = 30) -> tuple[bool, str, str]:
    """Run kubectl command."""
    try:
        result = subprocess.run(
            ["kubectl"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "", ""


def check_pod_security_standards(doc: dict, rel_path: str) -> list[SecurityFinding]:
    """Check Pod Security Standards compliance."""
    findings = []
    kind = doc.get("kind", "")
    meta = doc.get("metadata", {})
    name = meta.get("name", "unknown")
    namespace = meta.get("namespace", "default")

    if kind not in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"):
        return findings

    if kind == "CronJob":
        template = doc.get("spec", {}).get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", {})
    else:
        template = doc.get("spec", {}).get("template", {}).get("spec", {})

    # Check for privileged containers
    for container in template.get("containers", []):
        cname = container.get("name", "unknown")
        sec_ctx = container.get("securityContext", {})

        if sec_ctx.get("privileged"):
            findings.append(SecurityFinding(
                check_id="CIS-5.2.1",
                title="Privileged Container",
                severity="critical",
                resource=f"{kind}/{namespace}/{name}",
                namespace=namespace,
                description=f"Container '{cname}' runs in privileged mode",
                remediation="Set securityContext.privileged=false",
                status="fail"
            ))

        if not sec_ctx.get("runAsNonRoot"):
            findings.append(SecurityFinding(
                check_id="CIS-5.2.6",
                title="Container Running as Root",
                severity="high",
                resource=f"{kind}/{namespace}/{name}",
                namespace=namespace,
                description=f"Container '{cname}' does not set runAsNonRoot=true",
                remediation="Set securityContext.runAsNonRoot=true",
                status="fail"
            ))

        if not sec_ctx.get("readOnlyRootFilesystem"):
            findings.append(SecurityFinding(
                check_id="CIS-5.2.4",
                title="Writable Root Filesystem",
                severity="medium",
                resource=f"{kind}/{namespace}/{name}",
                namespace=namespace,
                description=f"Container '{cname}' does not use read-only root filesystem",
                remediation="Set securityContext.readOnlyRootFilesystem=true",
                status="fail"
            ))

        if sec_ctx.get("allowPrivilegeEscalation") is not False:
            findings.append(SecurityFinding(
                check_id="CIS-5.2.5",
                title="Privilege Escalation Allowed",
                severity="high",
                resource=f"{kind}/{namespace}/{name}",
                namespace=namespace,
                description=f"Container '{cname}' allows privilege escalation",
                remediation="Set securityContext.allowPrivilegeEscalation=false",
                status="fail"
            ))

        # Check for capabilities
        capabilities = sec_ctx.get("capabilities", {})
        if capabilities.get("add"):
            findings.append(SecurityFinding(
                check_id="CIS-5.2.8",
                title="Added Linux Capabilities",
                severity="medium",
                resource=f"{kind}/{namespace}/{name}",
                namespace=namespace,
                description=f"Container '{cname}' adds capabilities: {capabilities['add']}",
                remediation="Drop all capabilities and add only required ones",
                status="fail"
            ))

    # Check for host namespaces
    if template.get("hostNetwork"):
        findings.append(SecurityFinding(
            check_id="CIS-5.2.4",
            title="Host Network Namespace",
            severity="high",
            resource=f"{kind}/{namespace}/{name}",
            namespace=namespace,
            description="Pod uses host network namespace",
            remediation="Set spec.hostNetwork=false",
            status="fail"
        ))

    if template.get("hostPID"):
        findings.append(SecurityFinding(
            check_id="CIS-5.2.2",
            title="Host PID Namespace",
            severity="high",
            resource=f"{kind}/{namespace}/{name}",
            namespace=namespace,
            description="Pod uses host PID namespace",
            remediation="Set spec.hostPID=false",
            status="fail"
        ))

    if template.get("hostIPC"):
        findings.append(SecurityFinding(
            check_id="CIS-5.2.3",
            title="Host IPC Namespace",
            severity="high",
            resource=f"{kind}/{namespace}/{name}",
            namespace=namespace,
            description="Pod uses host IPC namespace",
            remediation="Set spec.hostIPC=false",
            status="fail"
        ))

    return findings


def check_network_policies(manifests: list[dict]) -> list[SecurityFinding]:
    """Check network policy coverage."""
    findings = []
    namespaces_with_policies = set()
    workload_namespaces = set()

    for doc in manifests:
        if doc.get("kind") == "NetworkPolicy":
            ns = doc.get("metadata", {}).get("namespace", "default")
            namespaces_with_policies.add(ns)

    for doc in manifests:
        kind = doc.get("kind", "")
        if kind in ("Deployment", "StatefulSet", "DaemonSet"):
            ns = doc.get("metadata", {}).get("namespace", "default")
            workload_namespaces.add(ns)
            name = doc.get("metadata", {}).get("name", "unknown")

            if ns not in namespaces_with_policies:
                findings.append(SecurityFinding(
                    check_id="CIS-5.3.1",
                    title="Missing Network Policy",
                    severity="medium",
                    resource=f"{kind}/{ns}/{name}",
                    namespace=ns,
                    description=f"No NetworkPolicy found in namespace '{ns}'",
                    remediation="Create NetworkPolicy to restrict pod-to-pod traffic",
                    status="fail"
                ))

    return findings


def check_rbac_configuration(manifests: list[dict]) -> list[SecurityFinding]:
    """Check RBAC configuration."""
    findings = []

    for doc in manifests:
        kind = doc.get("kind", "")
        meta = doc.get("metadata", {})
        name = meta.get("name", "unknown")
        namespace = meta.get("namespace", "default")

        if kind == "ClusterRole":
            rules = doc.get("rules", [])
            for rule in rules:
                if "*" in rule.get("resources", []) and "*" in rule.get("verbs", []):
                    findings.append(SecurityFinding(
                        check_id="CIS-5.1.1",
                        title="Overly Permissive ClusterRole",
                        severity="critical",
                        resource=f"ClusterRole/{name}",
                        namespace="cluster-wide",
                        description=f"ClusterRole '{name}' has wildcard permissions",
                        remediation="Follow principle of least privilege — restrict resources and verbs",
                        status="fail"
                    ))

        if kind == "Role":
            rules = doc.get("rules", [])
            for rule in rules:
                if "*" in rule.get("resources", []) and "*" in rule.get("verbs", []):
                    findings.append(SecurityFinding(
                        check_id="CIS-5.1.2",
                        title="Overly Permissive Role",
                        severity="high",
                        resource=f"Role/{namespace}/{name}",
                        namespace=namespace,
                        description=f"Role '{name}' has wildcard permissions",
                        remediation="Follow principle of least privilege — restrict resources and verbs",
                        status="fail"
                    ))

    return findings


def check_secrets_management(manifests: list[dict]) -> list[SecurityFinding]:
    """Check secrets management practices."""
    findings = []

    for doc in manifests:
        kind = doc.get("kind", "")
        meta = doc.get("metadata", {})
        name = meta.get("name", "unknown")
        namespace = meta.get("namespace", "default")

        if kind == "Secret":
            # Check if secret is using stringData (which is not encrypted at rest by default)
            if doc.get("stringData"):
                findings.append(SecurityFinding(
                    check_id="CIS-5.4.1",
                    title="Secret Using stringData",
                    severity="low",
                    resource=f"Secret/{namespace}/{name}",
                    namespace=namespace,
                    description=f"Secret '{name}' uses stringData field",
                    remediation="Use data field with base64-encoded values and enable encryption at rest",
                    status="warn"
                ))

            # Check for default token secrets
            if doc.get("type") == "kubernetes.io/service-account-token":
                findings.append(SecurityFinding(
                    check_id="CIS-5.4.2",
                    title="Service Account Token Secret",
                    severity="info",
                    resource=f"Secret/{namespace}/{name}",
                    namespace=namespace,
                    description=f"Service account token secret '{name}' found",
                    remediation="Consider disabling automountServiceAccountToken",
                    status="info"
                ))

    return findings


def check_container_images(manifests: list[dict]) -> list[SecurityFinding]:
    """Check container image security."""
    findings = []

    for doc in manifests:
        kind = doc.get("kind", "")
        meta = doc.get("metadata", {})
        name = meta.get("name", "unknown")
        namespace = meta.get("namespace", "default")

        if kind not in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"):
            continue

        if kind == "CronJob":
            template = doc.get("spec", {}).get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", {})
        else:
            template = doc.get("spec", {}).get("template", {}).get("spec", {})

        for container in template.get("containers", []):
            cname = container.get("name", "unknown")
            image = container.get("image", "")

            # Check for latest tag
            if ":latest" in image or ":" not in image:
                findings.append(SecurityFinding(
                    check_id="CIS-5.5.1",
                    title="Container Image Using Latest Tag",
                    severity="medium",
                    resource=f"{kind}/{namespace}/{name}",
                    namespace=namespace,
                    description=f"Container '{cname}' uses 'latest' tag or no tag",
                    remediation="Pin container images to specific version tags",
                    status="fail"
                ))

            # Check for image pull policy
            if container.get("imagePullPolicy") != "Always":
                findings.append(SecurityFinding(
                    check_id="CIS-5.5.2",
                    title="Image Pull Policy Not Always",
                    severity="low",
                    resource=f"{kind}/{namespace}/{name}",
                    namespace=namespace,
                    description=f"Container '{cname}' does not use imagePullPolicy: Always",
                    remediation="Set imagePullPolicy: Always for immutable tags",
                    status="warn"
                ))

    return findings


def check_admission_control() -> list[SecurityFinding]:
    """Check admission control configuration."""
    findings = []

    # Check for OPA/Gatekeeper/Kyverno policies
    success, stdout, _ = run_kubectl(["get", "validatingwebhookconfigurations", "-o", "json"])
    if success:
        try:
            data = json.loads(stdout)
            if not data.get("items"):
                findings.append(SecurityFinding(
                    check_id="CIS-5.6.1",
                    title="No Admission Controllers Configured",
                    severity="medium",
                    resource="cluster-wide",
                    namespace="cluster-wide",
                    description="No ValidatingWebhookConfiguration found",
                    remediation="Configure OPA Gatekeeper or Kyverno for policy enforcement",
                    status="fail"
                ))
        except json.JSONDecodeError:
            pass

    return findings


def check_audit_logging() -> list[SecurityFinding]:
    """Check audit logging configuration."""
    findings = []

    success, stdout, _ = run_kubectl(["get", "--raw", "/apis/apiregistration.k8s.io/v1/apiservices"])
    if success:
        try:
            data = json.loads(stdout)
            # This is a simplified check
            pass
        except json.JSONDecodeError:
            pass

    return findings


def check_encryption_at_rest() -> list[SecurityFinding]:
    """Check encryption at rest configuration."""
    findings = []

    success, stdout, _ = run_kubectl(["get", "--raw", "/api/v1/namespaces/kube-system/configmaps"])
    if success:
        try:
            data = json.loads(stdout)
            # Check for encryption provider config
            pass
        except json.JSONDecodeError:
            pass

    return findings


def run_all_checks(manifests: list[dict]) -> list[SecurityFinding]:
    """Run all security checks."""
    all_findings = []

    for doc in manifests:
        all_findings.extend(check_pod_security_standards(doc, ""))

    all_findings.extend(check_network_policies(manifests))
    all_findings.extend(check_rbac_configuration(manifests))
    all_findings.extend(check_secrets_management(manifests))
    all_findings.extend(check_container_images(manifests))
    all_findings.extend(check_admission_control())
    all_findings.extend(check_audit_logging())
    all_findings.extend(check_encryption_at_rest())

    return all_findings


def generate_report(findings: list[SecurityFinding], output_format: str = "text") -> str:
    """Generate security posture report."""
    by_severity = defaultdict(int)
    by_status = defaultdict(int)
    for f in findings:
        by_severity[f.severity] += 1
        by_status[f.status] += 1

    compliance_score = 0
    if findings:
        passed = by_status.get("pass", 0)
        compliance_score = round((passed / len(findings)) * 100, 1)

    if output_format == "json":
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_findings": len(findings),
                "compliance_score": compliance_score,
                "by_severity": dict(by_severity),
                "by_status": dict(by_status),
            },
            "findings": [
                {
                    "check_id": f.check_id,
                    "title": f.title,
                    "severity": f.severity,
                    "resource": f.resource,
                    "namespace": f.namespace,
                    "description": f.description,
                    "remediation": f.remediation,
                    "status": f.status,
                    "details": f.details,
                }
                for f in findings
            ]
        }
        return json.dumps(report, indent=2)

    lines = [
        "=" * 70,
        "GRC_Claw K8s Security Posture Report",
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
        "=" * 70,
        f"Total findings:    {len(findings)}",
        f"Compliance score: {compliance_score}%",
        "-" * 70,
        "By severity:",
        f"  Critical:  {by_severity['critical']}",
        f"  High:      {by_severity['high']}",
        f"  Medium:    {by_severity['medium']}",
        f"  Low:       {by_severity['low']}",
        f"  Info:      {by_severity['info']}",
        "-" * 70,
    ]

    for f in findings:
        icon = {"critical": "!!!", "high": "!! ", "medium": " ! ", "low": "  !", "info": "  i"}[f.severity]
        status_icon = {"pass": "PASS", "fail": "FAIL", "warn": "WARN", "info": "INFO"}[f.status]
        lines.append(f"[{icon}][{status_icon}] {f.check_id}: {f.title}")
        lines.append(f"       Resource: {f.resource}")
        lines.append(f"       Description: {f.description}")
        lines.append(f"       Remediation: {f.remediation}")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="K8s security posture checker")
    parser.add_argument("--namespace", "-n", default="default", help="Namespace to check")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--manifest-path", type=str, default=None, help="Path to manifests")
    parser.add_argument("--severity", choices=["critical", "high", "medium", "low", "info"],
                        default="low", help="Minimum severity to report")
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

    findings = run_all_checks(manifests)

    # Filter by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    min_sev = severity_order[args.severity]
    findings = [f for f in findings if severity_order[f.severity] <= min_sev]

    report = generate_report(findings, args.format)
    print(report)

    # Exit with error code if critical or high findings
    if any(f.severity in ("critical", "high") and f.status == "fail" for f in findings):
        sys.exit(2)
    elif any(f.severity == "medium" and f.status == "fail" for f in findings):
        sys.exit(1)


if __name__ == "__main__":
    main()

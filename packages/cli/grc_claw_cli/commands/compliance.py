"""Compliance commands for GRC_Claw CLI."""
import argparse
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from grc_claw_cli.utils.output import print_json, print_table, print_success, print_error, print_warning, print_info
from grc_claw_cli.utils.config import Config


# Compliance scan rules (mirrors the TS CLI)
SCAN_RULES = [
    {"id": "no-hardcoded-secrets", "name": "Hardcoded Secrets",
     "pattern": r"(?:password|secret|api_key|apikey|access_token|private_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
     "severity": "error", "message": "Hardcoded secret detected",
     "framework": "SOC 2 / ISO 27001", "control": "CC6.1 / A.9.4.3",
     "suggestion": "Use environment variables or a secrets manager"},
    {"id": "no-mfa-bypass", "name": "MFA Bypass",
     "pattern": r"skip_mfa|bypass_mfa|disable_2fa|mfa_enabled\s*=\s*false|two_factor\s*=\s*false",
     "severity": "error", "message": "Potential MFA bypass detected",
     "framework": "ISO 27001 / NIST CSF", "control": "A.9.4.2 / PR.AC-7",
     "suggestion": "MFA must be enforced for all privileged operations"},
    {"id": "no-weak-crypto", "name": "Weak Cryptography",
     "pattern": r"\b(?:md5|sha1|des|rc4|ecb)\b\s*\(",
     "severity": "error", "message": "Weak or deprecated cryptographic algorithm detected",
     "framework": "ISO 27001 / PCI DSS", "control": "A.10.1.1 / Req-3.4",
     "suggestion": "Use SHA-256 or stronger. For encryption: AES-256-GCM"},
    {"id": "no-sql-injection", "name": "SQL Injection Risk",
     "pattern": r"query\s*\(\s*['\"`][^'\"`]*\+",
     "severity": "error", "message": "Potential SQL injection via string concatenation",
     "framework": "SOC 2 / OWASP", "control": "CC6.6 / A1",
     "suggestion": "Use parameterized queries or an ORM"},
    {"id": "no-http-in-prod", "name": "Unencrypted Transport",
     "pattern": r"http:\/\/(?!localhost|127\.0\.0\.1|0\.0\.0\.0)",
     "severity": "warning", "message": "HTTP (non-TLS) URL detected",
     "framework": "ISO 27001 / NIST CSF", "control": "A.10.1.2 / PR.DS-2",
     "suggestion": "Replace http:// with https:// for all external URLs"},
    {"id": "no-eval", "name": "Dynamic Code Execution",
     "pattern": r"(?<!function\s)\beval\s*\(|\bnew\s+Function\s*\(",
     "severity": "error", "message": "eval() or new Function() creates code injection risk",
     "framework": "SOC 2 / ISO 27001", "control": "CC6.6 / A.12.6.1",
     "suggestion": "Eliminate eval(). Use JSON.parse() for data"},
    {"id": "no-cors-wildcard", "name": "Permissive CORS",
     "pattern": r"cors\s*\(\s*\{\s*origin\s*:\s*['\"]\*['\"]",
     "severity": "warning", "message": "CORS wildcard origin detected",
     "framework": "ISO 27001", "control": "A.13.1.3",
     "suggestion": "Specify allowed origins explicitly"},
    {"id": "pqc-recommendation", "name": "Post-Quantum Cryptography",
     "pattern": r"rsa|ecdsa|elliptic.*curve|diffie.hellman",
     "severity": "info", "message": "Classical asymmetric crypto — consider PQC migration",
     "framework": "ISO 27001 / NIST SP 800-208", "control": "A.10.1.1",
     "suggestion": "Plan migration to ML-KEM-1024 and ML-DSA-87"},
]

SCAN_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".java", ".rb", ".php", ".cs", ".rs", ".tf", ".yaml", ".yml", ".json", ".sh"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "__pycache__", ".venv", "vendor", "coverage"}

FRAMEWORK_SUMMARIES = {
    "iso27001": {"name": "ISO/IEC 27001:2022", "controls": 93, "description": "Information security management system"},
    "nist-csf": {"name": "NIST CSF 2.0", "controls": 106, "description": "Cybersecurity framework"},
    "soc2": {"name": "SOC 2 Type II", "controls": 64, "description": "Trust Service Criteria (AICPA)"},
    "iso42001": {"name": "ISO/IEC 42001:2023", "controls": 38, "description": "AI management system (AIMS)"},
    "eu-ai-act": {"name": "EU AI Act (2024/1689)", "controls": 44, "description": "EU regulation on artificial intelligence"},
    "dora": {"name": "DORA (EU 2022/2554)", "controls": 35, "description": "Digital operational resilience"},
    "hipaa": {"name": "HIPAA Security Rule", "controls": 42, "description": "US health information privacy and security"},
    "pci-dss": {"name": "PCI DSS v4.0", "controls": 64, "description": "Payment card industry data security standard"},
    "gdpr": {"name": "GDPR (2016/679)", "controls": 28, "description": "EU general data protection regulation"},
    "fedramp": {"name": "FedRAMP Moderate", "controls": 323, "description": "US federal cloud security authorization"},
    "cmmc": {"name": "CMMC Level 1-3", "controls": 171, "description": "Cybersecurity Maturity Model Certification"},
}


def walk_files(dir_path):
    """Recursively walk directory for scannable files."""
    results = []
    try:
        for entry in os.scandir(dir_path):
            if entry.name in SKIP_DIRS:
                continue
            if entry.is_dir():
                results.extend(walk_files(entry.path))
            elif Path(entry.name).suffix in SCAN_EXTENSIONS:
                results.append(entry.path)
    except (PermissionError, OSError):
        pass
    return results


def scan_file(file_path):
    """Scan a single file for compliance findings."""
    findings = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (IOError, OSError):
        return findings

    for rule in SCAN_RULES:
        for match in re.finditer(rule["pattern"], content, re.IGNORECASE):
            line_num = content[:match.start()].count("\n") + 1
            findings.append({
                "file": file_path,
                "line": line_num,
                "severity": rule["severity"],
                "rule": rule["id"],
                "message": rule["message"],
                "framework": rule["framework"],
                "control": rule["control"],
                "auto_fixable": rule.get("suggestion") is not None,
                "suggestion": rule.get("suggestion", ""),
            })
    return findings


def posture_score(findings):
    """Calculate posture score from findings."""
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    deduction = errors * 10 + warnings * 3
    return max(0, 100 - deduction)


def register(subparsers):
    """Register compliance subcommands."""
    parser = subparsers.add_parser("compliance", help="Compliance operations")
    comp_sub = parser.add_subparsers(dest="compliance_command", help="Compliance operations")

    # compliance scan
    scan_p = comp_sub.add_parser("scan", help="Scan codebase for compliance findings")
    scan_p.add_argument("path", nargs="?", default=".", help="Directory to scan")
    scan_p.add_argument("--framework", help="Filter by framework")
    scan_p.add_argument("--json", action="store_true", help="Output as JSON")

    # compliance frameworks
    fw_p = comp_sub.add_parser("frameworks", help="List available frameworks")
    fw_p.add_argument("--json", action="store_true", help="Output as JSON")

    # compliance report
    report_p = comp_sub.add_parser("report", help="Generate compliance report")
    report_p.add_argument("--framework", default="iso27001", help="Framework to report against")
    report_p.add_argument("--path", default=".", help="Directory to scan")
    report_p.add_argument("--output", help="Output file path")
    report_p.add_argument("--json", action="store_true", help="Output as JSON")

    # compliance audit
    audit_p = comp_sub.add_parser("audit", help="Run compliance audit")
    audit_p.add_argument("path", nargs="?", default=".", help="Directory to audit")
    audit_p.add_argument("--framework", default="iso27001", help="Framework to audit against")
    audit_p.add_argument("--output", help="Output file path")
    audit_p.add_argument("--json", action="store_true", help="Output as JSON")

    # compliance status
    status_p = comp_sub.add_parser("status", help="Show compliance status")
    status_p.add_argument("path", nargs="?", default=".", help="Directory to check")
    status_p.add_argument("--json", action="store_true", help="Output as JSON")

    # compliance drift
    drift_p = comp_sub.add_parser("drift", help="Detect compliance drift")
    drift_p.add_argument("path", nargs="?", default=".", help="Directory to check")
    drift_p.add_argument("--base", default="HEAD", help="Git ref to compare against")
    drift_p.add_argument("--output", help="Output file path")
    drift_p.add_argument("--json", action="store_true", help="Output as JSON")


def handle(args, config: Config):
    """Handle compliance commands."""
    cmd = args.compliance_command

    if cmd == "scan":
        target = Path(args.path).resolve()
        if not target.exists():
            print_error(f"Path not found: {target}")
            return 1
        files = walk_files(str(target))
        all_findings = []
        for f in files:
            all_findings.extend(scan_file(f))
        score = posture_score(all_findings)
        errors = [f for f in all_findings if f["severity"] == "error"]
        warnings = [f for f in all_findings if f["severity"] == "warning"]
        infos = [f for f in all_findings if f["severity"] == "info"]

        if args.json:
            print_json({"score": score, "findings": all_findings,
                        "summary": {"errors": len(errors), "warnings": len(warnings), "info": len(infos)}})
        else:
            print_info(f"Scanning: {target}")
            print_info(f"Files scanned: {len(files)}")
            print(f"\nPosture Score: {score}/100")
            print(f"Errors: {len(errors)}  Warnings: {len(warnings)}  Info: {len(infos)}")
            if errors:
                print(f"\n{len(errors)} error(s) found:")
                for f in errors[:20]:
                    print(f"  ✗ {f['file']}:{f['line']} — {f['message']}")
                    print(f"    {f['framework']} — {f['control']}")
        return 1 if errors else 0

    elif cmd == "frameworks":
        if args.json:
            print_json(FRAMEWORK_SUMMARIES)
        else:
            rows = [[k, v["name"], str(v["controls"]), v["description"]] for k, v in FRAMEWORK_SUMMARIES.items()]
            print_table(["ID", "Name", "Controls", "Description"], rows)
        return 0

    elif cmd == "report":
        target = Path(args.path).resolve()
        files = walk_files(str(target))
        all_findings = []
        for f in files:
            all_findings.extend(scan_file(f))
        score = posture_score(all_findings)
        meta = FRAMEWORK_SUMMARIES.get(args.framework, {"name": args.framework, "controls": 0})
        report = {
            "schema": "https://a2zsoc.com/schemas/compliance-report/v1.0",
            "report_id": f"grc-report-{int(datetime.now(timezone.utc).timestamp())}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "framework": args.framework,
            "framework_name": meta["name"],
            "path_scanned": str(target),
            "posture_score": score,
            "summary": {
                "files_scanned": len(files),
                "total_findings": len(all_findings),
                "errors": sum(1 for f in all_findings if f["severity"] == "error"),
                "warnings": sum(1 for f in all_findings if f["severity"] == "warning"),
                "info": sum(1 for f in all_findings if f["severity"] == "info"),
            },
            "findings": all_findings,
        }
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print_success(f"Report written to {args.output}")
        elif args.json:
            print_json(report)
        else:
            print_info(f"Compliance Report — {meta['name']}")
            print(f"  Score: {score}/100")
            print(f"  Files: {len(files)}")
            print(f"  Findings: {len(all_findings)}")
        return 0

    elif cmd == "audit":
        target = Path(args.path).resolve()
        files = walk_files(str(target))
        all_findings = []
        for f in files:
            all_findings.extend(scan_file(f))
        score = posture_score(all_findings)
        meta = FRAMEWORK_SUMMARIES.get(args.framework, {"name": args.framework, "controls": 0})
        audit = {
            "schema": "https://a2zsoc.com/schemas/compliance-audit/v1.0",
            "audit_id": f"grc-audit-{int(datetime.now(timezone.utc).timestamp())}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "framework": args.framework,
            "framework_name": meta["name"],
            "posture_score": score,
            "summary": {
                "files_scanned": len(files),
                "total_findings": len(all_findings),
                "errors": sum(1 for f in all_findings if f["severity"] == "error"),
                "warnings": sum(1 for f in all_findings if f["severity"] == "warning"),
                "info": sum(1 for f in all_findings if f["severity"] == "info"),
            },
            "findings": all_findings,
        }
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(audit, f, indent=2, default=str)
            print_success(f"Audit report written to {args.output}")
        elif args.json:
            print_json(audit)
        else:
            print_info(f"Compliance Audit — {meta['name']}")
            print(f"  Score: {score}/100")
            print(f"  Files: {len(files)}")
            print(f"  Findings: {len(all_findings)}")
        return 0

    elif cmd == "status":
        target = Path(args.path).resolve()
        files = walk_files(str(target))
        all_findings = []
        for f in files:
            all_findings.extend(scan_file(f))
        score = posture_score(all_findings)
        status = {
            "framework": config.get("framework", "iso27001"),
            "posture_score": score,
            "files_scanned": len(files),
            "errors": sum(1 for f in all_findings if f["severity"] == "error"),
            "warnings": sum(1 for f in all_findings if f["severity"] == "warning"),
            "info": sum(1 for f in all_findings if f["severity"] == "info"),
        }
        if args.json:
            print_json(status)
        else:
            print_info("Compliance Status")
            print(f"  Score: {score}/100")
            print(f"  Files: {len(files)}")
            print(f"  Errors: {status['errors']}  Warnings: {status['warnings']}  Info: {status['info']}")
        return 0

    elif cmd == "drift":
        target = Path(args.path).resolve()
        files = walk_files(str(target))
        all_findings = []
        for f in files:
            all_findings.extend(scan_file(f))
        score = posture_score(all_findings)
        drift = {
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "base_ref": args.base,
            "current_score": score,
            "findings_count": len(all_findings),
            "drift_detected": score < 60,
        }
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(drift, f, indent=2, default=str)
            print_success(f"Drift report written to {args.output}")
        elif args.json:
            print_json(drift)
        else:
            print_info(f"Compliance Drift — base: {args.base}")
            print(f"  Current score: {score}/100")
            print(f"  Drift detected: {'Yes' if drift['drift_detected'] else 'No'}")
        return 0

    else:
        print_error("No compliance subcommand specified. Use: grc compliance <scan|frameworks|report|audit|status|drift>")
        return 1

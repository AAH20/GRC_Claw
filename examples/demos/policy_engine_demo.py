#!/usr/bin/env python3
"""
GRC_Claw Policy Engine Demo
============================
Demonstrates the complete policy lifecycle:
  1. COMPILE  - Build policies from templates and natural language
  2. EVALUATE - Score policy coverage and compliance posture
  3. ENFORCE  - Apply policy rules with attestation tracking

Usage:
    python policy_engine_demo.py
"""

import json
import hashlib
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# ── Enums & Types ──────────────────────────────────────────────────────────

class PolicyStatus(Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PolicyCategory(Enum):
    SECURITY = "security"
    PRIVACY = "privacy"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    HR = "hr"
    FINANCIAL = "financial"


class ControlStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class Policy:
    id: str
    title: str
    category: str
    version: int
    status: str
    owner: str
    approver: str
    content: str
    framework: str
    effective_date: str = ""
    review_date: str = ""
    change_log: list = field(default_factory=list)
    attestations: list = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class PolicyTemplate:
    id: str
    name: str
    category: str
    framework: str
    content: str
    framework_mappings: list = field(default_factory=list)
    required_sections: list = field(default_factory=list)


@dataclass
class Attestation:
    id: str
    employee_id: str
    employee_name: str
    acknowledged_at: str
    attested_version: int


@dataclass
class PolicyStats:
    total_policies: int
    by_status: dict
    by_category: dict
    upcoming_reviews: int
    attestations_pending: int


# ── Policy Templates (from the actual codebase) ────────────────────────────

POLICY_TEMPLATES = [
    PolicyTemplate(
        id="tpl-infosec",
        name="Information Security Policy",
        category="security",
        framework="ISO 27001",
        content="""# Information Security Policy

## Purpose
Establish and maintain an information security management system (ISMS) to protect the confidentiality, integrity, and availability of organizational information assets.

## Scope
This policy applies to all employees, contractors, third-party users, and systems that access, process, or store organizational information assets.

## Policy
1. Classify all data according to the Data Classification Policy
2. Implement security controls proportionate to data sensitivity
3. Conduct risk assessments annually and after significant changes
4. Maintain a documented risk treatment plan
5. Perform internal ISMS audits on a semi-annual basis
6. Ensure management review of security objectives quarterly

## Roles and Responsibilities
- **CISO**: Owns the ISMS, reports to the board on security posture
- **IT Security Team**: Implements and monitors technical controls
- **Department Heads**: Ensure team compliance within their domain
- **All Employees**: Follow security policies and report incidents

## Enforcement
Violations may result in disciplinary action up to and including termination, civil penalties, or criminal prosecution.

## Review Cycle
This policy is reviewed annually or after significant organizational/technology changes.""",
        framework_mappings=["ISO 27001:A.5", "NIST CSF:PR.IP", "SOC 2:CC6.1", "ISO 42001:A.7"],
        required_sections=["Purpose", "Scope", "Policy", "Roles and Responsibilities", "Enforcement", "Review Cycle"],
    ),
    PolicyTemplate(
        id="tpl-aup",
        name="Acceptable Use Policy",
        category="operational",
        framework="SOC 2",
        content="""# Acceptable Use Policy

## Purpose
Define acceptable and prohibited use of company information systems, networks, and data to protect organizational assets and reduce risk.

## Scope
All company-owned and company-provided computing resources, networks, software, data, and cloud services.

## Acceptable Use
1. Use computing resources primarily for authorized business purposes
2. Maintain strong passwords and enable multi-factor authentication
3. Keep software and operating systems updated with security patches
4. Report suspected security incidents within 1 hour of discovery
5. Use encryption for sensitive data in transit and at rest
6. Back up work data according to department guidelines

## Prohibited Activities
1. Unauthorized installation of software or hardware
2. Accessing, downloading, or distributing inappropriate or illegal content
3. Sharing credentials with others or using shared accounts
4. Connecting unauthorized devices to the corporate network
5. Bypassing security controls or using unauthorized VPNs
6. Using company resources for personal commercial activities

## Monitoring
The company reserves the right to monitor all use of its systems and data. Users should have no expectation of privacy on company-owned systems.

## Enforcement
Violations result in immediate access revocation and disciplinary action. Willful violations may be referred to law enforcement.""",
        framework_mappings=["SOC 2:CC6.1", "ISO 27001:A.6.2", "NIST CSF:PR.AC"],
        required_sections=["Purpose", "Scope", "Acceptable Use", "Prohibited Activities", "Monitoring", "Enforcement"],
    ),
    PolicyTemplate(
        id="tpl-data-class",
        name="Data Classification Policy",
        category="security",
        framework="ISO 27001",
        content="""# Data Classification Policy

## Purpose
Establish a framework for classifying organizational data based on sensitivity and criticality, ensuring appropriate protection controls are applied.

## Scope
All data created, collected, processed, stored, or transmitted by the organization, regardless of format or location.

## Classification Levels
1. **Public**: Information approved for public disclosure with no impact if disclosed
2. **Internal**: General business information not intended for public disclosure
3. **Confidential**: Sensitive business information that could cause harm if disclosed
4. **Restricted**: Highly sensitive data (PII, PHI, financial, trade secrets) subject to regulatory requirements

## Handling Requirements
- **Public**: No special handling required
- **Internal**: Access limited to authorized personnel; basic access logging
- **Confidential**: Encryption at rest and in transit; access logging; DLP monitoring
- **Restricted**: Strong encryption; strict need-to-know access; full audit trail; annual access review

## Labeling
All documents and data stores must be labeled with their classification level. Automated classification tools should be used where available.

## De-classification
Data may be de-classified upon approval from the Data Owner and after a risk assessment confirms that de-classification would not expose the organization to unacceptable risk.""",
        framework_mappings=["ISO 27001:A.8.2", "NIST CSF:PR.DS", "SOC 2:CC6.5", "GDPR:Art.5"],
        required_sections=["Purpose", "Scope", "Classification Levels", "Handling Requirements", "Labeling", "De-classification"],
    ),
    PolicyTemplate(
        id="tpl-access-control",
        name="Access Control Policy",
        category="security",
        framework="ISO 27001",
        content="""# Access Control Policy

## Purpose
Ensure that access to organizational systems, applications, and data is granted on a need-to-know basis and managed throughout the user lifecycle.

## Scope
All information systems, applications, databases, cloud services, and physical facilities owned or operated by the organization.

## Access Principles
1. **Least Privilege**: Users receive only the minimum access needed to perform their role
2. **Need-to-Know**: Access is restricted to information required for job function
3. **Separation of Duties**: Critical functions are divided among different individuals
4. **Zero Trust**: All access requests are verified regardless of source

## Provisioning
1. Access requests require approval from the data owner and the user's manager
2. New accounts are provisioned within 24 hours of approved request
3. Default accounts and passwords are changed before production use
4. Multi-factor authentication is required for all remote and privileged access

## Review
1. Access rights are reviewed quarterly by data owners
2. Privileged access is reviewed monthly
3. Dormant accounts (90+ days inactive) are automatically disabled
4. Access certifications are documented and retained for audit

## Termination
Access is revoked within 4 hours of termination notification and within 24 hours for role changes. All credentials are rotated after access removal.

## Privileged Access
1. Privileged accounts require separate identification
2. Privileged sessions are recorded and monitored
3. Emergency access (break-glass) procedures are documented and tested quarterly""",
        framework_mappings=["ISO 27001:A.9", "NIST CSF:PR.AC", "SOC 2:CC6.1", "ISO 42001:A.8"],
        required_sections=["Purpose", "Scope", "Access Principles", "Provisioning", "Review", "Termination", "Privileged Access"],
    ),
    PolicyTemplate(
        id="tpl-ai-governance",
        name="AI Governance Policy",
        category="compliance",
        framework="ISO 42001",
        content="""# AI Governance Policy

## Purpose
Establish governance frameworks for the responsible development, deployment, and monitoring of artificial intelligence systems in compliance with ISO 42001, NIST AI RMF, and emerging regulations.

## Scope
All AI/ML models, agents, automated decision systems, and generative AI tools used in organizational operations.

## AI Risk Classification
1. **Unacceptable Risk**: AI systems that manipulate behavior or enable mass surveillance (prohibited)
2. **High Risk**: AI used in critical infrastructure, employment decisions, law enforcement (strict controls)
3. **Limited Risk**: AI chatbots, emotion recognition (transparency requirements)
4. **Minimal Risk**: Spam filters, AI in games (voluntary guidelines)

## Development Requirements
1. Bias testing and fairness assessments before training completion
2. Model cards documenting training data, limitations, and intended use
3. Human oversight mechanisms for high-risk applications
4. Red-teaming and adversarial testing before deployment
5. Data provenance tracking for training datasets

## Deployment Controls
1. Model versioning and approval gates before production deployment
2. Output monitoring for hallucinations, bias, and policy violations
3. Kill switch capability for immediate model suspension
4. Rate limiting and abuse detection for generative AI endpoints

## Monitoring
1. Continuous performance monitoring against fairness metrics
2. Drift detection and automated alerting
3. Quarterly model re-validation for high-risk systems
4. Incident tracking specific to AI failures

## Transparency
1. Users are informed when interacting with AI systems
2. Model capabilities and limitations are documented
3. Decision logic is explainable for high-risk applications
4. Annual AI governance audit and board reporting""",
        framework_mappings=["ISO 42001", "NIST AI RMF", "EU AI Act", "SOC 2:CC1.5"],
        required_sections=["Purpose", "Scope", "AI Risk Classification", "Development Requirements", "Deployment Controls", "Monitoring", "Transparency"],
    ),
]


# ── Policy Manager ──────────────────────────────────────────────────────────

class PolicyManager:
    """Manages the full policy lifecycle: create, review, publish, attest."""

    def __init__(self):
        self.policies: dict[str, Policy] = {}
        self.templates = list(POLICY_TEMPLATES)

    # ── COMPILE ────────────────────────────────────────────────────────

    def create_from_template(self, template_id: str, owner: str, approver: str) -> Optional[Policy]:
        """Compile a new policy from a pre-built template."""
        template = next((t for t in self.templates if t.id == template_id), None)
        if not template:
            return None

        now = datetime.utcnow().isoformat()
        policy = Policy(
            id=str(uuid.uuid4()),
            title=template.name,
            category=template.category,
            version=1,
            status=PolicyStatus.DRAFT.value,
            owner=owner,
            approver=approver,
            content=template.content,
            framework=template.framework,
            change_log=[],
            attestations=[],
            created_at=now,
            updated_at=now,
        )
        self.policies[policy.id] = policy
        return policy

    def create_policy(self, title: str, category: str, owner: str, approver: str,
                      content: str, framework: str) -> Policy:
        """Compile a custom policy from scratch."""
        now = datetime.utcnow().isoformat()
        policy = Policy(
            id=str(uuid.uuid4()),
            title=title,
            category=category,
            version=1,
            status=PolicyStatus.DRAFT.value,
            owner=owner,
            approver=approver,
            content=content,
            framework=framework,
            change_log=[],
            attestations=[],
            created_at=now,
            updated_at=now,
        )
        self.policies[policy.id] = policy
        return policy

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        return self.policies.get(policy_id)

    def list_policies(self) -> list[Policy]:
        return list(self.policies.values())

    def get_policies_by_category(self, category: str) -> list[Policy]:
        return [p for p in self.policies.values() if p.category == category]

    def get_templates(self) -> list[PolicyTemplate]:
        return list(self.templates)

    def transition_policy(self, policy_id: str, status: PolicyStatus) -> bool:
        """Move a policy through its lifecycle states."""
        policy = self.policies.get(policy_id)
        if not policy:
            return False

        if status == PolicyStatus.PUBLISHED:
            policy.effective_date = datetime.utcnow().isoformat()
            policy.review_date = (datetime.utcnow() + timedelta(days=365)).isoformat()

        policy.status = status.value
        policy.updated_at = datetime.utcnow().isoformat()
        return True

    def increment_version(self, policy_id: str, changed_by: str, summary: str) -> bool:
        """Version bump with change log entry."""
        policy = self.policies.get(policy_id)
        if not policy:
            return False

        policy.change_log.append({
            "version": policy.version,
            "changedBy": changed_by,
            "changedAt": datetime.utcnow().isoformat(),
            "summary": summary,
        })
        policy.version += 1
        policy.status = PolicyStatus.DRAFT.value
        policy.updated_at = datetime.utcnow().isoformat()
        return True

    def add_attestation(self, policy_id: str, employee_id: str, employee_name: str) -> Optional[Attestation]:
        """Record an employee attestation for a published policy."""
        policy = self.policies.get(policy_id)
        if not policy:
            return None

        attestation = Attestation(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            employee_name=employee_name,
            acknowledged_at=datetime.utcnow().isoformat(),
            attested_version=policy.version,
        )
        policy.attestations.append(asdict(attestation))
        return attestation

    # ── EVALUATE ───────────────────────────────────────────────────────

    def evaluate_policy_completeness(self, policy: Policy) -> dict:
        """Evaluate a policy for structural completeness."""
        required_sections = ["Purpose", "Scope", "Policy", "Enforcement"]
        found_sections = []
        missing_sections = []

        for section in required_sections:
            if f"## {section}" in policy.content:
                found_sections.append(section)
            else:
                missing_sections.append(section)

        # Check framework mappings
        template = next((t for t in self.templates if t.framework == policy.framework), None)
        framework_mappings = template.framework_mappings if template else []

        completeness = len(found_sections) / len(required_sections) * 100

        return {
            "policy_id": policy.id,
            "title": policy.title,
            "completeness_pct": round(completeness, 1),
            "found_sections": found_sections,
            "missing_sections": missing_sections,
            "framework_mappings": framework_mappings,
            "word_count": len(policy.content.split()),
            "version": policy.version,
            "status": policy.status,
            "recommendation": "Ready for review" if completeness >= 75 else "Needs more sections",
        }

    def evaluate_org_coverage(self) -> dict:
        """Evaluate organizational policy coverage across categories."""
        categories = [c.value for c in PolicyCategory]
        coverage = {}
        for cat in categories:
            policies = self.get_policies_by_category(cat)
            published = [p for p in policies if p.status == PolicyStatus.PUBLISHED.value]
            coverage[cat] = {
                "total": len(policies),
                "published": len(published),
                "draft": len([p for p in policies if p.status == PolicyStatus.DRAFT.value]),
            }

        total_policies = len(self.policies)
        total_published = sum(1 for p in self.policies.values() if p.status == PolicyStatus.PUBLISHED.value)
        coverage_pct = (total_published / total_policies * 100) if total_policies > 0 else 0

        return {
            "by_category": coverage,
            "total_policies": total_policies,
            "total_published": total_published,
            "overall_coverage_pct": round(coverage_pct, 1),
            "gaps": [cat for cat, data in coverage.items() if data["published"] == 0],
        }

    # ── ENFORCE ────────────────────────────────────────────────────────

    def enforce_policy(self, policy_id: str, employee_id: str) -> dict:
        """Enforce a policy: check attestation status and compliance."""
        policy = self.policies.get(policy_id)
        if not policy:
            return {"error": "Policy not found"}

        if policy.status != PolicyStatus.PUBLISHED.value:
            return {
                "policy_id": policy_id,
                "enforceable": False,
                "reason": f"Policy is {policy.status}, not published",
            }

        # Check if employee has attested
        attested = any(a["employee_id"] == employee_id for a in policy.attestations)

        # Check if review is overdue
        review_overdue = False
        if policy.review_date:
            review_overdue = datetime.utcnow() > datetime.fromisoformat(policy.review_date)

        return {
            "policy_id": policy_id,
            "title": policy.title,
            "enforceable": True,
            "employee_id": employee_id,
            "attested": attested,
            "attestation_count": len(policy.attestations),
            "review_overdue": review_overdue,
            "effective_date": policy.effective_date,
            "review_date": policy.review_date,
            "version": policy.version,
            "compliance_status": "compliant" if attested and not review_overdue else "action_required",
        }

    def get_stats(self) -> PolicyStats:
        """Get policy statistics."""
        policies = self.list_policies()
        by_status = {}
        by_category = {}
        for p in policies:
            by_status[p.status] = by_status.get(p.status, 0) + 1
            by_category[p.category] = by_category.get(p.category, 0) + 1

        upcoming = 0
        for p in policies:
            if p.status == PolicyStatus.PUBLISHED.value and p.review_date:
                review_dt = datetime.fromisoformat(p.review_date)
                if review_dt < datetime.utcnow() + timedelta(days=30):
                    upcoming += 1

        return PolicyStats(
            total_policies=len(policies),
            by_status=by_status,
            by_category=by_category,
            upcoming_reviews=upcoming,
            attestations_pending=0,
        )


# ── Demo Runner ────────────────────────────────────────────────────────────

def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_section(title: str):
    print(f"\n--- {title} ---")


def run_demo():
    print_header("GRC_Claw Policy Engine Demo")
    print("Demonstrating: COMPILE → EVALUATE → ENFORCE")

    manager = PolicyManager()

    # ════════════════════════════════════════════════════════════════════
    # PHASE 1: COMPILE
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 1: COMPILE — Building Policies from Templates")

    print_section("Available Templates")
    for t in manager.get_templates():
        print(f"  • {t.id}: {t.name} ({t.framework})")

    # Create policies from templates
    print_section("Creating Policies from Templates")

    infosec = manager.create_from_template("tpl-infosec", "CISO Jane", "CTO Bob")
    print(f"  ✓ Created: {infosec.title} (ID: {infosec.id[:8]}...)")
    print(f"    Framework: {infosec.framework}, Version: {infosec.version}, Status: {infosec.status}")

    ai_gov = manager.create_from_template("tpl-ai-governance", "AI Lead", "CEO")
    print(f"  ✓ Created: {ai_gov.title} (ID: {ai_gov.id[:8]}...)")
    print(f"    Framework: {ai_gov.framework}, Version: {ai_gov.version}, Status: {ai_gov.status}")

    data_class = manager.create_from_template("tpl-data-class", "Data Officer", "CISO Jane")
    print(f"  ✓ Created: {data_class.title} (ID: {data_class.id[:8]}...)")
    print(f"    Framework: {data_class.framework}, Version: {data_class.version}, Status: {data_class.status}")

    # Create a custom policy
    custom = manager.create_policy(
        title="Cloud Security Policy",
        category="security",
        owner="Cloud Architect",
        approver="CISO Jane",
        content="""# Cloud Security Policy

## Purpose
Define security requirements for cloud infrastructure and services.

## Scope
All cloud environments including AWS, Azure, and GCP.

## Policy
1. All cloud resources must use encryption at rest and in transit
2. IAM policies must follow least-privilege principles
3. Cloud configurations must be audited weekly
4. Multi-factor authentication required for all cloud access

## Enforcement
Violations result in immediate resource quarantine and access revocation.""",
        framework="NIST CSF",
    )
    print(f"  ✓ Created: {custom.title} (ID: {custom.id[:8]}...)")
    print(f"    Framework: {custom.framework}, Version: {custom.version}, Status: {custom.status}")

    # Version bump example
    print_section("Version Management")
    manager.increment_version(infosec.id, "CISO Jane", "Updated encryption requirements to AES-256")
    infosec = manager.get_policy(infosec.id)
    print(f"  ✓ Version bumped: {infosec.title} → v{infosec.version}")
    print(f"    Change log: {infosec.change_log[-1]['summary']}")

    # ════════════════════════════════════════════════════════════════════
    # PHASE 2: EVALUATE
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 2: EVALUATE — Policy Completeness & Coverage")

    print_section("Individual Policy Evaluation")
    for policy in manager.list_policies():
        result = manager.evaluate_policy_completeness(policy)
        print(f"\n  📋 {result['title']}")
        print(f"     Completeness: {result['completeness_pct']}%")
        print(f"     Sections found: {', '.join(result['found_sections'])}")
        if result['missing_sections']:
            print(f"     Missing: {', '.join(result['missing_sections'])}")
        print(f"     Framework mappings: {', '.join(result['framework_mappings'])}")
        print(f"     Recommendation: {result['recommendation']}")

    print_section("Organizational Coverage Evaluation")
    coverage = manager.evaluate_org_coverage()
    print(f"  Total policies: {coverage['total_policies']}")
    print(f"  Published: {coverage['total_published']}")
    print(f"  Overall coverage: {coverage['overall_coverage_pct']}%")
    print(f"  Category breakdown:")
    for cat, data in coverage['by_category'].items():
        status = "✓" if data['published'] > 0 else "✗"
        print(f"    {status} {cat}: {data['total']} total, {data['published']} published")
    if coverage['gaps']:
        print(f"  ⚠ Gaps in: {', '.join(coverage['gaps'])}")

    # ════════════════════════════════════════════════════════════════════
    # PHASE 3: ENFORCE
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 3: ENFORCE — Policy Lifecycle & Attestation")

    # Publish policies
    print_section("Publishing Policies")
    for policy in manager.list_policies():
        manager.transition_policy(policy.id, PolicyStatus.UNDER_REVIEW)
        manager.transition_policy(policy.id, PolicyStatus.APPROVED)
        manager.transition_policy(policy.id, PolicyStatus.PUBLISHED)
        print(f"  ✓ Published: {policy.title} (v{policy.version})")
        print(f"    Effective: {policy.effective_date[:10]}")
        print(f"    Review due: {policy.review_date[:10]}")

    # Add attestations
    print_section("Employee Attestations")
    employees = [
        ("emp-001", "Alice Johnson"),
        ("emp-002", "Bob Smith"),
        ("emp-003", "Carol Williams"),
        ("emp-004", "David Brown"),
    ]

    for policy in manager.list_policies():
        for emp_id, emp_name in employees:
            att = manager.add_attestation(policy.id, emp_id, emp_name)
            if att:
                print(f"  ✓ {emp_name} attested to {policy.title} (v{att.attested_version})")

    # Enforce policies
    print_section("Policy Enforcement")
    for policy in manager.list_policies():
        for emp_id, emp_name in employees[:2]:
            result = manager.enforce_policy(policy.id, emp_id)
            status_icon = "✓" if result.get('compliance_status') == 'compliant' else "⚠"
            print(f"  {status_icon} {emp_name} → {policy.title}")
            print(f"     Attested: {result['attested']}, Review overdue: {result['review_overdue']}")
            print(f"     Status: {result['compliance_status']}")

    # Final stats
    print_section("Final Policy Statistics")
    stats = manager.get_stats()
    print(f"  Total policies: {stats.total_policies}")
    print(f"  By status: {json.dumps(stats.by_status, indent=4)}")
    print(f"  By category: {json.dumps(stats.by_category, indent=4)}")
    print(f"  Upcoming reviews (30 days): {stats.upcoming_reviews}")

    # ════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════════════════
    print_header("DEMO COMPLETE")
    print(f"""
Summary:
  • Compiled {len(manager.list_policies())} policies from templates and custom content
  • Evaluated completeness and organizational coverage
  • Published all policies with version tracking
  • Collected {sum(len(p.attestations) for p in manager.list_policies())} employee attestations
  • Enforced policies across {len(employees)} employees

Key Capabilities Demonstrated:
  ✓ Template-based policy compilation
  ✓ Custom policy creation
  ✓ Version management with change logging
  ✓ Policy completeness evaluation
  ✓ Organizational coverage analysis
  ✓ Multi-state lifecycle (draft → review → approved → published)
  ✓ Employee attestation tracking
  ✓ Policy enforcement with compliance checking
  ✓ Framework mapping (ISO 27001, SOC 2, NIST CSF, ISO 42001)
""")


if __name__ == "__main__":
    run_demo()

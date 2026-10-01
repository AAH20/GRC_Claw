# Unified AI Governance Policy — Implementation Guide

**Companion to:** `unified-ai-governance-policy-template.md`  
**Architecture Reference:** `grc-claw-reference-architecture.md`  
**Version:** 1.0  
**Date:** 2026-10-01  
**Classification:** Internal  

---

## How to Use This Guide

This document provides detailed implementation guidance for each of the 10 sections in the Unified AI Governance Policy Template. It bridges the gap between policy requirements and technical implementation, with specific reference to the GRC_Claw reference architecture.

**Audience:**
- AI Governance Lead and Committee members
- Policy authors and reviewers
- Technical implementers (platform engineers, security engineers)
- Internal audit and compliance teams
- Agent owners and operators

**Structure:** Each subsection maps to a policy section and provides:
- Implementation steps
- Technical patterns (referencing GRC_Claw architecture)
- Roles and responsibilities
- Verification criteria

---

## 1. Policy Authoring Guide

### 1.1 Overview

Effective AI governance policies must be **specific, enforceable, measurable, and auditable**. Vague policies create compliance gaps and enforcement ambiguity. This guide establishes standards for authoring policies that satisfy the requirements of NIST AI RMF, ISO/IEC 42001, and the EU AI Act.

### 1.2 Policy Authoring Principles

| Principle | Description | Example |
|-----------|-------------|---------|
| **Specific** | Each policy statement identifies a clear actor, action, and constraint | ❌ "Use AI responsibly" → ✅ "Agents may only access data classifications at or below their assigned clearance level" |
| **Enforceable** | Policies must be technically enforceable through automated controls | Policies referencing GRC_Claw PDP/PEP enforcement points |
| **Measurable** | Compliance can be objectively assessed through evidence | "All Tier 3+ agents must have 100% of tool calls logged with decision certificates" |
| **Auditable** | Policy decisions and their rationale are documented and traceable | Version-controlled Cedar/Rego policies with change history |
| **Proportional** | Controls scale with risk tier | Tier 1: basic logging; Tier 4: continuous monitoring + kill-switch + board approval |

### 1.3 Policy Statement Structure

Every policy statement in the template follows this structure:

```
[ACTORY] must [ACTION] when [CONDITION] unless [EXCEPTION] enforced by [CONTROL]
```

**Example:**
> **Agent operators** must **activate the kill-switch** when **an agent exhibits goal drift** unless **the agent is in a controlled test environment** enforced by **GRC_Claw behavioral analytics + PEP quarantine action**.

### 1.4 Policy Authoring Workflow

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Identify   │───▶│   Draft      │───▶│   Technical  │───▶│   Legal &    │
│   Requirement│    │   Policy     │    │   Review     │    │   Compliance │
│              │    │   Statement  │    │              │    │   Review     │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                │
                                                                ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Publish    │◀───│   Approve    │◀───│   Pilot      │◀───│   Finalize   │
│   & Deploy   │    │   & Sign-off │    │   & Validate │    │   & Version  │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### 1.5 Policy Authoring by Section

#### Section 1: Purpose, Scope, and Definitions

**Authoring Steps:**
1. Define organizational boundaries — identify all business units, subsidiaries, and geographic jurisdictions
2. Enumerate all AI system categories in use or planned (GenAI, agentic AI, embedded AI, procured AI)
3. Map each AI system category to applicable regulatory frameworks
4. Define terms precisely — use ISO/IEC 22989 and EU AI Act Article 3 definitions as baseline
5. Establish scope exclusions with explicit justification and approval

**Technical Implementation:**
- Maintain scope inventory in GRC_Claw Agent Registry
- Tag each registered agent with applicable framework obligations
- Use GRC_Claw Compliance Mapping Layer to auto-generate framework applicability matrix

**Verification:**
- [ ] All AI systems in the organization are either explicitly in scope or excluded with documented justification
- [ ] Definitions align with ISO/IEC 22989 and EU AI Act Article 3
- [ ] Scope boundaries are approved by AI Governance Committee

#### Section 2: Governance Structure and Accountability

**Authoring Steps:**
1. Define committee composition with named roles (not just titles)
2. Establish decision-making authority and quorum requirements
3. Define escalation paths and SLAs
4. Document Three Lines of Defense responsibilities with specific AI governance activities
5. For agentic AI, define Accountable Owner and Technical Owner roles with specific duties

**Technical Implementation:**
- Configure GRC_Claw Agent Identity Layer with role-based access
- Map committee roles to GRC_Claw identity attributes
- Establish policy binding hierarchy: Organization → Business Unit → Agent

**Verification:**
- [ ] Committee charter documented with meeting cadence and decision logs
- [ ] Every deployed agent has named Accountable Owner and Technical Owner in Agent Registry
- [ ] Delegation Authority Lineage documented for each agentic AI system
- [ ] Three Lines of Defense model documented with specific AI activities per line

#### Section 3: AI System Classification and Risk Tiering

**Authoring Steps:**
1. Define risk tier criteria with quantitative thresholds where possible
2. Map autonomy levels (L1-L5) to oversight requirements
3. Establish EU AI Act classification procedures
4. Create classification decision trees for common use cases
5. Define reclassification triggers and procedures

**Technical Implementation:**
- Implement risk tier as a field in GRC_Claw Agent Registry (`risk_tier: enum [prohibited, high, limited, minimal]`)
- Configure autonomy level as agent attribute
- Use GRC_Claw Policy Definition Layer to encode classification rules as Cedar policies
- Implement automated classification assistance based on data types, use case, and potential impact

**Verification:**
- [ ] All AI systems classified and recorded in registry
- [ ] Classification criteria documented and consistently applied
- [ ] EU AI Act classification completed for all systems
- [ ] Reclassification triggers defined and monitored

#### Section 4: Data Governance and AI

**Authoring Steps:**
1. Define data classification scheme aligned with organizational data governance
2. Map data classifications to approved AI tool categories
3. Establish data minimization requirements per AI use case
4. Define training data governance procedures
5. Establish DPIA triggers and procedures

**Technical Implementation:**
- Integrate GRC_Claw PDP with data classification tags
- Implement data classification-based access control in Cedar policies:
  ```cedar
  permit(
    principal in Agent::"data-analyst",
    action == Action::"read",
    resource in DataClass::"public"
  ) when {
    resource.classification <= principal.clearance
  };
  ```
- Configure DLP integration for AI tool monitoring
- Implement data retention policies in GRC_Claw Evidence Store

**Verification:**
- [ ] Data classification scheme documented and aligned with organizational standard
- [ ] AI tool approvals mapped to data classifications
- [ ] DPIA completed for all qualifying AI systems
- [ ] Training data governance procedures documented and enforced

#### Section 5: Human Oversight and Transparency

**Authoring Steps:**
1. Define human oversight requirements per risk tier
2. Establish AI-generated content labeling requirements
3. Define automated decision-making safeguards
4. Establish model card requirements
5. Create transparency disclosure templates

**Technical Implementation:**
- Configure GRC_Claw PEP to enforce human-in-the-loop (HITL) and human-on-the-loop (HOTL) requirements
- Implement approval workflows for Tier 3+ decisions:
  ```python
  # PEP enforcement pattern for HITL
  if decision.verdict == "REQUIRE_APPROVAL":
      ticket = await create_approval_ticket(decision)
      return {"status": "pending_approval", "ticket_id": ticket.id}
  ```
- Implement AI content labeling through output transformation in PEP
- Maintain model cards as versioned documents in GRC_Claw Evidence Store

**Verification:**
- [ ] Human oversight requirements defined for each risk tier
- [ ] AI content labeling implemented and tested
- [ ] Automated decision-making safeguards documented
- [ ] Model cards maintained for all Tier 3+ systems

#### Section 6: Agentic AI Governance

**Authoring Steps:**
1. Define agent registry schema and required fields
2. Establish tool permission scoping methodology
3. Define budget and action constraint categories
4. Establish runtime monitoring requirements
5. Define agent-specific incident types and response procedures
6. Create agent lifecycle management procedures

**Technical Implementation:**
- Deploy GRC_Claw Agent Registry with full schema (see Reference Architecture §3.5)
- Implement deny-by-default tool permissions:
  ```cedar
  // Default deny all tool access
  forbid(principal, action, resource) when {
    not explicitly_permitted(principal, action, resource)
  };
  ```
- Configure budget enforcement in PEP:
  ```python
  # Budget enforcement in PEP
  if agent.daily_spend + transaction_amount > agent.budget_cap_daily:
      return Decision(verdict="DENY", reason="budget_cap_exceeded")
  ```
- Implement behavioral analytics for goal drift detection
- Deploy kill-switch mechanism with quarterly testing

**Verification:**
- [ ] All agentic AI systems registered with complete metadata
- [ ] Tool permissions scoped to minimum necessary
- [ ] Budget caps configured and enforced
- [ ] Runtime monitoring active with behavioral analytics
- [ ] Kill-switch tested within last quarter
- [ ] Agent lifecycle procedures documented and followed

#### Section 7: Third-Party and Vendor AI Governance

**Authoring Steps:**
1. Define vendor due diligence criteria and scoring methodology
2. Establish contract requirement templates
3. Define embedded AI feature assessment procedures
4. Establish ongoing vendor monitoring requirements
5. Create vendor risk rating methodology

**Technical Implementation:**
- Maintain vendor inventory in GRC_Claw with risk ratings
- Integrate vendor contract management with policy compliance tracking
- Implement automated vendor monitoring through GRC_Claw Evidence Collection Layer
- Use GRC_Claw Compliance Mapping Layer to map vendor controls to organizational frameworks

**Verification:**
- [ ] All AI vendors assessed and risk-rated
- [ ] Contracts include AI-specific provisions
- [ ] Embedded AI features assessed
- [ ] Ongoing vendor monitoring active

#### Section 8: Risk Assessment and Impact Assessment

**Authoring Steps:**
1. Define risk assessment methodology (qualitative, quantitative, or hybrid)
2. Establish risk appetite and tolerance thresholds
3. Define AI System Impact Assessment (AISIA) procedures
4. Establish FRIA procedures for high-risk AI systems
5. Create assessment templates and tools

**Technical Implementation:**
- Use GRC_Claw Analytics Engine for risk scoring
- Implement assessment workflows with evidence collection
- Store assessment results as OSCAL evidence in GRC_Claw Evidence Store
- Use GRC_Claw Crosswalk Engine to map assessment findings to framework controls

**Verification:**
- [ ] Risk assessment methodology documented
- [ ] Risk appetite and tolerance thresholds defined
- [ ] AISIA completed for all new AI systems
- [ ] FRIA completed for all high-risk AI systems
- [ ] Assessment results stored and traceable

#### Section 9: Monitoring, Enforcement, and Incident Management

**Authoring Steps:**
1. Define monitoring scope and metrics
2. Establish enforcement consequence framework
3. Define AI incident classification and response procedures
4. Establish record-keeping and logging requirements
5. Create incident response playbooks

**Technical Implementation:**
- Deploy GRC_Claw Observability Layer (OpenTelemetry + OpenInference)
- Configure real-time monitoring dashboards in Grafana
- Implement automated incident detection through GRC_Claw Analytics Engine
- Configure PEP for automated enforcement actions:
  - ALLOW → Execute
  - ALLOW_WITH_REDACTION → Execute with redaction
  - REQUIRE_APPROVAL → Queue for human review
  - DENY → Block
  - QUARANTINE → Isolate agent

**Verification:**
- [ ] Monitoring dashboards operational
- [ ] Enforcement actions configured and tested
- [ ] Incident response playbooks documented and drilled
- [ ] Record-keeping requirements met
- [ ] Log retention policies enforced

#### Section 10: Training, Awareness, and Continuous Improvement

**Authoring Steps:**
1. Define training curriculum by role
2. Establish training completion tracking
3. Define continuous improvement procedures
4. Establish policy review schedule and triggers
5. Create awareness materials and communication plans

**Technical Implementation:**
- Integrate training records with GRC_Claw identity attributes
- Use GRC_Claw Analytics Engine to track training completion rates
- Implement policy version control with automated review reminders
- Configure GRC_Claw to generate compliance posture reports for committee review

**Verification:**
- [ ] Training curriculum defined for all roles
- [ ] Training completion tracked and reported
- [ ] Policy review schedule established
- [ ] Continuous improvement process documented

---

## 2. Policy Review Checklist

### 2.1 Pre-Review Preparation

Before conducting a policy review, gather:

- [ ] Current policy version with change history
- [ ] GRC_Claw compliance posture report for the review period
- [ ] Incident reports and lessons learned
- [ ] Audit findings and corrective actions
- [ ] Stakeholder feedback and change requests
- [ ] Regulatory update summary
- [ ] AI inventory changes (new systems, decommissioned systems)
- [ ] Vendor risk assessment updates

### 2.2 Policy Content Review Checklist

#### Structural Completeness

| # | Checkpoint | Status | Notes |
|---|-----------|--------|-------|
| 1 | All 10 policy sections present and complete | ☐ | |
| 2 | Framework mapping legend current and accurate | ☐ | |
| 3 | Cross-reference matrix (Annex E) up to date | ☐ | |
| 4 | Document control information current | ☐ | |
| 5 | Version number and date incremented | ☐ | |
| 6 | Superseded versions documented | ☐ | |

#### Content Quality

| # | Checkpoint | Status | Notes |
|---|-----------|--------|-------|
| 7 | Policy statements follow actor-action-condition structure | ☐ | |
| 8 | All [ORGANIZATION] placeholders replaced | ☐ | |
| 9 | Definitions align with ISO/IEC 22989 and EU AI Act | ☐ | |
| 10 | Risk tier criteria are specific and measurable | ☐ | |
| 11 | Autonomy level definitions are clear and actionable | ☐ | |
| 12 | Data classification mappings are complete | ☐ | |
| 13 | Human oversight requirements are proportional to risk | ☐ | |
| 14 | Agent registry schema is complete and current | ☐ | |
| 15 | Vendor due diligence criteria are comprehensive | ☐ | |
| 16 | Risk assessment methodology is documented | ☐ | |
| 17 | Monitoring metrics are defined and measurable | ☐ | |
| 18 | Enforcement consequences are proportionate | ☐ | |
| 19 | Incident response procedures are complete | ☐ | |
| 20 | Training requirements are role-specific | ☐ | |

#### Regulatory Alignment

| # | Checkpoint | Status | Notes |
|---|-----------|--------|-------|
| 21 | NIST AI RMF 1.0 mappings verified | ☐ | |
| 22 | ISO/IEC 42001:2023 mappings verified | ☐ | |
| 23 | EU AI Act (Reg. 2024/1689) mappings verified | ☐ | |
| 24 | GDPR requirements addressed | ☐ | |
| 25 | Sector-specific regulations addressed | ☐ | |
| 26 | Recent regulatory changes incorporated | ☐ | |

#### Technical Enforceability

| # | Checkpoint | Status | Notes |
|---|-----------|--------|-------|
| 27 | Each policy statement is technically enforceable | ☐ | |
| 28 | GRC_Claw PDP policies cover all policy requirements | ☐ | |
| 29 | PEP enforcement points are configured | ☐ | |
| 30 | Evidence collection covers all policy requirements | ☐ | |
| 31 | Monitoring metrics are instrumented in GRC_Claw | ☐ | |
| 32 | Automated compliance checks are implemented | ☐ | |

### 2.3 Stakeholder Review Checklist

| Stakeholder | Review Focus | Sign-off | Date |
|-------------|-------------|----------|------|
| AI Governance Lead | Overall policy effectiveness | ☐ | |
| DPO | Privacy and data protection | ☐ | |
| CISO / Security Lead | Security controls and incident response | ☐ | |
| Legal / Compliance | Regulatory alignment and legal risk | ☐ | |
| Business Unit Representatives | Operational feasibility | ☐ | |
| Internal Audit | Control adequacy and audit trail | ☐ | |
| Executive Sponsor | Risk appetite alignment and resource adequacy | ☐ | |

### 2.4 Post-Review Actions

- [ ] All review findings documented
- [ ] Change requests logged and prioritized
- [ ] Updated policy drafted and re-reviewed
- [ ] Stakeholder sign-offs obtained
- [ ] Updated policy published and communicated
- [ ] Training materials updated
- [ ] GRC_Claw policies updated to match
- [ ] Review completion documented in Document Control

---

## 3. Policy Approval Workflow

### 3.1 Approval Authority Matrix

| Policy Change Type | Approval Authority | Escalation | SLA |
|-------------------|-------------------|------------|-----|
| Minor editorial (typos, formatting) | AI Governance Lead | None | 5 business days |
| Clarification (no requirement change) | AI Governance Lead + Legal | None | 10 business days |
| New policy section | AI Governance Committee | Executive Sponsor | 15 business days |
| Risk tier criteria change | AI Governance Committee + CISO | Executive Sponsor | 15 business days |
| Governance structure change | Executive Sponsor | Board (if needed) | 20 business days |
| Scope expansion | AI Governance Committee + Legal + DPO | Executive Sponsor | 20 business days |
| Regulatory-driven change | AI Governance Committee + Legal | Executive Sponsor + Board | Per regulatory deadline |
| Emergency policy (incident-driven) | AI Governance Lead + CISO (interim) | AI Governance Committee (ratification) | 48 hours interim / 15 days ratification |

### 3.2 Approval Workflow Steps

```
Step 1: Policy Change Request
├── Submitted via GRC_Claw Policy Definition Layer
├── Includes: rationale, affected sections, risk assessment
└── Logged in policy change register

Step 2: Technical Review
├── AI Governance Lead reviews for completeness
├── Technical feasibility assessed against GRC_Claw architecture
├── Impact on existing policies evaluated
└── Output: Technical review memo

Step 3: Stakeholder Review
├── Legal/Compliance review (regulatory alignment)
├── Security review (control adequacy)
├── Privacy review (data protection impact)
├── Business review (operational feasibility)
└── Output: Consolidated stakeholder feedback

Step 4: Revision
├── Author incorporates feedback
├── Revised policy drafted
├── Second technical review if significant changes
└── Output: Revised policy draft

Step 5: Committee Review
├── AI Governance Committee reviews revised policy
├── Risk appetite alignment assessed
├── Resource requirements evaluated
├── Vote: approve / approve with conditions / reject
└── Output: Committee decision with conditions

Step 6: Executive Approval
├── Executive Sponsor reviews committee recommendation
├── Budget and resource approval
├── Final sign-off
└── Output: Approved policy

Step 7: Publication & Communication
├── Policy published in document management system
├── Version incremented and dated
├── Stakeholders notified
├── Training scheduled
├── GRC_Claw policies updated
└── Output: Effective policy

Step 8: Implementation
├── Technical controls configured in GRC_Claw
├── Monitoring activated
├── Enforcement enabled
└── Output: Operational policy
```

### 3.3 Emergency Approval Procedure

For incident-driven or regulatory-deadline policy changes:

1. **Interim Authorization** (within 4 hours)
   - AI Governance Lead + CISO jointly authorize emergency policy
   - Documented in incident record
   - Effective immediately, valid for 30 days

2. **Expedited Review** (within 48 hours)
   - Emergency session of AI Governance Committee
   - Remote approval permitted
   - Legal review conducted concurrently

3. **Ratification** (within 15 days)
   - Full committee review at next scheduled meeting
   - Ratification or modification
   - If rejected, sunset clause activates

### 3.4 Approval Record Requirements

Each approval must be documented with:

| Field | Description |
|-------|-------------|
| Policy ID | Unique identifier |
| Version | Semantic version number |
| Change Summary | Description of changes |
| Approval Authority | Role/person who approved |
| Approval Date | Date of approval |
| Approval Method | Committee vote / individual sign-off / emergency authorization |
| Conditions | Any conditions attached to approval |
| Effective Date | Date policy becomes effective |
| Review Date | Scheduled next review date |
| Evidence | Link to approval evidence in GRC_Claw Evidence Store |

---

## 4. Policy Enforcement Patterns

### 4.1 Enforcement Architecture

The GRC_Claw reference architecture provides three enforcement layers that map to policy requirements:

```
┌─────────────────────────────────────────────────────────────┐
│                    POLICY ENFORCEMENT LAYERS                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: PREVENTIVE (Before Action)                        │
│  ├── Identity verification (mTLS/SPIFFE)                    │
│  ├── Capability declaration validation                      │
│  ├── Tool permission scoping (deny-by-default)              │
│  └── Budget pre-check                                       │
│                                                             │
│  Layer 2: DETECTIVE (During Action)                         │
│  ├── Real-time policy evaluation (PDP)                      │
│  ├── Behavioral analytics                                   │
│  ├── Anomaly detection                                      │
│  └── Rate limiting                                          │
│                                                             │
│  Layer 3: CORRECTIVE (After Action)                         │
│  ├── Kill-switch activation                                 │
│  ├── Agent quarantine                                       │
│  ├── Evidence preservation                                  │
│  └── Incident response                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Enforcement Pattern Catalog

#### Pattern 1: Data Access Control

**Policy Requirement:** Agents may only access data at or below their clearance level.

**Implementation:**
```cedar
// Cedar policy for data access control
permit(
  principal in Agent::"data-analyst",
  action == Action::"read",
  resource in DataClass::"public"
) when {
  resource.classification <= principal.clearance
};

forbid(
  principal,
  action == Action::"read",
  resource in DataClass::"pii"
) unless {
  context.approval_ticket exists &&
  context.approval_ticket.status == "approved"
};
```

**Enforcement Point:** PEP (MCP Gateway) intercepts all data access requests.

**Evidence:** Decision certificate logged to Evidence Store with data classification and agent clearance.

#### Pattern 2: Budget Enforcement

**Policy Requirement:** Agents must not exceed configured monetary, API call, or message volume budgets.

**Implementation:**
```python
# PEP budget enforcement
class BudgetEnforcer:
    def enforce(self, agent_id: str, action: str, estimated_cost: float) -> Decision:
        agent = self.agent_registry.get(agent_id)
        
        # Check daily monetary budget
        daily_spend = self.analytics.get_daily_spend(agent_id)
        if daily_spend + estimated_cost > agent.budget_cap_daily:
            return Decision(
                verdict="DENY",
                reason="daily_budget_cap_exceeded",
                context={"daily_spend": daily_spend, "cap": agent.budget_cap_daily}
            )
        
        # Check API call rate
        hourly_calls = self.analytics.get_hourly_api_calls(agent_id)
        if hourly_calls >= agent.api_call_cap_hourly:
            return Decision(
                verdict="DENY",
                reason="hourly_api_cap_exceeded",
                context={"hourly_calls": hourly_calls, "cap": agent.api_call_cap_hourly}
            )
        
        return Decision(verdict="ALLOW")
```

**Enforcement Point:** PEP pre-execution check.

**Evidence:** Budget check results logged with decision certificate.

#### Pattern 3: Human-in-the-Loop (HITL)

**Policy Requirement:** Tier 3+ AI systems require human approval for consequential decisions.

**Implementation:**
```python
# PEP HITL enforcement
async def enforce_hitl(agent_id: str, action: str, decision: Decision) -> Decision:
    agent = await agent_registry.get(agent_id)
    
    if agent.risk_tier in ["high", "prohibited"]:
        if action in agent.consequential_actions:
            if decision.verdict == "ALLOW":
                # Require human approval
                ticket = await approval_service.create_ticket(
                    agent_id=agent_id,
                    action=action,
                    decision_context=decision.context,
                    required_approver=agent.accountable_owner
                )
                return Decision(
                    verdict="REQUIRE_APPROVAL",
                    reason="hitl_required_for_consequential_action",
                    ticket_id=ticket.id
                )
    
    return decision
```

**Enforcement Point:** PEP post-PDP evaluation, pre-execution.

**Evidence:** Approval ticket created and linked to decision certificate.

#### Pattern 4: Tool Permission Scoping

**Policy Requirement:** Agents operate under deny-by-default permissions.

**Implementation:**
```cedar
// Cedar policy for tool permission scoping
// Default: deny all
forbid(principal, action, resource) when {
  not tool_permitted(principal, action)
};

// Explicit permission grants
permit(
  principal in Agent::"research-assistant",
  action == Action::"web_search",
  resource in Tool::"search-api"
) when {
  context.purpose == "research" &&
  context.user_authorized == true
};
```

**Enforcement Point:** PEP tool call interception.

**Evidence:** Tool permission check logged with principal, action, and resource.

#### Pattern 5: Behavioral Anomaly Detection

**Policy Requirement:** Agents exhibiting goal drift or anomalous behavior must be flagged and potentially quarantined.

**Implementation:**
```python
# GRC_Claw Analytics Engine - anomaly detection
class BehavioralMonitor:
    def evaluate(self, agent_id: str, action_event: dict) -> Optional[Decision]:
        baseline = self.get_behavioral_baseline(agent_id)
        current = self.get_recent_behavior(agent_id, window="1h")
        
        # Goal drift detection
        if self.detect_goal_drift(baseline, current):
            return Decision(
                verdict="QUARANTINE",
                reason="goal_drift_detected",
                context={
                    "baseline_purpose": baseline.purpose_vector,
                    "current_purpose": current.purpose_vector,
                    "drift_score": self.calculate_drift(baseline, current)
                }
            )
        
        # Permission escalation detection
        if self.detect_permission_escalation(agent_id, action_event):
            return Decision(
                verdict="DENY",
                reason="permission_escalation_attempt",
                context={"action": action_event}
            )
        
        # Looping/cascading failure detection
        if self.detect_looping(agent_id, window="5m"):
            return Decision(
                verdict="QUARANTINE",
                reason="looping_behavior_detected",
                context={"loop_count": self.get_loop_count(agent_id)}
            )
        
        return None
```

**Enforcement Point:** GRC_Claw Analytics Engine → PEP quarantine action.

**Evidence:** Anomaly detection results logged with behavioral metrics and decision.

#### Pattern 6: Kill-Switch Activation

**Policy Requirement:** A kill-switch mechanism must be available for immediate agent deactivation.

**Implementation:**
```python
# Kill-switch implementation
class KillSwitch:
    async def activate(self, agent_id: str, reason: str, activated_by: str):
        # 1. Immediately block all agent actions
        await self.pep.block_agent(agent_id)
        
        # 2. Isolate agent from all resources
        await self.pep.isolate_agent(agent_id)
        
        # 3. Preserve all agent state and logs
        await self.evidence_store.preserve_agent_state(agent_id)
        
        # 4. Update agent registry
        await self.agent_registry.update_status(
            agent_id, 
            status="quarantined",
            reason=reason,
            quarantined_by=activated_by,
            quarantined_at=datetime.utcnow()
        )
        
        # 5. Notify stakeholders
        await self.notification_service.notify(
            recipients=[agent.owner, agent.technical_owner, "ai-governance-committee"],
            subject=f"Agent {agent_id} KILLSWITCH ACTIVATED",
            body=f"Reason: {reason}\nActivated by: {activated_by}"
        )
        
        # 6. Log kill-switch event
        await self.audit_log.log({
            "event": "kill_switch_activated",
            "agent_id": agent_id,
            "reason": reason,
            "activated_by": activated_by,
            "timestamp": datetime.utcnow().isoformat()
        })
```

**Enforcement Point:** Manual activation by authorized personnel or automated by Analytics Engine.

**Evidence:** Kill-switch event logged with full context and chain of custody.

#### Pattern 7: Content Redaction

**Policy Requirement:** AI outputs containing sensitive data must be redacted before delivery.

**Implementation:**
```python
# PEP content redaction
class ContentRedactor:
    def redact(self, content: str, data_classification: str) -> RedactionResult:
        redaction_rules = self.get_rules_for_classification(data_classification)
        
        redacted_content = content
        redactions_applied = []
        
        for rule in redaction_rules:
            matches = rule.pattern.findall(redacted_content)
            for match in matches:
                redacted_content = redacted_content.replace(match, rule.replacement)
                redactions_applied.append({
                    "rule_id": rule.id,
                    "type": rule.type,
                    "position": redacted_content.find(rule.replacement)
                })
        
        return RedactionResult(
            content=redacted_content,
            redactions=redactions_applied,
            original_hash=hashlib.sha256(content.encode()).hexdigest(),
            redacted_hash=hashlib.sha256(redacted_content.encode()).hexdigest()
        )
```

**Enforcement Point:** PEP output transformation.

**Evidence:** Redaction log with original hash, redacted hash, and rules applied.

### 4.3 Enforcement Decision Matrix

| Policy Violation | Preventive Control | Detective Control | Corrective Control |
|-----------------|-------------------|-------------------|-------------------|
| Unauthorized data access | Capability declaration, clearance check | PDP policy evaluation, DLP monitoring | Access revocation, agent suspension |
| Budget overrun | Budget pre-check | Real-time spend monitoring | Agent suspension, budget adjustment |
| Goal drift | Purpose constraint in policy | Behavioral analytics | Kill-switch, quarantine |
| Tool misuse | Deny-by-default permissions | Tool call pattern analysis | Permission revocation, agent suspension |
| Data exfiltration | Data classification enforcement | DLP, network monitoring | Agent isolation, incident response |
| Prompt injection | Input validation | Anomaly detection | Agent quarantine, input filtering |
| Identity abuse | mTLS, SVID verification | Identity behavior analysis | Certificate revocation, agent termination |

### 4.4 Enforcement Automation Levels

| Level | Description | Use Case | Human Role |
|-------|-------------|----------|------------|
| **Fully Automated** | PEP enforces without human intervention | Tier 1-2 violations, budget caps, rate limits | Post-hoc review |
| **Human-in-the-Loop** | PEP queues for human approval | Tier 3 consequential decisions | Approve/deny with context |
| **Human-on-the-Loop** | PEP enforces, human monitors | Tier 4 operations | Monitor, override, kill-switch |
| **Manual** | Human initiates enforcement | Emergency response, complex incidents | Full human control |

---

## 5. Policy Testing Framework

### 5.1 Testing Overview

The policy testing framework ensures that governance policies are correctly implemented, effectively enforced, and produce the expected outcomes before and after deployment.

```
┌─────────────────────────────────────────────────────────────┐
│                  POLICY TESTING LIFECYCLE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Unit    │─▶│ Integration│─▶│  System  │─▶│  Live    │   │
│  │  Test    │  │  Test     │  │  Test    │  │  Test    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       │              │              │              │         │
│       ▼              ▼              ▼              ▼         │
│  Policy rule   PEP-PDP      Full enforcement  Production    │
│  correctness   interaction  chain           validation     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Unit Testing — Policy Rule Validation

**Objective:** Verify that individual Cedar/Rego policy rules produce correct decisions for given inputs.

**Test Framework:**
```python
# Policy unit test example
import pytest
from grc_claw.policy_tester import PolicyTester

class TestDataAccessPolicy:
    
    def setup_method(self):
        self.tester = PolicyTester(
            policy_file="policies/data_access.cedar",
            policy_engine="cedar"
        )
    
    def test_allow_public_data_access(self):
        """Agent with clearance 2 can access public data (classification 1)."""
        result = self.tester.evaluate(
            principal={"id": "agent-42", "clearance": 2},
            action="read",
            resource={"id": "dataset-1", "classification": 1},
            context={"time": "2026-10-01T14:00:00Z"}
        )
        assert result.verdict == "ALLOW"
    
    def test_deny_pii_without_approval(self):
        """Agent cannot access PII (classification 4) without approval ticket."""
        result = self.tester.evaluate(
            principal={"id": "agent-42", "clearance": 4},
            action="read",
            resource={"id": "pii-dataset", "classification": 4},
            context={"time": "2026-10-01T14:00:00Z"}
        )
        assert result.verdict == "DENY"
        assert result.reason == "pii_access_requires_approval"
    
    def test_allow_pii_with_approval(self):
        """Agent can access PII with valid approval ticket."""
        result = self.tester.evaluate(
            principal={"id": "agent-42", "clearance": 4},
            action="read",
            resource={"id": "pii-dataset", "classification": 4},
            context={
                "time": "2026-10-01T14:00:00Z",
                "approval_ticket": {"id": "ticket-123", "status": "approved"}
            }
        )
        assert result.verdict == "ALLOW"
    
    def test_deny_outside_business_hours(self):
        """Agent cannot access data outside configured hours."""
        result = self.tester.evaluate(
            principal={"id": "agent-42", "clearance": 2},
            action="read",
            resource={"id": "dataset-1", "classification": 1},
            context={"time": "2026-10-01T23:00:00Z"}
        )
        assert result.verdict == "DENY"
```

**Test Coverage Requirements:**
- [ ] Every `permit` rule has at least one positive test case
- [ ] Every `forbid` rule has at least one negative test case
- [ ] Every `when` condition has boundary value tests
- [ ] Every `unless` exception has test cases
- [ ] Default deny behavior verified
- [ ] Policy conflict resolution tested

### 5.3 Integration Testing — PEP-PDP Interaction

**Objective:** Verify that the PEP correctly intercepts actions, queries the PDP, and applies decisions.

**Test Framework:**
```python
# PEP-PDP integration test
import pytest
from grc_claw.integration_tester import PEPIntegrationTester

class TestEnforcementIntegration:
    
    def setup_method(self):
        self.tester = PEPIntegrationTester(
            pep_endpoint="http://pep-gateway:8080",
            pdp_endpoint="http://pdp-service:8181"
        )
    
    @pytest.mark.asyncio
    async def test_tool_call_allowed(self):
        """PEP allows tool call when PDP returns ALLOW."""
        response = await self.tester.simulate_tool_call(
            agent_id="agent-42",
            tool_name="web_search",
            arguments={"query": "public information"},
            auth_token="valid-mtls-token"
        )
        assert response.status == "success"
        assert response.decision.verdict == "ALLOW"
    
    @pytest.mark.asyncio
    async def test_tool_call_denied(self):
        """PEP blocks tool call when PDP returns DENY."""
        response = await self.tester.simulate_tool_call(
            agent_id="agent-42",
            tool_name="database_query",
            arguments={"query": "SELECT * FROM pii_table"},
            auth_token="valid-mtls-token"
        )
        assert response.status == "error"
        assert response.error.code == "POLICY_VIOLATION"
        assert response.decision.verdict == "DENY"
    
    @pytest.mark.asyncio
    async def test_tool_call_requires_approval(self):
        """PEP queues tool call for approval when PDP returns REQUIRE_APPROVAL."""
        response = await self.tester.simulate_tool_call(
            agent_id="agent-42",
            tool_name="send_email",
            arguments={"to": "external@client.com", "body": "confidential data"},
            auth_token="valid-mtls-token"
        )
        assert response.status == "pending_approval"
        assert response.ticket_id is not None
    
    @pytest.mark.asyncio
    async def test_agent_quarantine(self):
        """PEP quarantines agent when PDP returns QUARANTINE."""
        response = await self.tester.simulate_tool_call(
            agent_id="agent-42",
            tool_name="file_write",
            arguments={"path": "/etc/passwd", "content": "malicious"},
            auth_token="valid-mtls-token"
        )
        assert response.status == "error"
        assert response.error.code == "AGENT_QUARANTINED"
        
        # Verify agent is blocked
        agent_status = await self.tester.get_agent_status("agent-42")
        assert agent_status == "quarantined"
```

**Test Coverage Requirements:**
- [ ] All 5 decision verdicts tested (ALLOW, ALLOW_WITH_REDACTION, REQUIRE_APPROVAL, DENY, QUARANTINE)
- [ ] mTLS authentication failure tested
- [ ] PDP timeout/failure fallback tested
- [ ] Decision caching behavior tested
- [ ] Evidence logging verified for each decision
- [ ] Concurrent action handling tested

### 5.4 System Testing — Full Enforcement Chain

**Objective:** Verify the complete enforcement chain from agent action through PEP, PDP, evidence collection, and compliance mapping.

**Test Scenarios:**

| Scenario | Input | Expected Output | Evidence |
|----------|-------|-----------------|----------|
| Normal operation | Agent reads public data | ALLOW, data returned | Decision certificate logged |
| Policy violation | Agent accesses unauthorized data | DENY, access blocked | Violation logged, alert triggered |
| Budget exceeded | Agent attempts action over budget | DENY, budget message | Budget alert logged |
| Anomalous behavior | Agent exhibits goal drift | QUARANTINE, agent isolated | Incident created, stakeholders notified |
| Approval required | Agent requests consequential action | REQUIRE_APPROVAL, ticket created | Approval workflow initiated |
| PDP failure | PDP unavailable | Fail-closed, cached decision or DENY | Fallback behavior logged |
| Evidence store failure | Evidence store unavailable | Action allowed, evidence queued | Queue status monitored |

**Test Framework:**
```python
# System test - full enforcement chain
class TestEnforcementChain:
    
    @pytest.mark.asyncio
    async def test_full_chain_normal_operation(self):
        """Verify complete chain: Agent → PEP → PDP → Evidence → Compliance."""
        
        # 1. Agent initiates action
        action = AgentAction(
            agent_id="agent-42",
            tool="web_search",
            arguments={"query": "public data"},
            context={"purpose": "research", "user_authorized": True}
        )
        
        # 2. PEP intercepts and enforces
        result = await self.enforcement_chain.execute(action)
        
        # 3. Verify decision
        assert result.decision.verdict == "ALLOW"
        assert result.decision.policy_id == "pol-data-access-001"
        assert result.decision.evidence_hash is not None
        
        # 4. Verify evidence collection
        evidence = await self.evidence_store.get_evidence(
            result.decision.evidence_hash
        )
        assert evidence is not None
        assert evidence.verification_level >= "L2"
        
        # 5. Verify compliance mapping
        compliance_update = await self.compliance_service.get_update(
            result.decision.evidence_hash
        )
        assert compliance_update.control_id == "GRC-CLW-001"
        assert compliance_update.framework_mappings is not None
        
        # 6. Verify observability
        trace = await self.observability.get_trace(
            result.decision.decision_id
        )
        assert trace is not None
        assert len(trace.spans) >= 5  # At least 5 spans in the trace
```

### 5.5 Live Testing — Production Validation

**Objective:** Validate policy enforcement in production with real agents and real data.

**Approach:**

1. **Shadow Mode** (Week 1-2)
   - Policies deployed in observe-only mode
   - All decisions logged but not enforced
   - Compare policy decisions against actual agent behavior
   - Tune policies based on false positive/negative rates

2. **Canary Mode** (Week 3-4)
   - Policies enforced for 10% of agent actions
   - Monitor for unexpected disruptions
   - Collect feedback from agent operators
   - Adjust policies as needed

3. **Full Enforcement** (Week 5+)
   - Policies enforced for all agent actions
   - Continuous monitoring of enforcement metrics
   - Regular review of false positive/negative rates

**Live Testing Metrics:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| False positive rate | < 5% | Actions incorrectly denied / Total actions |
| False negative rate | < 1% | Actions incorrectly allowed / Total actions |
| Enforcement latency (p99) | < 100ms | End-to-end tool call latency |
| Policy evaluation latency (p99) | < 50ms | PDP evaluation time |
| Evidence collection latency | < 5 seconds | Collector to store |
| Agent availability | > 99.9% | Agent uptime during enforcement |
| Kill-switch response time | < 1 second | Activation to agent isolation |

### 5.6 Policy Regression Testing

**Objective:** Ensure policy changes do not break existing enforcement.

**Regression Test Suite:**
```python
# Regression test suite
class PolicyRegressionSuite:
    
    def __init__(self):
        self.baseline = self.load_baseline_decisions()
    
    def load_baseline_decisions(self) -> dict:
        """Load baseline decisions from previous policy version."""
        return {
            "test-case-001": {"verdict": "ALLOW", "reason": None},
            "test-case-002": {"verdict": "DENY", "reason": "pii_access_requires_approval"},
            # ... all baseline test cases
        }
    
    def run_regression(self, new_policy_version: str) -> RegressionReport:
        """Compare new policy decisions against baseline."""
        tester = PolicyTester(policy_file=f"policies/{new_policy_version}.cedar")
        
        results = []
        for case_id, baseline in self.baseline.items():
            test_case = self.get_test_case(case_id)
            new_result = tester.evaluate(**test_case)
            
            results.append({
                "case_id": case_id,
                "baseline_verdict": baseline["verdict"],
                "new_verdict": new_result.verdict,
                "match": baseline["verdict"] == new_result.verdict,
                "baseline_reason": baseline["reason"],
                "new_reason": new_result.reason
            })
        
        return RegressionReport(
            total_cases=len(results),
            matching=sum(1 for r in results if r["match"]),
            mismatches=[r for r in results if not r["match"]],
            new_policy_version=new_policy_version
        )
```

**Regression Test Triggers:**
- [ ] Any policy version change
- [ ] Any Cedar/Rego rule modification
- [ ] Any PDP configuration change
- [ ] Any PEP enforcement logic change
- [ ] Any agent registry schema change
- [ ] Any compliance mapping change

### 5.7 Test Evidence and Reporting

All test results must be stored as evidence in GRC_Claw Evidence Store:

| Test Type | Evidence Type | Retention | Verification Level |
|-----------|--------------|-----------|-------------------|
| Unit test results | `analysis` | 2 years | L2 |
| Integration test results | `analysis` | 2 years | L2 |
| System test results | `analysis` | 3 years | L3 |
| Live test results | `observation` | 3 years | L3 |
| Regression test results | `analysis` | 3 years | L2 |

---

## 6. Policy Maintenance Procedures

### 6.1 Maintenance Schedule

| Activity | Frequency | Responsible | Evidence |
|----------|-----------|-------------|----------|
| Policy review | Annual | AI Governance Committee | Review record |
| Risk tier re-assessment | Annual | AI Governance Lead + Business Owners | Updated registry |
| Vendor re-assessment | Annual (high-risk) / Biennial (others) | AI Governance Lead + Procurement | Vendor risk register |
| Agent recertification | Quarterly (Tier 4) / Semi-annual (Tier 3) / Annual (Tier 2) | Agent Owners | Recertification records |
| Kill-switch test | Quarterly | Technical Owner | Test results |
| Training completion check | Semi-annual | AI Governance Lead | Training records |
| Compliance posture review | Quarterly | AI Governance Committee | Compliance report |
| Policy regression test | On every policy change | Technical team | Test results |
| Evidence retention review | Annual | DPO + AI Governance Lead | Retention report |
| Framework mapping update | On regulatory change | Legal + Compliance | Updated crosswalk |

### 6.2 Change Management Procedure

```
┌─────────────────────────────────────────────────────────────┐
│              POLICY CHANGE MANAGEMENT                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CHANGE REQUEST                                          │
│     ├── Submit via GRC_Claw Policy Definition Layer         │
│     ├── Include: rationale, affected sections, urgency      │
│     └── Auto-assign change ID                               │
│                                                             │
│  2. IMPACT ASSESSMENT                                       │
│     ├── Technical impact (GRC_Claw architecture)            │
│     ├── Operational impact (business processes)             │
│     ├── Regulatory impact (compliance obligations)          │
│     └── Risk impact (risk tier changes)                     │
│                                                             │
│  3. CHANGE CLASSIFICATION                                   │
│     ├── Minor (editorial) → AI Governance Lead approval     │
│     ├── Standard (clarification) → Lead + Legal approval    │
│     ├── Major (new requirements) → Committee approval       │
│     └── Emergency (incident-driven) → Interim + ratification│
│                                                             │
│  4. IMPLEMENTATION PLANNING                                  │
│     ├── Technical changes (Cedar/Rego policies)             │
│     ├── PEP/PDP configuration changes                       │
│     ├── Evidence collection changes                        │
│     ├── Training material updates                           │
│     └── Communication plan                                  │
│                                                             │
│  5. TESTING & VALIDATION                                    │
│     ├── Unit tests updated and passing                      │
│     ├── Integration tests updated and passing               │
│     ├── Regression tests passing                            │
│     ├── Stakeholder sign-off obtained                       │
│     └── Rollback plan documented                            │
│                                                             │
│  6. DEPLOYMENT                                              │
│     ├── Deploy to staging environment                       │
│     ├── Validate in staging                                 │
│     ├── Deploy to production                                │
│     ├── Monitor for 48 hours                                │
│     └── Confirm stable operation                            │
│                                                             │
│  7. POST-IMPLEMENTATION REVIEW                              │
│     ├── 30-day review of enforcement metrics                │
│     ├── False positive/negative analysis                    │
│     ├── Stakeholder feedback collection                     │
│     └── Lessons learned documented                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Version Control and Documentation

**Version Control Requirements:**

| Element | Requirement |
|---------|-------------|
| Version numbering | Semantic versioning (MAJOR.MINOR.PATCH) |
| MAJOR | New policy section, scope change, governance structure change |
| MINOR | New requirement within existing section, criteria change |
| PATCH | Editorial correction, clarification, formatting |
| Change log | Every version must have documented changes |
| Approval record | Every version must have approval evidence |
| Superseded versions | Retained in archive with effective dates |
| Effective dates | Every version must have explicit effective date |

**Document Control Template:**

```
Version: [MAJOR.MINOR.PATCH]
Date: [YYYY-MM-DD]
Author: [Name, Role]
Changes: [Summary of changes from previous version]
Approved by: [Name, Role, Date]
Effective date: [YYYY-MM-DD]
Next review: [YYYY-MM-DD]
Supersedes: [Previous version]
```

### 6.4 Continuous Improvement Process

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   MEASURE   │───▶│   ANALYZE    │───▶│   IMPROVE    │───▶│   IMPLEMENT  │
│             │    │              │    │              │    │              │
│ • Metrics   │    │ • Trends     │    │ • Root cause │    │ • Policy     │
│ • Incidents │    │ • Patterns   │    │ • Gap analysis│   │   updates    │
│ • Audits    │    │ • Benchmarks │    │ • Best practice│  │ • Control    │
│ • Feedback  │    │ • Root cause │    │   adoption   │    │   changes    │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       ▲                                                            │
       └────────────────────────────────────────────────────────────┘
```

**Key Performance Indicators:**

| KPI | Target | Measurement Frequency | Owner |
|-----|--------|----------------------|-------|
| Policy compliance rate | > 95% | Monthly | AI Governance Lead |
| Mean time to detect (MTTD) AI incidents | < 1 hour | Per incident | CISO |
| Mean time to respond (MTTR) AI incidents | < 4 hours | Per incident | CISO |
| False positive enforcement rate | < 5% | Monthly | Technical team |
| Training completion rate | 100% | Semi-annual | AI Governance Lead |
| Agent recertification on-time rate | 100% | Per cycle | Agent Owners |
| Vendor reassessment on-time rate | 100% | Per cycle | Procurement |
| Policy review on-time rate | 100% | Annual | AI Governance Committee |
| Evidence verification level | L2+ for all | Monthly | Technical team |
| Kill-switch test success rate | 100% | Quarterly | Technical Owner |

### 6.5 Policy Sunset and Archival

**Sunset Triggers:**
- AI system decommissioned
- Regulatory requirement obsolete
- Technology no longer in use
- Superseded by new policy section

**Archival Procedure:**
1. Mark policy section as `deprecated` in GRC_Claw Policy Definition Layer
2. Set effective end date
3. Notify all stakeholders
4. Archive policy version with full change history
5. Retain archived policy for regulatory minimum period
6. Update cross-reference matrix (Annex E)
7. Update training materials

**Retention Requirements:**

| Record Type | Minimum Retention | Regulatory Basis |
|-------------|-------------------|-----------------|
| Policy versions | Life of AI system + 7 years | ISO 42001 Clause 7.5 |
| Risk assessments | Life of AI system + 7 years | EU AI Act Article 9 |
| Impact assessments | Life of AI system + 7 years | EU AI Act Article 27 |
| Decision certificates | 2-3 years (or longer if required) | EU AI Act Article 12 |
| Incident records | 7 years | EU AI Act Article 73 |
| Training records | Employment + 7 years | ISO 42001 Clause 7.2 |
| Vendor assessments | Contract term + 7 years | ISO 42001 Clause 8.1 |
| Audit records | 7 years | ISO 42001 Clause 9.2 |

### 6.6 Roles and Responsibilities Summary

| Role | Maintenance Responsibility | Frequency |
|------|--------------------------|-----------|
| AI Governance Lead | Overall policy maintenance, review coordination, change management | Continuous |
| AI Governance Committee | Policy approval, review oversight, continuous improvement | Quarterly |
| Executive Sponsor | Resource approval, risk appetite alignment, escalation | As needed |
| DPO | Privacy impact review, DPIA oversight, data protection compliance | Per change |
| CISO / Security Lead | Security control review, incident response, enforcement adequacy | Per change |
| Legal / Compliance Lead | Regulatory alignment, contract review, legal risk assessment | Per change |
| Agent Owners | Agent recertification, behavioral review, kill-switch testing | Per schedule |
| Technical Team | Policy implementation, testing, evidence collection, monitoring | Continuous |
| Internal Audit | Independent assurance, control testing, governance effectiveness | Annual |

---

## Appendix A: Policy-to-Architecture Mapping

| Policy Section | GRC_Claw Component | Key Technology |
|---------------|-------------------|----------------|
| 1. Purpose, Scope, Definitions | Agent Registry, Compliance Mapping | PostgreSQL, Neo4j |
| 2. Governance Structure | Agent Identity Layer, Policy Binding | SPIFFE/SPIRE, Vault |
| 3. Risk Classification | Policy Definition Layer, Agent Registry | Cedar, Rego, PostgreSQL |
| 4. Data Governance | PDP (data access policies), DLP integration | OPA, Cedar |
| 5. Human Oversight | PEP (HITL/HOTL enforcement), Approval workflows | MCP Gateway, FastAPI |
| 6. Agentic AI Governance | Agent Registry, PEP, Analytics Engine | PostgreSQL, Grafana, custom |
| 7. Third-Party/Vendor | Evidence Collection, Compliance Mapping | OSCAL, Crosswalk Engine |
| 8. Risk Assessment | Analytics Engine, Evidence Store | Custom ML, WORM storage |
| 9. Monitoring & Incidents | Observability Layer, PEP, Analytics | OTel, OpenInference, Grafana |
| 10. Training & Improvement | Compliance Mapping, Analytics | Crosswalk Engine, Grafana |

## Appendix B: Quick Reference — Policy Lifecycle States

```
draft → review → active → deprecated → archived
```

| State | Description | Allowed Actions |
|-------|-------------|-----------------|
| **draft** | Policy under development | Edit, version, test |
| **review** | Under stakeholder review | Comment, approve, reject |
| **active** | Enforced in production | Enforce, monitor, measure |
| **deprecated** | No longer enforced, retained for reference | Reference, archive |
| **archived** | Retained for regulatory/compliance purposes | Reference only |

---

*End of implementation guide.*

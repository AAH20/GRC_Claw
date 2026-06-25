import { randomUUID } from "node:crypto";
import type { Policy, PolicyTemplate, Attestation, PolicyStatus, PolicyCategory, PolicyStats } from "../types.js";

const DEFAULT_TEMPLATES: PolicyTemplate[] = [
  { id: "tpl-1", name: "Information Security Policy", category: "security", framework: "ISO 27001", content: "# Information Security Policy\n\n## Purpose\nEstablish information security management.\n\n## Scope\nAll employees and systems.\n\n## Policy\n1. Classify data by sensitivity\n2. Implement controls per classification\n3. Review annually", isDefault: true },
  { id: "tpl-2", name: "Acceptable Use Policy", category: "operational", framework: "SOC 2", content: "# Acceptable Use Policy\n\n## Purpose\nDefine acceptable use of company resources.\n\n## Policy\n1. Use resources for business purposes\n2. No unauthorized software\n3. Report security incidents immediately", isDefault: true },
  { id: "tpl-3", name: "Data Privacy Policy", category: "privacy", framework: "GDPR", content: "# Data Privacy Policy\n\n## Purpose\nEnsure GDPR compliance.\n\n## Policy\n1. Collect minimal data\n2. Obtain consent\n3. Honor data subject rights\n4. Report breaches within 72 hours", isDefault: true },
  { id: "tpl-4", name: "Incident Response Policy", category: "security", framework: "NIST CSF", content: "# Incident Response Policy\n\n## Purpose\nDefine incident response procedures.\n\n## Policy\n1. Detect and report incidents\n2. Contain and eradicate threats\n3. Recover and post-incident review", isDefault: true },
  { id: "tpl-5", name: "Access Control Policy", category: "security", framework: "ISO 27001", content: "# Access Control Policy\n\n## Purpose\nManage access to systems and data.\n\n## Policy\n1. Least privilege principle\n2. Role-based access control\n3. Regular access reviews\n4. MFA for all users", isDefault: true },
];

export class PolicyManager {
  private policies: Map<string, Policy> = new Map();
  private templates: PolicyTemplate[] = [...DEFAULT_TEMPLATES];

  createFromTemplate(templateId: string, owner: string, approver: string): Policy | null {
    const template = this.templates.find((t) => t.id === templateId);
    if (!template) return null;
    return this.createPolicy({ title: template.name, category: template.category, owner, approver, content: template.content, framework: template.framework });
  }

  createPolicy(input: { title: string; category: PolicyCategory; owner: string; approver: string; content: string; framework: string }): Policy {
    const policy: Policy = {
      id: randomUUID(),
      title: input.title,
      category: input.category,
      version: 1,
      status: "draft",
      owner: input.owner,
      approver: input.approver,
      content: input.content,
      framework: input.framework,
      effectiveDate: "",
      reviewDate: "",
      changeLog: [],
      attestations: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.policies.set(policy.id, policy);
    return policy;
  }

  getPolicy(id: string): Policy | undefined { return this.policies.get(id); }
  listPolicies(): Policy[] { return Array.from(this.policies.values()); }
  getPoliciesByCategory(cat: PolicyCategory): Policy[] { return this.listPolicies().filter((p) => p.category === cat); }
  getTemplates(): PolicyTemplate[] { return [...this.templates]; }

  transitionPolicy(id: string, status: PolicyStatus): boolean {
    const policy = this.policies.get(id);
    if (!policy) return false;
    if (status === "published") {
      policy.effectiveDate = new Date().toISOString();
      policy.reviewDate = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString();
    }
    policy.status = status;
    policy.updatedAt = new Date().toISOString();
    return true;
  }

  incrementVersion(id: string, changedBy: string, summary: string): boolean {
    const policy = this.policies.get(id);
    if (!policy) return false;
    policy.changeLog.push({ version: policy.version, changedBy, changedAt: new Date().toISOString(), summary });
    policy.version++;
    policy.status = "draft";
    policy.updatedAt = new Date().toISOString();
    return true;
  }

  addAttestation(policyId: string, employeeId: string, employeeName: string): Attestation | null {
    const policy = this.policies.get(policyId);
    if (!policy) return null;
    const attestation: Attestation = { id: randomUUID(), employeeId, employeeName, acknowledgedAt: new Date().toISOString(), attestedVersion: policy.version };
    policy.attestations.push(attestation);
    return attestation;
  }

  getStats(): PolicyStats {
    const policies = this.listPolicies();
    return {
      totalPolicies: policies.length,
      byStatus: {
        draft: policies.filter((p) => p.status === "draft").length,
        under_review: policies.filter((p) => p.status === "under_review").length,
        approved: policies.filter((p) => p.status === "approved").length,
        published: policies.filter((p) => p.status === "published").length,
        archived: policies.filter((p) => p.status === "archived").length,
      },
      byCategory: {
        security: policies.filter((p) => p.category === "security").length,
        privacy: policies.filter((p) => p.category === "privacy").length,
        compliance: policies.filter((p) => p.category === "compliance").length,
        operational: policies.filter((p) => p.category === "operational").length,
        hr: policies.filter((p) => p.category === "hr").length,
        financial: policies.filter((p) => p.category === "financial").length,
      },
      upcomingReviews: policies.filter((p) => p.status === "published" && new Date(p.reviewDate) < new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)).length,
      attestationsPending: 0,
    };
  }
}

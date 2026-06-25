import { randomUUID } from "node:crypto";
import type { KnowledgeBaseEntry, ResponseConfidence } from "../types.js";

const KNOWLEDGE_BASE: KnowledgeBaseEntry[] = [
  { id: "kb-1", category: "encryption", keywords: ["encrypt", "aes", "tls", "ssl", "crypto"], answer: "We use AES-256 encryption at rest and TLS 1.3 in transit. All cryptographic operations use FIPS 140-2 validated modules.", confidence: "high", evidenceUrls: [], framework: "soc2" },
  { id: "kb-2", category: "access_control", keywords: ["mfa", "multi-factor", "2fa", "two-factor"], answer: "Multi-factor authentication is enforced for all employees, contractors, and customers. We support TOTP, WebAuthn, and SMS.", confidence: "high", evidenceUrls: [], framework: "soc2" },
  { id: "kb-3", category: "access_control", keywords: ["rbac", "role-based", "least privilege", "access control"], answer: "Role-based access control is implemented across all systems. Access reviews are conducted quarterly. Least privilege is enforced.", confidence: "high", evidenceUrls: [], framework: "iso27001" },
  { id: "kb-4", category: "monitoring", keywords: ["siem", "monitor", "log", "alert", "detection"], answer: "We operate 24/7 security monitoring with real-time SIEM. Alerts are triaged within 15 minutes. Log retention is 1 year minimum.", confidence: "high", evidenceUrls: [], framework: "soc2" },
  { id: "kb-5", category: "incident_response", keywords: ["incident", "breach", "response", "notification"], answer: "Incident response plan is documented and tested annually via tabletop exercises. Breach notification within 72 hours per GDPR.", confidence: "high", evidenceUrls: [], framework: "gdpr" },
  { id: "kb-6", category: "backup", keywords: ["backup", "recovery", "restore", "dr", "disaster"], answer: "Daily automated backups with 30-day retention. RTO: 4 hours, RPO: 1 hour. DR tested quarterly.", confidence: "high", evidenceUrls: [], framework: "soc2" },
  { id: "kb-7", category: "vendor_management", keywords: ["vendor", "sub-processor", "third-party", "supplier"], answer: "All vendors undergo security assessment before onboarding. Critical vendors reviewed annually. Sub-processors documented in DPA.", confidence: "medium", evidenceUrls: [], framework: "gdpr" },
  { id: "kb-8", category: "data_protection", keywords: ["privacy", "pii", "personal data", "data protection"], answer: "Data minimization is enforced. PII is encrypted and access-controlled. Data retention policies enforced per framework requirements.", confidence: "high", evidenceUrls: [], framework: "gdpr" },
  { id: "kb-9", category: "vulnerability_management", keywords: ["vulnerability", "patch", "scan", "penetration"], answer: "Automated vulnerability scanning weekly. Critical patches within 48 hours. Annual penetration testing by third party.", confidence: "high", evidenceUrls: [], framework: "soc2" },
  { id: "kb-10", category: "business_continuity", keywords: ["bcp", "continuity", "availability", "uptime"], answer: "99.9% SLA with automated failover. BCP tested semi-annually. Multi-region deployment for redundancy.", confidence: "medium", evidenceUrls: [], framework: "iso27001" },
  { id: "kb-11", category: "training", keywords: ["security awareness", "training", "phishing", "education"], answer: "Mandatory security awareness training upon hire and annually. Monthly phishing simulations. Role-specific training for developers.", confidence: "high", evidenceUrls: [], framework: "soc2" },
  { id: "kb-12", category: "code_review", keywords: ["code review", "sast", "dast", "secure development"], answer: "All code changes require peer review. SAST/DAST in CI/CD pipeline. Secure coding training for developers.", confidence: "high", evidenceUrls: [], framework: "soc2" },
];

export class QuestionnaireKnowledgeBase {
  private entries: KnowledgeBaseEntry[] = [...KNOWLEDGE_BASE];

  search(category: string, keywords: string[]): KnowledgeBaseEntry[] {
    return this.entries.filter((e) => {
      const categoryMatch = e.category.toLowerCase().includes(category.toLowerCase()) || category === "";
      const keywordMatch = keywords.some((k) => e.keywords.some((ek) => ek.includes(k.toLowerCase()) || k.toLowerCase().includes(ek)));
      return categoryMatch || keywordMatch;
    });
  }

  addEntry(entry: Omit<KnowledgeBaseEntry, "id">): KnowledgeBaseEntry {
    const newEntry: KnowledgeBaseEntry = { ...entry, id: randomUUID() };
    this.entries.push(newEntry);
    return newEntry;
  }

  getEntriesByFramework(framework: string): KnowledgeBaseEntry[] {
    return this.entries.filter((e) => e.framework === framework);
  }

  matchQuestion(question: string): { entry: KnowledgeBaseEntry; matchScore: number } | null {
    const lower = question.toLowerCase();
    let bestMatch: { entry: KnowledgeBaseEntry; matchScore: number } | null = null;

    for (const entry of this.entries) {
      let score = 0;
      for (const keyword of entry.keywords) {
        if (lower.includes(keyword)) score += 2;
        if (lower.split(" ").includes(keyword)) score += 1;
      }
      if (lower.includes(entry.category)) score += 3;

      if (score > 0 && (!bestMatch || score > bestMatch.matchScore)) {
        bestMatch = { entry, matchScore: score };
      }
    }

    return bestMatch;
  }
}

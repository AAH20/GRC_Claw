import { randomUUID } from "node:crypto";
import type {
  Vendor,
  VendorStatus,
  VendorTier,
  VendorContact,
  VendorContract,
  VendorDocument,
  VendorRiskScore,
  RiskFactor,
  QuestionnaireTemplate,
  QuestionnaireType,
  VendorAssessment,
  AssessmentFinding,
  VendorMonitoring,
  VendorAlert,
  VendorRiskRegisterEntry,
  VendorRiskDashboard,
  VendorRiskChange,
  VendorSearchFilter,
} from "./types.js";
import { newId, nowIso, computeTier } from "./types.js";

// ─── Questionnaire Templates ──────────────────────────────────────────

const QUESTIONNAIRE_TEMPLATES: QuestionnaireTemplate[] = [
  {
    id: "qt-sig-lite",
    name: "SIG Lite",
    type: "sig_lite",
    framework: "SIG",
    totalQuestions: 12,
    version: 1,
    createdAt: nowIso(),
    questions: [
      { id: "q-1", category: "Security", question: "Does the vendor have a formal information security policy?", type: "boolean", required: true, controlId: "A.5.1.1", framework: "ISO 27001" },
      { id: "q-2", category: "Security", question: "Does the vendor perform regular vulnerability scanning?", type: "boolean", required: true, controlId: "A.12.6.1", framework: "ISO 27001" },
      { id: "q-3", category: "Access Control", question: "Does the vendor enforce multi-factor authentication?", type: "boolean", required: true, controlId: "A.9.4.2", framework: "ISO 27001" },
      { id: "q-4", category: "Access Control", question: "How does the vendor manage user access provisioning?", type: "select", required: true, options: ["Automated", "Manual", "Hybrid"] },
      { id: "q-5", category: "Data Protection", question: "Is data encrypted at rest?", type: "boolean", required: true },
      { id: "q-6", category: "Data Protection", question: "Is data encrypted in transit?", type: "boolean", required: true },
      { id: "q-7", category: "Incident Response", question: "Does the vendor have a documented incident response plan?", type: "boolean", required: true },
      { id: "q-8", category: "Incident Response", question: "Within what timeframe does the vendor notify customers of a security incident?", type: "select", required: true, options: ["24 hours", "48 hours", "72 hours", "7 days"] },
      { id: "q-9", category: "Business Continuity", question: "Does the vendor have a business continuity plan?", type: "boolean", required: true },
      { id: "q-10", category: "Compliance", question: "Does the vendor hold SOC 2 Type II certification?", type: "boolean", required: false },
      { id: "q-11", category: "Compliance", question: "Does the vendor hold ISO 27001 certification?", type: "boolean", required: false },
      { id: "q-12", category: "Data Protection", question: "Provide evidence of encryption implementation.", type: "evidence", required: true },
    ],
  },
  {
    id: "qt-caiq",
    name: "Consensus Assessment Initiative Questionnaire (CAIQ)",
    type: "caiq",
    framework: "CSA CCM",
    totalQuestions: 10,
    version: 1,
    createdAt: nowIso(),
    questions: [
      { id: "c-1", category: "IAM", question: "Does the vendor support identity federation?", type: "boolean", required: true, controlId: "IAM-01", framework: "CSA CCM" },
      { id: "c-2", category: "IAM", question: "Are passwords hashed with a strong algorithm?", type: "boolean", required: true, controlId: "IAM-02", framework: "CSA CCM" },
      { id: "c-3", category: "DSP", question: "Does the vendor perform data classification?", type: "boolean", required: true, controlId: "DSP-01", framework: "CSA CCM" },
      { id: "c-4", category: "DSP", question: "What data retention policy does the vendor follow?", type: "text", required: true },
      { id: "c-5", category: "SEF", question: "Does the vendor encrypt data in transit?", type: "boolean", required: true, controlId: "SEF-04", framework: "CSA CCM" },
      { id: "c-6", category: "SEF", question: "Does the vendor encrypt data at rest?", type: "boolean", required: true, controlId: "SEF-05", framework: "CSA CCM" },
      { id: "c-7", category: "IVS", question: "Does the vendor perform regular infrastructure vulnerability assessments?", type: "boolean", required: true, controlId: "IVS-01", framework: "CSA CCM" },
      { id: "c-8", category: "LOG", question: "Are audit logs retained for at least 90 days?", type: "boolean", required: true, controlId: "LOG-01", framework: "CSA CCM" },
      { id: "c-9", category: "BCR", question: "Does the vendor have a disaster recovery plan?", type: "boolean", required: true, controlId: "BCR-01", framework: "CSA CCM" },
      { id: "c-10", category: "STA", question: "Does the vendor provide security awareness training?", type: "boolean", required: true, controlId: "STA-01", framework: "CSA CCM" },
    ],
  },
  {
    id: "qt-custom-basic",
    name: "Custom Basic Assessment",
    type: "custom",
    framework: "Custom",
    totalQuestions: 8,
    version: 1,
    createdAt: nowIso(),
    questions: [
      { id: "x-1", category: "General", question: "Provide a description of the services provided.", type: "text", required: true },
      { id: "x-2", category: "General", question: "What is the vendor's annual revenue?", type: "text", required: false },
      { id: "x-3", category: "Security", question: "Does the vendor have cyber insurance?", type: "boolean", required: true },
      { id: "x-4", category: "Security", question: "Has the vendor experienced a data breach in the last 3 years?", type: "boolean", required: true },
      { id: "x-5", category: "Security", question: "Describe the vendor's security program.", type: "text", required: true },
      { id: "x-6", category: "Compliance", question: "What compliance frameworks does the vendor adhere to?", type: "text", required: true },
      { id: "x-7", category: "Operations", question: "What is the vendor's SLA commitment?", type: "text", required: true },
      { id: "x-8", category: "Financial", question: "Provide audited financial statements for the last 2 years.", type: "evidence", required: false },
    ],
  },
];

// ─── VendorRiskManagement ──────────────────────────────────────────────

export class VendorRiskManagement {
  private vendors: Map<string, Vendor> = new Map();
  private riskScores: Map<string, VendorRiskScore> = new Map();
  private assessments: Map<string, VendorAssessment> = new Map();
  private monitoring: Map<string, VendorMonitoring> = new Map();
  private riskRegisters: Map<string, VendorRiskRegisterEntry[]> = new Map();
  private questionnaireTemplates: Map<string, QuestionnaireTemplate> = new Map();
  private alerts: VendorAlert[] = [];

  constructor() {
    for (const qt of QUESTIONNAIRE_TEMPLATES) {
      this.questionnaireTemplates.set(qt.id, { ...qt });
    }
  }

  // ─── Vendor CRUD ─────────────────────────────────────────────────

  createVendor(input: {
    name: string;
    domain: string;
    description: string;
    categories: string[];
    contacts?: VendorContact[];
    contracts?: VendorContract[];
  }): Vendor {
    const id = newId();
    const now = nowIso();

    const vendor: Vendor = {
      id,
      name: input.name,
      domain: input.domain,
      description: input.description,
      status: "prospect",
      tier: "low",
      overallScore: 0,
      categories: input.categories,
      contacts: input.contacts ?? [],
      contracts: input.contracts ?? [],
      documents: [],
      createdAt: now,
      updatedAt: now,
    };

    this.vendors.set(id, vendor);
    return vendor;
  }

  getVendor(id: string): Vendor | undefined {
    return this.vendors.get(id);
  }

  listVendors(): Vendor[] {
    return Array.from(this.vendors.values());
  }

  updateVendorStatus(id: string, status: VendorStatus): Vendor {
    const vendor = this.vendors.get(id);
    if (!vendor) throw new Error(`Vendor ${id} not found`);
    vendor.status = status;
    vendor.updatedAt = nowIso();
    if (status === "onboarding") vendor.onboardedAt = nowIso();
    return vendor;
  }

  deleteVendor(id: string): boolean {
    return this.vendors.delete(id);
  }

  // ─── Onboarding ───────────────────────────────────────────────────

  onboardVendor(vendorId: string): Vendor {
    const vendor = this.vendors.get(vendorId);
    if (!vendor) throw new Error(`Vendor ${vendorId} not found`);

    vendor.status = "onboarding";
    vendor.onboardedAt = nowIso();
    vendor.updatedAt = nowIso();

    this.monitoring.set(vendorId, {
      vendorId,
      enabled: true,
      frequencyDays: this.getMonitoringFrequency(vendor.tier),
      nextCheckAt: this.addDays(nowIso(), this.getMonitoringFrequency(vendor.tier)),
      alerts: [],
      trend: "stable",
    });

    return vendor;
  }

  private getMonitoringFrequency(tier: VendorTier): number {
    switch (tier) {
      case "critical": return 30;
      case "high": return 60;
      case "medium": return 90;
      case "low": return 180;
    }
  }

  private addDays(isoDate: string, days: number): string {
    const d = new Date(isoDate);
    d.setDate(d.getDate() + days);
    return d.toISOString();
  }

  // ─── Contacts & Documents ────────────────────────────────────────

  addContact(vendorId: string, contact: Omit<VendorContact, "id">): VendorContact {
    const vendor = this.vendors.get(vendorId);
    if (!vendor) throw new Error(`Vendor ${vendorId} not found`);

    const newContact: VendorContact = { id: newId(), ...contact };
    vendor.contacts.push(newContact);
    vendor.updatedAt = nowIso();
    return newContact;
  }

  addDocument(vendorId: string, doc: Omit<VendorDocument, "id" | "uploadedAt">): VendorDocument {
    const vendor = this.vendors.get(vendorId);
    if (!vendor) throw new Error(`Vendor ${vendorId} not found`);

    const newDoc: VendorDocument = { id: newId(), uploadedAt: nowIso(), ...doc };
    vendor.documents.push(newDoc);
    vendor.updatedAt = nowIso();
    return newDoc;
  }

  addContract(vendorId: string, contract: Omit<VendorContract, "id">): VendorContract {
    const vendor = this.vendors.get(vendorId);
    if (!vendor) throw new Error(`Vendor ${vendorId} not found`);

    const newContract: VendorContract = { id: newId(), ...contract };
    vendor.contracts.push(newContract);
    vendor.updatedAt = nowIso();
    return newContract;
  }

  // ─── Risk Scoring (4-factor model) ───────────────────────────────

  calculateRiskScore(vendorId: string, factors: Array<{ category: RiskFactor["category"]; name: string; score: number; weight: number; evidence: string; details: string }>): VendorRiskScore {
    const vendor = this.vendors.get(vendorId);
    if (!vendor) throw new Error(`Vendor ${vendorId} not found`);

    const riskFactors: RiskFactor[] = factors.map((f) => ({
      id: newId(),
      ...f,
    }));

    const categoryScores: Record<string, { total: number; weight: number }> = {};
    for (const f of riskFactors) {
      if (!categoryScores[f.category]) categoryScores[f.category] = { total: 0, weight: 0 };
      categoryScores[f.category].total += f.score * f.weight;
      categoryScores[f.category].weight += f.weight;
    }

    const avg = (cat: string): number => {
      const c = categoryScores[cat];
      return c ? c.total / c.weight : 0;
    };

    const cybersecurityScore = avg("cybersecurity");
    const complianceScore = avg("compliance");
    const operationalScore = avg("operational");
    const financialScore = avg("financial");
    const overallScore = (cybersecurityScore * 0.35 + complianceScore * 0.30 + operationalScore * 0.20 + financialScore * 0.15);

    const tier = computeTier(overallScore);

    const riskScore: VendorRiskScore = {
      vendorId,
      cybersecurityScore: Math.round(cybersecurityScore * 100) / 100,
      complianceScore: Math.round(complianceScore * 100) / 100,
      operationalScore: Math.round(operationalScore * 100) / 100,
      financialScore: Math.round(financialScore * 100) / 100,
      overallScore: Math.round(overallScore * 100) / 100,
      tier,
      calculatedAt: nowIso(),
      factors: riskFactors,
    };

    this.riskScores.set(vendorId, riskScore);
    vendor.overallScore = riskScore.overallScore;
    vendor.tier = tier;
    vendor.lastAssessedAt = nowIso();
    vendor.updatedAt = nowIso();

    return riskScore;
  }

  getRiskScore(vendorId: string): VendorRiskScore | undefined {
    return this.riskScores.get(vendorId);
  }

  // ─── Questionnaire Templates ─────────────────────────────────────

  getQuestionnaireTemplates(): QuestionnaireTemplate[] {
    return Array.from(this.questionnaireTemplates.values());
  }

  getQuestionnaireByType(type: QuestionnaireType): QuestionnaireTemplate[] {
    return Array.from(this.questionnaireTemplates.values()).filter((t) => t.type === type);
  }

  // ─── Assessments ──────────────────────────────────────────────────

  createAssessment(vendorId: string, questionnaireId: string): VendorAssessment {
    const vendor = this.vendors.get(vendorId);
    if (!vendor) throw new Error(`Vendor ${vendorId} not found`);

    const qt = this.questionnaireTemplates.get(questionnaireId);
    if (!qt) throw new Error(`Questionnaire template ${questionnaireId} not found`);

    const assessment: VendorAssessment = {
      id: newId(),
      vendorId,
      questionnaireId,
      questionnaireType: qt.type,
      status: "pending",
      responses: {},
      findings: [],
      score: 0,
      expiresAt: this.addDays(nowIso(), 365),
      createdAt: nowIso(),
    };

    this.assessments.set(assessment.id, assessment);
    return assessment;
  }

  submitAssessmentResponse(assessmentId: string, responses: Record<string, string>): VendorAssessment {
    const assessment = this.assessments.get(assessmentId);
    if (!assessment) throw new Error(`Assessment ${assessmentId} not found`);

    assessment.responses = responses;
    assessment.status = "completed";
    assessment.completedAt = nowIso();
    assessment.startedAt = assessment.startedAt ?? nowIso();

    const findings = this.evaluateAssessment(assessment);
    assessment.findings = findings;

    const severityWeights: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1 };
    const totalSeverity = findings.reduce((sum, f) => sum + severityWeights[f.severity], 0);
    const maxPossible = findings.length * 4;
    assessment.score = maxPossible > 0 ? Math.round(((maxPossible - totalSeverity) / maxPossible) * 100) : 100;

    const vendor = this.vendors.get(assessment.vendorId);
    if (vendor) vendor.lastAssessedAt = nowIso();

    return assessment;
  }

  private evaluateAssessment(assessment: VendorAssessment): AssessmentFinding[] {
    const findings: AssessmentFinding[] = [];
    const qt = this.questionnaireTemplates.get(assessment.questionnaireId);
    if (!qt) return findings;

    for (const q of qt.questions) {
      const response = assessment.responses[q.id];
      if (q.type === "boolean" && response === "false") {
        findings.push({
          id: newId(),
          severity: q.required ? "high" : "medium",
          category: q.category,
          questionId: q.id,
          description: `Negative response to: ${q.question}`,
          controlId: q.controlId,
          remediation: `Address: ${q.question}`,
        });
      }
    }

    return findings;
  }

  getAssessments(vendorId: string): VendorAssessment[] {
    return Array.from(this.assessments.values()).filter((a) => a.vendorId === vendorId);
  }

  // ─── Continuous Monitoring ────────────────────────────────────────

  getMonitoring(vendorId: string): VendorMonitoring | undefined {
    return this.monitoring.get(vendorId);
  }

  runMonitoringCheck(vendorId: string): VendorMonitoring {
    const mon = this.monitoring.get(vendorId);
    if (!mon) throw new Error(`No monitoring configured for vendor ${vendorId}`);

    const vendor = this.vendors.get(vendorId);
    const previousScore = mon.previousScore;
    const currentScore = vendor?.overallScore ?? 0;

    if (previousScore !== undefined) {
      const diff = currentScore - previousScore;
      if (diff < -10) {
        mon.trend = "degrading";
        this.addAlert(vendorId, "score_degradation", "high", `Risk score decreased by ${Math.abs(Math.round(diff))} points`);
      } else if (diff > 10) {
        mon.trend = "improving";
      } else {
        mon.trend = "stable";
      }
    }

    mon.previousScore = currentScore;
    mon.lastCheckedAt = nowIso();
    mon.nextCheckAt = this.addDays(nowIso(), mon.frequencyDays);
    mon.alerts = this.alerts.filter((a) => a.vendorId === vendorId);

    return mon;
  }

  // ─── Alerts ───────────────────────────────────────────────────────

  addAlert(vendorId: string, type: VendorAlert["type"], severity: VendorAlert["severity"], message: string): VendorAlert {
    const alert: VendorAlert = {
      id: newId(),
      vendorId,
      type,
      severity,
      message,
      details: {},
      detectedAt: nowIso(),
      acknowledged: false,
    };
    this.alerts.push(alert);
    return alert;
  }

  acknowledgeAlert(alertId: string, acknowledgedBy: string): VendorAlert | undefined {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (alert) {
      alert.acknowledged = true;
      alert.acknowledgedAt = nowIso();
      alert.acknowledgedBy = acknowledgedBy;
    }
    return alert;
  }

  getActiveAlerts(vendorId?: string): VendorAlert[] {
    const unacknowledged = this.alerts.filter((a) => !a.acknowledged);
    if (vendorId) return unacknowledged.filter((a) => a.vendorId === vendorId);
    return unacknowledged;
  }

  // ─── Risk Register ───────────────────────────────────────────────

  addRiskRegisterEntry(vendorId: string, input: { description: string; category: string; likelihood: number; impact: number; mitigations: string[]; owner: string }): VendorRiskRegisterEntry {
    const vendor = this.vendors.get(vendorId);
    if (!vendor) throw new Error(`Vendor ${vendorId} not found`);

    const entry: VendorRiskRegisterEntry = {
      id: newId(),
      vendorId,
      riskId: `RR-${Math.floor(Math.random() * 9000) + 1000}`,
      description: input.description,
      category: input.category,
      likelihood: input.likelihood,
      impact: input.impact,
      riskScore: input.likelihood * input.impact,
      mitigations: input.mitigations,
      status: "open",
      owner: input.owner,
      identifiedAt: nowIso(),
      createdAt: nowIso(),
      updatedAt: nowIso(),
    };

    const register = this.riskRegisters.get(vendorId) ?? [];
    register.push(entry);
    this.riskRegisters.set(vendorId, register);

    return entry;
  }

  getRiskRegister(vendorId: string): VendorRiskRegisterEntry[] {
    return this.riskRegisters.get(vendorId) ?? [];
  }

  updateRiskRegisterEntry(vendorId: string, entryId: string, updates: Partial<Pick<VendorRiskRegisterEntry, "status" | "mitigations" | "likelihood" | "impact">>): VendorRiskRegisterEntry | undefined {
    const entries = this.riskRegisters.get(vendorId);
    if (!entries) return undefined;

    const entry = entries.find((e) => e.id === entryId);
    if (!entry) return undefined;

    if (updates.status) entry.status = updates.status;
    if (updates.mitigations) entry.mitigations = updates.mitigations;
    if (updates.likelihood !== undefined) {
      entry.likelihood = updates.likelihood;
      entry.riskScore = entry.likelihood * entry.impact;
    }
    if (updates.impact !== undefined) {
      entry.impact = updates.impact;
      entry.riskScore = entry.likelihood * entry.impact;
    }
    entry.updatedAt = nowIso();

    return entry;
  }

  // ─── Dashboard ────────────────────────────────────────────────────

  getDashboard(): VendorRiskDashboard {
    const vendors = this.listVendors();
    const now = new Date();

    const byTier: Record<VendorTier, number> = { critical: 0, high: 0, medium: 0, low: 0 };
    const byStatus: Record<VendorStatus, number> = {
      prospect: 0,
      onboarding: 0,
      active: 0,
      monitoring: 0,
      offboarding: 0,
      terminated: 0,
    };

    let totalScore = 0;
    let highRiskVendors = 0;
    let pendingAssessments = 0;
    let overdueAssessments = 0;
    let expiringDocuments30Days = 0;

    for (const v of vendors) {
      byTier[v.tier]++;
      byStatus[v.status]++;
      totalScore += v.overallScore;
      if (v.overallScore >= 60) highRiskVendors++;

      const vendorAssessments = this.getAssessments(v.id);
      pendingAssessments += vendorAssessments.filter((a) => a.status === "pending").length;
      overdueAssessments += vendorAssessments.filter((a) => a.status === "completed" && a.expiresAt && new Date(a.expiresAt) < now).length;

      const thirtyDaysFromNow = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
      expiringDocuments30Days += v.documents.filter((d) => d.expiresAt && new Date(d.expiresAt) < thirtyDaysFromNow).length;
    }

    const activeAlerts = this.getActiveAlerts().length;
    const criticalAlerts = this.alerts.filter((a) => !a.acknowledged && a.severity === "critical").length;

    return {
      totalVendors: vendors.length,
      byTier,
      byStatus,
      averageRiskScore: vendors.length > 0 ? Math.round((totalScore / vendors.length) * 100) / 100 : 0,
      highRiskVendors,
      pendingAssessments,
      overdueAssessments,
      activeAlerts,
      criticalAlerts,
      expiringDocuments30Days,
      recentRiskChanges: [],
    };
  }

  // ─── Search & Filter ──────────────────────────────────────────────

  searchVendors(filter: VendorSearchFilter): Vendor[] {
    let results = Array.from(this.vendors.values());

    if (filter.query) {
      const q = filter.query.toLowerCase();
      results = results.filter(
        (v) =>
          v.name.toLowerCase().includes(q) ||
          v.domain.toLowerCase().includes(q) ||
          v.description.toLowerCase().includes(q) ||
          v.categories.some((c) => c.toLowerCase().includes(q))
      );
    }
    if (filter.status && filter.status.length > 0) {
      results = results.filter((v) => filter.status!.includes(v.status));
    }
    if (filter.tier && filter.tier.length > 0) {
      results = results.filter((v) => filter.tier!.includes(v.tier));
    }
    if (filter.categories && filter.categories.length > 0) {
      results = results.filter((v) => filter.categories!.some((c) => v.categories.includes(c)));
    }
    if (filter.minScore !== undefined) {
      results = results.filter((v) => v.overallScore >= filter.minScore!);
    }
    if (filter.maxScore !== undefined) {
      results = results.filter((v) => v.overallScore <= filter.maxScore!);
    }

    return results;
  }
}

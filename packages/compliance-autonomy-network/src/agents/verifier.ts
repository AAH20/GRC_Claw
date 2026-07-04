import { randomBytes } from "node:crypto";
import { BaseAgent } from "./base-agent.js";
import type {
  SwarmTask,
  SwarmResult,
  VerificationResult,
  ControlStatus,
  EvidenceItem,
  ComplianceFramework,
} from "../types.js";

// ============================================================================
// Verifier – post-remediation verification agent
// ============================================================================

export class Verifier extends BaseAgent {
  private verificationHistory: Map<string, VerificationResult[]> = new Map();

  constructor(signingKey: string = randomBytes(32).toString("hex")) {
    super(
      "verifier",
      "Verification Agent",
      "1.0.0",
      [
        {
          name: "verify-remediation",
          frameworks: ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS", "HIPAA", "GDPR", "CCPA", "SOX", "FedRAMP", "Custom"],
          confidenceLevel: 0.93,
        },
        {
          name: "verify-evidence-integrity",
          frameworks: ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS", "HIPAA", "GDPR"],
          confidenceLevel: 0.97,
        },
      ],
      signingKey,
    );
  }

  protected async doExecute(task: SwarmTask): Promise<SwarmResult["output"]> {
    const controlStatuses = (task.input.customParameters?.controlStatuses as ControlStatus[]) ?? [];
    const evidence = (task.input.customParameters?.evidence as EvidenceItem[]) ?? [];

    const verificationResults = await this.verifyControls(task.framework, controlStatuses, evidence, task);
    this.verificationHistory.set(task.id, verificationResults);

    const passed = verificationResults.filter((r) => r.passed).length;
    const failed = verificationResults.filter((r) => !r.passed).length;
    const total = verificationResults.length;

    const evidenceIntegrityResults = await this.verifyEvidenceIntegrity(evidence);
    const allEvidenceValid = evidenceIntegrityResults.every((r) => r.passed);

    return {
      verificationResults: [
        ...verificationResults,
        ...evidenceIntegrityResults,
      ],
      summary: `Verification complete: ${passed}/${total} control checks passed, ${failed} failed. Evidence integrity: ${allEvidenceValid ? "VALID" : "COMPROMISED"}.`,
      recommendations: this.generateVerificationRecommendations(verificationResults, evidenceIntegrityResults, task.framework),
    };
  }

  // ------------------------------------------------------------------
  // Verification logic
  // ------------------------------------------------------------------

  private async verifyControls(
    framework: ComplianceFramework,
    controlStatuses: ControlStatus[],
    evidence: EvidenceItem[],
    task: SwarmTask,
  ): Promise<VerificationResult[]> {
    const results: VerificationResult[] = [];

    for (const status of controlStatuses) {
      const controlResults = await this.verifySingleControl(framework, status, evidence, task);
      results.push(...controlResults);
    }

    if (results.length === 0 && controlStatuses.length === 0) {
      results.push(
        this.createVerificationResult(
          framework,
          "general",
          "no-controls",
          true,
          "N/A",
          "N/A",
          task.assignedAgent ?? "unknown",
        ),
      );
    }

    return results;
  }

  private async verifySingleControl(
    framework: ComplianceFramework,
    status: ControlStatus,
    evidence: EvidenceItem[],
    task: SwarmTask,
  ): Promise<VerificationResult[]> {
    const results: VerificationResult[] = [];

    // Check 1: Compliance status verification
    const complianceCheck = this.verifyComplianceStatus(status);
    results.push(
      this.createVerificationResult(
        framework,
        status.controlId,
        "compliance-status",
        complianceCheck.passed,
        complianceCheck.expected,
        complianceCheck.actual,
        task.assignedAgent ?? "unknown",
      ),
    );

    // Check 2: Evidence presence verification
    const controlEvidence = evidence.filter((e) => e.controlId === status.controlId);
    const evidenceCheck = this.verifyEvidencePresence(status.controlId, controlEvidence);
    results.push(
      this.createVerificationResult(
        framework,
        status.controlId,
        "evidence-presence",
        evidenceCheck.passed,
        evidenceCheck.expected,
        evidenceCheck.actual,
        task.assignedAgent ?? "unknown",
      ),
    );

    // Check 3: Evidence integrity verification
    if (controlEvidence.length > 0) {
      const integrityCheck = this.verifyEvidenceIntegrityForControl(controlEvidence);
      results.push(
        this.createVerificationResult(
          framework,
          status.controlId,
          "evidence-integrity",
          integrityCheck.passed,
          integrityCheck.expected,
          integrityCheck.actual,
          task.assignedAgent ?? "unknown",
        ),
      );
    }

    // Check 4: Control effectiveness verification
    const effectivenessCheck = this.verifyControlEffectiveness(status);
    results.push(
      this.createVerificationResult(
        framework,
        status.controlId,
        "control-effectiveness",
        effectivenessCheck.passed,
        effectivenessCheck.expected,
        effectivenessCheck.actual,
        task.assignedAgent ?? "unknown",
      ),
    );

    return results;
  }

  private verifyComplianceStatus(status: ControlStatus): { passed: boolean; expected: string; actual: string } {
    const isCompliant = status.status === "compliant";
    return {
      passed: isCompliant,
      expected: "compliant",
      actual: status.status,
    };
  }

  private verifyEvidencePresence(controlId: string, evidence: EvidenceItem[]): { passed: boolean; expected: string; actual: string } {
    const hasEvidence = evidence.length > 0;
    return {
      passed: hasEvidence,
      expected: ">=1 evidence item(s)",
      actual: `${evidence.length} evidence item(s)`,
    };
  }

  private verifyEvidenceIntegrityForControl(evidence: EvidenceItem[]): { passed: boolean; expected: string; actual: string } {
    const invalidEvidence = evidence.filter((e) => {
      const computedHash = this.hash(e.content);
      return computedHash !== e.contentHash;
    });

    return {
      passed: invalidEvidence.length === 0,
      expected: "0 invalid evidence items",
      actual: `${invalidEvidence.length} invalid evidence item(s)`,
    };
  }

  private verifyControlEffectiveness(status: ControlStatus): { passed: boolean; expected: string; actual: string } {
    const isEffective = status.confidence >= 0.8 && status.status === "compliant";
    return {
      passed: isEffective,
      expected: "confidence >= 0.8 and status compliant",
      actual: `confidence ${status.confidence.toFixed(3)}, status ${status.status}`,
    };
  }

  private async verifyEvidenceIntegrity(evidence: EvidenceItem[]): Promise<VerificationResult[]> {
    const results: VerificationResult[] = [];
    const invalidEvidence = evidence.filter((e) => {
      const computedHash = this.hash(e.content);
      return computedHash !== e.contentHash;
    });

    results.push(
      this.createVerificationResult(
        evidence[0]?.framework ?? "SOC2",
        "evidence-batch",
        "batch-integrity",
        invalidEvidence.length === 0,
        `0/${evidence.length} invalid`,
        `${invalidEvidence.length}/${evidence.length} invalid`,
        this.id,
      ),
    );

    return results;
  }

  private createVerificationResult(
    framework: ComplianceFramework,
    controlId: string,
    checkType: string,
    passed: boolean,
    expected: string,
    actual: string,
    verifiedBy: string,
  ): VerificationResult {
    return {
      controlId,
      framework,
      checkType,
      passed,
      expected,
      actual,
      verifiedAt: new Date().toISOString(),
      verifiedBy,
    };
  }

  private generateVerificationRecommendations(
    controlResults: VerificationResult[],
    integrityResults: VerificationResult[],
    framework: ComplianceFramework,
  ): string[] {
    const recs: string[] = [];

    const failed = controlResults.filter((r) => !r.passed);
    const passed = controlResults.filter((r) => r.passed);

    if (failed.length === 0 && controlResults.length > 0) {
      recs.push(`All ${controlResults.length} verification check(s) passed for ${framework}`);
    }

    if (failed.length > 0) {
      recs.push(`${failed.length} verification check(s) failed – remediation not effective or incomplete`);

      const complianceFails = failed.filter((r) => r.checkType === "compliance-status");
      if (complianceFails.length > 0) {
        recs.push(`${complianceFails.length} control(s) still non-compliant after remediation – review remediation approach`);
      }

      const evidenceFails = failed.filter((r) => r.checkType === "evidence-presence");
      if (evidenceFails.length > 0) {
        recs.push(`${evidenceFails.length} control(s) missing evidence – collect required evidence artifacts`);
      }

      const integrityFails = failed.filter((r) => r.checkType === "evidence-integrity");
      if (integrityFails.length > 0) {
        recs.push(`${integrityFails.length} control(s) have evidence integrity issues – investigate potential tampering`);
      }
    }

    const failedIntegrity = integrityResults.filter((r) => !r.passed);
    if (failedIntegrity.length > 0) {
      recs.push("CRITICAL: Evidence batch integrity check failed – investigate evidence chain");
    }

    if (passed.length > 0 && failed.length === 0) {
      recs.push("All controls verified as effective – ready for audit submission");
    }

    return recs;
  }

  getVerificationHistory(taskId: string): VerificationResult[] {
    return this.verificationHistory.get(taskId) ?? [];
  }
}

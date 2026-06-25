import type { FrameworkCode } from "../types.js";

export interface CICDConfig {
  framework: FrameworkCode;
  failOnSeverity: "critical" | "high" | "medium" | "low";
  maxScore: number;
}

export interface CICDResult {
  passed: boolean;
  score: number;
  findings: { rule: string; severity: string; file: string; line: number; message: string }[];
  gateName: string;
  framework: FrameworkCode;
  timestamp: string;
}

export class CICDComplianceGate {
  private config: CICDConfig;

  constructor(config: CICDConfig) {
    this.config = config;
  }

  async evaluate(changes: { files: string[]; content: Map<string, string> }): Promise<CICDResult> {
    const findings: { rule: string; severity: string; file: string; line: number; message: string }[] = [];

    for (const [file, content] of changes.content) {
      const lines = content.split("\n");
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.includes("password") && line.includes("=")) {
          findings.push({ rule: "HARDCODED_PASSWORD", severity: "critical", file, line: i + 1, message: "Hardcoded password detected" });
        }
        if (line.includes("md5") || line.includes("sha1")) {
          findings.push({ rule: "WEAK_CRYPTO", severity: "high", file, line: i + 1, message: "Weak cryptography detected" });
        }
      }
    }

    const criticalFindings = findings.filter((f) => f.severity === this.config.failOnSeverity);
    const passed = criticalFindings.length === 0;
    const score = Math.max(0, 100 - findings.length * 10);

    return {
      passed,
      score,
      findings,
      gateName: `grc-claw-${this.config.framework}`,
      framework: this.config.framework,
      timestamp: new Date().toISOString(),
    };
  }
}

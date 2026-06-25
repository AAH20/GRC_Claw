import type { ComplianceFinding, FrameworkCode } from "../types.js";

export interface GitHubPR {
  number: number;
  repo: string;
  title: string;
  body: string;
  files: GitHubFile[];
}

export interface GitHubFile {
  filename: string;
  patch: string;
  additions: number;
  deletions: number;
}

export class GitHubPRReviewer {
  private frameworks: FrameworkCode[];

  constructor(frameworks: FrameworkCode[] = ["iso27001", "soc2"]) {
    this.frameworks = frameworks;
  }

  async reviewPR(pr: GitHubPR): Promise<{
    findings: ComplianceFinding[];
    summary: string;
    status: "approved" | "changes_requested" | "commented";
  }> {
    const findings: ComplianceFinding[] = [];

    for (const file of pr.files) {
      const fileFindings = await this.analyzeFile(file);
      findings.push(...fileFindings);
    }

    const criticalCount = findings.filter((f) => f.severity === "critical").length;
    const highCount = findings.filter((f) => f.severity === "high").length;

    let status: "approved" | "changes_requested" | "commented" = "approved";
    if (criticalCount > 0) status = "changes_requested";
    else if (highCount > 2) status = "changes_requested";
    else if (findings.length > 0) status = "commented";

    const summary = this.generateSummary(findings, criticalCount, highCount);
    return { findings, summary, status };
  }

  private async analyzeFile(file: GitHubFile): Promise<ComplianceFinding[]> {
    const findings: ComplianceFinding[] = [];
    const lines = file.patch.split("\n");

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.startsWith("-")) continue;

      const secretFindings = this.detectHardcodedSecrets(file.filename, i, line);
      findings.push(...secretFindings);

      const cryptoFindings = this.detectWeakCrypto(file.filename, i, line);
      findings.push(...cryptoFindings);

      const sqlFindings = this.detectSQLInjection(file.filename, i, line);
      findings.push(...sqlFindings);
    }

    return findings;
  }

  private detectHardcodedSecrets(file: string, line: number, content: string): ComplianceFinding[] {
    const patterns = [
      { regex: /(?:api_key|apikey|secret|password|token)\s*[:=]\s*["'][^"']+["']/i, rule: "HARDCODED_SECRET", framework: "iso27001" as FrameworkCode, control: "A.5.1" },
      { regex: /(?:AKIA|ASIA)[A-Z0-9]{16}/, rule: "AWS_KEY_EXPOSED", framework: "iso27001" as FrameworkCode, control: "A.5.1" },
      { regex: /-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----/, rule: "PRIVATE_KEY_EXPOSED", framework: "soc2" as FrameworkCode, control: "CC6.1" },
    ];

    return patterns
      .filter((p) => p.regex.test(content))
      .map((p) => ({
        file,
        line,
        severity: "critical" as const,
        rule: p.rule,
        message: `Hardcoded secret detected: ${p.rule}`,
        framework: p.framework,
        controlId: p.control,
        autoFix: "Use environment variables or secret manager",
      }));
  }

  private detectWeakCrypto(file: string, line: number, content: string): ComplianceFinding[] {
    const patterns = [
      { regex: /(?:md5|sha1)\s*\(/i, rule: "WEAK_HASH", framework: "iso27001" as FrameworkCode, control: "A.14.1" },
      { regex: /DES\s*\(/i, rule: "WEAK_ENCRYPTION", framework: "pci-dss" as FrameworkCode, control: "3.4" },
    ];

    return patterns
      .filter((p) => p.regex.test(content))
      .map((p) => ({
        file,
        line,
        severity: "high" as const,
        rule: p.rule,
        message: `Weak cryptography detected: ${p.rule}`,
        framework: p.framework,
        controlId: p.control,
        autoFix: "Use SHA-256+ or AES-256",
      }));
  }

  private detectSQLInjection(file: string, line: number, content: string): ComplianceFinding[] {
    const patterns = [
      { regex: /query\s*\(\s*["`].*\$\{.*\}.*["`]/i, rule: "SQL_INJECTION", framework: "pci-dss" as FrameworkCode, control: "6.5" },
    ];

    return patterns
      .filter((p) => p.regex.test(content))
      .map((p) => ({
        file,
        line,
        severity: "high" as const,
        rule: p.rule,
        message: "Potential SQL injection: use parameterized queries",
        framework: p.framework,
        controlId: p.control,
        autoFix: "Use parameterized queries instead of string interpolation",
      }));
  }

  private generateSummary(findings: ComplianceFinding[], critical: number, high: number): string {
    if (findings.length === 0) return "No compliance issues found. PR approved.";
    return `Found ${findings.length} compliance issues: ${critical} critical, ${high} high. ${critical > 0 ? "Changes requested." : "Please review findings."}`;
  }
}

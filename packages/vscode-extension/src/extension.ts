// GRC_Claw VS Code Extension — shift-left compliance in the editor
// Every scan produces evidence attached to the org's proof ledger.

import * as vscode from "vscode";
import * as path from "path";
import * as cp from "child_process";

// ─── Compliance scan rules (mirrors CLI src/index.ts) ─────────────────────────

interface ComplianceFinding {
  line: number;
  col: number;
  severity: "critical" | "high" | "medium" | "low";
  ruleId: string;
  controlId: string;
  message: string;
  fix?: string;
}

const SCAN_RULES: Array<{
  id: string;
  controlId: string;
  pattern: RegExp;
  severity: "critical" | "high" | "medium" | "low";
  message: string;
  fix: string;
}> = [
  { id: "hardcoded-secret", controlId: "A.9.4.3", pattern: /(?:password|secret|api_?key|token)\s*=\s*["'][^"']{8,}["']/i, severity: "critical", message: "Hardcoded secret detected — move to environment variable", fix: "Use process.env.SECRET_NAME or a secrets manager" },
  { id: "weak-crypto-md5", controlId: "A.10.1.1", pattern: /createHash\(['"]md5['"]\)|md5\s*\(/i, severity: "high", message: "MD5 is cryptographically broken — use SHA-256 or SHA-3", fix: "Replace with createHash('sha256')" },
  { id: "weak-crypto-sha1", controlId: "A.10.1.1", pattern: /createHash\(['"]sha1['"]\)|\.sha1\s*\(/i, severity: "high", message: "SHA-1 is deprecated — use SHA-256", fix: "Replace with createHash('sha256')" },
  { id: "http-in-prod", controlId: "A.13.2.3", pattern: /http:\/\/(?!localhost|127\.0\.0\.1|0\.0\.0\.0)/i, severity: "high", message: "HTTP URL in code — use HTTPS for all external connections", fix: "Replace http:// with https://" },
  { id: "sql-injection", controlId: "A.14.2.5", pattern: /`\s*SELECT.*\$\{|query\s*\+\s*(?:req|input|user)/i, severity: "critical", message: "Potential SQL injection — use parameterized queries", fix: "Use parameterized queries: db.query('SELECT ... WHERE id = ?', [id])" },
  { id: "mfa-bypass", controlId: "A.9.4.2", pattern: /skip.*mfa|bypass.*auth|mfa.*disabled|auth.*skip/i, severity: "critical", message: "MFA bypass pattern detected", fix: "Remove auth bypass; enforce MFA on all authentication paths" },
  { id: "eval-usage", controlId: "A.14.2.5", pattern: /\beval\s*\(|\bnew\s+Function\s*\(/i, severity: "high", message: "eval() / new Function() enables code injection", fix: "Remove eval(); use JSON.parse() for data or static function definitions" },
  { id: "cors-wildcard", controlId: "A.13.1.3", pattern: /Access-Control-Allow-Origin['":\s]+['"]\*['"]/i, severity: "medium", message: "CORS wildcard (*) allows any origin", fix: "Restrict CORS to specific allowed origins" },
  { id: "sensitive-logging", controlId: "A.12.4.1", pattern: /console\.log\s*\(.*(?:password|token|secret|key|ssn|credit)/i, severity: "medium", message: "Sensitive data in log statement", fix: "Remove sensitive fields from logs or redact them" },
  { id: "missing-hsts", controlId: "A.13.2.3", pattern: /setHeader\s*\(.*Content-Type.*\)(?![\s\S]{0,500}Strict-Transport)/i, severity: "low", message: "HTTP Strict-Transport-Security header may be missing", fix: "Add: res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')" },
  { id: "rsa-weak", controlId: "PQC-FIPS203", pattern: /RSA[._]?(?:generate|create|key).*(?:1024|2048)/i, severity: "medium", message: "RSA key size should be ≥4096 bits; plan migration to ML-KEM (FIPS 203)", fix: "Upgrade to RSA-4096 now; migrate to ML-KEM per NIST FIPS 203 by 2030" },
  { id: "ecdh-usage", controlId: "PQC-FIPS203", pattern: /\b(?:ECDH|ecdh)\b/i, severity: "low", message: "ECDH is quantum-vulnerable — plan migration to ML-KEM (FIPS 203)", fix: "Plan ML-KEM migration per NIST PQC timeline (harvest-now-decrypt-later risk)" },
];

function scanText(text: string): ComplianceFinding[] {
  const lines = text.split("\n");
  const findings: ComplianceFinding[] = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const rule of SCAN_RULES) {
      const match = rule.pattern.exec(line);
      if (match) {
        findings.push({
          line: i,
          col: match.index,
          severity: rule.severity,
          ruleId: rule.id,
          controlId: rule.controlId,
          message: rule.message,
          fix: rule.fix,
        });
      }
    }
  }
  return findings;
}

// ─── Diagnostics collection ────────────────────────────────────────────────────

const diagCollection = vscode.languages.createDiagnosticCollection("grc-claw");

function severityToVscode(s: "critical" | "high" | "medium" | "low"): vscode.DiagnosticSeverity {
  if (s === "critical" || s === "high") return vscode.DiagnosticSeverity.Error;
  if (s === "medium") return vscode.DiagnosticSeverity.Warning;
  return vscode.DiagnosticSeverity.Information;
}

function runScanOnDocument(doc: vscode.TextDocument): void {
  const supported = [".ts", ".tsx", ".js", ".mjs", ".py", ".go", ".java", ".cs", ".rb", ".rs"];
  if (!supported.some((ext) => doc.fileName.endsWith(ext))) return;

  const findings = scanText(doc.getText());
  const diagnostics: vscode.Diagnostic[] = findings.map((f) => {
    const range = new vscode.Range(f.line, f.col, f.line, doc.lineAt(f.line).text.length);
    const diag = new vscode.Diagnostic(
      range,
      `[GRC ${f.controlId}] ${f.message}`,
      severityToVscode(f.severity),
    );
    diag.source = "GRC_Claw";
    diag.code = f.ruleId;
    if (f.fix) {
      (diag as vscode.Diagnostic & { hint?: string }).hint = f.fix;
    }
    return diag;
  });

  diagCollection.set(doc.uri, diagnostics);
  updateStatusBar(diagnostics);
}

// ─── Status bar ────────────────────────────────────────────────────────────────

let statusBarItem: vscode.StatusBarItem;

function updateStatusBar(diagnostics: vscode.Diagnostic[]): void {
  const critical = diagnostics.filter((d) => d.severity === vscode.DiagnosticSeverity.Error).length;
  const warn = diagnostics.filter((d) => d.severity === vscode.DiagnosticSeverity.Warning).length;
  if (critical > 0) {
    statusBarItem.text = `$(shield) GRC: ${critical} critical`;
    statusBarItem.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
    statusBarItem.tooltip = `${critical} critical compliance issues — click to view`;
  } else if (warn > 0) {
    statusBarItem.text = `$(shield) GRC: ${warn} warnings`;
    statusBarItem.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
    statusBarItem.tooltip = `${warn} compliance warnings`;
  } else {
    statusBarItem.text = `$(shield) GRC: Clean`;
    statusBarItem.backgroundColor = undefined;
    statusBarItem.tooltip = "No compliance issues detected";
  }
  statusBarItem.show();
}

// ─── Posture webview ──────────────────────────────────────────────────────────

async function fetchPosture(gatewayUrl: string, apiKey: string, a2zUrl: string, orgSlug: string): Promise<string> {
  try {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;

    // Try A2Z SOC verify endpoint first
    if (orgSlug && a2zUrl) {
      const res = await fetch(`${a2zUrl}/api/platform/verify/${orgSlug}/iso27001`);
      if (res.ok) {
        const data = await res.json() as Record<string, unknown>;
        return JSON.stringify(data, null, 2);
      }
    }

    // Fall back to gateway
    const res = await fetch(`${gatewayUrl}/api/assurance`, { headers });
    if (res.ok) return JSON.stringify(await res.json(), null, 2);
    return `{"error": "Could not fetch posture from ${gatewayUrl}"}`;
  } catch (e) {
    return `{"error": "${String(e)}"}`;
  }
}

function showPosturePanel(context: vscode.ExtensionContext, postureJson: string): void {
  const panel = vscode.window.createWebviewPanel(
    "grcPosture",
    "GRC Compliance Posture",
    vscode.ViewColumn.Beside,
    { enableScripts: false },
  );
  const posture = (() => { try { return JSON.parse(postureJson) as Record<string, unknown>; } catch { return {}; } })();
  panel.webview.html = `<!DOCTYPE html><html><head><style>
    body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); }
    h1 { color: var(--vscode-textLink-foreground); }
    pre { background: var(--vscode-editor-background); padding: 12px; border-radius: 4px; overflow: auto; font-size: 12px; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin: 2px; }
    .pass { background: #1a7340; color: #fff; } .fail { background: #8b1a1a; color: #fff; }
  </style></head><body>
  <h1>🛡️ GRC_Claw Compliance Posture</h1>
  <p>Powered by <strong>A2Z SOC</strong> — Last refreshed: ${new Date().toLocaleTimeString()}</p>
  <pre>${JSON.stringify(posture, null, 2)}</pre>
  </body></html>`;
}

// ─── Extension activation ─────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext): void {
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.command = "grc.scan";
  statusBarItem.text = "$(shield) GRC";
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);
  context.subscriptions.push(diagCollection);

  const cfg = () => vscode.workspace.getConfiguration("grc");

  // Scan active document
  context.subscriptions.push(
    vscode.commands.registerCommand("grc.scan", () => {
      const doc = vscode.window.activeTextEditor?.document;
      if (doc) runScanOnDocument(doc);
    }),
  );

  // Scan entire workspace
  context.subscriptions.push(
    vscode.commands.registerCommand("grc.scanWorkspace", async () => {
      const files = await vscode.workspace.findFiles("**/*.{ts,tsx,js,py,go,java,cs,rb,rs}", "**/node_modules/**");
      let total = 0;
      for (const file of files) {
        const doc = await vscode.workspace.openTextDocument(file);
        const findings = scanText(doc.getText());
        total += findings.length;
        if (findings.length > 0) {
          const diags = findings.map((f) => {
            const r = new vscode.Range(f.line, f.col, f.line, doc.lineAt(f.line).text.length);
            const d = new vscode.Diagnostic(r, `[GRC ${f.controlId}] ${f.message}`, severityToVscode(f.severity));
            d.source = "GRC_Claw";
            d.code = f.ruleId;
            return d;
          });
          diagCollection.set(file, diags);
        }
      }
      void vscode.window.showInformationMessage(`GRC_Claw: Scanned ${files.length} files — ${total} findings`);
    }),
  );

  // Show posture panel
  context.subscriptions.push(
    vscode.commands.registerCommand("grc.showPosture", async () => {
      const config = cfg();
      const postureJson = await fetchPosture(
        config.get<string>("gatewayUrl") ?? "http://localhost:18791",
        config.get<string>("apiKey") ?? "",
        config.get<string>("a2zSocUrl") ?? "https://a2zsoc.com",
        config.get<string>("orgSlug") ?? "",
      );
      showPosturePanel(context, postureJson);
    }),
  );

  // Open Trust Center
  context.subscriptions.push(
    vscode.commands.registerCommand("grc.openTrustCenter", () => {
      const config = cfg();
      const slug = config.get<string>("orgSlug");
      const base = config.get<string>("a2zSocUrl") ?? "https://a2zsoc.com";
      const url = slug ? `${base}/trust/${slug}` : `${base}/trust`;
      void vscode.env.openExternal(vscode.Uri.parse(url));
    }),
  );

  // PQC scan via CLI
  context.subscriptions.push(
    vscode.commands.registerCommand("grc.runPqcScan", () => {
      const terminal = vscode.window.createTerminal("GRC PQC Scan");
      terminal.show();
      terminal.sendText("npx @grc-claw/cli pqc-scan .");
    }),
  );

  // Auto-scan on save
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((doc) => {
      if (cfg().get<boolean>("enableOnSave") !== false) runScanOnDocument(doc);
    }),
  );

  // Scan current file on open
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) runScanOnDocument(editor.document);
    }),
  );

  // Initial scan if a file is open
  const activeDoc = vscode.window.activeTextEditor?.document;
  if (activeDoc) runScanOnDocument(activeDoc);
}

export function deactivate(): void {
  diagCollection.clear();
  diagCollection.dispose();
}

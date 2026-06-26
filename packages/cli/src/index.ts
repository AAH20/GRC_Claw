#!/usr/bin/env node
// @grc-claw/cli — The GRC_Claw command-line interface
// Usage: grc <command> [options]

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { resolve, join, extname } from 'node:path';
import { createHash } from 'node:crypto';

const VERSION = '1.0.0';

// ─── ANSI colors ─────────────────────────────────────────────────────────────
const c = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m',
};

function log(msg: string) { process.stdout.write(msg + '\n'); }
function info(msg: string) { log(`${c.cyan}ℹ${c.reset} ${msg}`); }
function success(msg: string) { log(`${c.green}✓${c.reset} ${msg}`); }
function warn(msg: string) { log(`${c.yellow}⚠${c.reset} ${msg}`); }
function error(msg: string) { log(`${c.red}✗${c.reset} ${msg}`); }
function bold(msg: string) { return `${c.bold}${msg}${c.reset}`; }
function dim(msg: string) { return `${c.dim}${msg}${c.reset}`; }

// ─── Compliance Rules (mirrors compliance-copilot PRReviewEngine) ─────────────
interface Finding {
  file: string;
  line: number;
  severity: 'error' | 'warning' | 'info';
  rule: string;
  message: string;
  framework: string;
  control: string;
  autoFixable: boolean;
  suggestion?: string;
}

const SCAN_RULES: Array<{
  id: string;
  name: string;
  pattern: RegExp;
  severity: 'error' | 'warning' | 'info';
  message: string;
  framework: string;
  control: string;
  suggestion?: string;
}> = [
  {
    id: 'no-hardcoded-secrets',
    name: 'Hardcoded Secrets',
    pattern: /(?:password|secret|api_key|apikey|access_token|private_key)\s*[:=]\s*['"][^'"]{8,}['"]/gi,
    severity: 'error',
    message: 'Hardcoded secret detected — use environment variables or a secrets manager',
    framework: 'SOC 2 / ISO 27001',
    control: 'CC6.1 / A.9.4.3',
    suggestion: 'Replace with process.env.SECRET_NAME and rotate the exposed credential immediately',
  },
  {
    id: 'no-mfa-bypass',
    name: 'MFA Bypass',
    pattern: /skip.*mfa|bypass.*mfa|disable.*2fa|mfa.*false|two_factor.*false/gi,
    severity: 'error',
    message: 'Potential MFA bypass detected',
    framework: 'ISO 27001 / NIST CSF',
    control: 'A.9.4.2 / PR.AC-7',
    suggestion: 'MFA must be enforced for all privileged operations per ISO 27001 A.9.4.2',
  },
  {
    id: 'no-weak-crypto',
    name: 'Weak Cryptography',
    pattern: /\b(?:md5|sha1|des|rc4|ecb)\b(?!\w)/gi,
    severity: 'error',
    message: 'Weak or deprecated cryptographic algorithm detected',
    framework: 'ISO 27001 / PCI DSS',
    control: 'A.10.1.1 / Req-3.4',
    suggestion: 'Use SHA-256 or stronger. For encryption: AES-256-GCM or ChaCha20-Poly1305',
  },
  {
    id: 'no-sql-injection',
    name: 'SQL Injection Risk',
    pattern: /`\s*SELECT[^`]*\$\{[^}]+\}[^`]*`|query\s*\(\s*['"`][^'"`]*\+/gi,
    severity: 'error',
    message: 'Potential SQL injection via string concatenation',
    framework: 'SOC 2 / OWASP',
    control: 'CC6.6 / A1',
    suggestion: 'Use parameterized queries or an ORM. Never concatenate user input into SQL strings',
  },
  {
    id: 'no-http-in-prod',
    name: 'Unencrypted Transport',
    pattern: /http:\/\/(?!localhost|127\.0\.0\.1|0\.0\.0\.0)/g,
    severity: 'warning',
    message: 'HTTP (non-TLS) URL detected — use HTTPS in production',
    framework: 'ISO 27001 / NIST CSF',
    control: 'A.10.1.2 / PR.DS-2',
    suggestion: 'Replace http:// with https:// for all external URLs',
  },
  {
    id: 'no-console-log-sensitive',
    name: 'Sensitive Data Logging',
    pattern: /console\.log\([^)]*(?:password|token|secret|key|ssn|credit)[^)]*\)/gi,
    severity: 'warning',
    message: 'Potentially logging sensitive data — verify no PII/credentials reach logs',
    framework: 'GDPR / ISO 27001',
    control: 'Art.32 / A.12.4.1',
    suggestion: 'Remove or mask sensitive fields before logging',
  },
  {
    id: 'no-eval',
    name: 'Dynamic Code Execution',
    pattern: /\beval\s*\(|\bnew\s+Function\s*\(/g,
    severity: 'error',
    message: 'eval() or new Function() creates code injection risk',
    framework: 'SOC 2 / ISO 27001',
    control: 'CC6.6 / A.12.6.1',
    suggestion: 'Eliminate eval(). Use JSON.parse() for data, explicit function references for behavior',
  },
  {
    id: 'no-todo-security',
    name: 'Security TODO',
    pattern: /TODO.*(?:security|auth|encrypt|validate|sanitize)|FIXME.*(?:security|auth)/gi,
    severity: 'info',
    message: 'Security-related TODO/FIXME — track and resolve before audit',
    framework: 'ISO 27001',
    control: 'A.12.6.1',
  },
  {
    id: 'no-debug-endpoints',
    name: 'Debug Endpoint',
    pattern: /route\s*\(['"`]\/debug|app\.(get|post)\s*\(['"`]\/debug|path.*['"`]\/debug/gi,
    severity: 'warning',
    message: 'Debug endpoint detected — ensure it is disabled or gated in production',
    framework: 'SOC 2 / ISO 27001',
    control: 'CC6.6 / A.14.2.6',
  },
  {
    id: 'no-cors-wildcard-prod',
    name: 'Permissive CORS',
    pattern: /cors\s*\(\s*\{\s*origin\s*:\s*['"]\*['"]/gi,
    severity: 'warning',
    message: 'CORS wildcard origin — restrict to known origins in production',
    framework: 'ISO 27001',
    control: 'A.13.1.3',
    suggestion: "Specify allowed origins: origin: ['https://your-domain.com']",
  },
  {
    id: 'no-missing-auth-check',
    name: 'Missing Auth Check',
    pattern: /app\.(get|post|put|delete|patch)\s*\(['"`][^'"`,]+['"`]\s*,\s*(?:async\s*)?\([^)]*\)\s*=>/g,
    severity: 'info',
    message: 'Route handler — verify authentication middleware is applied',
    framework: 'SOC 2 / ISO 27001',
    control: 'CC6.1 / A.9.4.1',
  },
  {
    id: 'pqc-recommendation',
    name: 'Post-Quantum Cryptography',
    pattern: /rsa|ecdsa|elliptic.*curve|diffie.hellman/gi,
    severity: 'info',
    message: 'Classical asymmetric crypto — consider PQC migration path per NIST FIPS 203/204/205',
    framework: 'ISO 27001 / NIST SP 800-208',
    control: 'A.10.1.1',
    suggestion: 'Plan migration to ML-KEM-1024 (key exchange) and ML-DSA-87 (signatures) per NIST PQC standards',
  },
];

const SCAN_EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.java', '.rb', '.php', '.cs', '.rs', '.tf', '.yaml', '.yml', '.json', '.sh', '.env.example']);
const SKIP_DIRS = new Set(['node_modules', '.git', 'dist', 'build', '.next', '__pycache__', '.venv', 'vendor', 'coverage']);

function walkFiles(dir: string, files: string[] = []): string[] {
  try {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (SKIP_DIRS.has(entry)) continue;
      try {
        const stat = statSync(full);
        if (stat.isDirectory()) walkFiles(full, files);
        else if (SCAN_EXTENSIONS.has(extname(entry))) files.push(full);
      } catch { /* skip unreadable */ }
    }
  } catch { /* skip unreadable dir */ }
  return files;
}

function scanFile(filePath: string): Finding[] {
  let content: string;
  try { content = readFileSync(filePath, 'utf8'); } catch { return []; }
  const findings: Finding[] = [];
  for (const rule of SCAN_RULES) {
    let match: RegExpExecArray | null;
    const re = new RegExp(rule.pattern.source, rule.pattern.flags);
    while ((match = re.exec(content)) !== null) {
      const lineNum = content.slice(0, match.index).split('\n').length;
      findings.push({
        file: filePath,
        line: lineNum,
        severity: rule.severity,
        rule: rule.id,
        message: rule.message,
        framework: rule.framework,
        control: rule.control,
        autoFixable: !!rule.suggestion,
        suggestion: rule.suggestion,
      });
    }
  }
  return findings;
}

function posture(findings: Finding[]): number {
  const errors = findings.filter((f) => f.severity === 'error').length;
  const warnings = findings.filter((f) => f.severity === 'warning').length;
  const deduction = errors * 10 + warnings * 3;
  return Math.max(0, 100 - deduction);
}

// ─── Framework pack data (inline minimal — full data from @grc-claw/frameworks in bundled version) ──
const FRAMEWORK_SUMMARIES: Record<string, { name: string; controls: number; description: string }> = {
  'iso27001': { name: 'ISO/IEC 27001:2022', controls: 93, description: 'Information security management system' },
  'nist-csf': { name: 'NIST CSF 2.0', controls: 106, description: 'Cybersecurity framework (Govern/Identify/Protect/Detect/Respond/Recover)' },
  'soc2': { name: 'SOC 2 Type II', controls: 64, description: 'Trust Service Criteria (AICPA)' },
  'iso42001': { name: 'ISO/IEC 42001:2023', controls: 38, description: 'Artificial intelligence management system (AIMS)' },
  'eu-ai-act': { name: 'EU AI Act (2024/1689)', controls: 44, description: 'EU regulation on artificial intelligence' },
  'dora': { name: 'DORA (EU 2022/2554)', controls: 35, description: 'Digital operational resilience for financial entities' },
  'hipaa': { name: 'HIPAA Security Rule', controls: 42, description: 'US health information privacy and security' },
  'pci-dss': { name: 'PCI DSS v4.0', controls: 64, description: 'Payment card industry data security standard' },
  'gdpr': { name: 'GDPR (2016/679)', controls: 28, description: 'EU general data protection regulation' },
  'fedramp': { name: 'FedRAMP Moderate', controls: 323, description: 'US federal cloud security authorization' },
};

// ─── Commands ─────────────────────────────────────────────────────────────────

async function cmdScan(args: string[]) {
  const targetPath = resolve(args[0] ?? '.');
  if (!existsSync(targetPath)) { error(`Path not found: ${targetPath}`); process.exit(1); }

  const framework = args.find((a, i) => args[i - 1] === '--framework') ?? null;
  const jsonMode = args.includes('--json');

  if (!jsonMode) {
    log(`\n${bold('GRC_Claw')} ${dim(`v${VERSION}`)}`);
    log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);
    info(`Scanning: ${bold(targetPath)}`);
    if (framework) info(`Framework filter: ${bold(framework)}`);
  }

  const files = walkFiles(targetPath);
  if (!jsonMode) info(`Found ${bold(String(files.length))} files to scan`);

  const allFindings: Finding[] = [];
  for (const file of files) {
    const findings = scanFile(file);
    allFindings.push(...findings);
  }

  const errors = allFindings.filter((f) => f.severity === 'error');
  const warnings = allFindings.filter((f) => f.severity === 'warning');
  const infos = allFindings.filter((f) => f.severity === 'info');
  const score = posture(allFindings);

  if (jsonMode) {
    process.stdout.write(JSON.stringify({ score, findings: allFindings, summary: { errors: errors.length, warnings: warnings.length, info: infos.length } }, null, 2) + '\n');
    process.exit(errors.length > 0 ? 1 : 0);
    return;
  }

  log('');
  if (errors.length > 0) {
    log(`${c.red}${bold('ERRORS')} (${errors.length})${c.reset}`);
    for (const f of errors) {
      log(`  ${c.red}✗${c.reset} ${dim(f.file.replace(targetPath, '.'))}:${f.line}`);
      log(`    ${bold(f.message)}`);
      log(`    ${dim(`${f.framework} — ${f.control}`)}`);
      if (f.suggestion) log(`    ${c.cyan}Fix:${c.reset} ${f.suggestion}`);
      log('');
    }
  }

  if (warnings.length > 0) {
    log(`${c.yellow}${bold('WARNINGS')} (${warnings.length})${c.reset}`);
    for (const f of warnings) {
      log(`  ${c.yellow}⚠${c.reset} ${dim(f.file.replace(targetPath, '.'))}:${f.line}`);
      log(`    ${f.message}`);
      log(`    ${dim(`${f.framework} — ${f.control}`)}`);
      log('');
    }
  }

  log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);

  const scoreColor = score >= 80 ? c.green : score >= 50 ? c.yellow : c.red;
  log(`${bold('Compliance Posture Score:')} ${scoreColor}${bold(String(score))}/100${c.reset}`);
  log(`${bold('Errors:')} ${errors.length > 0 ? c.red : c.green}${errors.length}${c.reset}   ${bold('Warnings:')} ${warnings.length > 0 ? c.yellow : c.green}${warnings.length}${c.reset}   ${bold('Info:')} ${infos.length}`);

  if (score < 60) {
    log(`\n${c.bgRed}${c.white} BLOCKING ${c.reset} Score below 60 — resolve errors before audit`);
  } else if (score >= 90) {
    log(`\n${c.bgGreen}${c.white} PASS ${c.reset} Excellent compliance posture`);
  }

  log(`\n${dim('Full report:')} grc report --framework iso27001`);
  log(`${dim('Fix issues:')}   grc scan ${args[0] ?? '.'} --json | jq '.findings[] | select(.severity==\"error\")'`);
  log(`${dim('Gateway:')}      grc doctor\n`);

  process.exit(errors.length > 0 ? 1 : 0);
}

function cmdFrameworks(args: string[]) {
  const sub = args[0] ?? 'list';
  if (sub === 'list') {
    log(`\n${bold('Available Framework Packs')}\n`);
    for (const [id, meta] of Object.entries(FRAMEWORK_SUMMARIES)) {
      log(`  ${c.cyan}${id.padEnd(12)}${c.reset} ${bold(meta.name)}`);
      log(`  ${' '.repeat(12)} ${dim(meta.description)} ${dim(`(${meta.controls} controls)`)}\n`);
    }
    log(`${dim('Install additional packs: grc add <framework>')}\n`);
  }
}

function cmdReport(args: string[]) {
  const fw = args.find((a, i) => args[i - 1] === '--framework') ?? 'iso27001';
  const targetPath = resolve(args.find((a, i) => args[i - 1] === '--path') ?? '.');
  const meta = FRAMEWORK_SUMMARIES[fw];

  log(`\n${bold('Generating Compliance Report')}`);
  log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);
  info(`Framework: ${bold(meta?.name ?? fw)}`);
  info(`Path: ${bold(targetPath)}`);

  const files = walkFiles(targetPath);
  const allFindings = files.flatMap(scanFile);
  const score = posture(allFindings);
  const timestamp = new Date().toISOString();
  const reportHash = createHash('sha256').update(JSON.stringify({ fw, allFindings, timestamp })).digest('hex');

  const report = {
    grc_claw_version: VERSION,
    report_id: `grc-report-${Date.now()}`,
    sha256: reportHash,
    generated_at: timestamp,
    framework: fw,
    framework_name: meta?.name ?? fw,
    path_scanned: targetPath,
    posture_score: score,
    summary: {
      files_scanned: files.length,
      total_findings: allFindings.length,
      errors: allFindings.filter((f) => f.severity === 'error').length,
      warnings: allFindings.filter((f) => f.severity === 'warning').length,
      info: allFindings.filter((f) => f.severity === 'info').length,
    },
    findings: allFindings,
    attestation: {
      method: 'grc-claw-static-scan',
      auditable: true,
      hash_algorithm: 'sha256',
      hash: reportHash,
    },
  };

  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  log(`\n${c.green}✓${c.reset} Report generated — hash: ${dim(reportHash.slice(0, 16))}…`);
  log(`${dim('Save:')} grc report --framework ${fw} > report-${fw}-${timestamp.slice(0, 10)}.json\n`);
}

async function cmdDoctor() {
  log(`\n${bold('GRC_Claw Doctor')} ${dim(`v${VERSION}`)}`);
  log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}\n`);

  const checks = [
    { name: 'Node.js version', fn: () => { const v = parseInt(process.version.slice(1)); if (v < 20) throw new Error(`Node ${process.version} — requires ≥20`); return `Node ${process.version}`; } },
    { name: 'GRC_CLAW_GATEWAY_TOKEN', fn: () => { const t = process.env.GRC_CLAW_GATEWAY_TOKEN; if (!t) throw new Error('Not set — export GRC_CLAW_GATEWAY_TOKEN=<token>'); return 'Set'; } },
    { name: 'Gateway connectivity', fn: async () => {
      const url = `http://${process.env.GRC_CLAW_HOST ?? '127.0.0.1'}:${process.env.GRC_CLAW_PORT ?? 18791}/health`;
      const r = await fetch(url, { signal: AbortSignal.timeout(3000) });
      if (!r.ok) throw new Error(`Gateway returned ${r.status}`);
      const body = await r.json() as { ok: boolean };
      if (!body.ok) throw new Error('Gateway not healthy');
      return `Connected (${url})`;
    }},
    { name: 'grcfile.yaml', fn: () => { if (!existsSync('grcfile.yaml') && !existsSync('.grcfile.yaml')) throw new Error('Not found — run: grc init'); return 'Found'; } },
  ];

  let failures = 0;
  for (const check of checks) {
    try {
      const result = await check.fn();
      success(`${check.name.padEnd(32)} ${dim(result)}`);
    } catch (e) {
      error(`${check.name.padEnd(32)} ${(e as Error).message}`);
      failures++;
    }
  }

  log('');
  if (failures === 0) {
    log(`${c.bgGreen}${c.white} ALL CHECKS PASSED ${c.reset}\n`);
  } else {
    log(`${c.bgRed}${c.white} ${failures} CHECK${failures > 1 ? 'S' : ''} FAILED ${c.reset}\n`);
    process.exit(1);
  }
}

function cmdVersion() {
  log(`@grc-claw/cli ${VERSION}`);
  log(`Node: ${process.version}`);
  log(`Platform: ${process.platform} ${process.arch}`);
}

function cmdHelp() {
  log(`
${bold('grc')} — GRC_Claw CLI ${dim(`v${VERSION}`)}

${bold('USAGE')}
  grc <command> [options]

${bold('COMMANDS')}
  ${c.cyan}scan${c.reset} [path]                  Scan codebase for compliance findings
    --framework <id>          Filter findings to a specific framework
    --json                    Output JSON (suitable for CI/CD gates)

  ${c.cyan}report${c.reset}                        Generate a compliance evidence report
    --framework <id>          Framework to report against (default: iso27001)
    --path <dir>              Directory to scan (default: .)

  ${c.cyan}frameworks${c.reset} list               List available framework packs

  ${c.cyan}doctor${c.reset}                        Check environment and gateway connectivity

  ${c.cyan}version${c.reset}                       Print version information

${bold('EXAMPLES')}
  ${dim('# Scan current directory')}
  grc scan .

  ${dim('# Scan and gate CI/CD (exits 1 if errors found)')}
  grc scan . --json | jq '.summary.errors'

  ${dim('# Generate ISO 27001 evidence report')}
  grc report --framework iso27001 > evidence-$(date +%F).json

  ${dim('# Check framework packs')}
  grc frameworks list

  ${dim('# Verify environment')}
  grc doctor

${bold('ENVIRONMENT')}
  GRC_CLAW_GATEWAY_TOKEN     Gateway auth token
  GRC_CLAW_HOST              Gateway host (default: 127.0.0.1)
  GRC_CLAW_PORT              Gateway port (default: 18791)
  A2Z_SOC_API_KEY            A2Z SOC integration key

${bold('DOCS')}
  https://a2zsoc.com/developers/compliance-as-code
  https://github.com/AAH20/GRC_Claw
`);
}

// ─── Entry point ──────────────────────────────────────────────────────────────
const [,, cmd, ...rest] = process.argv;

switch (cmd) {
  case 'scan':       await cmdScan(rest); break;
  case 'report':     cmdReport(rest); break;
  case 'frameworks': cmdFrameworks(rest); break;
  case 'doctor':     await cmdDoctor(); break;
  case 'version':    cmdVersion(); break;
  case 'help':
  case '--help':
  case '-h':
  case undefined:    cmdHelp(); break;
  default:
    error(`Unknown command: ${cmd}`);
    log(`Run ${bold('grc help')} for usage`);
    process.exit(1);
}

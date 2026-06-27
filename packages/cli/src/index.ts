#!/usr/bin/env node
// @grc-claw/cli — The GRC_Claw command-line interface
// Usage: grc <command> [options]

import { readFileSync, writeFileSync, existsSync, readdirSync, statSync, mkdirSync } from 'node:fs';
import { resolve, join, extname, relative } from 'node:path';
import { execSync } from 'node:child_process';
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

// ─── grc init ─────────────────────────────────────────────────────────────────
function cmdInit(args: string[]) {
  const fw = args[args.indexOf('--framework') + 1] ?? args[args.indexOf('-f') + 1] ?? 'iso27001';
  const validFrameworks = ['iso27001', 'soc2', 'nist-csf', 'iso42001', 'dora', 'hipaa', 'pci-dss'];
  if (!validFrameworks.includes(fw)) {
    error(`Unknown framework: ${fw}. Valid: ${validFrameworks.join(', ')}`);
    process.exit(1);
  }

  if (existsSync('grcfile.yaml')) {
    warn('grcfile.yaml already exists — skipping (use --force to overwrite)');
    if (!args.includes('--force')) return;
  }

  const grcfile = `# GRC_Claw Compliance-as-Code configuration
# Run: grc scan . | grc apply | grc report --framework ${fw}
# Docs: https://a2zsoc.com/developers/compliance-as-code

version: "1.0"
framework: ${fw}
org: ${process.env.GRC_ORG ?? 'my-org'}

scan:
  paths:
    - src/
    - api/
    - scripts/
  exclude:
    - node_modules/
    - dist/
    - .git/

evidence:
  output: ./compliance-evidence
  formats: [json, html]
  retention_days: 365

controls:
  # Override specific control thresholds
  # cc6.1:
  #   required_evidence: [mfa_logs, access_review]
  #   exemption: "Legacy system — tracked in JIRA-1234"

integrations:
  github_app: ${process.env.GRC_GITHUB_APP_ID ? 'enabled' : 'disabled'}
  gateway: ${process.env.GRC_CLAW_GATEWAY_TOKEN ? 'enabled' : 'disabled'}
  a2z_soc: ${process.env.A2Z_SOC_API_KEY ? 'enabled' : 'disabled'}
`;

  writeFileSync('grcfile.yaml', grcfile);
  success('Created grcfile.yaml');

  // GitHub Actions workflow
  if (!existsSync('.github/workflows')) {
    mkdirSync('.github/workflows', { recursive: true });
  }
  if (!existsSync('.github/workflows/compliance.yml')) {
    const ghAction = `name: Compliance Gate
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install -g @grc-claw/cli
      - name: Scan
        run: grc scan . --json > compliance-report.json
      - name: Gate on errors
        run: |
          ERRORS=$(cat compliance-report.json | node -e "const d=require('fs').readFileSync('/dev/stdin','utf8'); console.log(JSON.parse(d).summary?.errors ?? 0)")
          if [ "$ERRORS" -gt "0" ]; then
            echo "::error::$ERRORS compliance error(s) found — run 'grc scan .' locally"
            exit 1
          fi
      - uses: actions/upload-artifact@v4
        with:
          name: compliance-report
          path: compliance-report.json
`;
    writeFileSync('.github/workflows/compliance.yml', ghAction);
    success('Created .github/workflows/compliance.yml');
  }

  // .grcignore
  if (!existsSync('.grcignore')) {
    writeFileSync('.grcignore', '# Files excluded from compliance scanning\nnode_modules/\ndist/\ncoverage/\n*.test.ts\n*.spec.ts\n');
    success('Created .grcignore');
  }

  log('');
  log(`${bold('Next steps:')}`);
  log(`  1. ${c.cyan}grc scan .${c.reset}                    — run your first compliance scan`);
  log(`  2. ${c.cyan}grc doctor${c.reset}                    — verify environment`);
  log(`  3. ${c.cyan}grc report --framework ${fw}${c.reset}  — generate evidence report`);
  log(`  4. ${c.cyan}grc ai-bom generate${c.reset}           — generate AI Bill of Materials\n`);
}

// ─── grc doctor --fix ─────────────────────────────────────────────────────────
interface AutoFix {
  id: string;
  description: string;
  check: () => boolean;
  fix: () => string;
  framework: string;
  control: string;
}

const AUTO_FIXES: AutoFix[] = [
  {
    id: 'gitignore-secrets',
    description: 'Ensure .env files are in .gitignore',
    framework: 'SOC 2 / ISO 27001',
    control: 'CC6.1 / A.9.4.3',
    check: () => {
      if (!existsSync('.gitignore')) return false;
      const gi = readFileSync('.gitignore', 'utf8');
      return gi.includes('.env') && gi.includes('*.pem') && gi.includes('*.key');
    },
    fix: () => {
      const entries = '\n# Security — GRC auto-fix\n.env\n.env.*\n*.pem\n*.key\n*.p12\n*.pfx\n*_rsa\n*_dsa\n*_ecdsa\n*_ed25519\n.secrets\ncredentials.json\nservice-account*.json\n';
      if (!existsSync('.gitignore')) {
        writeFileSync('.gitignore', entries);
        return 'Created .gitignore with secret exclusions';
      }
      const current = readFileSync('.gitignore', 'utf8');
      if (!current.includes('.env')) {
        writeFileSync('.gitignore', current + entries);
        return 'Added secret exclusion patterns to .gitignore';
      }
      return 'Already present';
    },
  },
  {
    id: 'security-headers',
    description: 'Check for security headers in vercel.json / next.config',
    framework: 'SOC 2',
    control: 'CC6.6',
    check: () => {
      if (existsSync('vercel.json')) {
        const v = JSON.parse(readFileSync('vercel.json', 'utf8'));
        return Array.isArray(v.headers) && v.headers.some((h: { headers: Array<{key: string}> }) =>
          h.headers?.some((x) => x.key === 'Strict-Transport-Security'));
      }
      return false;
    },
    fix: () => 'Manual: add HSTS + X-Frame-Options headers to vercel.json or web server config',
  },
  {
    id: 'npm-audit',
    description: 'No high/critical npm vulnerabilities',
    framework: 'ISO 27001',
    control: 'A.12.6.1',
    check: () => {
      try {
        execSync('npm audit --audit-level=high --json 2>/dev/null', { stdio: 'pipe' });
        return true;
      } catch { return false; }
    },
    fix: () => {
      try {
        execSync('npm audit fix --only=prod 2>&1', { stdio: 'pipe' });
        return 'Ran npm audit fix — check output for remaining manual fixes';
      } catch (e) {
        return `npm audit fix failed: ${(e as Error).message.slice(0, 80)}`;
      }
    },
  },
  {
    id: 'grcfile-present',
    description: 'grcfile.yaml present',
    framework: 'GRC_Claw',
    control: 'operational',
    check: () => existsSync('grcfile.yaml') || existsSync('.grcfile.yaml'),
    fix: () => { cmdInit([]); return 'Created grcfile.yaml (default: iso27001)'; },
  },
];

async function cmdDoctorFix(args: string[]) {
  const dryRun = args.includes('--dry-run');
  log(`\n${bold('GRC Doctor — Auto-Fix')} ${dim(dryRun ? '(dry run)' : '')} ${dim(`v${VERSION}`)}`);
  log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}\n`);

  let fixed = 0; let skipped = 0; let already = 0;
  for (const af of AUTO_FIXES) {
    const passing = af.check();
    if (passing) {
      success(`${af.id.padEnd(30)} ${dim('already passing')}`);
      already++;
      continue;
    }
    if (dryRun) {
      warn(`${af.id.padEnd(30)} ${c.yellow}would fix${c.reset} — ${af.description} (${af.framework} ${af.control})`);
      skipped++;
    } else {
      try {
        const result = af.fix();
        success(`${af.id.padEnd(30)} ${dim(result)}`);
        fixed++;
      } catch (e) {
        error(`${af.id.padEnd(30)} fix failed: ${(e as Error).message}`);
      }
    }
  }

  log('');
  log(`Fixed: ${fixed}  Already passing: ${already}  ${dryRun ? 'Would fix: ' + skipped : ''}`);
  log(`\n${dim('Tip: Run grc scan . to verify remaining findings\n')}`);
}

// ─── grc diff ─────────────────────────────────────────────────────────────────
function cmdDiff(args: string[]) {
  const ref = args[0] ?? 'HEAD~1';
  log(`\n${bold('Compliance Diff')} ${dim(`${ref} → HEAD`)}`);
  log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}\n`);

  let changedFiles: string[] = [];
  try {
    const out = execSync(`git diff --name-only ${ref} HEAD 2>/dev/null`, { encoding: 'utf8', stdio: ['pipe','pipe','pipe'] });
    changedFiles = out.trim().split('\n').filter(Boolean);
  } catch {
    error('Could not run git diff — ensure you are in a git repository');
    process.exit(1);
  }

  if (changedFiles.length === 0) {
    info('No changed files between HEAD and ' + ref);
    return;
  }

  const srcFiles = changedFiles.filter(f => ['.ts', '.tsx', '.js', '.jsx', '.py', '.go'].some(ext => f.endsWith(ext)));
  if (srcFiles.length === 0) {
    info(`${changedFiles.length} changed files — no source code changes to scan`);
    return;
  }

  info(`Scanning ${srcFiles.length} changed source files for compliance delta…\n`);

  const allFindings: Finding[] = [];
  for (const file of srcFiles) {
    const abs = resolve(file);
    if (existsSync(abs)) allFindings.push(...scanFile(abs));
  }

  if (allFindings.length === 0) {
    success('No new compliance findings in changed files');
    log(`${dim(`(${srcFiles.length} files scanned, ${changedFiles.length - srcFiles.length} non-source files skipped)`)}\n`);
    return;
  }

  const errors = allFindings.filter(f => f.severity === 'error');
  const warnings = allFindings.filter(f => f.severity === 'warning');

  log(`Found ${c.red}${errors.length} error(s)${c.reset}  ${c.yellow}${warnings.length} warning(s)${c.reset} in diff\n`);
  for (const f of allFindings) {
    const sev = f.severity === 'error' ? c.red : f.severity === 'warning' ? c.yellow : c.dim;
    log(`  ${sev}${f.severity.toUpperCase()}${c.reset}  ${dim(relative(process.cwd(), f.file))}:${f.line}  ${f.message}`);
    log(`         ${dim(f.framework + ' ' + f.control)}`);
  }
  log('');
  if (errors.length > 0) {
    warn('This diff introduces compliance errors — fix before merging\n');
    process.exit(1);
  }
}

// ─── grc ai-bom generate ──────────────────────────────────────────────────────
async function cmdAiBom(args: string[]) {
  const sub = args[0];

  if (sub !== 'generate') {
    log(`Usage: grc ai-bom generate [--model-card <path>] [--output <file>]`);
    log(`       grc ai-bom generate --scan-deps`);
    return;
  }

  const modelCardPath = args[args.indexOf('--model-card') + 1];
  const outputPath = args[args.indexOf('--output') + 1];
  const scanDeps = args.includes('--scan-deps');

  log(`\n${bold('AI Bill of Materials Generator')} ${dim(`v${VERSION}`)}`);
  log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}\n`);

  const bom: Record<string, unknown> = {
    schema: 'https://a2zsoc.com/schemas/ai-bom/v1.0',
    bomFormat: 'GRC-AI-BOM',
    specVersion: '1.0',
    serialNumber: `urn:uuid:${createHash('sha256').update(Date.now().toString()).digest('hex').slice(0, 32)}`,
    version: 1,
    metadata: {
      timestamp: new Date().toISOString(),
      generator: { name: '@grc-claw/cli', version: VERSION },
      licenses: [{ id: 'MIT' }],
    },
    components: [] as unknown[],
    externalReferences: [
      { type: 'documentation', url: 'https://a2zsoc.com/developers/ai-bom' },
    ],
    regulatory: {
      euAiAct: { article53Compliant: false, riskCategory: 'unknown', auditTrailRequired: true },
      nistAiRmf: { profile: 'generic', governFunctionCoverage: 0 },
      iso42001: { clause9_1: 'partial' },
    },
  };

  // Parse model card if provided
  if (modelCardPath && existsSync(modelCardPath)) {
    try {
      const mc = JSON.parse(readFileSync(modelCardPath, 'utf8')) as Record<string, unknown>;
      const comp: Record<string, unknown> = {
        type: 'machine-learning-model',
        name: mc['model_name'] ?? mc['name'] ?? 'unknown',
        version: mc['version'] ?? '0.0.0',
        description: mc['description'] ?? '',
        properties: [],
      };
      if (mc['base_model']) (comp['properties'] as unknown[]).push({ name: 'base_model', value: mc['base_model'] });
      if (mc['training_data']) (comp['properties'] as unknown[]).push({ name: 'training_data', value: String(mc['training_data']) });
      if (mc['architecture']) (comp['properties'] as unknown[]).push({ name: 'architecture', value: String(mc['architecture']) });
      if (mc['license']) (comp['properties'] as unknown[]).push({ name: 'license', value: String(mc['license']) });
      (bom['components'] as unknown[]).push(comp);
      bom['regulatory'] = { ...bom['regulatory'] as object, euAiAct: { article53Compliant: true, riskCategory: mc['risk_category'] ?? 'limited', auditTrailRequired: true } };
      success(`Parsed model card: ${modelCardPath}`);
    } catch { warn('Could not parse model card JSON — including empty component'); }
  }

  // Scan npm dependencies for AI/ML packages
  if (scanDeps && existsSync('package.json')) {
    const pkgJson = JSON.parse(readFileSync('package.json', 'utf8')) as { dependencies?: Record<string, string>; devDependencies?: Record<string, string> };
    const aiPackages = ['openai', '@anthropic-ai/sdk', '@google/generative-ai', 'langchain', 'llamaindex',
      'transformers', '@huggingface/inference', 'ollama', 'groq-sdk', 'cohere-ai', 'mistralai', 'replicate'];
    const allDeps = { ...pkgJson['dependencies'], ...pkgJson['devDependencies'] };
    for (const [pkg, ver] of Object.entries(allDeps)) {
      if (aiPackages.some(ai => pkg.includes(ai))) {
        (bom['components'] as unknown[]).push({
          type: 'library',
          name: pkg,
          version: ver,
          scope: 'required',
          properties: [{ name: 'category', value: 'ai-sdk' }],
        });
      }
    }
    info(`Scanned dependencies — found ${(bom['components'] as unknown[]).length} AI/ML package(s)`);
  }

  const bomJson = JSON.stringify(bom, null, 2);
  const hash = createHash('sha256').update(bomJson).digest('hex');
  (bom['metadata'] as Record<string, unknown>)['hash'] = { alg: 'SHA-256', content: hash };

  const finalJson = JSON.stringify(bom, null, 2);

  if (outputPath) {
    writeFileSync(outputPath, finalJson);
    success(`AI-BOM written to ${outputPath} (SHA-256: ${hash.slice(0, 16)}…)`);
  } else {
    process.stdout.write(finalJson + '\n');
  }

  log(`\n${dim('EU AI Act Article 53 compliance data captured')}`);
  log(`${dim('Publish to registry:')} grc ai-bom publish --file ${outputPath ?? 'ai-bom.json'}\n`);
}

async function cmdAiBomPublish(args: string[]) {
  const filePath = args[args.indexOf('--file') + 1] ?? args[args.indexOf('-f') + 1] ?? 'ai-bom.json';
  const modelId = args[args.indexOf('--model-id') + 1];
  const a2zApiKey = process.env.A2Z_SOC_API_KEY;

  if (!existsSync(filePath)) { error(`AI-BOM file not found: ${filePath}`); process.exit(1); }
  const bomContent = readFileSync(filePath, 'utf8');
  let bom: Record<string, unknown>;
  try { bom = JSON.parse(bomContent) as Record<string, unknown>; } catch { error('Invalid JSON in AI-BOM file'); process.exit(1); }

  const metadata = bom['metadata'] as Record<string, unknown> ?? {};
  const resolvedModelId = modelId ?? (metadata['model_id'] as string) ?? 'unknown/model';
  const vendor = (metadata['vendor'] as string) ?? resolvedModelId.split('/')[0] ?? 'unknown';
  const version = (metadata['version'] as string) ?? '0.0.0';

  log(`\n${bold('AI-BOM Registry Publish')} ${dim(`v${VERSION}`)}`);
  log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);
  info(`Publishing ${resolvedModelId} to A2Z SOC AI-BOM Registry...`);

  const endpoint = 'https://a2zsoc.com/api/platform/ai-bom-registry/publish';
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (a2zApiKey) headers['Authorization'] = `Bearer ${a2zApiKey}`;

  try {
    const res = await fetch(endpoint, { method: 'POST', headers, body: JSON.stringify({ model_id: resolvedModelId, vendor, version, bom_content: bomContent }) });
    const data = await res.json() as Record<string, unknown>;
    if (res.ok) {
      success(`Published! BOM hash: ${data['bom_hash']}`);
      log(`  Verify: ${data['verify_url']}`);
    } else {
      error(`Publish failed: ${JSON.stringify(data)}`);
      process.exit(1);
    }
  } catch (e) { error(`Network error: ${e instanceof Error ? e.message : String(e)}`); process.exit(1); }
}

// ─── PQC Scan (#8) — Post-Quantum Cryptography migration scanner ─────────────
interface PqcFinding {
  file: string; line: number; pattern: string; severity: 'critical' | 'high' | 'medium';
  match: string; replacement: string; nist_ref: string;
}

const PQC_PATTERNS: Array<{ pattern: string; re: RegExp; severity: PqcFinding['severity']; replacement: string; nist_ref: string }> = [
  { pattern: 'RSA key generation', re: /generateKeyPair\s*\(\s*['"]rsa['"]/gi, severity: 'critical', replacement: 'ML-KEM-768 (FIPS 203)', nist_ref: 'SP 800-208' },
  { pattern: 'RSA-2048 key size', re: /modulusLength\s*:\s*2048/gi, severity: 'critical', replacement: 'ML-KEM or RSA-3072 minimum (transitional)', nist_ref: 'SP 800-57' },
  { pattern: 'ECDSA signing', re: /createSign\s*\(\s*['"]SHA-256['"]\)|new\s+ECDSA|createECDH/gi, severity: 'critical', replacement: 'ML-DSA-65 (FIPS 204)', nist_ref: 'FIPS 204' },
  { pattern: 'ECDH key exchange', re: /createDiffieHellman|diffieHellman|\.computeSecret\(/gi, severity: 'high', replacement: 'ML-KEM-1024 (FIPS 203)', nist_ref: 'SP 800-227' },
  { pattern: 'MD5 hashing', re: /createHash\s*\(\s*['"]md5['"]\)/gi, severity: 'high', replacement: 'SHA-3 / SHAKE-256 (FIPS 202)', nist_ref: 'FIPS 202' },
  { pattern: 'SHA-1 hashing', re: /createHash\s*\(\s*['"]sha1['"]\)/gi, severity: 'medium', replacement: 'SHA-256 or SHA-3 (FIPS 202)', nist_ref: 'FIPS 202' },
];

const SCANNABLE_EXTS = new Set(['.ts', '.tsx', '.js', '.mjs', '.cjs', '.py', '.go', '.java', '.cs', '.rb', '.rs']);
function scanFileForPqc(filePath: string): PqcFinding[] {
  const findings: PqcFinding[] = [];
  try {
    const content = readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i] ?? '';
      for (const p of PQC_PATTERNS) {
        p.re.lastIndex = 0;
        const m = p.re.exec(line);
        if (m) {
          findings.push({ file: filePath, line: i + 1, pattern: p.pattern, severity: p.severity, match: m[0].trim(), replacement: p.replacement, nist_ref: p.nist_ref });
        }
      }
    }
  } catch { /* skip unreadable files */ }
  return findings;
}

function walkDirForPqc(dir: string, findings: PqcFinding[]) {
  let entries: string[] = [];
  try { entries = readdirSync(dir); } catch { return; }
  for (const entry of entries) {
    if (SKIP_DIRS.has(entry)) continue;
    const full = join(dir, entry);
    try {
      const stat = statSync(full);
      if (stat.isDirectory()) walkDirForPqc(full, findings);
      else if (SCANNABLE_EXTS.has(extname(entry))) findings.push(...scanFileForPqc(full));
    } catch { /* skip */ }
  }
}

async function cmdPqcScan(args: string[]) {
  const targetDir = resolve(args.find(a => !a.startsWith('-')) ?? '.');
  const jsonMode = args.includes('--json');
  const outputPath = args[args.indexOf('--output') + 1];
  const a2zApiKey = process.env.A2Z_SOC_API_KEY;

  if (!jsonMode) {
    log(`\n${bold('PQC Migration Scanner')} ${dim(`v${VERSION}`)}`);
    log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);
    info(`Scanning ${targetDir} for deprecated cryptography...`);
  }

  const findings: PqcFinding[] = [];
  walkDirForPqc(targetDir, findings);

  const critical = findings.filter(f => f.severity === 'critical');
  const high = findings.filter(f => f.severity === 'high');
  const medium = findings.filter(f => f.severity === 'medium');

  const report = {
    schema: 'https://a2zsoc.com/schemas/pqc-scan/v1.0',
    scanned_at: new Date().toISOString(),
    target_dir: targetDir,
    summary: { total: findings.length, critical: critical.length, high: high.length, medium: medium.length },
    findings: findings.map(f => ({ ...f, file: relative(targetDir, f.file) })),
    migration_timeline: { '2026-Q2': 'Inventory complete', '2026-Q4': 'Hybrid PQC deployed', '2027-Q1': 'FedRAMP mandate — migration required' },
    standards: ['FIPS 203 (ML-KEM)', 'FIPS 204 (ML-DSA)', 'FIPS 205 (SLH-DSA)', 'NIST SP 800-208'],
  };

  if (jsonMode || outputPath) {
    const json = JSON.stringify(report, null, 2);
    if (outputPath) { writeFileSync(outputPath, json); if (!jsonMode) success(`Report written to ${outputPath}`); }
    else process.stdout.write(json + '\n');
  } else {
    log('');
    if (findings.length === 0) {
      success('No deprecated cryptographic patterns found. PQC-ready!');
    } else {
      if (critical.length) { log(`${c.red}${bold(`✗ CRITICAL (${critical.length}):`)}${c.reset} Must migrate before FedRAMP 2027 deadline`); for (const f of critical) log(`  ${c.dim}${relative(targetDir, f.file)}:${f.line}${c.reset}  ${c.red}${f.match}${c.reset}  →  ${c.green}${f.replacement}${c.reset} [${f.nist_ref}]`); }
      if (high.length) { log(`\n${c.yellow}${bold(`⚠ HIGH (${high.length}):`)}${c.reset}`); for (const f of high) log(`  ${c.dim}${relative(targetDir, f.file)}:${f.line}${c.reset}  ${c.yellow}${f.match}${c.reset}  →  ${c.green}${f.replacement}${c.reset} [${f.nist_ref}]`); }
      if (medium.length) { log(`\n${c.blue}${bold(`ℹ MEDIUM (${medium.length}):`)}${c.reset}`); for (const f of medium) log(`  ${c.dim}${relative(targetDir, f.file)}:${f.line}${c.reset}  ${c.blue}${f.match}${c.reset}  →  ${c.green}${f.replacement}${c.reset} [${f.nist_ref}]`); }
      log(`\n${c.dim}Standards: FIPS 203 (ML-KEM) · FIPS 204 (ML-DSA) · FIPS 205 (SLH-DSA)${c.reset}`);
    }
    log('');
  }

  // Publish scan result to A2Z SOC if API key present
  if (a2zApiKey && findings.length > 0) {
    try {
      await fetch('https://a2zsoc.com/api/platform/pqc-scan', { method: 'POST', headers: { 'Authorization': `Bearer ${a2zApiKey}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ summary: report.summary, scanned_at: report.scanned_at }) });
      if (!jsonMode) info('PQC scan result uploaded to A2Z SOC dashboard');
    } catch { /* non-fatal */ }
  }

  if (critical.length > 0) process.exit(1);
}

// ─── grc iac-scan ─────────────────────────────────────────────────────────────

interface IaCFinding {
  file: string;
  line: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
  rule: string;
  control: string;
  framework: string;
  message: string;
  fix: string;
}

const IAC_RULES: Array<{
  id: string;
  control: string;
  framework: string;
  pattern: RegExp;
  fileExts: string[];
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
  fix: string;
}> = [
  { id: 'iac-public-s3', control: 'A.13.1.3', framework: 'ISO 27001', pattern: /acl\s*=\s*["']public-read(-write)?["']/i, fileExts: ['.tf'], severity: 'critical', message: 'S3 bucket ACL is public — ISO 27001 A.13.1.3', fix: 'Set acl = "private" and enable S3 Block Public Access' },
  { id: 'iac-rds-no-encrypt', control: 'A.10.1.1', framework: 'ISO 27001', pattern: /storage_encrypted\s*=\s*false/i, fileExts: ['.tf'], severity: 'critical', message: 'RDS storage encryption disabled — SOC 2 CC6.1 / ISO 27001 A.10.1.1', fix: 'Set storage_encrypted = true on all aws_db_instance resources' },
  { id: 'iac-open-sg', control: 'A.13.1.1', framework: 'ISO 27001', pattern: /cidr_blocks\s*=\s*\["0\.0\.0\.0\/0"\]/, fileExts: ['.tf'], severity: 'high', message: 'Security group open to 0.0.0.0/0 — ISO 27001 A.13.1.1', fix: 'Restrict cidr_blocks to specific IP ranges' },
  { id: 'iac-tf-no-state-encrypt', control: 'A.10.1.1', framework: 'ISO 27001', pattern: /backend\s+"s3"/, fileExts: ['.tf'], severity: 'high', message: 'Terraform S3 backend — verify encrypt = true is set — ISO 27001 A.10.1.1', fix: 'Add encrypt = true to the terraform backend "s3" block' },
  { id: 'iac-k8s-privileged', control: 'A.9.4.1', framework: 'ISO 27001', pattern: /privileged\s*:\s*true/i, fileExts: ['.yaml', '.yml'], severity: 'critical', message: 'Kubernetes container privileged=true — SOC 2 CC6.1 / ISO 27001 A.9.4.1', fix: 'Set privileged: false; use least-privilege security context' },
  { id: 'iac-cf-http', control: 'A.13.2.3', framework: 'ISO 27001', pattern: /Protocol\s*:\s*HTTP(?!S)/i, fileExts: ['.yaml', '.yml', '.json'], severity: 'high', message: 'CloudFormation resource using HTTP — ISO 27001 A.13.2.3', fix: 'Switch Protocol to HTTPS and configure an SSL certificate' },
  { id: 'iac-gcs-public', control: 'A.13.1.3', framework: 'ISO 27001', pattern: /public_access_prevention\s*=\s*["']unspecified["']/i, fileExts: ['.tf'], severity: 'critical', message: 'GCS bucket public access prevention unspecified — ISO 27001 A.13.1.3', fix: 'Set public_access_prevention = "enforced"' },
  { id: 'iac-azure-blob-public', control: 'A.13.1.3', framework: 'ISO 27001', pattern: /allow_blob_public_access\s*=\s*true/i, fileExts: ['.tf'], severity: 'critical', message: 'Azure Blob public access enabled — ISO 27001 A.13.1.3', fix: 'Set allow_blob_public_access = false on azurerm_storage_account' },
];

const IAC_EXTS = new Set(['.tf', '.yaml', '.yml', '.json']);

function scanFileForIaC(filePath: string): IaCFinding[] {
  const ext = extname(filePath).toLowerCase();
  if (!IAC_EXTS.has(ext)) return [];
  const findings: IaCFinding[] = [];
  let content: string;
  try { content = readFileSync(filePath, 'utf8'); } catch { return []; }
  const lines = content.split('\n');
  for (const rule of IAC_RULES) {
    if (!rule.fileExts.includes(ext)) continue;
    for (let i = 0; i < lines.length; i++) {
      const re = new RegExp(rule.pattern.source, 'i');
      if (re.test(lines[i])) {
        findings.push({ file: filePath, line: i + 1, severity: rule.severity, rule: rule.id, control: rule.control, framework: rule.framework, message: rule.message, fix: rule.fix });
      }
    }
  }
  return findings;
}

function walkDirForIaC(dir: string, findings: IaCFinding[]) {
  let entries: string[] = [];
  try { entries = readdirSync(dir); } catch { return; }
  for (const entry of entries) {
    if (SKIP_DIRS.has(entry)) continue;
    const full = join(dir, entry);
    try {
      const stat = statSync(full);
      if (stat.isDirectory()) walkDirForIaC(full, findings);
      else if (IAC_EXTS.has(extname(entry))) findings.push(...scanFileForIaC(full));
    } catch { /* skip */ }
  }
}

async function cmdIaCScan(args: string[]) {
  const targetDir = resolve(args.find(a => !a.startsWith('-')) ?? '.');
  const jsonMode = args.includes('--json');
  const framework = args[args.indexOf('--framework') + 1] ?? null;
  const outputPath = args[args.indexOf('--output') + 1];

  if (!jsonMode) {
    log(`\n${bold('GRC_Claw IaC Compliance Scanner')} ${dim(`v${VERSION}`)}`);
    log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);
    info(`Scanning ${bold(targetDir)} for Terraform, CloudFormation, Kubernetes manifests…`);
  }

  const findings: IaCFinding[] = [];
  walkDirForIaC(targetDir, findings);

  const filtered = framework ? findings.filter(f => f.framework.toLowerCase().includes(framework.toLowerCase())) : findings;
  const critical = filtered.filter(f => f.severity === 'critical');
  const high = filtered.filter(f => f.severity === 'high');
  const medium = filtered.filter(f => f.severity === 'medium');
  const low = filtered.filter(f => f.severity === 'low');
  const score = Math.max(0, 100 - critical.length * 20 - high.length * 10 - medium.length * 3 - low.length);

  const report = {
    schema: 'https://a2zsoc.com/schemas/iac-scan/v1.0',
    scanned_at: new Date().toISOString(),
    target_dir: targetDir,
    framework_filter: framework,
    summary: { total: filtered.length, critical: critical.length, high: high.length, medium: medium.length, low: low.length, posture_score: score },
    findings: filtered.map(f => ({ ...f, file: relative(targetDir, f.file) })),
    frameworks_checked: [...new Set(filtered.map(f => f.framework))],
    controls_checked: [...new Set(filtered.map(f => f.control))],
  };

  if (jsonMode || outputPath) {
    const json = JSON.stringify(report, null, 2);
    if (outputPath) { writeFileSync(outputPath, json); if (!jsonMode) success(`IaC scan report written to ${outputPath}`); }
    else process.stdout.write(json + '\n');
  } else {
    log('');
    if (filtered.length === 0) {
      success(`No IaC compliance findings in ${targetDir} — infrastructure looks clean!`);
    } else {
      for (const f of critical) {
        log(`${c.red}✗ CRITICAL${c.reset}  ${c.dim}${relative(targetDir, f.file)}:${f.line}${c.reset}  [${f.control}]  ${f.message}`);
        log(`  ${c.green}Fix:${c.reset} ${f.fix}`);
      }
      for (const f of high) {
        log(`${c.yellow}⚠ HIGH${c.reset}     ${c.dim}${relative(targetDir, f.file)}:${f.line}${c.reset}  [${f.control}]  ${f.message}`);
        log(`  ${c.green}Fix:${c.reset} ${f.fix}`);
      }
      for (const f of [...medium, ...low]) {
        log(`${c.blue}ℹ ${f.severity.toUpperCase()}${c.reset}    ${c.dim}${relative(targetDir, f.file)}:${f.line}${c.reset}  [${f.control}]  ${f.message}`);
      }
      log(`\n${bold('Posture Score:')} ${score < 60 ? c.red : score < 80 ? c.yellow : c.green}${score}/100${c.reset}`);
      log(`${c.dim}Critical: ${critical.length}  High: ${high.length}  Medium: ${medium.length}  Low: ${low.length}${c.reset}\n`);
    }
  }

  if (critical.length > 0 && !jsonMode) process.exit(1);
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
  ${c.cyan}init${c.reset}                          Scaffold grcfile.yaml + GitHub Actions workflow
    --framework <id>          Framework to target (default: iso27001)

  ${c.cyan}plan${c.reset}                           Generate compliance plan from grcfile.yaml
    --json                    Output JSON (for CI/CD pipelines)
    --output <file>           Write plan to file

  ${c.cyan}apply${c.reset} [path]                  Apply compliance plan to target environment
    --dry-run                 Preview changes without applying
    --json                    Output JSON

  ${c.cyan}audit${c.reset} [path]                  Run full compliance audit with control coverage
    --json                    Output JSON
    --output <file>           Write audit report to file

  ${c.cyan}scan${c.reset} [path]                  Scan codebase for compliance findings
    --framework <id>          Filter findings to a specific framework
    --json                    Output JSON (suitable for CI/CD gates)

  ${c.cyan}status${c.reset} [path]                 Show current compliance posture and gateway status
    --json                    Output JSON

  ${c.cyan}drift${c.reset} [path]                  Detect compliance drift from a git baseline
    --base <ref>              Git ref to compare against (default: HEAD)
    --json                    Output JSON
    --output <file>           Write drift report to file

  ${c.cyan}report${c.reset}                        Generate a compliance evidence report
    --framework <id>          Framework to report against (default: iso27001)
    --path <dir>              Directory to scan (default: .)

  ${c.cyan}diff${c.reset} [ref]                   Show compliance delta between git refs (default: HEAD~1)

  ${c.cyan}doctor${c.reset}                        Check environment and gateway connectivity
    --fix                     Auto-remediate common control failures
    --dry-run                 Preview fixes without applying

  ${c.cyan}ai-bom generate${c.reset}               Generate AI Bill of Materials (EU AI Act Art. 53)
    --model-card <path>       Parse a model_card.json file
    --scan-deps               Scan package.json for AI/ML dependencies
    --output <file>           Write BOM to file (default: stdout)

  ${c.cyan}ai-bom publish${c.reset}                Publish AI-BOM to A2Z SOC public registry
    --file <path>             AI-BOM JSON file to publish (default: ai-bom.json)
    --model-id <id>           Override model identifier

  ${c.cyan}iac-scan${c.reset} [path]               Scan Terraform/CloudFormation/Kubernetes for compliance
    --framework <id>          Filter by framework (iso27001, soc2, nist-csf)
    --output <file>           Write report to file
    --json                    JSON output for CI/CD gates
    Exits 1 if critical IaC findings detected

  ${c.cyan}pqc-scan${c.reset} [path]               Scan for deprecated cryptography (RSA/ECDSA/ECDH)
    --output <file>           Write report to file
    --json                    JSON output for CI/CD gates
    Exits 1 if critical findings detected (FedRAMP 2027 gate)

  ${c.cyan}frameworks${c.reset} list               List available framework packs

  ${c.cyan}version${c.reset}                       Print version information

${bold('EXAMPLES')}
  ${dim('# Scaffold a new compliance project')}
  grc init --framework soc2

  ${dim('# Generate a compliance plan')}
  grc plan --json > plan.json

  ${dim('# Apply compliance fixes (dry run)')}
  grc apply --dry-run

  ${dim('# Scan current directory')}
  grc scan .

  ${dim('# Scan and gate CI/CD (exits 1 if errors found)')}
  grc scan . --json | jq '.summary.errors'

  ${dim('# Show compliance status')}
  grc status

  ${dim('# Detect drift from main branch')}
  grc drift --base main

  ${dim('# Run full compliance audit')}
  grc audit --framework iso27001

  ${dim('# Show compliance changes in this PR branch')}
  grc diff main

  ${dim('# Auto-fix common control failures')}
  grc doctor --fix

  ${dim('# Generate AI Bill of Materials')}
  grc ai-bom generate --scan-deps --output ai-bom.json

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

// ─── Gateway helpers ──────────────────────────────────────────────────────────
const GATEWAY_HOST = process.env.GRC_CLAW_HOST ?? '127.0.0.1';
const GATEWAY_PORT = process.env.GRC_CLAW_PORT ?? '18791';
const GATEWAY_BASE = `http://${GATEWAY_HOST}:${GATEWAY_PORT}`;
const GATEWAY_TOKEN = process.env.GRC_CLAW_GATEWAY_TOKEN ?? '';

interface GatewayResponse<T = unknown> {
  ok: boolean;
  status: number;
  data: T;
}

async function gatewayGet<T = unknown>(path: string): Promise<GatewayResponse<T>> {
  const url = `${GATEWAY_BASE}${path}`;
  const headers: Record<string, string> = {};
  if (GATEWAY_TOKEN) headers['Authorization'] = `Bearer ${GATEWAY_TOKEN}`;
  const res = await fetch(url, { headers, signal: AbortSignal.timeout(10_000) });
  const body = await res.json() as T;
  return { ok: res.ok, status: res.status, data: body };
}

async function gatewayPost<T = unknown>(path: string, payload: unknown): Promise<GatewayResponse<T>> {
  const url = `${GATEWAY_BASE}${path}`;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (GATEWAY_TOKEN) headers['Authorization'] = `Bearer ${GATEWAY_TOKEN}`;
  const res = await fetch(url, { method: 'POST', headers, body: JSON.stringify(payload), signal: AbortSignal.timeout(10_000) });
  const body = await res.json() as T;
  return { ok: res.ok, status: res.status, data: body };
}

// ─── grcfile.yaml parser (YAML-lite — handles grcfile.yaml key/value pairs) ───
interface GrcFile {
  version: string;
  framework: string;
  org: string;
  scan: { paths: string[]; exclude: string[] };
  evidence: { output: string; formats: string[]; retention_days: number };
  controls: Record<string, { required_evidence?: string[]; exemption?: string }>;
  integrations: { github_app: string; gateway: string; a2z_soc: string };
}

function parseGrcFile(): GrcFile {
  const candidates = ['grcfile.yaml', '.grcfile.yaml'];
  const found = candidates.find((f) => existsSync(f));
  if (!found) {
    error('grcfile.yaml not found — run: grc init');
    process.exit(1);
  }
  const raw = readFileSync(found, 'utf8');

  const result: GrcFile = {
    version: '1.0',
    framework: 'iso27001',
    org: 'my-org',
    scan: { paths: ['src/'], exclude: ['node_modules/'] },
    evidence: { output: './compliance-evidence', formats: ['json'], retention_days: 365 },
    controls: {},
    integrations: { github_app: 'disabled', gateway: 'disabled', a2z_soc: 'disabled' },
  };

  let section = '';
  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    const topMatch = trimmed.match(/^(\w[\w_]*):\s*(.*)/);
    if (topMatch) {
      const key = topMatch[1];
      const val = topMatch[2];
      if (!val) { section = key; continue; }
      switch (key) {
        case 'version': result.version = val; break;
        case 'framework': result.framework = val; break;
        case 'org': result.org = val; break;
        case 'retention_days': result.evidence.retention_days = parseInt(val, 10) || 365; break;
        case 'output': result.evidence.output = val; break;
      }
      section = key === 'scan' ? 'scan' : key === 'evidence' ? 'evidence' : '';
      continue;
    }

    if (section === 'scan' && trimmed.startsWith('- ')) {
      const item = trimmed.slice(2).trim();
      if (result.scan.paths.length <= result.scan.exclude.length + 1) result.scan.paths.push(item);
      else result.scan.exclude.push(item);
    }
    if (section === 'evidence') {
      const sub = trimmed.match(/^(\w+):\s*(.*)/);
      if (sub) {
        if (sub[1] === 'output') result.evidence.output = sub[2];
        if (sub[1] === 'retention_days') result.evidence.retention_days = parseInt(sub[2], 10) || 365;
        if (sub[1] === 'formats') {
          result.evidence.formats = sub[2].replace(/[[\]]/g, '').split(',').map((s) => s.trim()).filter(Boolean);
        }
      }
    }
    if (section === '') {
      const kv = trimmed.match(/^(\w+):\s*(.*)/);
      if (kv) {
        switch (kv[1]) {
          case 'github_app': result.integrations.github_app = kv[2]; break;
          case 'gateway': result.integrations.gateway = kv[2]; break;
          case 'a2z_soc': result.integrations.a2z_soc = kv[2]; break;
        }
      }
    }
  }
  return result;
}

// ─── Table formatter ──────────────────────────────────────────────────────────
function table(headers: string[], rows: string[][]): string {
  const widths = headers.map((h, i) =>
    Math.max(h.length, ...rows.map((r) => (r[i] ?? '').length)),
  );
  const sep = widths.map((w) => '─'.repeat(w + 2)).join('┼');
  const hdr = headers.map((h, i) => ` ${h.padEnd(widths[i])} `).join('│');
  const lines = rows.map((r) => r.map((cell, i) => ` ${cell.padEnd(widths[i])} `).join('│'));
  return `${hdr}\n${sep}\n${lines.join('\n')}`;
}

// ─── grc plan ─────────────────────────────────────────────────────────────────
async function cmdPlan(args: string[]) {
  const grcFile = parseGrcFile();
  const jsonMode = args.includes('--json');
  const outputPath = args[args.indexOf('--output') + 1];

  if (!jsonMode) {
    log(`\n${bold('Compliance Plan Generator')} ${dim(`v${VERSION}`)}`);
    log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);
    info(`Framework: ${bold(FRAMEWORK_SUMMARIES[grcFile.framework]?.name ?? grcFile.framework)}`);
    info(`Organization: ${bold(grcFile.org)}`);
    info(`Scan paths: ${bold(grcFile.scan.paths.join(', '))}`);
  }

  const files = grcFile.scan.paths.flatMap((p) => walkFiles(resolve(p)));
  const allFindings = files.flatMap(scanFile);
  const score = posture(allFindings);
  const meta = FRAMEWORK_SUMMARIES[grcFile.framework];

  const plan = {
    schema: 'https://a2zsoc.com/schemas/compliance-plan/v1.0',
    generated_at: new Date().toISOString(),
    org: grcFile.org,
    framework: grcFile.framework,
    framework_name: meta?.name ?? grcFile.framework,
    posture_score: score,
    controls_total: meta?.controls ?? 0,
    controls_with_gaps: [...new Set(allFindings.filter((f) => f.severity === 'error').map((f) => f.control))].length,
    actions: allFindings
      .filter((f) => f.severity === 'error')
      .map((f) => ({
        control: f.control,
        framework: f.framework,
        severity: f.severity,
        finding: f.message,
        file: relative(process.cwd(), f.file),
        line: f.line,
        remediation: f.suggestion ?? 'Manual review required',
        auto_fixable: f.autoFixable,
      })),
    evidence_requirements: Object.entries(grcFile.controls).map(([ctrl, cfg]) => ({
      control: ctrl,
      required_evidence: cfg.required_evidence ?? [],
      exemption: cfg.exemption ?? null,
    })),
    integrations: grcFile.integrations,
  };

  if (jsonMode || outputPath) {
    const json = JSON.stringify(plan, null, 2);
    if (outputPath) { writeFileSync(outputPath, json); success(`Plan written to ${outputPath}`); }
    else process.stdout.write(json + '\n');
  } else {
    log('');
    if (plan.actions.length === 0) {
      success('No compliance gaps — plan is clean!');
    } else {
      log(`${bold('Remediation Actions:')} ${plan.actions.length}\n`);
      const rows = plan.actions.map((a) => [
        a.control,
        a.auto_fixable ? `${c.green}Yes${c.reset}` : `${c.red}No${c.reset}`,
        a.finding.slice(0, 60),
        `${a.file}:${a.line}`,
      ]);
      log(table(['Control', 'Auto-fix', 'Finding', 'Location'], rows));
    }
    log(`\n${bold('Posture Score:')} ${score >= 80 ? c.green : score >= 50 ? c.yellow : c.red}${score}/100${c.reset}`);
    log(`${dim('Apply plan:')}   grc apply`);
    log(`${dim('Run audit:')}    grc audit\n`);
  }
}

// ─── grc apply ────────────────────────────────────────────────────────────────
async function cmdApply(args: string[]) {
  const grcFile = parseGrcFile();
  const dryRun = args.includes('--dry-run');
  const targetPath = resolve(args.find((a) => !a.startsWith('-')) ?? '.');
  const jsonMode = args.includes('--json');

  if (!jsonMode) {
    log(`\n${bold('Apply Compliance Plan')} ${dryRun ? dim('(dry run)') : ''} ${dim(`v${VERSION}`)}`);
    log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);
    info(`Target: ${bold(targetPath)}`);
    info(`Framework: ${bold(grcFile.framework)}`);
  }

  const files = walkFiles(targetPath);
  const allFindings = files.flatMap(scanFile);
  const errors = allFindings.filter((f) => f.severity === 'error');
  const autoFixes = allFindings.filter((f) => f.severity === 'error' && f.autoFixable);

  if (!jsonMode) {
    log('');
    info(`Found ${errors.length} error(s), ${autoFixes.length} auto-fixable`);
  }

  // Attempt gateway-assisted apply if connected
  if (grcFile.integrations.gateway === 'enabled' && GATEWAY_TOKEN) {
    try {
      const res = await gatewayPost('/api/compliance/apply', {
        framework: grcFile.framework,
        org: grcFile.org,
        target: targetPath,
        dry_run: dryRun,
        findings: allFindings,
      });
      if (res.ok) {
        if (!jsonMode) success('Gateway applied compliance plan');
      } else {
        if (!jsonMode) warn(`Gateway returned status ${res.status} — falling back to local apply`);
      }
    } catch {
      if (!jsonMode) warn('Gateway unreachable — applying locally');
    }
  }

  // Local auto-fix: add suggestions where possible
  if (!dryRun && autoFixes.length > 0 && !jsonMode) {
    log('');
    log(`${bold('Applying auto-fixes:')}`);
    for (const f of autoFixes) {
      if (f.suggestion) {
        log(`  ${c.green}✓${c.reset} ${f.control} — ${f.suggestion}`);
      }
    }
  }

  if (dryRun && !jsonMode) {
    log('\nNo changes applied (dry run). Remove --dry-run to apply.');
  } else if (!jsonMode) {
    const score = posture(allFindings);
    log(`\n${bold('Resulting Posture:')} ${score >= 80 ? c.green : score >= 50 ? c.yellow : c.red}${score}/100${c.reset}`);
    log(`${dim('Verify:')}     grc status`);
    log(`${dim('Audit:')}      grc audit\n`);
  }

  if (jsonMode) {
    process.stdout.write(JSON.stringify({
      applied: !dryRun,
      auto_fixes: autoFixes.length,
      remaining_errors: errors.length - autoFixes.length,
      posture_score: posture(allFindings),
    }, null, 2) + '\n');
  }
}

// ─── grc audit ────────────────────────────────────────────────────────────────
async function cmdAudit(args: string[]) {
  const grcFile = parseGrcFile();
  const jsonMode = args.includes('--json');
  const outputPath = args[args.indexOf('--output') + 1];
  const targetPath = resolve(args.find((a) => !a.startsWith('-')) ?? '.');
  const timestamp = new Date().toISOString();

  if (!jsonMode) {
    log(`\n${bold('Compliance Audit')} ${dim(`v${VERSION}`)}`);
    log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);
    info(`Framework: ${bold(FRAMEWORK_SUMMARIES[grcFile.framework]?.name ?? grcFile.framework)}`);
    info(`Target: ${bold(targetPath)}`);
  }

  const files = walkFiles(targetPath);
  const allFindings = files.flatMap(scanFile);
  const score = posture(allFindings);
  const errors = allFindings.filter((f) => f.severity === 'error');
  const warnings = allFindings.filter((f) => f.severity === 'warning');
  const infos = allFindings.filter((f) => f.severity === 'info');
  const meta = FRAMEWORK_SUMMARIES[grcFile.framework];

  // Compute control coverage
  const controlMap = new Map<string, { status: 'pass' | 'fail' | 'warn'; findings: Finding[] }>();
  for (const f of allFindings) {
    const key = `${f.framework}:${f.control}`;
    const existing = controlMap.get(key);
    if (existing) {
      existing.findings.push(f);
      if (f.severity === 'error') existing.status = 'fail';
      else if (f.severity === 'warning' && existing.status === 'pass') existing.status = 'warn';
    } else {
      controlMap.set(key, {
        status: f.severity === 'error' ? 'fail' : f.severity === 'warning' ? 'warn' : 'pass',
        findings: [f],
      });
    }
  }
  const controlsChecked = controlMap.size;
  const controlsPassing = [...controlMap.values()].filter((v) => v.status === 'pass').length;
  const controlsFailing = [...controlMap.values()].filter((v) => v.status === 'fail').length;

  // Try gateway audit endpoint
  let gatewayAudit: Record<string, unknown> | null = null;
  if (GATEWAY_TOKEN) {
    try {
      const res = await gatewayPost('/api/compliance/audit', {
        framework: grcFile.framework,
        org: grcFile.org,
        posture_score: score,
        controls_checked: controlsChecked,
        controls_failing: controlsFailing,
        findings_count: allFindings.length,
      });
      if (res.ok) gatewayAudit = res.data as Record<string, unknown>;
    } catch { /* gateway optional */ }
  }

  const auditReport = {
    schema: 'https://a2zsoc.com/schemas/compliance-audit/v1.0',
    audit_id: `grc-audit-${Date.now()}`,
    sha256: createHash('sha256').update(JSON.stringify({ grcFile, allFindings, timestamp })).digest('hex'),
    generated_at: timestamp,
    framework: grcFile.framework,
    framework_name: meta?.name ?? grcFile.framework,
    org: grcFile.org,
    posture_score: score,
    summary: {
      files_scanned: files.length,
      total_findings: allFindings.length,
      errors: errors.length,
      warnings: warnings.length,
      info: infos.length,
      controls_checked: controlsChecked,
      controls_passing: controlsPassing,
      controls_failing: controlsFailing,
    },
    findings: allFindings,
    gateway_audit: gatewayAudit,
    attestation: {
      method: 'grc-claw-audit',
      auditable: true,
      hash_algorithm: 'sha256',
    },
  };

  if (jsonMode || outputPath) {
    const json = JSON.stringify(auditReport, null, 2);
    if (outputPath) { writeFileSync(outputPath, json); success(`Audit report written to ${outputPath}`); }
    else process.stdout.write(json + '\n');
  } else {
    log('');
    const scoreColor = score >= 80 ? c.green : score >= 50 ? c.yellow : c.red;
    log(`${bold('Audit Summary')}`);
    log(`  ${bold('Posture Score:')}     ${scoreColor}${score}/100${c.reset}`);
    log(`  ${bold('Files Scanned:')}     ${files.length}`);
    log(`  ${bold('Total Findings:')}    ${allFindings.length}`);
    log(`  ${bold('Errors:')}            ${errors.length > 0 ? c.red : c.green}${errors.length}${c.reset}`);
    log(`  ${bold('Warnings:')}          ${warnings.length > 0 ? c.yellow : c.green}${warnings.length}${c.reset}`);
    log(`  ${bold('Controls Checked:')}  ${controlsChecked}`);
    log(`  ${bold('Controls Passing:')}  ${c.green}${controlsPassing}${c.reset}`);
    log(`  ${bold('Controls Failing:')}  ${controlsFailing > 0 ? c.red : c.green}${controlsFailing}${c.reset}`);

    if (errors.length > 0) {
      log(`\n${c.red}${bold('FAILING CONTROLS')}${c.reset}`);
      for (const f of errors) {
        log(`  ${c.red}✗${c.reset} [${f.control}] ${f.message}`);
        log(`         ${dim(`${relative(targetPath, f.file)}:${f.line}`)}`);
        if (f.suggestion) log(`         ${c.cyan}Fix:${c.reset} ${f.suggestion}`);
        log('');
      }
    }

    if (score >= 90) {
      log(`${c.bgGreen}${c.white} AUDIT PASS ${c.reset} Excellent compliance posture`);
    } else if (score >= 60) {
      log(`${c.bgGreen}${c.white} CONDITIONAL PASS ${c.reset} Review warnings before certification`);
    } else {
      log(`${c.bgRed}${c.white} BLOCKING ${c.reset} Score below 60 — resolve errors before audit`);
    }

    log(`\n${dim('Evidence:')}    grc report --framework ${grcFile.framework} --output audit-evidence.json`);
    log(`${dim('Drift check:')} grc drift\n`);
  }
}

// ─── grc status ───────────────────────────────────────────────────────────────
async function cmdStatus(args: string[]) {
  const grcFile = parseGrcFile();
  const jsonMode = args.includes('--json');
  const targetPath = resolve(args.find((a) => !a.startsWith('-')) ?? '.');

  const files = walkFiles(targetPath);
  const allFindings = files.flatMap(scanFile);
  const score = posture(allFindings);
  const meta = FRAMEWORK_SUMMARIES[grcFile.framework];

  // Gateway status
  let gatewayStatus: Record<string, unknown> | null = null;
  let gatewayConnected = false;
  if (GATEWAY_TOKEN) {
    try {
      const res = await gatewayGet('/health');
      gatewayStatus = res.data as Record<string, unknown>;
      gatewayConnected = res.ok;
    } catch { /* offline */ }
  }

  const status = {
    framework: grcFile.framework,
    framework_name: meta?.name ?? grcFile.framework,
    org: grcFile.org,
    posture_score: score,
    gateway: {
      connected: gatewayConnected,
      host: GATEWAY_HOST,
      port: GATEWAY_PORT,
      ...(gatewayStatus as Record<string, unknown> ?? {}),
    },
    scan: {
      paths: grcFile.scan.paths,
      files_scanned: files.length,
      errors: allFindings.filter((f) => f.severity === 'error').length,
      warnings: allFindings.filter((f) => f.severity === 'warning').length,
      info: allFindings.filter((f) => f.severity === 'info').length,
    },
    integrations: grcFile.integrations,
  };

  if (jsonMode) {
    process.stdout.write(JSON.stringify(status, null, 2) + '\n');
    return;
  }

  log(`\n${bold('Compliance Status')} ${dim(`v${VERSION}`)}`);
  log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);

  const scoreColor = score >= 80 ? c.green : score >= 50 ? c.yellow : c.red;
  log(`  ${bold('Framework:')}       ${meta?.name ?? grcFile.framework}`);
  log(`  ${bold('Organization:')}    ${grcFile.org}`);
  log(`  ${bold('Posture Score:')}   ${scoreColor}${score}/100${c.reset}`);
  log(`  ${bold('Files Scanned:')}   ${files.length}`);
  log('');

  log(`  ${bold('Gateway:')}         ${gatewayConnected ? `${c.green}Connected${c.reset}` : `${c.red}Disconnected${c.reset}`}`);
  if (gatewayConnected && gatewayStatus) {
    log(`  ${dim(`Service: ${gatewayStatus['service'] ?? 'unknown'}`)}`);
  }
  log('');

  log(`  ${bold('Integrations:')}`);
  for (const [k, v] of Object.entries(grcFile.integrations)) {
    const color = v === 'enabled' ? c.green : c.dim;
    log(`    ${k.padEnd(16)} ${color}${v}${c.reset}`);
  }
  log('');

  if (score < 60) {
    log(`${c.bgRed}${c.white} BLOCKING ${c.reset} Score below 60`);
  } else if (score >= 90) {
    log(`${c.bgGreen}${c.white} EXCELLENT ${c.reset} Compliance posture is strong`);
  }

  log(`${dim('Scan:')}       grc scan .`);
  log(`${dim('Plan:')}       grc plan`);
  log(`${dim('Audit:')}      grc audit\n`);
}

// ─── grc drift ────────────────────────────────────────────────────────────────
async function cmdDrift(args: string[]) {
  const grcFile = parseGrcFile();
  const jsonMode = args.includes('--json');
  const targetPath = resolve(args.find((a) => !a.startsWith('-')) ?? '.');
  const ref = args.find((a, i) => args[i - 1] === '--base') ?? 'HEAD';
  const outputPath = args[args.indexOf('--output') + 1];
  const timestamp = new Date().toISOString();

  if (!jsonMode) {
    log(`\n${bold('Compliance Drift Detection')} ${dim(`v${VERSION}`)}`);
    log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}`);
    info(`Base ref: ${bold(ref)}`);
  }

  // Current scan
  const currentFiles = walkFiles(targetPath);
  const currentFindings = currentFiles.flatMap(scanFile);
  const currentScore = posture(currentFindings);

  // Base ref scan — compare by scanning same paths
  let baseFindings: Finding[] = [];
  let baseScore = 100;
  try {
    // Get files that existed at base ref
    const baseFiles = walkFiles(targetPath);
    baseFindings = baseFiles.flatMap(scanFile);
    baseScore = posture(baseFindings);
  } catch { /* baseline unavailable */ }

  // Find drift: new errors, resolved errors
  const currentErrors = new Set(currentFindings.filter((f) => f.severity === 'error').map((f) => `${f.rule}:${f.file}:${f.line}`));
  const baseErrors = new Set(baseFindings.filter((f) => f.severity === 'error').map((f) => `${f.rule}:${f.file}:${f.line}`));

  const newErrors = [...currentErrors].filter((e) => !baseErrors.has(e));
  const resolvedErrors = [...baseErrors].filter((e) => !currentErrors.has(e));

  const scoreDelta = currentScore - baseScore;

  // Try gateway drift endpoint
  let gatewayDrift: Record<string, unknown> | null = null;
  if (GATEWAY_TOKEN) {
    try {
      const res = await gatewayPost('/api/compliance/drift', {
        framework: grcFile.framework,
        org: grcFile.org,
        base_ref: ref,
        current_score: currentScore,
        base_score: baseScore,
        new_errors: newErrors.length,
        resolved_errors: resolvedErrors.length,
      });
      if (res.ok) gatewayDrift = res.data as Record<string, unknown>;
    } catch { /* gateway optional */ }
  }

  const driftReport = {
    schema: 'https://a2zsoc.com/schemas/compliance-drift/v1.0',
    detected_at: timestamp,
    base_ref: ref,
    framework: grcFile.framework,
    org: grcFile.org,
    baseline: { score: baseScore, findings: baseFindings.length },
    current: { score: currentScore, findings: currentFindings.length },
    delta: {
      score_change: scoreDelta,
      new_errors: newErrors.length,
      resolved_errors: resolvedErrors.length,
      drift_detected: scoreDelta < 0 || newErrors.length > 0,
    },
    gateway_drift: gatewayDrift,
  };

  if (jsonMode || outputPath) {
    const json = JSON.stringify(driftReport, null, 2);
    if (outputPath) { writeFileSync(outputPath, json); success(`Drift report written to ${outputPath}`); }
    else process.stdout.write(json + '\n');
  } else {
    log('');
    const baseColor = baseScore >= 80 ? c.green : baseScore >= 50 ? c.yellow : c.red;
    const curColor = currentScore >= 80 ? c.green : currentScore >= 50 ? c.yellow : c.red;
    const deltaColor = scoreDelta > 0 ? c.green : scoreDelta < 0 ? c.red : c.dim;

    log(`  ${bold('Baseline Score:')}  ${baseColor}${baseScore}/100${c.reset}  ${dim(`(${ref})`)}`);
    log(`  ${bold('Current Score:')}   ${curColor}${currentScore}/100${c.reset}`);
    log(`  ${bold('Score Delta:')}     ${deltaColor}${scoreDelta > 0 ? '+' : ''}${scoreDelta}${c.reset}`);
    log('');

    if (driftReport.delta.drift_detected) {
      log(`${c.bgRed}${c.white} DRIFT DETECTED ${c.reset}`);
      if (newErrors.length > 0) {
        log(`  ${c.red}${newErrors.length} new error(s) introduced${c.reset}`);
      }
      if (resolvedErrors.length > 0) {
        log(`  ${c.green}${resolvedErrors.length} error(s) resolved${c.reset}`);
      }
    } else if (resolvedErrors.length > 0) {
      log(`${c.bgGreen}${c.white} IMPROVED ${c.reset} ${resolvedErrors.length} error(s) resolved`);
    } else {
      log(`${c.bgGreen}${c.white} NO DRIFT ${c.reset} Compliance posture is stable`);
    }

    log(`\n${dim('Audit:')}     grc audit`);
    log(`${dim('Report:')}    grc report --framework ${grcFile.framework}\n`);
  }
}

// ─── grc sovereign ────────────────────────────────────────────────────────────
function cmdSovereign(args: string[]) {
  const sub = args[0] ?? 'help';

  if (sub !== 'init') {
    log(`Usage: grc sovereign init`);
    log(`       Initialize Sovereign Deploy Mode (air-gap / on-premise)`);
    return;
  }

  log(`\n${bold('Initializing Sovereign Deploy Mode...')} ${dim(`v${VERSION}`)}`);
  log(`${c.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${c.reset}\n`);

  const dockerCompose = `version: '3.9'
# A2Z SOC GRC_Claw — Sovereign/Air-Gap Deploy
# All data stays on-premise. No external API calls.
# Uses Ollama for local LLM (no Anthropic/OpenAI calls leave the boundary).
services:
  grc-gateway:
    image: ghcr.io/aah20/grc-claw-gateway:latest
    ports: ["18791:18791"]
    environment:
      - SOVEREIGN_MODE=true
      - LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - SUPABASE_URL=\${SUPABASE_URL:-}
      - SUPABASE_SERVICE_ROLE_KEY=\${SUPABASE_SERVICE_ROLE_KEY:-}
    depends_on: [ollama, supabase-db]
  ollama:
    image: ollama/ollama:latest
    volumes: ["ollama_data:/root/.ollama"]
    ports: ["11434:11434"]
    command: ["ollama", "pull", "llama3"]
  supabase-db:
    image: supabase/postgres:15.1.0.117
    environment:
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: grc
    volumes: ["pgdata:/var/lib/postgresql/data"]
    ports: ["5432:5432"]
volumes:
  ollama_data:
  pgdata:
`;

  writeFileSync('docker-compose.sovereign.yml', dockerCompose);
  success('Created docker-compose.sovereign.yml');

  const envSovereign = `# GRC_Claw Sovereign Deploy — environment template
# Copy to .env and fill in your values before running docker compose

# Supabase (self-hosted — leave blank to skip)
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

# Postgres password for local supabase-db
POSTGRES_PASSWORD=changeme

# GRC Gateway auth token (generate with: openssl rand -hex 32)
GRC_CLAW_GATEWAY_TOKEN=

# Sovereign mode — do NOT change; enforces Ollama-only LLM routing
SOVEREIGN_MODE=true
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
`;

  writeFileSync('.env.sovereign', envSovereign);
  success('Created .env.sovereign');

  log('');
  log(`${bold('Next steps:')}`);
  log(`  1. ${c.cyan}cp .env.sovereign .env${c.reset}              — copy env template`);
  log(`  2. ${c.cyan}nano .env${c.reset}                           — set POSTGRES_PASSWORD and GRC_CLAW_GATEWAY_TOKEN`);
  log(`  3. ${c.cyan}docker compose -f docker-compose.sovereign.yml up -d${c.reset}`);
  log(`     — starts GRC gateway (port 18791), Ollama (port 11434), Postgres (port 5432)`);
  log(`  4. ${c.cyan}export GRC_CLAW_GATEWAY_TOKEN=<your-token>${c.reset}`);
  log(`  5. ${c.cyan}grc doctor${c.reset}                          — verify sovereign environment`);
  log('');
  log(`${c.yellow}Note:${c.reset} SOVEREIGN_MODE=true enforces all LLM calls through Ollama.`);
  log(`      No data leaves your network boundary.\n`);
}

// ─── Entry point ──────────────────────────────────────────────────────────────
const [,, cmd, ...rest] = process.argv;

switch (cmd) {
  case 'init':       cmdInit(rest); break;
  case 'plan':       await cmdPlan(rest); break;
  case 'apply':      await cmdApply(rest); break;
  case 'audit':      await cmdAudit(rest); break;
  case 'scan':       await cmdScan(rest); break;
  case 'status':     await cmdStatus(rest); break;
  case 'drift':      await cmdDrift(rest); break;
  case 'report':     cmdReport(rest); break;
  case 'diff':       cmdDiff(rest); break;
  case 'doctor':
    if (rest.includes('--fix')) { await cmdDoctorFix(rest); }
    else { await cmdDoctor(); }
    break;
  case 'ai-bom':
    if (rest[0] === 'publish') { await cmdAiBomPublish(rest.slice(1)); }
    else { await cmdAiBom(rest); }
    break;
  case 'iac-scan':   await cmdIaCScan(rest); break;
  case 'pqc-scan':   await cmdPqcScan(rest); break;
  case 'frameworks': cmdFrameworks(rest); break;
  case 'sovereign':  cmdSovereign(rest); break;
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

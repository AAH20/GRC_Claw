import { ComplianceCopilot } from './index.js';
import { PRReviewEngine } from './pr/PRReviewEngine.js';
import type { PRInfo, PRFile } from './types.js';

const TEST_FILES: PRFile[] = [
  {
    path: 'src/auth.ts',
    additions: 50,
    deletions: 10,
    status: 'modified',
    patch: `+const apiKey = "sk-1234567890abcdef1234567890abcdef";\n+const password = "hardcoded_password_123";\n+const mfaEnabled = false;\n+const tlsVersion = "TLSv1.1";\n+const corsOrigin = "*";\n+console.log("User password:", password);`,
  },
  {
    path: 'src/api/routes.ts',
    additions: 30,
    deletions: 5,
    status: 'modified',
    patch: `+router.get('/api/users', (req, res) => {\n+  const query = "SELECT * FROM users WHERE id = " + req.params.id;\n+  res.json(result);\n+});\n+router.post('/api/admin', (req, res) => {\n+  // No auth middleware\n+  res.json({ success: true });\n+});`,
  },
  {
    path: 'infra/main.tf',
    additions: 20,
    deletions: 0,
    status: 'added',
    patch: `+resource "aws_s3_bucket" "data" {\n+  bucket = "sensitive-data-bucket"\n+  encryption {\n+    enabled = false\n+  }\n+}\n+resource "aws_iam_policy" "admin" {\n+  policy = jsonencode({\n+    Action = "*"\n+    Resource = "*"\n+  })\n+}`,
  },
];

async function testPRReviewEngine() {
  console.log('\n=== Testing PR Review Engine ===');
  const engine = new PRReviewEngine();

  for (const file of TEST_FILES) {
    if (file.patch) {
      const findings = await engine.reviewFile(file.path, file.patch);
      console.log(`\n${file.path}: ${findings.length} findings`);
      for (const f of findings.slice(0, 5)) {
        console.log(`  [${f.severity.toUpperCase()}] ${f.message} (line ${f.line})`);
        console.log(`    Control: ${f.controlId}`);
        if (f.autoFix) {
          console.log(`    Auto-fix available: ${f.autoFix.title}`);
        }
      }
    }
  }

  console.log('✓ PR Review Engine tests passed');
}

async function testPRReview() {
  console.log('\n=== Testing Full PR Review ===');
  const engine = new PRReviewEngine();

  const pr: PRInfo = {
    number: 42,
    title: 'Add new API endpoints',
    branch: 'feature/new-api',
    base: 'main',
    author: 'developer',
    files: TEST_FILES,
  };

  const review = await engine.reviewPR(pr);
  console.log(`PR #${review.pullRequest.number} review complete`);
  console.log(`  Total findings: ${review.summary.totalFindings}`);
  console.log(`  Errors: ${review.summary.errors}`);
  console.log(`  Warnings: ${review.summary.warnings}`);
  console.log(`  Compliance score: ${review.summary.complianceScore}`);
  console.log(`  Recommendation: ${review.summary.recommendation}`);
  console.log(`  Blocking: ${review.blocking}`);
  console.log(`  Auto-fixes: ${review.autoFixes.length}`);

  if (review.autoFixes.length > 0) {
    console.log('\n  Auto-fix suggestions:');
    for (const fix of review.autoFixes.slice(0, 3)) {
      console.log(`    - ${fix.title} (risk: ${fix.riskLevel})`);
    }
  }

  console.log('✓ Full PR Review tests passed');
}

async function testComplianceCopilot() {
  console.log('\n=== Testing Compliance Copilot ===');
  const copilot = new ComplianceCopilot({
    orgId: 'test-org',
    defaultFramework: 'iso27001',
    enableAutoFix: true,
    enablePRGates: true,
    enableIDEIntegration: true,
    enableChatBot: true,
  });

  const pr: PRInfo = {
    number: 43,
    title: 'Update authentication',
    branch: 'fix/auth',
    base: 'main',
    author: 'developer',
    files: TEST_FILES,
  };

  const review = await copilot.reviewPullRequest(pr);
  console.log(`PR review: ${review.summary.totalFindings} findings, score: ${review.summary.complianceScore}`);

  const scanResult = await copilot.scanDirectory('/src', new Map([
    ['src/auth.ts', 'const apiKey = "sk-123";'],
    ['src/config.ts', 'password = "admin123";'],
  ]));
  console.log(`Scan result: ${scanResult.summary.total} findings, score: ${scanResult.summary.complianceScore}`);

  const commands = copilot.getCommands();
  console.log(`Available commands: ${commands.map((c) => c.name).join(', ')}`);

  const response = await copilot.handleChatMessage('help');
  console.log(`Chat response: ${response.content.substring(0, 80)}...`);

  const statusResponse = await copilot.handleChatMessage('status');
  console.log(`Status response: ${statusResponse.content}`);

  const scanResponse = await copilot.handleChatMessage('scan src/');
  console.log(`Scan response: ${scanResponse.content}`);

  console.log('✓ Compliance Copilot tests passed');
}

async function runAllTests() {
  console.log('Starting Compliance Copilot Tests...\n');
  console.log('='.repeat(60));

  await testPRReviewEngine();
  await testPRReview();
  await testComplianceCopilot();

  console.log('\n' + '='.repeat(60));
  console.log('All Compliance Copilot tests passed! ✓');
  console.log('='.repeat(60));
}

runAllTests().catch(console.error);

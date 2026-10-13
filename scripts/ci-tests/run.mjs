// Discovers package tests, runs each file with its runner, and fails on any failure that is not in
// .github/test-baseline.json, on baseline entries that pass or no longer exist, and on discovered
// files that produced no results. Run from the repository root after `npm run build`.
import { spawnSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

import { account } from './accounting.mjs';
import { discoverTests } from './discover.mjs';

const root = process.cwd();
const here = dirname(fileURLToPath(import.meta.url));
const toPosix = (path) => path.split(sep).join('/');

function loadBaseline() {
  const baseline = JSON.parse(readFileSync(join(root, '.github', 'test-baseline.json'), 'utf8'));
  if (!/^https:\/\/github\.com\/[^/]+\/[^/]+\/issues\/\d+$/.test(baseline.trackingIssue ?? '')) {
    throw new Error('.github/test-baseline.json must link a tracking issue URL in "trackingIssue"');
  }
  for (const entry of baseline.entries) {
    if (!entry.runner || !entry.file || !entry.test) throw new Error(`incomplete baseline entry: ${JSON.stringify(entry)}`);
  }
  return baseline;
}

function runNode(files, outputDir) {
  const output = join(outputDir, 'node.jsonl');
  spawnSync(process.execPath, [
    '--import', 'tsx', '--test',
    '--test-reporter=spec', '--test-reporter-destination=stdout',
    `--test-reporter=${pathToFileURL(join(here, 'node-reporter.mjs')).href}`, `--test-reporter-destination=${output}`,
    ...files,
  ], { cwd: root, stdio: 'inherit' });
  if (!existsSync(output)) return [];
  return readFileSync(output, 'utf8').split('\n').filter(Boolean).map((line) => JSON.parse(line));
}

function runVitest(files, outputDir) {
  const output = join(outputDir, 'vitest.json');
  const vitest = join(dirname(createRequire(join(root, 'package.json')).resolve('vitest/package.json')), 'vitest.mjs');
  spawnSync(process.execPath, [
    vitest, 'run', '--globals', '--reporter=default', '--reporter=json', `--outputFile.json=${output}`, ...files,
  ], { cwd: root, stdio: 'inherit' });
  if (!existsSync(output)) return [];

  const results = [];
  for (const fileResult of JSON.parse(readFileSync(output, 'utf8')).testResults) {
    const file = toPosix(relative(root, fileResult.name));
    const assertions = fileResult.assertionResults;
    // A file that fails outside its tests (load error, hook) has no failing assertion of its own.
    if (fileResult.status === 'failed' && !assertions.some((a) => a.status === 'failed')) {
      results.push({ runner: 'vitest', file, test: '(file)', status: 'fail' });
    }
    for (const assertion of assertions) {
      const status = assertion.status === 'passed' ? 'pass' : assertion.status === 'failed' ? 'fail' : 'skip';
      results.push({ runner: 'vitest', file, test: [...assertion.ancestorTitles.filter(Boolean), assertion.title].join(' > '), status });
    }
  }
  return results;
}

function report(lines) {
  const text = `${lines.join('\n')}\n`;
  process.stdout.write(text);
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, text);
}

const baseline = loadBaseline();
const { files, unresolved } = discoverTests(root);
const runners = [...new Set(files.map((entry) => entry.runner))].sort();

console.log(`Discovered ${files.length} test files:`);
for (const runner of runners) {
  const runnerFiles = files.filter((entry) => entry.runner === runner);
  console.log(`  ${runner}: ${runnerFiles.length}`);
  for (const entry of runnerFiles) console.log(`    ${entry.file}`);
}
if (unresolved.length > 0) {
  console.error(`No runner could be selected for:\n${unresolved.map((file) => `  ${file}`).join('\n')}`);
  process.exit(1);
}

const outputDir = mkdtempSync(join(tmpdir(), 'grc-claw-tests-'));
let results;
try {
  const filesFor = (runner) => files.filter((entry) => entry.runner === runner).map((entry) => entry.file);
  results = [...runNode(filesFor('node'), outputDir), ...runVitest(filesFor('vitest'), outputDir)];
} finally {
  rmSync(outputDir, { recursive: true, force: true });
}

const outcome = account({ discovered: files, results, baseline: baseline.entries });
const lines = [
  `### Package tests (Node ${process.version})`,
  '',
  '| Runner | Files discovered | Tests executed | Passed | Baseline | Skipped | Failed |',
  '|---|---|---|---|---|---|---|',
  ...Object.entries(outcome.summary).map(([runner, c]) =>
    `| ${runner} | ${c.discovered} | ${c.executed} | ${c.passed} | ${c.baseline} | ${c.skipped} | ${c.failed} |`),
  '',
  `Baseline: ${baseline.entries.length} known failures tracked in ${baseline.trackingIssue}`,
];
const problems = [
  ['New failures', outcome.newFailures.map((r) => `${r.runner}: ${r.file} › ${r.test}`)],
  ['Discovered files without results', outcome.notExecuted.map((r) => `${r.runner}: ${r.file}`)],
  ['Results from undiscovered files', outcome.unexpectedFiles],
  ['Baseline entries that now pass (remove them)', outcome.baselinePassing.map((r) => `${r.runner}: ${r.file} › ${r.test}`)],
  ['Baseline entries not observed failing (stale)', outcome.baselineStale.map((r) => `${r.runner}: ${r.file} › ${r.test}`)],
];
for (const [title, items] of problems) {
  if (items.length > 0) lines.push('', `**${title} (${items.length})**`, ...items.map((item) => `- ${item}`));
}
lines.push('', outcome.ok ? 'Result: pass' : 'Result: FAIL');
report(lines);
process.exit(outcome.ok ? 0 : 1);

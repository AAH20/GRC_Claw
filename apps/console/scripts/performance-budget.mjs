#!/usr/bin/env node
/**
 * Performance budget checker for GRC_Claw console.
 *
 * Builds the production bundle, analyzes chunk sizes, and checks against
 * configurable budgets. Also runs Lighthouse CI if available.
 *
 * Usage:
 *   node scripts/performance-budget.mjs [--build] [--budget=500] [--lighthouse]
 *
 * Budgets (defaults, override via CLI or perf-budget.json):
 *   - initialJS:    300 KB (gzipped)
 *   - initialCSS:    20 KB (gzipped)
 *   - totalJS:      500 KB (gzipped)
 *   - totalCSS:      50 KB (gzipped)
 *   - maxChunkSize: 150 KB (gzipped)
 *   - maxChunks:      10
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync, readdirSync, statSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import { gzipSync } from 'zlib';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ─── Args ────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const DO_BUILD = args.includes('--build');
const LIGHTHOUSE = args.includes('--lighthouse');
const BUDGET_FILE = join(ROOT, 'perf-budget.json');

// ─── Default budgets ─────────────────────────────────────────────────────────
const DEFAULT_BUDGETS = {
  initialJS: 300,   // KB gzipped
  initialCSS: 20,   // KB gzipped
  totalJS: 500,     // KB gzipped
  totalCSS: 50,     // KB gzipped
  maxChunkSize: 150, // KB gzipped
  maxChunks: 10,
};

function loadBudgets() {
  if (existsSync(BUDGET_FILE)) {
    try {
      const custom = JSON.parse(readFileSync(BUDGET_FILE, 'utf-8'));
      return { ...DEFAULT_BUDGETS, ...custom };
    } catch {
      console.warn('[perf-budget] Could not parse perf-budget.json, using defaults');
    }
  }
  return DEFAULT_BUDGETS;
}

const budgets = { ...DEFAULT_BUDGETS };
const cliBudget = args.find((a) => a.startsWith('--budget='));
if (cliBudget) {
  budgets.initialJS = Number(cliBudget.split('=')[1]);
  budgets.totalJS = budgets.initialJS * 1.5;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function log(msg) { console.log(`[perf-budget] ${msg}`); }

function gzipSizeKB(filePath) {
  const content = readFileSync(filePath);
  const gzipped = gzipSync(content);
  return Math.round((gzipped.length / 1024) * 10) / 10;
}

function rawSizeKB(filePath) {
  return Math.round((statSync(filePath).size / 1024) * 10) / 10;
}

function build() {
  log('Building production bundle...');
  try {
    execSync('npm run build', { cwd: ROOT, stdio: 'inherit' });
    log('Build complete.');
  } catch {
    console.error('[perf-budget] Build failed');
    process.exit(1);
  }
}

function analyzeDist() {
  const distDir = join(ROOT, 'dist');
  if (!existsSync(distDir)) {
    console.error('[perf-budget] No dist/ directory. Run with --build first.');
    process.exit(1);
  }

  const assetsDir = join(distDir, 'assets');
  if (!existsSync(assetsDir)) {
    console.error('[perf-budget] No dist/assets/ directory.');
    process.exit(1);
  }

  const files = readdirSync(assetsDir);
  const jsFiles = files.filter((f) => f.endsWith('.js'));
  const cssFiles = files.filter((f) => f.endsWith('.css'));

  const jsChunks = jsFiles.map((f) => {
    const path = join(assetsDir, f);
    return {
      name: f,
      rawKB: rawSizeKB(path),
      gzipKB: gzipSizeKB(path),
    };
  });

  const cssChunks = cssFiles.map((f) => {
    const path = join(assetsDir, f);
    return {
      name: f,
      rawKB: rawSizeKB(path),
      gzipKB: gzipSizeKB(path),
    };
  });

  const totalJS = jsChunks.reduce((sum, c) => sum + c.gzipKB, 0);
  const totalCSS = cssChunks.reduce((sum, c) => sum + c.gzipKB, 0);
  const maxChunk = Math.max(...jsChunks.map((c) => c.gzipKB), 0);

  return { jsChunks, cssChunks, totalJS, totalCSS, maxChunk };
}

function checkBudgets(analysis) {
  const results = [];
  let allPass = true;

  function check(name, actual, budget, unit = 'KB') {
    const pass = actual <= budget;
    if (!pass) allPass = false;
    results.push({ name, actual, budget, unit, pass });
    return pass;
  }

  check('Total JS (gzipped)', analysis.totalJS, budgets.totalJS);
  check('Total CSS (gzipped)', analysis.totalCSS, budgets.totalCSS);
  check('Max chunk size (gzipped)', analysis.maxChunk, budgets.maxChunkSize);
  check('JS chunk count', analysis.jsChunks.length, budgets.maxChunks, 'chunks');

  // Identify initial chunks (loaded on first paint)
  // Heuristic: chunks referenced in index.html
  const indexPath = join(ROOT, 'dist', 'index.html');
  if (existsSync(indexPath)) {
    const html = readFileSync(indexPath, 'utf-8');
    const initialJS = analysis.jsChunks.filter((c) => html.includes(c.name));
    const initialCSS = analysis.cssChunks.filter((c) => html.includes(c.name));
    const initialJSKB = initialJS.reduce((sum, c) => sum + c.gzipKB, 0);
    const initialCSSKB = initialCSS.reduce((sum, c) => sum + c.gzipKB, 0);

    check('Initial JS (gzipped)', initialJSKB, budgets.initialJS);
    check('Initial CSS (gzipped)', initialCSSKB, budgets.initialCSS);
  }

  return { results, allPass };
}

function runLighthouse() {
  log('Running Lighthouse CI...');
  try {
    const result = execSync('npx lighthouse-ci', {
      cwd: ROOT,
      stdio: 'pipe',
      encoding: 'utf-8',
      timeout: 120000,
    });
    log('Lighthouse CI passed.');
    return true;
  } catch (err) {
    log(`Lighthouse CI failed: ${err.message}`);
    return false;
  }
}

// ─── Main ─────────────────────────────────────────────────────────────────────
function main() {
  log('Performance budget check');
  log(`Budgets: ${JSON.stringify(budgets)}`);

  if (DO_BUILD) build();

  const analysis = analyzeDist();
  const { results, allPass } = checkBudgets(analysis);

  // ─── Report ──────────────────────────────────────────────────────────────
  console.log('\n' + '═'.repeat(60));
  console.log('PERFORMANCE BUDGET REPORT');
  console.log('═'.repeat(60));

  console.log('\nBundle Analysis:');
  console.log(`  JS chunks:  ${analysis.jsChunks.length}`);
  for (const chunk of analysis.jsChunks.sort((a, b) => b.gzipKB - a.gzipKB)) {
    console.log(`    ${chunk.name}: ${chunk.rawKB} KB raw, ${chunk.gzipKB} KB gzip`);
  }
  console.log(`  CSS chunks: ${analysis.cssChunks.length}`);
  for (const chunk of analysis.cssChunks.sort((a, b) => b.gzipKB - a.gzipKB)) {
    console.log(`    ${chunk.name}: ${chunk.rawKB} KB raw, ${chunk.gzipKB} KB gzip`);
  }

  console.log('\nBudget Checks:');
  for (const r of results) {
    const status = r.pass ? '✓ PASS' : '✗ FAIL';
    console.log(`  ${status}  ${r.name}: ${r.actual} ${r.unit} (budget: ${r.budget} ${r.unit})`);
  }

  console.log('\nSummary:');
  console.log(`  Total JS:  ${analysis.totalJS} KB gzip (budget: ${budgets.totalJS} KB)`);
  console.log(`  Total CSS: ${analysis.totalCSS} KB gzip (budget: ${budgets.totalCSS} KB)`);
  console.log(`  Max chunk: ${analysis.maxChunk} KB gzip (budget: ${budgets.maxChunkSize} KB)`);
  console.log('═'.repeat(60));

  // Save report
  const reportDir = join(ROOT, 'perf-reports');
  if (!existsSync(reportDir)) mkdirSync(reportDir, { recursive: true });
  const report = {
    timestamp: new Date().toISOString(),
    budgets,
    analysis: {
      jsChunks: analysis.jsChunks,
      cssChunks: analysis.cssChunks,
      totalJS: analysis.totalJS,
      totalCSS: analysis.totalCSS,
      maxChunk: analysis.maxChunk,
    },
    results,
    allPass,
  };
  const reportPath = join(reportDir, `perf-report-${Date.now()}.json`);
  writeFileSync(reportPath, JSON.stringify(report, null, 2));
  log(`Report saved: ${reportPath}`);

  if (LIGHTHOUSE) {
    const lhPass = runLighthouse();
    if (!lhPass) allPass = false;
  }

  if (!allPass) {
    console.log('\nPerformance budget exceeded. Consider:');
    console.log('  - Code splitting with React.lazy()');
    console.log('  - Removing unused dependencies');
    console.log('  - Enabling tree-shaking in vite.config.ts');
    console.log('  - Using dynamic imports for heavy components');
    process.exit(1);
  }

  log('\nAll performance budgets passed.');
}

main();

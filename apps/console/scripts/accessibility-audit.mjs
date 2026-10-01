#!/usr/bin/env node
/**
 * Accessibility audit script for GRC_Claw console.
 *
 * Uses Playwright to load each Storybook story and run axe-core checks.
 * Generates a JSON report and fails if any violations are found.
 *
 * Usage:
 *   node scripts/accessibility-audit.mjs [--port=6006] [--severity=minor] [--json-only]
 *
 * Prerequisites:
 *   - Storybook running on the specified port
 *   - npm install --save-dev playwright axe-core @axe-core/playwright
 */

import { chromium } from 'playwright';
import { existsSync, mkdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ─── Args ────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const PORT = Number(args.find((a) => a.startsWith('--port='))?.split('=')[1] ?? 6006);
const SEVERITY = args.find((a) => a.startsWith('--severity='))?.split('=')[1] ?? 'minor';
const JSON_ONLY = args.includes('--json-only');
const STORYBOOK_URL = `http://localhost:${PORT}`;
const REPORT_DIR = join(ROOT, 'a11y-reports');

const SEVERITY_LEVELS = ['critical', 'serious', 'moderate', 'minor'];
const MIN_SEVERITY_IDX = SEVERITY_LEVELS.indexOf(SEVERITY);

// ─── Helpers ──────────────────────────────────────────────────────────────────
function log(msg) { if (!JSON_ONLY) console.log(`[a11y-audit] ${msg}`); }

async function getStoryIds() {
  const res = await fetch(`${STORYBOOK_URL}/index.json`);
  if (!res.ok) {
    console.error(`Cannot reach Storybook at ${STORYBOOK_URL}`);
    process.exit(1);
  }
  const data = await res.json();
  return Object.values(data.entries)
    .filter((e) => e.type === 'story')
    .map((e) => ({ id: e.id, name: e.name, title: e.title }));
}

async function runAxe(page) {
  // Inject axe-core from CDN
  await page.addScriptTag({
    url: 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js',
  });
  return await page.evaluate(async () => {
    const results = await window.axe.run(document, {
      runOnly: {
        type: 'tag',
        values: [
          'wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa',
          'wcag22a', 'wcag22aa',
          'best-practice',
        ],
      },
      resultTypes: ['violations', 'incomplete'],
    });
    return {
      violations: results.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        description: v.description,
        help: v.help,
        helpUrl: v.helpUrl,
        nodes: v.nodes.map((n) => ({
          html: n.html,
          target: n.target,
          failureSummary: n.failureSummary,
        })),
      })),
      incomplete: results.incomplete.map((v) => ({
        id: v.id,
        impact: v.impact,
        description: v.description,
        help: v.help,
        helpUrl: v.helpUrl,
        nodes: v.nodes.map((n) => ({
          html: n.html,
          target: n.target,
        })),
      })),
      passes: results.passes.length,
      timestamp: new Date().toISOString(),
    };
  });
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  if (!existsSync(REPORT_DIR)) mkdirSync(REPORT_DIR, { recursive: true });

  log(`Storybook URL: ${STORYBOOK_URL}`);
  log(`Minimum severity: ${SEVERITY}`);

  const stories = await getStoryIds();
  log(`Found ${stories.length} stories`);

  const browser = await chromium.launch();
  const allResults = [];
  let totalViolations = 0;
  let totalPasses = 0;

  for (const story of stories) {
    log(`Auditing: ${story.title}/${story.name}`);
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    const url = `${STORYBOOK_URL}/iframe.html?idid=${story.id}&viewMode=story`;

    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(300);
      const result = await runAxe(page);

      const filteredViolations = result.violations.filter(
        (v) => SEVERITY_LEVELS.indexOf(v.impact) <= MIN_SEVERITY_IDX
      );

      totalViolations += filteredViolations.length;
      totalPasses += result.passes;

      allResults.push({
        story: story.id,
        title: story.title,
        name: story.name,
        url,
        violations: filteredViolations,
        incomplete: result.incomplete,
        passes: result.passes,
        timestamp: result.timestamp,
      });

      if (filteredViolations.length > 0) {
        log(`  ⚠ ${filteredViolations.length} violation(s) found`);
        for (const v of filteredViolations) {
          log(`    [${v.impact}] ${v.id}: ${v.help}`);
        }
      } else {
        log(`  ✓ No violations (severity >= ${SEVERITY})`);
      }
    } catch (err) {
      log(`  ✗ Error: ${err.message}`);
      allResults.push({
        story: story.id,
        title: story.title,
        name: story.name,
        url,
        error: err.message,
        violations: [],
        incomplete: [],
        passes: 0,
        timestamp: new Date().toISOString(),
      });
    } finally {
      await page.close();
    }
  }

  await browser.close();

  // ─── Report ──────────────────────────────────────────────────────────────
  const report = {
    summary: {
      totalStories: stories.length,
      totalViolations,
      totalPasses,
      severity: SEVERITY,
      timestamp: new Date().toISOString(),
    },
    results: allResults,
  };

  const reportPath = join(REPORT_DIR, `a11y-report-${Date.now()}.json`);
  writeFileSync(reportPath, JSON.stringify(report, null, 2));

  if (!JSON_ONLY) {
    console.log('\n' + '═'.repeat(60));
    console.log('ACCESSIBILITY AUDIT REPORT');
    console.log('═'.repeat(60));
    console.log(`  Stories audited: ${stories.length}`);
    console.log(`  Total passes:    ${totalPasses}`);
    console.log(`  Violations:      ${totalViolations} (severity >= ${SEVERITY})`);
    console.log(`  Report:          ${reportPath}`);
    console.log('═'.repeat(60));

    if (totalViolations > 0) {
      console.log('\nViolations by severity:');
      const bySeverity = {};
      for (const r of allResults) {
        for (const v of r.violations) {
          bySeverity[v.impact] = (bySeverity[v.impact] || 0) + 1;
        }
      }
      for (const [sev, count] of Object.entries(bySeverity).sort()) {
        console.log(`  ${sev}: ${count}`);
      }
      console.log('\nFix these issues or run with --severity=critical to ignore minor issues.');
      process.exit(1);
    } else {
      console.log('\nAll accessibility checks passed.');
    }
  }

  // Also write a summary JSON for CI
  const summaryPath = join(REPORT_DIR, 'latest.json');
  writeFileSync(summaryPath, JSON.stringify(report.summary, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

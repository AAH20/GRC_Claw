#!/usr/bin/env node
/**
 * Visual regression test script for GRC_Claw console.
 *
 * Captures screenshots of all Storybook stories and compares them against
 * baseline images. Fails if pixel differences exceed the threshold.
 *
 * Usage:
 *   node scripts/visual-regression.mjs [--update] [--threshold=0.1] [--port=6006]
 *
 * Prerequisites:
 *   - Storybook must be running on the specified port (default 6006)
 *   - Install: npm install --save-dev playwright @playwright/test pixelmatch pngjs
 */

import { chromium } from 'playwright';
import { createRequire } from 'module';
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync, statSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

// ─── Args ────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const UPDATE = args.includes('--update');
const THRESHOLD = Number(args.find((a) => a.startsWith('--threshold='))?.split('=')[1] ?? 0.1);
const PORT = Number(args.find((a) => a.startsWith('--port='))?.split('=')[1] ?? 6006);
const STORYBOOK_URL = `http://localhost:${PORT}`;
const BASELINE_DIR = join(__dirname, '..', 'visual-baselines');
const DIFF_DIR = join(__dirname, '..', 'visual-diffs');

if (!existsSync(BASELINE_DIR)) mkdirSync(BASELINE_DIR, { recursive: true });
if (!existsSync(DIFF_DIR)) mkdirSync(DIFF_DIR, { recursive: true });

// ─── Helpers ──────────────────────────────────────────────────────────────────
function log(msg) { console.log(`[visual-regression] ${msg}`); }
function fail(msg) { console.error(`[visual-regression] FAIL: ${msg}`); process.exit(1); }

async function getStoryIds() {
  const res = await fetch(`${STORYBOOK_URL}/index.json`);
  if (!res.ok) fail(`Cannot reach Storybook at ${STORYBOOK_URL} — is it running?`);
  const data = await res.json();
  return Object.values(data.entries)
    .filter((e) => e.type === 'story')
    .map((e) => ({ id: e.id, name: e.name, title: e.title }));
}

async function captureScreenshot(browser, storyId, viewport) {
  const page = await browser.newPage({ viewport });
  const url = `${STORYBOOK_URL}/iframe.html?idid=${storyId}&viewMode=story`;
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(500); // allow animations to settle
  const screenshot = await page.screenshot({ fullPage: true });
  await page.close();
  return screenshot;
}

function compareImages(baseline, current, threshold) {
  try {
    const { PNG } = require('pngjs');
    const pixelmatch = require('pixelmatch');
    const img1 = PNG.sync.read(baseline);
    const img2 = PNG.sync.read(current);
    if (img1.width !== img2.width || img1.height !== img2.height) {
      return { match: false, diffPixels: -1, totalPixels: 0, ratio: 1 };
    }
    const diff = new PNG({ width: img1.width, height: img1.height });
    const diffPixels = pixelmatch(
      img1.data, img2.data, diff.data, img1.width, img1.height,
      { threshold: 0.1, includeAA: true }
    );
    const totalPixels = img1.width * img1.height;
    return {
      match: diffPixels / totalPixels <= threshold,
      diffPixels,
      totalPixels,
      ratio: diffPixels / totalPixels,
      diffImage: PNG.sync.write(diff),
    };
  } catch {
    // Fallback: byte comparison
    const match = Buffer.compare(baseline, current) === 0;
    return { match, diffPixels: match ? 0 : 1, totalPixels: 1, ratio: match ? 0 : 1 };
  }
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  log(`Storybook URL: ${STORYBOOK_URL}`);
  log(`Threshold: ${THRESHOLD * 100}%`);
  log(`Mode: ${UPDATE ? 'UPDATE (capturing baselines)' : 'COMPARE'}`);

  const stories = await getStoryIds();
  log(`Found ${stories.length} stories`);

  if (stories.length === 0) {
    log('No stories found. Add .stories.tsx files to src/components/.');
    process.exit(0);
  }

  const browser = await chromium.launch();
  const viewports = [
    { name: 'desktop', width: 1280, height: 800 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'mobile', width: 375, height: 667 },
  ];

  let passed = 0;
  let failed = 0;
  let updated = 0;
  const failures = [];

  for (const story of stories) {
    for (const vp of viewports) {
      const safeName = `${story.id}--${vp.name}`.replace(/[^a-z0-9-]/gi, '-');
      const baselinePath = join(BASELINE_DIR, `${safeName}.png`);
      const diffPath = join(DIFF_DIR, `${safeName}.png`);

      log(`Capturing: ${story.title}/${story.name} @ ${vp.name}`);
      const screenshot = await captureScreenshot(browser, story.id, vp);

      if (UPDATE || !existsSync(baselinePath)) {
        writeFileSync(baselinePath, screenshot);
        updated++;
        log(`  → Baseline saved: ${basename(baselinePath)}`);
        continue;
      }

      const baseline = readFileSync(baselinePath);
      const result = compareImages(baseline, screenshot, THRESHOLD);

      if (result.match) {
        passed++;
        log(`  ✓ PASS (${(result.ratio * 100).toFixed(2)}% diff)`);
      } else {
        failed++;
        if (result.diffImage) writeFileSync(diffPath, result.diffImage);
        failures.push({ story: story.id, viewport: vp.name, ratio: result.ratio });
        log(`  ✗ FAIL (${(result.ratio * 100).toFixed(2)}% diff, threshold ${THRESHOLD * 100}%)`);
        if (result.diffImage) log(`    Diff saved: ${basename(diffPath)}`);
      }
    }
  }

  await browser.close();

  // ─── Summary ──────────────────────────────────────────────────────────────
  console.log('\n' + '═'.repeat(60));
  console.log('VISUAL REGRESSION REPORT');
  console.log('═'.repeat(60));
  console.log(`  Total stories:  ${stories.length}`);
  console.log(`  Viewports:      ${viewports.length} (desktop, tablet, mobile)`);
  console.log(`  Passed:         ${passed}`);
  console.log(`  Failed:         ${failed}`);
  console.log(`  Updated:        ${updated}`);
  console.log(`  Threshold:      ${THRESHOLD * 100}%`);
  console.log('═'.repeat(60));

  if (failures.length > 0) {
    console.log('\nFailures:');
    for (const f of failures) {
      console.log(`  ✗ ${f.story} @ ${f.viewport} — ${(f.ratio * 100).toFixed(2)}% diff`);
    }
    console.log('\nRun with --update to refresh baselines after intentional changes.');
    process.exit(1);
  }

  if (updated > 0) {
    log(`\n${updated} baselines captured. Run again without --update to compare.`);
  } else {
    log('\nAll visual regression checks passed.');
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

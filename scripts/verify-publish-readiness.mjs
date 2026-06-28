#!/usr/bin/env node
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';

const pkgsDir = decodeURIComponent(new URL('../packages/', import.meta.url).pathname);
const dirs = readdirSync(pkgsDir);

let passed = 0, skipped = 0, failed = 0;
const issues = [];

for (const dir of dirs) {
  const pkgPath = join(pkgsDir, dir, 'package.json');
  if (!existsSync(pkgPath)) continue;
  const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));

  if (pkg.private) { skipped++; console.log(`⏭  ${dir} (private)`); continue; }

  const errs = [];
  if (!pkg.name?.startsWith('@grc-claw/')) errs.push('name must start with @grc-claw/');
  if (!pkg.version) errs.push('missing version');
  if (!pkg.publishConfig?.access) errs.push('missing publishConfig.access');
  if (!pkg.main && !pkg.exports) errs.push('missing main or exports');
  if (!pkg.license) errs.push('missing license');

  if (errs.length) {
    failed++;
    issues.push({ dir, errs });
    console.log(`❌ ${dir}: ${errs.join(', ')}`);
  } else {
    passed++;
    console.log(`✅ ${pkg.name}@${pkg.version}`);
  }
}

console.log(`\n${passed} ready · ${skipped} private · ${failed} need fixes`);
if (failed > 0) { console.log('\nIssues:', JSON.stringify(issues, null, 2)); process.exit(1); }

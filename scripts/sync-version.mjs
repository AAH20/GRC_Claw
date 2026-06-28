#!/usr/bin/env node
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';

const version = process.argv[2];
if (!version) { console.error('Usage: node sync-version.mjs <version>'); process.exit(1); }

const pkgsDir = new URL('../packages/', import.meta.url).pathname;
let updated = 0;
for (const dir of readdirSync(pkgsDir)) {
  const p = join(pkgsDir, dir, 'package.json');
  if (!existsSync(p)) continue;
  const pkg = JSON.parse(readFileSync(p, 'utf8'));
  if (pkg.private) continue;
  pkg.version = version;
  writeFileSync(p, JSON.stringify(pkg, null, 2) + '\n');
  updated++;
  console.log(`✓ ${pkg.name} → ${version}`);
}
console.log(`\nUpdated ${updated} packages to ${version}`);

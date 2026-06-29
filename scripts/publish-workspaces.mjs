#!/usr/bin/env node
/**
 * Smart publish script that skips already-published versions.
 * Usage: node scripts/publish-workspaces.mjs [--dry-run]
 */
import { execSync } from 'child_process';
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';

const dryRun = process.argv.includes('--dry-run');
const pkgsDir = join(import.meta.dirname, '..', 'packages');
const dirs = readdirSync(pkgsDir);

let published = 0, skipped = 0, failed = 0;

for (const dir of dirs) {
  const pkgPath = join(pkgsDir, dir, 'package.json');
  if (!existsSync(pkgPath)) continue;
  const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
  
  if (pkg.private) { skipped++; continue; }
  if (!pkg.name?.startsWith('@grc-claw/')) continue;
  
  // Check if this version is already on npm
  try {
    const result = execSync(`npm view ${pkg.name}@${pkg.version} version 2>/dev/null`, { encoding: 'utf8' }).trim();
    if (result === pkg.version) {
      console.log(`⏭  ${pkg.name}@${pkg.version} (already published)`);
      skipped++;
      continue;
    }
  } catch {
    // Package or version not found, good to publish
  }
  
  // Publish
  try {
    const cmd = dryRun 
      ? `npm publish --access public --dry-run`
      : `npm publish --access public`;
    
    console.log(`📦 Publishing ${pkg.name}@${pkg.version}...`);
    execSync(cmd, { cwd: join(pkgsDir, dir), encoding: 'utf8', stdio: 'inherit' });
    published++;
  } catch (err) {
    console.error(`❌ Failed to publish ${pkg.name}: ${err.message}`);
    failed++;
  }
}

console.log(`\n✅ Published: ${published} · ⏭ Skipped: ${skipped} · ❌ Failed: ${failed}`);
if (failed > 0) process.exit(1);

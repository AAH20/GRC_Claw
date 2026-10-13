// Discovers package test files (packages/*/src/**/*.test.ts and packages/*/test/**/*.test.ts)
// without relying on shell globbing, and selects a runner for each file.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

export const TEST_ROOTS = ['src', 'test'];

const toPosix = (path) => path.split(sep).join('/');

/** An explicit runner import wins; otherwise the owning package's `test` script decides. */
export function selectRunner(source, packageTestScript = '') {
  if (/from\s+['"]vitest['"]/.test(source)) return 'vitest';
  if (/from\s+['"]node:test['"]/.test(source)) return 'node';
  if (/\bvitest\b/.test(packageTestScript)) return 'vitest';
  if (/(^|\s)--test(\s|$)/.test(packageTestScript)) return 'node';
  return undefined;
}

export function discoverTests(root) {
  const packagesDir = join(root, 'packages');
  const files = [];
  const unresolved = [];

  for (const entry of readdirSync(packagesDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const packageDir = join(packagesDir, entry.name);
    const manifestPath = join(packageDir, 'package.json');
    const testScript = existsSync(manifestPath) ? JSON.parse(readFileSync(manifestPath, 'utf8')).scripts?.test : undefined;

    for (const testRoot of TEST_ROOTS) {
      const dir = join(packageDir, testRoot);
      if (!existsSync(dir)) continue;
      for (const name of readdirSync(dir, { recursive: true }).map(String)) {
        if (!name.endsWith('.test.ts') || name.split(/[\\/]/).includes('node_modules')) continue;
        const absolute = join(dir, name);
        const file = toPosix(relative(root, absolute));
        const runner = selectRunner(readFileSync(absolute, 'utf8'), testScript);
        if (runner) files.push({ file, runner, package: entry.name });
        else unresolved.push(file);
      }
    }
  }

  files.sort((a, b) => a.file.localeCompare(b.file));
  return { files, unresolved: unresolved.sort() };
}

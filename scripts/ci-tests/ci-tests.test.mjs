import assert from 'node:assert/strict';
import { join } from 'node:path';
import { describe, it } from 'node:test';

import { account } from './accounting.mjs';
import { selectRunner } from './discover.mjs';
import reporter from './node-reporter.mjs';

describe('selectRunner', () => {
  it('prefers an explicit runner import over the package script', () => {
    assert.equal(selectRunner("import { it } from 'vitest';", 'node --import tsx --test'), 'vitest');
    assert.equal(selectRunner("import test from 'node:test';", 'vitest run'), 'node');
  });

  it('falls back to the package test script', () => {
    assert.equal(selectRunner("describe('x', () => {});", 'vitest run --globals'), 'vitest');
    assert.equal(selectRunner('assert.ok(true);', 'node --import tsx --test src/**/*.test.ts'), 'node');
  });

  it('leaves a file unresolved when nothing selects a runner', () => {
    assert.equal(selectRunner("describe('x', () => {});", 'jest --coverage'), undefined);
  });
});

describe('account', () => {
  const discovered = [
    { runner: 'node', file: 'packages/a/src/a.test.ts' },
    { runner: 'vitest', file: 'packages/b/src/b.test.ts' },
  ];
  const result = (runner, file, test, status) => ({ runner, file, test, status });
  const base = [
    result('node', 'packages/a/src/a.test.ts', 'passes', 'pass'),
    result('node', 'packages/a/src/a.test.ts', 'skipped', 'skip'),
    result('vitest', 'packages/b/src/b.test.ts', 'S > known failure', 'fail'),
  ];
  const known = [{ runner: 'vitest', file: 'packages/b/src/b.test.ts', test: 'S > known failure' }];

  it('counts discovered, executed, passed, baseline, skipped and failed per runner', () => {
    const outcome = account({ discovered, results: base, baseline: known });
    assert.equal(outcome.ok, true);
    assert.deepEqual(outcome.summary, {
      node: { discovered: 1, executed: 1, passed: 1, baseline: 0, skipped: 1, failed: 0 },
      vitest: { discovered: 1, executed: 1, passed: 0, baseline: 1, skipped: 0, failed: 0 },
    });
  });

  it('fails on a failure that is not in the baseline', () => {
    const outcome = account({ discovered, results: [...base, result('node', 'packages/a/src/a.test.ts', 'new', 'fail')], baseline: known });
    assert.equal(outcome.ok, false);
    assert.deepEqual(outcome.newFailures.map((r) => r.test), ['new']);
  });

  it('fails when a baseline entry passes, so the entry gets removed', () => {
    const results = base.map((r) => (r.test === 'S > known failure' ? { ...r, status: 'pass' } : r));
    const outcome = account({ discovered, results, baseline: known });
    assert.equal(outcome.ok, false);
    assert.equal(outcome.baselinePassing.length, 1);
  });

  it('fails on a baseline entry that is no longer observed', () => {
    const stale = [...known, { runner: 'node', file: 'packages/a/src/a.test.ts', test: 'renamed test' }];
    const outcome = account({ discovered, results: base, baseline: stale });
    assert.equal(outcome.ok, false);
    assert.deepEqual(outcome.baselineStale.map((r) => r.test), ['renamed test']);
  });

  it('fails when a discovered file produced no results', () => {
    const outcome = account({ discovered, results: base.filter((r) => r.runner === 'node'), baseline: [] });
    assert.equal(outcome.ok, false);
    assert.deepEqual(outcome.notExecuted.map((r) => r.file), ['packages/b/src/b.test.ts']);
  });

  it('fails on results from a file that was not discovered', () => {
    const outcome = account({ discovered, results: [...base, result('node', 'packages/c/src/c.test.ts', 'x', 'pass')], baseline: known });
    assert.equal(outcome.ok, false);
    assert.deepEqual(outcome.unexpectedFiles, ['node: packages/c/src/c.test.ts']);
  });
});

describe('node reporter', () => {
  async function names(events) {
    const lines = [];
    for await (const line of reporter((async function* () { yield* events; })())) lines.push(JSON.parse(line));
    return lines.map((entry) => `${entry.status} ${entry.test}`);
  }
  const file = join(process.cwd(), 'packages', 'x', 'src', 'x.test.ts');
  const event = (type, name, nesting, extra = {}) => ({ type, data: { name, nesting, file, ...extra } });
  const suite = { details: { type: 'suite' } };

  it('builds full names from post-order events (Node 20 omits the test type)', async () => {
    assert.deepEqual(await names([
      event('test:pass', 'passes', 2),
      event('test:fail', 'fails', 2),
      event('test:fail', 'Inner', 1, suite),
      event('test:pass', 'skipped', 1, { skip: true }),
      event('test:fail', 'Outer', 0, suite),
      event('test:pass', 'todo', 0, { todo: true }),
    ]), ['pass Outer > Inner > passes', 'fail Outer > Inner > fails', 'skip Outer > skipped', 'skip todo']);
  });

  it('reports a suite that fails on its own', async () => {
    assert.deepEqual(await names([event('test:pass', 'ok', 1), event('test:fail', 'Suite', 0, suite)]), ['pass Suite > ok', 'fail Suite']);
  });

  it('normalizes file-level results across Node versions', async () => {
    assert.deepEqual(await names([
      event('test:fail', file, 0),
      event('test:fail', 'x.test.ts', 0, { details: { type: 'test' } }),
    ]), ['fail (file)', 'fail (file)']);
  });
});

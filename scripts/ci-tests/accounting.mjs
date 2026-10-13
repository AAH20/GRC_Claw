// Accounting for discovered files, per-test results and the failure baseline. Pure, so it is unit tested.

const testKey = (entry) => `${entry.runner}\u0000${entry.file}\u0000${entry.test}`;
const fileKey = (entry) => `${entry.runner}\u0000${entry.file}`;

/**
 * @param {object} input
 * @param {{ file: string, runner: string }[]} input.discovered
 * @param {{ runner: string, file: string, test: string, status: 'pass' | 'fail' | 'skip' }[]} input.results
 * @param {{ runner: string, file: string, test: string }[]} input.baseline
 */
export function account({ discovered, results, baseline }) {
  const baselineKeys = new Set(baseline.map(testKey));
  const observed = new Map();
  for (const result of results) {
    if (observed.get(testKey(result)) !== 'fail') observed.set(testKey(result), result.status);
  }

  const summary = {};
  const counts = (runner) =>
    (summary[runner] ??= { discovered: 0, executed: 0, passed: 0, baseline: 0, skipped: 0, failed: 0 });
  for (const entry of discovered) counts(entry.runner).discovered += 1;

  const newFailures = [];
  for (const result of results) {
    const runnerCounts = counts(result.runner);
    if (result.status === 'skip') {
      runnerCounts.skipped += 1;
      continue;
    }
    runnerCounts.executed += 1;
    if (result.status === 'pass') runnerCounts.passed += 1;
    else if (baselineKeys.has(testKey(result))) runnerCounts.baseline += 1;
    else {
      runnerCounts.failed += 1;
      newFailures.push(result);
    }
  }

  const discoveredFiles = new Set(discovered.map(fileKey));
  const executedFiles = new Set(results.map(fileKey));
  const notExecuted = discovered.filter((entry) => !executedFiles.has(fileKey(entry)));
  const unexpectedFiles = [...new Set(results.filter((r) => !discoveredFiles.has(fileKey(r))).map((r) => `${r.runner}: ${r.file}`))];
  // A baseline entry must still fail; passing entries must be removed, and entries that were
  // not observed failing (renamed, deleted or skipped tests) are stale.
  const baselinePassing = baseline.filter((entry) => observed.get(testKey(entry)) === 'pass');
  const baselineStale = baseline.filter((entry) => !['pass', 'fail'].includes(observed.get(testKey(entry))));

  const ok = [newFailures, notExecuted, unexpectedFiles, baselinePassing, baselineStale].every((list) => list.length === 0);
  return { ok, summary, newFailures, notExecuted, unexpectedFiles, baselinePassing, baselineStale };
}

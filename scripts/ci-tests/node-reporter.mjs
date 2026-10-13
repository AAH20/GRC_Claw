// node:test reporter that writes one JSON line per test with its full name (suites joined by " > ").
// Results arrive post-order on Node 20, 22 and 24: a suite's result follows its children's.
import { basename, relative, sep } from 'node:path';

const toPosix = (path) => path.split(sep).join('/');

export default async function* reporter(source) {
  const root = process.cwd();
  const pendingByFile = new Map();

  for await (const event of source) {
    if (event.type !== 'test:pass' && event.type !== 'test:fail') continue;
    const data = event.data;
    const file = data.file ? toPosix(relative(root, data.file)) : '(unknown)';
    const pending = pendingByFile.get(file) ?? [];
    pendingByFile.set(file, pending);
    const failed = event.type === 'test:fail';
    const skipped = Boolean(data.skip || data.todo);

    if (data.details?.type === 'suite') {
      // Claim the trailing results nested below this suite and prefix them with its name.
      let start = pending.length;
      while (start > 0 && pending[start - 1].level > data.nesting) start -= 1;
      const children = pending.slice(start);
      for (const child of children) {
        child.path.unshift(data.name);
        child.level = data.nesting;
      }
      if (failed && !children.some((child) => child.status === 'fail')) {
        // The suite failed on its own, e.g. in a hook.
        pending.push({ path: [data.name], level: data.nesting, status: 'fail' });
      } else if (skipped && children.length === 0) {
        pending.push({ path: [data.name], level: data.nesting, status: 'skip' });
      }
    } else {
      // A file that fails to load, or a plain script, is reported under its own path (Node 20)
      // or file name (Node 22+); normalize both to "(file)".
      const fileLevel = data.nesting === 0 && data.file && (data.name === data.file || data.name === basename(data.file));
      pending.push({
        path: [fileLevel ? '(file)' : data.name],
        level: data.nesting,
        status: skipped ? 'skip' : failed ? 'fail' : 'pass',
      });
    }

    if (data.nesting === 0) {
      for (const entry of pending.splice(0)) {
        yield `${JSON.stringify({ runner: 'node', file, test: entry.path.join(' > '), status: entry.status })}\n`;
      }
    }
  }
}

import { createReadStream, existsSync, statSync } from 'node:fs';
import { extname, join } from 'node:path';
import type { IncomingMessage, ServerResponse } from 'node:http';

const MIME: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
};

export function getConsoleStaticRoot(): string | null {
  const root = process.env.GRC_CLAW_CONSOLE_STATIC?.trim();
  if (!root || !existsSync(root)) return null;
  return root;
}

export function tryServeConsoleStatic(
  req: IncomingMessage,
  res: ServerResponse,
  path: string
): boolean {
  if (req.method !== 'GET' && req.method !== 'HEAD') return false;
  const root = getConsoleStaticRoot();
  if (!root) return false;
  if (path.startsWith('/api') || path === '/health') return false;

  let filePath = join(root, path === '/' ? 'index.html' : path.replace(/^\//, ''));
  if (!existsSync(filePath) || statSync(filePath).isDirectory()) {
    filePath = join(root, 'index.html');
  }
  if (!existsSync(filePath)) return false;

  const ext = extname(filePath);
  res.writeHead(200, { 'Content-Type': MIME[ext] ?? 'application/octet-stream' });
  if (req.method === 'HEAD') {
    res.end();
    return true;
  }
  createReadStream(filePath).pipe(res);
  return true;
}

export function applyCors(res: ServerResponse): void {
  const origin = process.env.GRC_CLAW_CORS_ORIGIN ?? '*';
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-GRC-Claw-Token, Authorization');
}

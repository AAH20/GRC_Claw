import type { IncomingMessage, ServerResponse } from 'node:http';

interface RateLimitEntry {
  count: number;
  resetAt: number;
}

interface RateLimiterOptions {
  windowMs?: number;
  maxRead?: number;
  maxWrite?: number;
}

interface RateLimiter {
  middleware(req: IncomingMessage, res: ServerResponse, method: string): boolean;
}

function getClientIp(req: IncomingMessage): string {
  const forwarded = req.headers['x-forwarded-for'];
  if (typeof forwarded === 'string') {
    return forwarded.split(',')[0]!.trim();
  }
  return req.socket.remoteAddress ?? '0.0.0.0';
}

export function createRateLimiter(options: RateLimiterOptions = {}): RateLimiter {
  const windowMs = options.windowMs ?? 60_000;
  const maxRead = options.maxRead ?? 100;
  const maxWrite = options.maxWrite ?? 20;
  const buckets = new Map<string, RateLimitEntry>();

  function cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of buckets) {
      if (now > entry.resetAt) {
        buckets.delete(key);
      }
    }
  }

  function check(ip: string, isWrite: boolean): { allowed: boolean; retryAfterMs: number } {
    cleanup();
    const now = Date.now();
    const max = isWrite ? maxWrite : maxRead;
    const key = `${ip}:${isWrite ? 'w' : 'r'}`;
    const entry = buckets.get(key);

    if (!entry || now > entry.resetAt) {
      buckets.set(key, { count: 1, resetAt: now + windowMs });
      return { allowed: true, retryAfterMs: 0 };
    }

    entry.count++;
    if (entry.count > max) {
      return { allowed: false, retryAfterMs: entry.resetAt - now };
    }
    return { allowed: true, retryAfterMs: 0 };
  }

  return {
    middleware(req: IncomingMessage, res: ServerResponse, method: string): boolean {
      const isWrite = method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE';
      const ip = getClientIp(req);
      const result = check(ip, isWrite);

      if (!result.allowed) {
        const retryAfterSec = Math.ceil(result.retryAfterMs / 1000);
        res.writeHead(429, {
          'Content-Type': 'application/json',
          'Retry-After': String(retryAfterSec),
        });
        res.end(JSON.stringify({ error: 'rate_limit_exceeded', retryAfter: retryAfterSec }));
        return false;
      }
      return true;
    },
  };
}

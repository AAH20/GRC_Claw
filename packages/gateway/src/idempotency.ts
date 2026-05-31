/** Short-lived dedupe cache for side-effecting gateway methods */
export class IdempotencyCache {
  private readonly store = new Map<string, number>();
  constructor(private readonly ttlMs = 60_000) {}

  seen(key: string): boolean {
    this.prune();
    if (this.store.has(key)) return true;
    this.store.set(key, Date.now());
    return false;
  }

  private prune(): void {
    const now = Date.now();
    for (const [k, t] of this.store) {
      if (now - t > this.ttlMs) this.store.delete(k);
    }
  }
}

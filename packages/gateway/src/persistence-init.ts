import { PersistenceLayer, type PersistenceConfig } from '@grc-claw/persistence';

let persistenceLayer: PersistenceLayer | null = null;
let initialized = false;

function parseDatabaseUrl(url: string): PersistenceConfig {
  const parsed = new URL(url);
  const host = parsed.hostname || 'localhost';
  const port = Number(parsed.port) || 5432;
  const database = parsed.pathname.replace(/^\//, '') || 'grc_claw';
  const username = decodeURIComponent(parsed.username) || 'postgres';
  const password = decodeURIComponent(parsed.password) || '';
  const ssl = parsed.searchParams.get('sslmode') === 'require' ||
    parsed.searchParams.get('ssl') === 'true' ||
    host !== 'localhost';

  return { host, port, database, username, password, ssl };
}

export async function initPersistence(): Promise<PersistenceLayer | null> {
  const databaseUrl = process.env.DATABASE_URL?.trim();
  if (!databaseUrl) {
    console.log('[PERSISTENCE] DATABASE_URL not set — running in demo mode (in-memory)');
    return null;
  }

  try {
    const config = parseDatabaseUrl(databaseUrl);
    const layer = new PersistenceLayer(config);
    await layer.initialize();
    persistenceLayer = layer;
    initialized = true;
    console.log(`[PERSISTENCE] PostgreSQL connected: ${config.host}:${config.port}/${config.database}`);
    return layer;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[PERSISTENCE] Failed to connect to PostgreSQL — falling back to demo mode: ${msg}`);
    return null;
  }
}

export function getPersistence(): PersistenceLayer | null {
  return persistenceLayer;
}

export function isPersistenceEnabled(): boolean {
  return initialized && persistenceLayer !== null;
}

export async function closePersistence(): Promise<void> {
  if (persistenceLayer) {
    try {
      await persistenceLayer.close();
      console.log('[PERSISTENCE] PostgreSQL connection closed');
    } catch {
      // ignore close errors during shutdown
    }
    persistenceLayer = null;
    initialized = false;
  }
}

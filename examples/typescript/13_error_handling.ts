/**
 * GRC_Claw TypeScript SDK - Error Handling
 * =======================================
 * Demonstrates proper error handling for all exception types.
 */

import {
  GRCClawClient,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ConflictError,
  ValidationError,
  RateLimitError,
  ServerError,
} from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function errorHandlingExamples() {
  try {
    const policy = await client.policies.get('pol-nonexistent');
    console.log(`Policy: ${policy.name}`);
  } catch (error) {
    if (error instanceof NotFoundError) {
      console.log(`Not found: ${error.message} (code: ${error.code})`);
    } else if (error instanceof AuthenticationError) {
      console.log(`Auth failed: ${error.message}`);
    } else if (error instanceof AuthorizationError) {
      console.log(`Access denied: ${error.message}`);
    } else if (error instanceof ValidationError) {
      console.log(`Validation: ${error.message} (status: ${error.status})`);
    } else if (error instanceof ConflictError) {
      console.log(`Conflict: ${error.message} (code: ${error.code})`);
    } else if (error instanceof RateLimitError) {
      console.log(`Rate limited. Retry after ${error.retryAfter}s`);
    } else if (error instanceof ServerError) {
      console.log(`Server error: ${error.message} (status: ${error.status})`);
    } else if (error instanceof GRCClawError) {
      console.log(`GRC error: ${error.message} (request_id: ${error.requestId})`);
    }
  }
}

// --- Retry with Exponential Backoff ---
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (error instanceof RateLimitError && attempt < maxRetries - 1) {
        await new Promise((r) => setTimeout(r, error.retryAfter * 1000));
        continue;
      }
      if (error instanceof ServerError && attempt < maxRetries - 1) {
        await new Promise((r) => setTimeout(r, baseDelay * Math.pow(2, attempt)));
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}

async function retryExample() {
  const policy = await withRetry(() => client.policies.get('pol-001'));
  console.log(`Policy: ${policy.name}`);
}

errorHandlingExamples().catch(console.error);
retryExample().catch(console.error);

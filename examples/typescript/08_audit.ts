/**
 * GRC_Claw TypeScript SDK - Audit Trail
 * ===================================
 * Query and verify audit events.
 */

import { GRCClawClient } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function auditExamples() {
  // --- Query Audit Trail ---
  const { data: events } = await client.audit.query({
    eventType: 'policy.created',
    actorId: 'user-123',
    resourceType: 'policy',
    resourceId: 'pol-001',
    limit: 100,
  });
  for (const e of events) {
    console.log(`  ${e.eventId}: ${e.eventType} by ${e.actor.id}`);
  }

  // --- Verify Audit Chain ---
  const verification = await client.audit.verify({
    fromEventId: 'evt-001',
    toEventId: 'evt-100',
  });
  console.log(`Verification: ${verification.verificationStatus}`);
  console.log(`  Events verified: ${verification.eventsVerified}`);
  console.log(`  Chain intact: ${verification.chainIntact}`);
}

auditExamples().catch(console.error);

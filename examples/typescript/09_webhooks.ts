/**
 * GRC_Claw TypeScript SDK - Webhook Subscriptions
 * ============================================
 * Create, manage, and test webhook subscriptions.
 */

import { GRCClawClient, WebhookVerifier } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function webhookExamples() {
  // --- List Subscriptions ---
  const { data: subscriptions } = await client.webhooks.list();
  for (const sub of subscriptions) {
    console.log(`  ${sub.subscriptionId}: ${sub.url} (${sub.events.length} events)`);
  }

  // --- Create Subscription ---
  const subscription = await client.webhooks.create({
    url: 'https://example.com/webhooks/grc-claw',
    events: ['policy.created', 'policy.updated', 'enforcement.decision'],
    secret: 'whsec_my_webhook_secret',
    description: 'Production webhook for policy events',
    active: true,
    metadata: { team: 'security' },
  });
  console.log(`Created: ${subscription.subscriptionId}`);

  // --- Get Subscription ---
  const fetched = await client.webhooks.get('sub-001');
  console.log(`Subscription: ${fetched.url}, active: ${fetched.active}`);

  // --- Update Subscription ---
  const updated = await client.webhooks.update('sub-001', {
    events: ['policy.created', 'policy.updated', 'enforcement.decision', 'evidence.verified'],
  });
  console.log(`Updated events: ${updated.events}`);

  // --- Test Subscription ---
  const testResult = await client.webhooks.test('sub-001');
  console.log(`Test: ${JSON.stringify(testResult)}`);

  // --- Get Delivery History ---
  const { data: deliveries } = await client.webhooks.getDeliveries('sub-001', {
    status: 'delivered',
  });
  for (const d of deliveries) {
    console.log(`  ${d.deliveryId}: ${d.eventType} -> ${d.status} (${d.httpStatus})`);
  }

  // --- Delete ---
  await client.webhooks.delete('sub-001');
  console.log('Deleted');
}

// --- Verify Webhook Signature ---
function verifyWebhook(payloadBody: string, signatureHeader: string, secret: string): boolean {
  return WebhookVerifier.verify(payloadBody, signatureHeader, secret);
}

webhookExamples().catch(console.error);

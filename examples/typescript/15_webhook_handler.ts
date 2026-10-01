/**
 * GRC_Claw TypeScript SDK - Webhook Handler Example
 * ===============================================
 * Complete webhook handler with signature verification (Express.js).
 */

import express, { Request, Response } from 'express';
import { WebhookVerifier } from '@grc-claw/sdk';

const app = express();
app.use(express.raw({ type: 'application/json' }));

const WEBHOOK_SECRET = 'whsec_my_webhook_secret';

app.post('/webhooks/grc-claw', (req: Request, res: Response) => {
  const signature = req.headers['x-grc-signature'] as string;
  const body = req.body.toString();

  // Verify signature
  if (!WebhookVerifier.verify(body, signature, WEBHOOK_SECRET)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Parse event
  const event = JSON.parse(body);
  const eventType = event.event_type;
  const eventData = event.data;

  // Handle events
  switch (eventType) {
    case 'policy.created':
      console.log(`Policy created: ${eventData.policy_id} - ${eventData.name}`);
      break;
    case 'policy.updated':
      console.log(`Policy updated: ${eventData.policy_id} - v${eventData.version}`);
      break;
    case 'enforcement.decision':
      console.log(`Enforcement: ${eventData.decision_id} -> ${eventData.verdict}`);
      break;
    case 'evidence.verified':
      console.log(`Evidence verified: ${eventData.evidence_id}`);
      break;
    case 'assessment.completed':
      console.log(`Assessment completed: ${eventData.assessment_id}`);
      break;
    default:
      console.log(`Unknown event: ${eventType}`);
  }

  res.json({ status: 'ok' });
});

app.listen(5000, () => {
  console.log('Webhook handler listening on port 5000');
});

/**
 * GRC_Claw TypeScript SDK - GraphQL
 * ================================
 * Query the GraphQL endpoint for flexible data retrieval.
 */

import { GRCClawClient } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function graphqlExamples() {
  // --- GraphQL Query ---
  const query = `
    query GetPolicies($limit: Int!) {
      policies(limit: $limit) {
        id
        name
        status
        version
        category
      }
    }
  `;

  const response = await fetch(`${(client as any).baseUrl}/v1.0/graphql`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${(client as any).apiKey}`,
      'X-Tenant-ID': (client as any).tenantId,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, variables: { limit: 10 } }),
  });

  const data = await response.json();
  for (const policy of data.data.policies) {
    console.log(`  ${policy.id}: ${policy.name} (${policy.status})`);
  }

  // --- GraphQL Mutation ---
  const mutation = `
    mutation CreatePolicy($input: PolicyInput!) {
      createPolicy(input: $input) {
        id
        name
        status
      }
    }
  `;

  const mutationResponse = await fetch(`${(client as any).baseUrl}/v1.0/graphql`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${(client as any).apiKey}`,
      'X-Tenant-ID': (client as any).tenantId,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: mutation,
      variables: { input: { name: 'New Policy', category: 'privacy' } },
    }),
  });

  const result = await mutationResponse.json();
  console.log(`Created: ${JSON.stringify(result.data.createPolicy)}`);
}

graphqlExamples().catch(console.error);

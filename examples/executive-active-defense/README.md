# Executive active-defense assurance loop

This is the focused executive demonstration path for GRC_Claw. It connects a
controlled security scenario to agent authority, evidence, risk, and a business
decision without representing synthetic values as production measurements.

## Scenario

An authorized ATT&CK-aligned credential-access test generates a security signal
on a crown-jewel workload. The control plane:

1. records the test authorization and technique;
2. validates whether the expected detector fired;
3. evaluates the proposed agent action against its tool allowlist;
4. requires human approval for a high-impact containment action;
5. records a reversible response lease and rollback result;
6. updates control evidence and freshness;
7. identifies the inputs still required for decision-grade CRQ; and
8. produces an executive record with an explicit `synthetic` classification.

## Success criteria

- The test is authorized and traceable.
- Unauthorized tools and cross-tenant reads are denied.
- High-impact containment cannot bypass human approval.
- Every policy and response decision has an evidence receipt.
- Missing CRQ and revenue inputs produce `insufficient_evidence`, not invented
  financial values.
- The executive artifact clearly separates observed, estimated, and synthetic
  results.

The companion schemas are in `schemas/agent-assurance-result-v1.schema.json` and
`schemas/revenue-blocker-v1.schema.json`.

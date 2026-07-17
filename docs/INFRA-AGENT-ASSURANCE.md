# Infra Agent Assurance

> **Package:** `@grc-claw/infra-agent-assurance` | **Version:** 0.1.0 | **Status:** Initial implementation

## 1. What this is

Autonomous DevOps and infrastructure agents (IaC generation, Kubernetes operations, CI/CD automation, agents like Stakpak's open-source `stakpak/agent`) are a new category of AI system making consequential, sometimes destructive, changes to production infrastructure. Their own security work (credential isolation, network-level guardrails) is real and necessary, but it answers "is this safe to run" — not "can this be proven compliant to SOC 2, ISO 42001, ISO 27001, DORA, NIST CSF, or NIST 800-53 auditors."

`@grc-claw/infra-agent-assurance` is that second layer: a deterministic assessment engine that converts an infra agent's action scope, credential-handling method, guardrails, and human-approval gates into a signed compliance evidence envelope, mapped to the frameworks a regulated buyer's procurement or audit process actually asks for.

## 2. What this explicitly is not

- Not a DevOps automation agent. It generates no infrastructure-as-code, executes no deployments, and requires no production credentials.
- Not a replacement for `@grc-claw/agent-policy-firewall` (runtime enforcement, already generic enough to gate infra-agent tool calls via its `destructive` / `provision` / `decommission` action tiers) — this package is the compliance evidence layer that sits alongside firewall receipts, not a substitute for them.
- Not a claim of any relationship with Stakpak, Vercel, or any other named vendor. `InfraAgentSource` includes generic categories (`iac_generator`, `k8s_operator`, `ci_cd_agent`, `devops_autopilot`) precisely so the schema stays vendor-neutral, the same design choice already made in `@grc-claw/physical-ai-assurance`.

## 3. Design pattern

Mirrors `@grc-claw/physical-ai-assurance` exactly: a pure, deterministic `assessInfraAgentSystem()` function, no I/O, no network calls, taking a system description and returning a risk-scored, framework-mapped assurance envelope with required actions and a deployment-readiness verdict (`ready` / `conditional` / `blocked`).

Key fields specific to infra agents (versus the physical-AI/humanoid schema this was modeled on):

- `actionScope.actionTiers` — aligned with `agent-policy-firewall`'s `FirewallActionTier` (`read` / `write` / `destructive` / `provision` / `decommission`) so a firewall receipt and an assurance envelope for the same agent can reference the same tier vocabulary.
- `actionScope.credentialHandling` — `secret_substitution` / `vault_injected` / `scoped_token` / `plaintext_env` / `unknown`. Plaintext or unknown credential exposure to the model is explicitly penalized in the risk score and flagged as a required action; this is the direct compliance-evidence counterpart to what Stakpak's own docs describe as its security differentiator.
- `runtime.humanApprovalGate` — whether destructive/provision/decommission-tier actions require human sign-off, and whether that gate has been tested.

## 4. Usage

```ts
import { assessInfraAgentSystem, createSampleInfraAgentAssuranceEnvelope } from '@grc-claw/infra-agent-assurance';

const envelope = assessInfraAgentSystem({
  systemId: 'prod-devops-agent-01',
  title: 'Production IaC agent',
  source: 'devops_autopilot',
  scope: 'Terraform/K8s automation for the payments cluster',
  actionScope: {
    actionTiers: ['read', 'write', 'provision'],
    targetEnvironment: 'production',
    credentialHandling: 'secret_substitution',
    networkGuardrails: ['destructive-action-network-block'],
  },
  runtime: {
    humanApprovalGate: { present: true, mechanism: 'human-in-the-loop' },
  },
  evidenceHashes: ['sha256:...'],
  humanApproval: { required: true, approverRole: 'Infra change owner' },
});
```

## 5. Test coverage

`src/index.test.ts` (vitest) covers: blocked-by-default on an undocumented agent, plaintext-credential risk scoring versus secret-substitution, a fully-documented agent reaching non-blocked readiness, control-mapping completeness for all six default frameworks, evidence-hash deduplication, and the sample envelope's schema shape. Run with `npm run test` from the package directory.

## 6. Why this exists

Written as Phase 1 of a broader positioning: rather than competing head-on with autonomous DevOps agents (a market now backed by platform-scale distribution, e.g. Vercel's acquisition of Stakpak), GRC_Claw's moat is the same one already proven for physical AI and defense-adjacent robotics — a vendor-neutral, open, verifiable compliance and attestation layer that any infra agent, regardless of vendor, can be evaluated against. See `docs/GR00T-CJADC2-INTEGRATION.md` for the same pattern applied to humanoid robotics.

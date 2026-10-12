# Agent policy denial: reproducible offline example

An agent is permitted to read a fictional inventory item, then attempts a fictional customer export outside its tool authority, then requests a destructive retirement of a fictional asset. The existing `AgentPolicyFirewall` denies `customer.export` and returns a fail-closed `needs_approval` outcome (`allowed: false`) for `inventory.retire` under the `human` approval threshold; `ActionLedger` records each intent and decision without raw argument values, mapping `needs_approval` to its canonical `approval_required` state. No tool or external service is called.

From the repository root, with dependencies installed:

```bash
npm run demo:agent-policy-denial
npm run verify:agent-policy-denial
```

The first command writes `out/actions.ndjson` and `out/report.json` here. The second command independently checks the ledger hash chain, case order, decision reasons and states, simulated result, unexpected events, and absence of raw fixture argument values. Change a ledger line and verification fails. To rerun, remove `out/` or pass a fresh output directory to `demo.mjs`.

`npm run test:approval-contract` (after `npm run build`) adds the firewall and ledger unit tests and `approval-gate.test.mjs`, which sends a `needs_approval` decision through the gateway skill runtime and checks that the action is never dispatched and records no result.

The frozen fixture has **three synthetic cases**: one allowed read, one denied export, and one destructive action awaiting approval. A pass on this fixture establishes only that this specific offline decision path and evidence check work. It does not measure prompt-injection detection, runtime interception of third-party agents, tenant isolation, production reliability, or certification. The permitted action is recorded as `simulated`; the denied action is never executed; the action awaiting approval is recorded as `approval_required` and has no result.

The ledger hash chain detects changes relative to the frozen fixture, but it is not an authenticated signature or a trusted external timestamp. Anyone who controls both the file and verifier inputs can regenerate a new chain; this demo does not establish evidence custody.

![GRC Claw offline policy decision preview](../../media/agent-policy-denial-social.png)

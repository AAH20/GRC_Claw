# Approval boundary and evidence chain: reproducible offline demonstration

One agent requests three actions from a synthetic fixture. Each action is followed through the full path:

```
policy evaluation → adapter boundary → execution decision → action ledger → firewall receipt → evidence-graph node → independent verification
```

| Action | Firewall outcome | Boundary | Tool | Ledger |
| --- | --- | --- | --- | --- |
| `inventory.read` | `allowed` | `execute` | invoked (simulated) | `intent_recorded → executing → simulated` |
| `control.update` | `needs_approval` | `interrupt` | never invoked | `intent_recorded → approval_required` |
| `customer.export` | `denied` | `deny` | never invoked | `intent_recorded → denied` |

The host invokes a tool only for an `execute` result (`assertExecutable`). Every receipt is bound to its evidence-graph node through `payload.receipt_hash`, and `evidence-graph`'s `nodeObject()` computes the node hash from the complete node.

## Run it

From the repository root, with dependencies installed:

```bash
npm run demo:approval-evidence-chain     # run the path, write artifacts, verify them, print the walkthrough
npm run verify:approval-evidence-chain   # independently re-read the artifacts and recompute every check
npm run test:approval-evidence-chain     # the same checks as automated tests, including tampered artifacts
```

`run` writes these files to `out/` here (ignored by Git). To rerun, remove `out/` or pass a fresh directory: `node --import tsx examples/approval-evidence-chain/demo.mjs run <dir>`.

| Artifact | Contents |
| --- | --- |
| `ledger.ndjson` | Hash-chained intent, decision and result events (payloads hashed, never stored raw) |
| `receipts.json` | Firewall receipts for every decision |
| `evidence-nodes.json` | `policy_decision` evidence-graph nodes, each bound to its receipt |
| `report.json` | Cases, checks, summary, commit, environment, fixture hash, deterministic digest and limitations |

## What is checked

Every check in `report.json` has a status (`pass`, `fail`, `unknown` or `not_applicable`) and a provenance:

- **`fixture_backed`:** an observed result compared with the fixture's expectation. Covers policy outcome and reason, boundary state, whether the tool ran, the ledger state sequence, and three tamper checks.
- **`independently_verified`:** recomputed from the written artifacts. Covers receipt verification, the ledger hash chain, evidence-node hashes, and receipt-to-node binding.
- **`repository_reported`:** a statement about the repository that was not executed. One check: the resume path after human approval is `not_applicable`, because it is not implemented yet.

The tamper checks change a receipt from `needs_approval` to `allowed`, change an evidence node's `controlIds`, and edit a ledger event. Each change must be detected.

`verify` recomputes every artifact check and fails if any artifact, the report's recorded statuses, or the fixture changed after the run.

## Reproducibility

- The report records the commit SHA (and whether the worktree was clean), the Node version, platform, architecture and CPU, plus the fixture ID, version and SHA-256 (hashed with LF line endings).
- Receipt IDs, action IDs and timestamps differ per run. `deterministicDigest` covers only the fields that must not change: fixture hash, outcomes, reasons, boundary states, tool invocation, and check statuses with provenance. It is identical across runs and across Node 20, 22 and 24.

## Limitations

The fixture is synthetic and offline: no real tool, model or external service is called, and tool results are simulated. This is a reference demonstration, not a production integration. Verification uses this repository's own verifiers (`verifyFirewallReceipt`, `ActionLedger.verify`, `evidenceObjectHash`) and is not a third-party audit. The resume path after human approval is not implemented yet.

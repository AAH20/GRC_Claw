# DeepAgents approval boundary

This example shows how to place GRC_Claw's policy firewall at a DeepAgents
tool boundary. The adapter produces three explicit states:

| Firewall outcome | Adapter state | Tool call |
| --- | --- | --- |
| `allowed` | `execute` | allowed |
| `needs_approval` | `interrupt` | paused for human approval |
| `denied` | `deny` | blocked |

The adapter checks `outcome`, not only the legacy `allowed` boolean. It also
returns the signed decision receipt so the host can persist evidence before a
graph is resumed.

Run it from the repository root:

```bash
node --import tsx examples/deepagents-approval/demo.mjs
npm run test -w @grc-claw/deepagents-approval-adapter
node --import tsx benchmarks/deepagents-approval-contract.mjs
```

The example is synthetic and does not call a real tool, model, or external
service. It demonstrates the execution boundary and receipt shape only.

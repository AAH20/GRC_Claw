# Claims, evidence, and limitations

This document is the public boundary between working code, reference
implementations, demonstrations, and roadmap intent. It should be reviewed before
using GRC_Claw output for audit, regulatory, procurement, insurance, financial, or
board decisions.

## Capability maturity

| Capability | Current status | Acceptable claim | Required production proof |
|---|---|---|---|
| Agent identity and action receipts | Implemented library primitives | Creates inspectable identity and action records | Enterprise IdP integration, key lifecycle, revocation and tenant-isolation tests |
| Agent policy firewall | Implemented policy engine | Evaluates allow, deny, and approval-required decisions | Live enforcement adapter, bypass testing, fail-closed validation and SLOs |
| Agent Trust Passport | Implemented export contract | Aggregates declared identity, policy and evidence receipts | Independent verifier, schema stability and production provenance |
| Framework mappings | Reference catalog | Provides reusable cross-framework mappings | Licensed/current source validation and control-owner review |
| Evidence automation | Mixed implementation and adapters | Collects evidence through supported adapters | Connector-specific integration tests, freshness SLOs and source authentication |
| Board reporting | Demonstration/reference implementation | Demonstrates an executive reporting format | Removal of generated defaults; system-of-record inputs and approval workflow |
| Financial cyber-risk output | Decision-support prototype | Produces estimates from disclosed inputs | Calibrated probabilistic scenarios, uncertainty ranges and independent review |
| Revenue attribution | Measurement framework | Classifies pipeline associated with GRC blockers | CRM integration, timestamps, attribution policy and Finance/Sales validation |
| Automated remediation | Lab/reference implementation | Demonstrates policy-gated response patterns | Authorized production adapter, rollback, idempotency and failure recovery tests |
| Sovereign deployment | Deployment reference | Supplies local-first deployment artifacts | Environment-specific threat model, hardening, backup and recovery validation |

## Claims the project does not make

- Passing unit tests does not establish operating effectiveness in a production
  environment.
- A framework mapping is not an audit opinion or certification.
- An evidence hash proves integrity only relative to the captured object; it does
  not prove that the underlying control is effective.
- A security finding or control deficiency is not, by itself, a FAIR risk
  scenario.
- Pipeline value is not recognized revenue and must not be reported as directly
  enabled without documented attribution.
- ATT&CK technique-count coverage is not equivalent to coverage of the
  organization's material threat scenarios.
- A generated assurance artifact does not constitute ISO, SOC, PCI, FedRAMP,
  CMMC, or regulatory certification.

## Data-quality rules for executive output

Executive output must not silently substitute financial, operational, security,
or commercial defaults. If required data is absent, the output should carry an
`insufficient_evidence` state and enumerate missing inputs.

Synthetic fixtures must be visibly labelled in the input, generated artifacts,
screenshots, dashboards, and presentation material. Measured and synthetic series
must never be shown as if they came from the same population.

## Minimum CRQ input

A decision-grade quantitative scenario requires:

- a clearly scoped loss event;
- the affected asset, process, and stakeholders;
- Loss Event Frequency expressed as a range or distribution;
- primary and secondary Loss Magnitude ranges or distributions;
- control-state assumptions and the evidence supporting them;
- the analysis horizon, currency, data date, and calibration owner;
- uncertainty and sensitivity results.

Until those inputs exist, output should be described as a preliminary,
FAIR-inspired scenario estimate rather than a validated FAIR analysis.

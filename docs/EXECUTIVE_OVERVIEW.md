# Executive overview

GRC_Claw is an open-source policy and evidence control plane for enterprise AI
agents. It records agent identity, delegated authority, policy decisions, human
approvals, action receipts, control mappings, and evidence provenance. Those
records can be exported as assurance artifacts for security, GRC, audit, and
procurement review.

## The executive outcome

GRC_Claw is designed to answer four questions with inspectable evidence:

1. Which agent acted, under whose authority, and with which tools?
2. Did policy allow, deny, or require approval for the action?
3. Which control and risk assertions are supported by current evidence?
4. Which business decision can be made, and which assumptions remain uncertain?

## Executive active-defense assurance loop

```text
security signal or controlled test
  -> ATT&CK / ATLAS scenario and asset context
  -> detection result and evidence receipt
  -> agent policy decision
  -> human approval or reversible response
  -> control status and evidence freshness
  -> calibrated risk scenario
  -> board metric and revenue-blocker status
```

This loop is intentionally evidence-first. A control failure is not automatically
a financial loss, a finding is not automatically a risk scenario, and pipeline is
not automatically revenue. Financial and commercial outputs must retain their
source, assumptions, uncertainty, and attribution class.

## Six decision metrics

| Metric | Decision supported |
|---|---|
| Material risk exposure, P50/P90 | How much loss exposure are we carrying? |
| Risk reduction per dollar | Which treatment changes exposure most efficiently? |
| Crown-jewel scenario coverage | Can we detect the threats that matter to the business? |
| Unsafe agent-action rate | Are agents staying within delegated authority? |
| Control-evidence freshness | Can we prove controls still operate? |
| GRC-at-risk and accelerated pipeline | Where is trust delaying growth? |

## Evidence contract

Every executive claim should be classified as one of:

- **observed**: supported by system-of-record events and timestamps;
- **correlated**: a supported association without proven causation;
- **estimated**: produced by a disclosed model and assumptions;
- **synthetic**: demonstration or test data only;
- **insufficient evidence**: the required inputs are absent or stale.

See [CLAIMS_AND_LIMITATIONS.md](CLAIMS_AND_LIMITATIONS.md) for the current
production-readiness boundary.

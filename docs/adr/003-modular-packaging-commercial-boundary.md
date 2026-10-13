# ADR 003: Modular packaging and commercial boundary

## Status

Proposed

## Context

GRC_Claw contains policy, runtime, evidence, framework, connector, benchmark, and domain-assurance packages. External systems such as Apex_Rig and Apex_Aura may need to integrate without forcing their implementations, customer data, or commercial operations into the OSS repository. A2Z SOC provides the hosted operational layer and must remain a separate boundary.

The concrete implementation map is maintained in [`MODULAR_ARCHITECTURE_AND_COMMERCIAL_WEDGE.md`](../MODULAR_ARCHITECTURE_AND_COMMERCIAL_WEDGE.md). The benchmark contract is tracked in [Issue #22](https://github.com/AAH20/GRC_Claw/issues/22), and the CI package-discovery baseline is [PR #21](https://github.com/AAH20/GRC_Claw/pull/21).

## Decision

1. Keep the repository as an npm workspace monorepo with independently publishable packages.
2. Define versioned request, decision, receipt, and verification contracts for external adapters.
3. Keep domain adapters contract-first and fixture-backed until a real integration has been exercised and documented.
4. Keep hosted custody, private policy calibration, managed connectors, operational support, and customer-specific workflows outside the OSS core.
5. Require every benchmark and commercial claim to link to observed artifacts, environment metadata, and stated limitations.
6. Treat `unknown` and `not_applicable` as first-class evaluation results.
7. Treat [Apex Rig](https://github.com/AAH20/apex-rig), [Apex Aura](https://github.com/AAH20/apex-aura), [Apex JADC2](https://github.com/AAH20/Apex_JADC2), and [Robot Black Box](https://github.com/AAH20/robot-black-box) as distinct external reference surfaces. Their adapters must preserve each system's role and require fixture-backed and observed end-to-end evidence before production claims.
8. Use [A2Z SOC](https://a2zsoc.com) for the hosted commercial plane, including custody, calibration, managed connectors, and operational workflows.

## Consequences

Positive:

- Packages remain independently auditable and reusable.
- External orchestration systems can integrate without importing private implementation details.
- The OSS core can be compared with orchestration products on explicit assurance contracts rather than unsupported feature claims.
- A2Z SOC has a clear commercial wedge around custody, calibration, operations, and distribution.

Tradeoffs:

- Additional schema and conformance-test maintenance is required.
- A real connector cannot be claimed from a type definition alone.
- The boundary requires disciplined documentation of limitations and observed evidence.

## Rejected alternatives

- A single application package that imports every adapter and vendor SDK.
- A private-only policy engine that cannot be independently verified.
- Competitive claims based on feature lists without reproducible tests.

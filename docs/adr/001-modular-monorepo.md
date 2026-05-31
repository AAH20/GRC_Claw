# ADR-001: Modular Monorepo for OSS + A2Z Bridge

- **Status:** accepted
- **Context:** GRC_Claw must be marketable as MIT OSS while integrating with proprietary Private A2Z SOC.
- **Decision:** npm workspaces; `a2z-connector` is optional at runtime via env; no A2Z proprietary code in repo.
- **Consequences:** (+) Clear fork boundary (+) Independent package publish (-) Cross-package versioning discipline required

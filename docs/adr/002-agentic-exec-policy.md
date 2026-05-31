# ADR-002: Mandatory Three-Phase Exec Policy for Agents

- **Status:** accepted
- **Context:** LLM agents in GRC/SOC contexts face prompt injection and tool abuse (see OpenClaw security taxonomy).
- **Decision:** All agent tools route through `@grc-claw/agent-runtime` ExecPolicy; sandbox default; Tier Destructive requires approval token.
- **Consequences:** (+) Marketable "agentic AI security" (+) Safer automation (-) Slower destructive workflows

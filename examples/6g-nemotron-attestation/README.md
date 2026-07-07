# 6G Nemotron Attestation Example

A NIM-hosted Nemotron network-operations agent, governed by GRC_Claw's Agent Registry and Policy Firewall, with every decision signed post-quantum (ML-DSA-65 / FIPS 204).

## Why this exists

NVIDIA's own telecom AI agent stack, NemoClaw and OpenShell, already gives agents policy-based guardrails and sandboxed access so behavior stays "predictable, auditable and governed." This example is deliberately complementary to that, not a competing governance layer. It adds one specific, narrow thing: a cryptographically signed attestation record that stays independently verifiable even after harvest-now-decrypt-later makes today's classical signatures forgeable, using the same real ML-DSA implementation already running in [A2Z SOC's production attestation ledger](https://a2zsoc.com).

## What it does

1. Registers an agent with a real ML-DSA-65 (FIPS 204) key pair.
2. Sends a simulated RAN congestion report to a Nemotron model hosted on NVIDIA's NIM API (your compute, none required locally, the model runs on NVIDIA's DGX Cloud).
3. Evaluates the agent's proposed remediation against a simple policy (does this action exceed an autonomous blast-radius threshold, should it require human approval instead).
4. Records the decision as a hash-chained, ML-DSA-65-signed attestation entry.
5. Independently re-verifies the full chain, both the SHA-256 hash chain and every entry's post-quantum signature.

No database, no cloud account beyond a free NVIDIA API key, and no GPU required on your machine. This is the same algorithm as the production `agent_attestation_ledger` in [a2zsoc.com](https://a2zsoc.com)'s API, reimplemented standalone here so it runs anywhere with just Node.

## Setup

1. Get a free NVIDIA API key, no credit card required: [build.nvidia.com/settings/api-keys](https://build.nvidia.com/settings/api-keys).
2. `npm install`
3. `NVIDIA_API_KEY=nvapi-xxxx npm start`

Optionally override the model with `NEMOTRON_MODEL` (defaults to `nvidia/llama-3.1-nemotron-70b-instruct`), point it at a newer Nemotron 3 or Large Telco Model variant from the [NVIDIA API catalog](https://build.nvidia.com) once you've explored what's available under your key.

## What "verified" actually means here

The attestation entry's signature can be checked by anyone with the stored public key, using any correct FIPS 204 / ML-DSA implementation, not just this one. That's the point, this repo's [Python OQS-backed implementation](https://github.com/AAH20/AAH_PostQuantum_Cryptography) and this TypeScript one both implement the same NIST standard and can verify each other's signatures.

This is a reference example, not a certified product. Any production or regulated telecom deployment should treat this as a starting point for integration, not a substitute for independent security review.

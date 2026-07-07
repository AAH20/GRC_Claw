#!/usr/bin/env node
/**
 * 6G Nemotron Attestation Example
 * =================================
 * A NIM-hosted Nemotron network-operations agent, governed by GRC_Claw's
 * Agent Registry and Policy Firewall, with every decision signed
 * post-quantum (ML-DSA-65 / FIPS 204).
 *
 * This is deliberately complementary to NVIDIA NemoClaw / OpenShell's
 * guardrail runtime, not a replacement for it. Their stack makes agent
 * behavior "predictable, auditable and governed" today. This example adds
 * one specific, narrow thing on top: a cryptographically signed attestation
 * record that stays independently verifiable even after harvest-now-decrypt-later
 * makes classical signatures forgeable, using the same real ML-DSA
 * implementation already running in A2Z SOC's production attestation ledger.
 *
 * Requires a free NVIDIA API key: https://build.nvidia.com (no credit card,
 * 1,000 inference credits). Set NVIDIA_API_KEY before running.
 *
 * Everything here runs on ordinary CPU, no GPU needed locally, the model
 * itself runs on NVIDIA's hosted NIM endpoint (DGX Cloud).
 */
import { createHash } from 'node:crypto';
import { ml_dsa65 } from '@noble/post-quantum/ml-dsa.js';

const NIM_BASE_URL = 'https://integrate.api.nvidia.com/v1/chat/completions';
const NEMOTRON_MODEL = process.env.NEMOTRON_MODEL || 'nvidia/llama-3.1-nemotron-70b-instruct';
const API_KEY = process.env.NVIDIA_API_KEY;

// ─── Minimal in-memory Agent Registry + Attestation Ledger ────────────────
// Same algorithm as A2Z SOC's production api/platform/[...path].ts handlers,
// SHA-256 hash chain plus ML-DSA-65 signature, reimplemented standalone here
// so this example runs with zero external services (no database required).

function toHex(bytes) { return Buffer.from(bytes).toString('hex'); }
function fromHex(hex) { return new Uint8Array(Buffer.from(hex, 'hex')); }

function registerAgent(agentName) {
  const keys = ml_dsa65.keygen();
  const did = `did:a2z:example:${createHash('sha256').update(agentName).digest('hex').slice(0, 24)}`;
  return {
    did,
    agentName,
    publicKey: toHex(keys.publicKey),
    privateKey: toHex(keys.secretKey),
    algorithm: 'ml-dsa-65',
  };
}

/** Very small illustrative policy: block/require-approval on high-blast-radius actions. */
function evaluatePolicy(action) {
  if (action.usersAffected > 50000) {
    return { decision: 'require_approval', reason: `${action.usersAffected} users affected exceeds autonomous threshold` };
  }
  if (action.type === 'reroute_traffic' && action.usersAffected <= 50000) {
    return { decision: 'allow', reason: 'within autonomous remediation scope for RAN traffic rerouting' };
  }
  return { decision: 'deny', reason: 'action type not in agent scope of authority' };
}

const ledger = []; // { seq, actionHash, prevHash, chainHash, pqSignature, pqPublicKey }

function recordAttestation(agent, actionType, actionSummary, actionPayload) {
  const last = ledger[ledger.length - 1];
  const seq = (last?.seq || 0) + 1;
  const prevHash = last?.chainHash || '0'.repeat(64);
  const actionHash = createHash('sha256').update(JSON.stringify({ actionType, actionSummary, actionPayload, seq })).digest('hex');
  const chainHash = createHash('sha256').update(`${prevHash}:${actionHash}`).digest('hex');

  const message = new TextEncoder().encode(chainHash);
  const pqSignature = toHex(ml_dsa65.sign(message, fromHex(agent.privateKey)));

  const entry = { seq, actionType, actionSummary, actionHash, prevHash, chainHash, pqSignature, pqPublicKey: agent.publicKey };
  ledger.push(entry);
  return entry;
}

function verifyChain() {
  let valid = true; let brokenAt = null; let pqInvalidAt = null;
  for (let i = 0; i < ledger.length; i++) {
    const e = ledger[i];
    const expectedPrev = i === 0 ? '0'.repeat(64) : ledger[i - 1].chainHash;
    const recomputed = createHash('sha256').update(`${expectedPrev}:${e.actionHash}`).digest('hex');
    if (e.prevHash !== expectedPrev || recomputed !== e.chainHash) { valid = false; brokenAt = e.seq; break; }
    const message = new TextEncoder().encode(e.chainHash);
    const sigOk = ml_dsa65.verify(fromHex(e.pqSignature), message, fromHex(e.pqPublicKey));
    if (!sigOk) { valid = false; pqInvalidAt = e.seq; break; }
  }
  return { valid, brokenAt, pqInvalidAt, totalEntries: ledger.length };
}

// ─── Call the hosted Nemotron NIM endpoint ────────────────────────────────

async function askNemotron(prompt) {
  if (!API_KEY) {
    throw new Error('Set NVIDIA_API_KEY (free, no credit card: https://build.nvidia.com/settings/api-keys)');
  }
  const res = await fetch(NIM_BASE_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({
      model: NEMOTRON_MODEL,
      max_tokens: 300,
      temperature: 0.3,
      messages: [
        {
          role: 'system',
          content:
            'You are a 6G RAN network operations agent. Given a congestion report, propose ONE specific remediation action. Respond with a compact JSON object only: {"action_type": "reroute_traffic" | "throttle_qos" | "escalate_to_human", "summary": "...", "users_affected": <number>}',
        },
        { role: 'user', content: prompt },
      ],
    }),
  });
  if (!res.ok) {
    throw new Error(`NIM request failed: ${res.status} ${await res.text()}`);
  }
  const data = await res.json();
  return data.choices[0].message.content;
}

// ─── Run the full flow ────────────────────────────────────────────────────

async function main() {
  console.log('1. Registering agent (ML-DSA-65 identity, FIPS 204)...');
  const agent = registerAgent('ran-congestion-agent');
  console.log(`   DID: ${agent.did}`);

  console.log('\n2. Asking Nemotron (via NVIDIA hosted NIM) for a remediation decision...');
  const congestionReport =
    'Cell tower cluster EG-CAI-014 is at 94% capacity during peak hours, affecting an estimated 12,000 subscribers. Latency has increased 3x over baseline.';
  console.log(`   Report: ${congestionReport}`);
  const raw = await askNemotron(congestionReport);
  console.log(`   Nemotron response: ${raw}`);

  let action;
  try {
    action = JSON.parse(raw.match(/\{[\s\S]*\}/)?.[0] ?? raw);
  } catch {
    action = { action_type: 'escalate_to_human', summary: 'Could not parse model output', users_affected: 0 };
  }
  const normalizedAction = { type: action.action_type, usersAffected: Number(action.users_affected) || 0 };

  console.log('\n3. Evaluating proposed action against policy (before it is treated as authoritative)...');
  const policyResult = evaluatePolicy(normalizedAction);
  console.log(`   Decision: ${policyResult.decision} (${policyResult.reason})`);

  console.log('\n4. Recording a post-quantum signed attestation entry (ML-DSA-65)...');
  const entry = recordAttestation(agent, action.action_type, action.summary, {
    ...normalizedAction,
    policyDecision: policyResult.decision,
    policyReason: policyResult.reason,
  });
  console.log(`   Entry #${entry.seq}, chain hash: ${entry.chainHash.slice(0, 16)}...`);
  console.log(`   PQ signature (ML-DSA-65): ${entry.pqSignature.slice(0, 32)}...`);

  console.log('\n5. Independently verifying the full chain (hash + post-quantum signature)...');
  const verification = verifyChain();
  console.log(`   Valid: ${verification.valid}, entries: ${verification.totalEntries}`);

  console.log('\nDone. This entry is verifiable by anyone with the public key and the same');
  console.log('FIPS 204 ML-DSA implementation, no trust in this process required.');
}

main().catch((err) => {
  console.error('\nError:', err.message);
  process.exit(1);
});

import { createHash } from 'node:crypto';

export type VerifierScope = 'auditor' | 'customer' | 'prime_contractor' | 'insurer' | 'board' | 'regulator' | 'acquirer' | 'msp' | 'pe_firm';

export type VerifierAction = 'access' | 'review' | 'accept' | 'reject' | 'comment' | 'export' | 'revoke';

export type RoomStatus = 'active' | 'expired' | 'revoked' | 'pending_verification';

export interface VerifierIdentity {
  verifierId: string;
  name: string;
  email: string;
  organization: string;
  role: string;
  scope: VerifierScope;
  did?: string;
  trustScore?: number;
}

export interface VerifierRoom {
  roomId: string;
  version: 'v1';
  createdAt: string;
  tenantId: number;
  orgSlug: string;
  status: RoomStatus;
  scope: VerifierScope;
  host: {
    orgSlug: string;
    tenantId: number;
  };
  verifiers: VerifierIdentity[];
  accessPolicy: {
    maxVerifiers: number;
    expiryDays: number;
    requireDid: boolean;
    allowedScopes: VerifierScope[];
    dataRedaction: boolean;
  };
  exposedGraphPaths: string[];
  exposedEvidenceIds: string[];
  exposedControlIds: string[];
  exposedFrameworks: string[];
  packetMode?: string;
  roomHash: string;
}

export interface VerifierEvent {
  eventId: string;
  roomId: string;
  timestamp: string;
  verifierId: string;
  action: VerifierAction;
  target: {
    type: 'evidence' | 'control' | 'graph_path' | 'packet' | 'room';
    id: string;
  };
  details?: string;
  receiptHash: string;
}

export interface VerifierAcceptance {
  acceptanceId: string;
  roomId: string;
  verifierId: string;
  controlId: string;
  evidenceId?: string;
  accepted: boolean;
  confidence: number;
  comments?: string;
  timestamp: string;
  receiptHash: string;
}

export interface VerifierExportPacket {
  packetId: string;
  roomId: string;
  exportedAt: string;
  exportedBy: string;
  format: 'json' | 'oscal_ssp' | 'pdf' | 'sarif' | 'stix';
  graphPaths: string[];
  evidenceHashes: string[];
  controlIds: string[];
  redacted: boolean;
  packetHash: string;
}

function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, v]) => v !== undefined)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([k, v]) => [k, stable(v)]),
    );
  }
  return value;
}

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(stable(value))).digest('hex');
}

export function generateRoomId(orgSlug: string, scope: VerifierScope): string {
  return `vroom:${orgSlug}:${scope}:${sha256({ orgSlug, scope, ts: Date.now() }).slice(0, 12)}`;
}

export function createVerifierRoom(input: {
  tenantId: number;
  orgSlug: string;
  scope: VerifierScope;
  verifiers: VerifierIdentity[];
  accessPolicy?: Partial<VerifierRoom['accessPolicy']>;
  exposedGraphPaths?: string[];
  exposedEvidenceIds?: string[];
  exposedControlIds?: string[];
  exposedFrameworks?: string[];
  packetMode?: string;
}): VerifierRoom {
  const roomId = generateRoomId(input.orgSlug, input.scope);
  const createdAt = new Date().toISOString();
  const accessPolicy = {
    maxVerifiers: 10,
    expiryDays: 90,
    requireDid: false,
    allowedScopes: [input.scope],
    dataRedaction: true,
    ...input.accessPolicy,
  };

  const base: Omit<VerifierRoom, 'roomHash'> = {
    roomId,
    version: 'v1',
    createdAt,
    tenantId: input.tenantId,
    orgSlug: input.orgSlug,
    status: 'active',
    scope: input.scope,
    host: { orgSlug: input.orgSlug, tenantId: input.tenantId },
    verifiers: input.verifiers,
    accessPolicy,
    exposedGraphPaths: input.exposedGraphPaths ?? [],
    exposedEvidenceIds: input.exposedEvidenceIds ?? [],
    exposedControlIds: input.exposedControlIds ?? [],
    exposedFrameworks: input.exposedFrameworks ?? [],
    packetMode: input.packetMode,
  };

  return { ...base, roomHash: sha256(base) };
}

export function createVerifierEvent(input: {
  roomId: string;
  verifierId: string;
  action: VerifierAction;
  targetType: VerifierEvent['target']['type'];
  targetId: string;
  details?: string;
}): VerifierEvent {
  const eventId = `vevt:${sha256({ ...input, ts: Date.now() }).slice(0, 16)}`;
  const timestamp = new Date().toISOString();
  const receiptHash = sha256({ eventId, timestamp, ...input });

  return {
    eventId,
    roomId: input.roomId,
    timestamp,
    verifierId: input.verifierId,
    action: input.action,
    target: { type: input.targetType, id: input.targetId },
    details: input.details,
    receiptHash,
  };
}

export function createVerifierAcceptance(input: {
  roomId: string;
  verifierId: string;
  controlId: string;
  evidenceId?: string;
  accepted: boolean;
  confidence: number;
  comments?: string;
}): VerifierAcceptance {
  const acceptanceId = `vacc:${sha256({ ...input, ts: Date.now() }).slice(0, 16)}`;
  const timestamp = new Date().toISOString();
  const receiptHash = sha256({ acceptanceId, ...input, timestamp });

  return {
    acceptanceId,
    roomId: input.roomId,
    verifierId: input.verifierId,
    controlId: input.controlId,
    evidenceId: input.evidenceId,
    accepted: input.accepted,
    confidence: input.confidence,
    comments: input.comments,
    timestamp,
    receiptHash,
  };
}

export function buildVerifierExportPacket(input: {
  roomId: string;
  exportedBy: string;
  format: VerifierExportPacket['format'];
  graphPaths: string[];
  evidenceHashes: string[];
  controlIds: string[];
  redacted?: boolean;
}): VerifierExportPacket {
  const packetId = `vexport:${sha256({ ...input, ts: Date.now() }).slice(0, 16)}`;
  const exportedAt = new Date().toISOString();
  const base: Omit<VerifierExportPacket, 'packetHash'> = {
    packetId,
    roomId: input.roomId,
    exportedAt,
    exportedBy: input.exportedBy,
    format: input.format,
    graphPaths: input.graphPaths,
    evidenceHashes: input.evidenceHashes,
    controlIds: input.controlIds,
    redacted: input.redacted ?? true,
  };
  return { ...base, packetHash: sha256(base) };
}

export function verifyRoomAccess(room: VerifierRoom, verifierId: string): { allowed: boolean; reason: string } {
  if (room.status !== 'active') return { allowed: false, reason: `room_status_${room.status}` };
  const verifier = room.verifiers.find((v) => v.verifierId === verifierId);
  if (!verifier) return { allowed: false, reason: 'verifier_not_in_room' };
  if (!room.accessPolicy.allowedScopes.includes(verifier.scope)) {
    return { allowed: false, reason: 'scope_not_allowed' };
  }
  const expiryMs = room.accessPolicy.expiryDays * 24 * 60 * 60 * 1000;
  if (Date.now() - new Date(room.createdAt).getTime() > expiryMs) {
    return { allowed: false, reason: 'room_expired' };
  }
  return { allowed: true, reason: 'access_granted' };
}

export function computeAcceptanceStats(acceptances: VerifierAcceptance[]): {
  total: number;
  accepted: number;
  rejected: number;
  avgConfidence: number;
  byControl: Map<string, { accepted: number; rejected: number }>;
} {
  let accepted = 0;
  let rejected = 0;
  let confidenceSum = 0;
  const byControl = new Map<string, { accepted: number; rejected: number }>();

  for (const acc of acceptances) {
    if (acc.accepted) accepted++;
    else rejected++;
    confidenceSum += acc.confidence;

    const existing = byControl.get(acc.controlId) ?? { accepted: 0, rejected: 0 };
    if (acc.accepted) existing.accepted++;
    else existing.rejected++;
    byControl.set(acc.controlId, existing);
  }

  return {
    total: acceptances.length,
    accepted,
    rejected,
    avgConfidence: acceptances.length > 0 ? confidenceSum / acceptances.length : 0,
    byControl,
  };
}

export function formatRoomForEvidenceGraph(room: VerifierRoom): Record<string, unknown> {
  return {
    objectKind: 'node',
    objectType: 'verifier_room',
    label: `Verifier Room: ${room.scope} (${room.orgSlug})`,
    source: 'verifier-network',
    payload: {
      room_id: room.roomId,
      scope: room.scope,
      status: room.status,
      verifiers: room.verifiers.length,
      exposed_controls: room.exposedControlIds.length,
      exposed_evidence: room.exposedEvidenceIds.length,
      exposed_frameworks: room.exposedFrameworks,
      packet_mode: room.packetMode,
    },
  };
}

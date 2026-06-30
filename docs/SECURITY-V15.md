# GRC_Claw Security Architecture V15

> Last updated: 2026-06-30 | Status: Living Document

---

## 1. Container Hardening

### Multi-Stage Dockerfile

```dockerfile
# Stage 1: Build
FROM node:22-alpine AS builder
RUN apk add --no-cache python3 make g++
WORKDIR /app
COPY package*.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build
RUN npm prune --production

# Stage 2: Production
FROM gcr.io/distroless/nodejs22-debian12:nonroot AS production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
USER nonroot:nonroot
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD ["/nodejs/bin/node", "/app/dist/health.js"]
ENTRYPOINT ["/nodejs/bin/node", "/app/dist/server.js"]
```

### Hardening Checklist

| Control | Implementation | Verification |
|---------|---------------|--------------|
| Non-root user | `USER nonroot:nonroot` (UID 65534) | `docker run --rm <image> whoami` → `nonroot` |
| Read-only filesystem | `--read-only` flag + tmpfs mounts | `docker inspect` → `ReadonlyRootfs: true` |
| No new privileges | `--security-opt no-new-privileges` | `docker inspect` → `NoNewPrivileges: true` |
| Digest-pinned base | `FROM gcr.io/distroless/...@sha256:<digest>` | Image tag includes `@sha256:` |
| SBOM generation | `syft` scan in CI → SBOM.json artifact | SBOM attached to container registry |
| Vulnerability scan | `trivy image --severity HIGH,CRITICAL` | CI gate, no HIGH/CRITICAL allowed |
| Minimal attack surface | Distroless base (no shell, no package manager) | `docker run --rm <image> sh` → fails |
| Resource limits | `--memory 512m --cpus 1.0` | Kubernetes `resources.limits` |
| Temp directory | `--tmpfs /tmp:rw,noexec,nosuid,size=64m` | Docker Compose or K8s spec |

### Image Scanning Pipeline

```
PR Opened → Build Image → Trivy Scan (HIGH/CRITICAL gate)
                          → SBOM Generation (syft)
                          → Cosign Signing (keyless, OIDC)
                          → Push to Registry (with scan results)
                          → Admission Controller verifies signature + scan
```

---

## 2. Kubernetes Security

### Pod Security Standards (PSS) — Restricted

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: grc-claw-gateway
  labels:
    app.kubernetes.io/name: grc-claw
    app.kubernetes.io/component: gateway
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
    runAsGroup: 65534
    fsGroup: 65534
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: gateway
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
      privileged: false
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "1000m"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir:
      sizeLimit: 64Mi
```

### RBAC Least-Privilege

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: grc-claw-role
  namespace: grc-claw
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create", "patch"]
# No verbs: create/delete deployments, services, or cluster-wide resources
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: grc-claw-binding
  namespace: grc-claw
subjects:
- kind: ServiceAccount
  name: grc-claw-sa
  namespace: grc-claw
roleRef:
  kind: Role
  name: grc-claw-role
  apiGroup: rbac.authorization.k8s.io
```

### NetworkPolicy — Default Deny

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: grc-claw
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-gateway-ingress
  namespace: grc-claw
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/component: gateway
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 3000
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-gateway-to-evidence-store
  namespace: grc-claw
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/component: gateway
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: supabase-db
    ports:
    - protocol: TCP
      port: 5432
```

### Admission Control

```yaml
# Kyverno policy: enforce image signing and scan results
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: grc-claw-admission
spec:
  validationFailureAction: Enforce
  background: false
  rules:
  - name: verify-image-signature
    match:
      any:
      - resources:
          kinds: ["Pod"]
          selector:
            matchLabels:
              app.kubernetes.io/name: grc-claw
    verifyImages:
    - imageReferences:
      - "ghcr.io/grc-claw/*"
      attestors:
      - entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              ...
              -----END PUBLIC KEY-----
          rekor:
            url: https://rekor.sigstore.dev
  - name: require-scan-pass
    match:
      any:
      - resources:
          kinds: ["Pod"]
    validate:
      message: "Trivy scan must show no HIGH/CRITICAL vulnerabilities"
      deny:
        conditions:
          any:
          - key: "{{ images.configmaps.data.trivy-scan-result }}"
            operator: Equals
            value: "FAIL"
```

---

## 3. Supply Chain Security

### CI/CD Pipeline Security Gates

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Code        │    │  Build       │    │  Test        │    │  Publish     │
│  Commit      │───►│  Image       │───►│  Suite       │───►│  Registry    │
│              │    │              │    │              │    │              │
│  - Pre-      │    │  - Trivy     │    │  - Unit      │    │  - Cosign    │
│    commit    │    │    scan      │    │    tests     │    │    sign      │
│    hooks     │    │  - SBOM gen  │    │  - Integration│   │  - Provenance│
│  - Secret    │    │  - Checkov   │    │    tests     │    │    attestation│
│    scanning  │    │    IaC scan  │    │  - E2E       │    │  - Scan      │
│              │    │              │    │    tests     │    │    result    │
│              │    │              │    │  - Policy    │    │    attached  │
│              │    │              │    │    tests     │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### Tooling Matrix

| Tool | Purpose | Gate | Configuration |
|------|---------|------|---------------|
| Trivy | Container image vulnerability scanning | PR + Release | `--severity HIGH,CRITICAL --exit-code 1` |
| Checkov | IaC security scanning (Terraform/K8s) | PR + Release | `--check CKV_K8S,CKV_AWS` |
| Coskey | Container image signing (Sigstore) | Release | Keyless OIDC via GitHub Actions |
| Syft | SBOM generation | Release | CycloneDX format, attached to image |
| Grype | SBOM-based vulnerability scanning | Release | Cross-reference SBOM against CVE DB |
| Gitleaks | Secret detection in source code | Pre-commit + PR | `--config .gitleaks.toml` |
| Scorecard | Supply chain security assessment | Weekly | OSSF Scorecard, target ≥7.0 |

### SBOM / CBOM Artifacts

```
Every release produces:
  - SBOM.json (CycloneDX): Full dependency tree with versions
  - SBOM.sig: Cosign signature of SBOM
  - attestation.json: SLSA Provenance attestation
  - scan-results.json: Trivy scan output (human + machine readable)
  - cbom.json: Cryptographic Bill of Materials (algorithms, key sizes)
```

### Sigstore Integration

```yaml
# GitHub Actions workflow snippet
- name: Sign image with Cosign
  uses: sigstore/cosign-installer@v3
  
- name: Sign container image
  run: |
    cosign sign --yes \
      --predicate attestation.json \
      --type slsaprovenance \
      ghcr.io/grc-claw/gateway:${{ github.sha }}
    
    cosign attach sbom \
      --sbom SBOM.json \
      ghcr.io/grc-claw/gateway:${{ github.sha }}
```

---

## 4. Runtime Security

### Falco / eBPF Monitoring

```yaml
# Custom Falco rules for GRC_Claw
- rule: Unexpected Process in Gateway Container
  desc: Detect unexpected process execution in gateway pods
  condition: >
    container and container_name=gateway and
    spawned_process and
    not proc.name in (node, npm, gateway) and
    not proc.name in (container_privileged_procs)
  output: >
    Unexpected process in gateway (user=%user.name command=%proc.cmdline
    container=%container.id image=%container.image.repository)
  priority: CRITICAL
  tags: [container, gateway, GRC_Claw]

- rule: Evidence Chain Tampering
  desc: Detect write attempts to evidence graph outside normal flow
  condition: >
    container and container_name=evidence-writer and
    open_write and
    fd.name startswith /data/evidence and
    not proc.name in (node, postgres)
  output: >
    Evidence chain write outside normal flow (file=%fd.name
    process=%proc.name container=%container.id)
  priority: CRITICAL
  tags: [evidence, tampering, GRC_Claw]

- rule: Anomalous Outbound Connection
  desc: Detect unexpected outbound network connections from SOC pods
  condition: >
    container and
    outbound and
    not fd.sip.name in (allowed_destinations) and
    container_namespace=grc-claw
  output: >
    Anomalous outbound connection (dest=%fd.rip container=%container.id
    process=%proc.name)
  priority: HIGH
  tags: [network, anomaly, GRC_Claw]
```

### SIEM Integration

```
Falco Events → Falcosidekick → Webhook → GRC_Claw Ingest API
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │ Normalize to  │
                                   │ security_events│
                                   └──────┬───────┘
                                          │
                         ┌────────────────┼────────────────┐
                         ▼                ▼                ▼
                   ┌──────────┐    ┌──────────┐    ┌──────────┐
                   │ Detection│    │ Evidence │    │ Alert    │
                   │ Engine   │    │ Graph    │    │ Manager  │
                   └──────────┘    └──────────┘    └──────────┘
```

### Incident Response Playbooks

| Incident Type | Severity | Auto-Response | Manual Steps |
|---------------|----------|---------------|--------------|
| Container escape | Critical | Kill pod, isolate node, snapshot disk | Forensic analysis, root cause |
| Evidence tampering | Critical | Freeze evidence chain, lock tenant | Verify integrity, restore from backup |
| Credential leak | High | Rotate secrets, revoke sessions | Notify affected parties, audit trail |
| Anomalous access | High | Step-up auth, rate limit source | Review access logs, adjust policies |
| Supply chain compromise | Critical | Quarantine image, block deployments | Audit all affected artifacts, notify |
| DDoS attack | Medium | Rate limit, activate WAF rules | Scale infrastructure, analyze patterns |

---

## 5. Agent Security

### ExecPolicy Framework

```typescript
interface ExecPolicy {
  policyId: string;
  tenantId: string;
  rules: ExecPolicyRule[];
  enforcement: 'enforce' | 'audit' | 'disabled';
  metadata: {
    version: number;
    effectiveFrom: string;     // ISO 8601
    effectiveTo: string;       // ISO 8601
    approvedBy: string;        // User ID
  };
}

interface ExecPolicyRule {
  ruleId: string;
  action: 'allow' | 'deny' | 'challenge';
  targets: {
    principal?: string;        // User or service account
    resource?: string;         // API endpoint or resource pattern
    action?: string;           // HTTP method or operation
    conditions?: Record<string, unknown>;  // Context-dependent
  };
  priority: number;            // Higher = evaluated first
  effect: 'permit' | 'deny';
}
```

### Separation of Duties (SoD)

```
Critical operations require multi-party approval:
  - Evidence chain deletion: 2 of 3 SOC leads
  - Policy changes: SOC lead + Compliance officer
  - Connector credential rotation: DevOps + Security
  - Tenant data export: Tenant admin + Data protection officer

Implementation:
  - Approval workflow with timeout (24h)
  - Cryptographic attestation of approvals
  - Audit trail in evidence graph
  - SoD violations blocked at policy firewall
```

### Canary Traps

```typescript
// Honeypot credentials embedded in production systems
interface CanaryTrap {
  trapId: string;
  type: 'credential' | 'data' | 'endpoint' | 'file';
  value: string;               // The canary value (e.g., fake API key)
  alertOn: 'read' | 'write' | 'use' | 'all';
  severity: 'critical';        // Any use = critical incident
  decoy: {
    description: string;       // What this appears to be
    location: string;          // Where it's planted
  };
  response: {
    notify: string[];           // Email/Slack channels
    autoBlock: boolean;         // Auto-block source IP
    preserveForensics: boolean; // Snapshot state before blocking
  };
}

// Types of canary traps:
// 1. Fake AWS credentials in environment files
// 2. Decoy database entries with tracking markers
// 3. Fake API endpoints that log all access
// 4. Canary tokens in exported reports
```

### Behavioral Anomaly Detection

```
Baseline Learning Phase (14 days):
  - Normal access patterns per user/service
  - Typical API call volumes and endpoints
  - Expected data access scopes
  - Standard working hours

Detection Rules:
  1. Access from new IP/geo → Step-up auth
  2. API call volume >3σ from baseline → Rate limit + alert
  3. Access to resources outside normal scope → Block + alert
  4. Off-hours access to critical systems → Challenge + alert
  5. Rapid sequential resource access (scraping) → Block + alert
  6. Authentication failures >5 in 5min → Lock account + alert
  7. Service account behaving like human user → Alert + investigate

Response Actions:
  - Alert via SIEM integration
  - Evidence node created in graph
  - Automatic policy adjustment (temporary blocks)
  - Forensic snapshot of session
```

---

## 6. Post-Quantum Readiness

### Current Cryptographic Inventory

| Component | Current Algorithm | Key Size | Quantum Risk |
|-----------|------------------|----------|--------------|
| TLS termination | RSA-2048 / ECDSA P-256 | 2048-bit / 256-bit | HIGH |
| JWT signing | RS256 / ES256 | 2048-bit / 256-bit | HIGH |
| Database encryption | AES-256-GCM | 256-bit | LOW |
| Evidence hash chain | SHA-256 | 256-bit | MEDIUM |
| mTLS certificates | RSA-2048 / ECDSA P-256 | 2048-bit / 256-bit | HIGH |
| Code signing | RSA-4096 | 4096-bit | MEDIUM |
| Backup encryption | AES-256-CBC | 256-bit | LOW |

### FIPS 203/204 Migration Roadmap

```
Phase 1: Inventory & Assessment (Q3 2026)
  ├── Complete cryptographic inventory
  ├── Map all certificate chains
  ├── Identify quantum-vulnerable components
  └── Define migration priorities

Phase 2: Hybrid Mode (Q4 2026)
  ├── Deploy hybrid certificates (classical + PQ)
  ├── Enable hybrid TLS (X25519 + ML-KEM-768)
  ├── Update JWT to support hybrid signatures
  └── Update mTLS to hybrid mode

Phase 3: PQ-First (Q2 2027)
  ├── Transition to PQ-primary certificates
  ├── ML-KEM-1024 for key encapsulation
  ├── ML-DSA-87 for digital signatures
  ├── Update evidence hash chain (SHA-3-256)
  └── Update code signing

Phase 4: Classical Deprecation (Q4 2027)
  ├── Remove classical crypto from non-legacy paths
  ├── Maintain hybrid for backward compatibility
  ├── Complete audit trail
  └── Update compliance documentation
```

### FIPS 203 (ML-KEM) Integration

```typescript
// Key Encapsulation Mechanism (replacing RSA/ECDH key exchange)
interface MlKemConfig {
  variant: 'ML-KEM-512' | 'ML-KEM-768' | 'ML-KEM-1024';
  hybrid: {
    classical: 'X25519' | 'P-256' | 'RSA-2048';
    mode: 'parallel' | 'concat' | 'split';
  };
  fallback: {
    allowed: boolean;
    maxAge: string;           // ISO 8601 duration
    auditLog: boolean;
  };
}

// Implementation path:
// 1. Use mlkem-js or noble-post-quantum libraries
// 2. TLS 1.3 with hybrid key exchange via Node.js tls module
// 3. Update certificate templates for hybrid keys
```

### FIPS 204 (ML-DSA) Integration

```typescript
// Digital Signature Algorithm (replacing RSA/ECDSA signatures)
interface MlDsaConfig {
  variant: 'ML-DSA-44' | 'ML-DSA-65' | 'ML-DSA-87';
  hybrid: {
    classical: 'RSA-PSS-2048' | 'ECDSA-P256' | 'Ed25519';
    mode: 'parallel' | 'concat';
  };
  useCases: {
    jwtSigning: boolean;
    codeSigning: boolean;
    documentSigning: boolean;
    certificateSigning: boolean;
  };
}

// Migration notes:
// - ML-DSA signatures are 2.4–4.6 KB (vs 64–256 bytes classical)
// - JWT payloads will increase significantly
// - Consider JWS with ML-DSA for evidence chain
// - Code signing: update CI/CD to dual-sign (classical + PQ)
```

### Compliance Mapping

| Framework | PQ Requirement | GRC_Claw Control | Status |
|-----------|---------------|-------------------|--------|
| NIST SP 800-208 | PQ algorithm adoption | ML-KEM + ML-DSA hybrid | Planned Q4 2026 |
| FIPS 140-3 | FIPS-validated modules | BoringCrypto module | In progress |
| SOC 2 CC6.1 | Encryption controls | AES-256-GCM + PQ key exchange | Compliant |
| ISO 27001 A.10.1 | Cryptographic controls | Crypto inventory + migration plan | Compliant |
| PCI DSS 4.0 Req. 4 | Strong cryptography | TLS 1.3 + PQ hybrid | Compliant |

### Testing & Validation

```
PQ Readiness Tests:
  1. Hybrid TLS handshake verification (unit + integration)
  2. ML-DSA signature verification performance benchmarks
  3. ML-KEM encapsulation/decapsulation correctness
  4. Backward compatibility with classical-only clients
  5. Certificate chain validation with hybrid certs
  6. Evidence hash chain integrity with SHA-3-256
  7. Load testing with PQ overhead (expected: <15% latency increase)

Acceptance Criteria:
  - All tests pass
  - Performance degradation <15% vs classical-only
  - Zero security regressions
  - Compliance framework mapping complete
  - Migration runbook documented and tested
```

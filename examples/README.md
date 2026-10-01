# GRC_Claw SDK Examples

Comprehensive SDK examples for the GRC_Claw API — AI governance, risk, and compliance management.

## Structure

```
examples/
├── python/           # 15 Python SDK examples
│   ├── 01_client_setup.py
│   ├── 02_policies.py
│   ├── 03_evidence.py
│   ├── 04_enforcement.py
│   ├── 05_assessments.py
│   ├── 06_compliance.py
│   ├── 07_agents.py
│   ├── 08_audit.py
│   ├── 09_webhooks.py
│   ├── 10_system.py
│   ├── 11_composed.py
│   ├── 12_graphql.py
│   ├── 13_error_handling.py
│   ├── 14_async.py
│   └── 15_webhook_handler.py
├── typescript/       # 15 TypeScript SDK examples
│   ├── 01_client_setup.ts
│   ├── 02_policies.ts
│   ├── 03_evidence.ts
│   ├── 04_enforcement.ts
│   ├── 05_assessments.ts
│   ├── 06_compliance.ts
│   ├── 07_agents.ts
│   ├── 08_audit.ts
│   ├── 09_webhooks.ts
│   ├── 10_system.ts
│   ├── 11_composed.ts
│   ├── 12_graphql.ts
│   ├── 13_error_handling.ts
│   ├── 14_async.ts
│   └── 15_webhook_handler.ts
├── curl/             # 11 cURL example scripts
│   ├── 01_health.sh
│   ├── 02_policies.sh
│   ├── 03_evidence.sh
│   ├── 04_enforcement.sh
│   ├── 05_assessments.sh
│   ├── 06_compliance.sh
│   ├── 07_agents.sh
│   ├── 08_audit.sh
│   ├── 09_webhooks.sh
│   ├── 10_composed.sh
│   └── 11_graphql.sh
└── GRC_Claw_Postman_Collection.json  # Full Postman collection
```

## Quick Start

### Python
```bash
pip install grc-claw-sdk
export GRC_API_KEY="grc_live_abc123..."
export GRC_TENANT_ID="org-acme"
python python/01_client_setup.py
```

### TypeScript
```bash
npm install @grc-claw/sdk
export GRC_API_KEY="grc_live_abc123..."
export GRC_TENANT_ID="org-acme"
npx ts-node typescript/01_client_setup.ts
```

### cURL
```bash
export GRC_API_KEY="grc_live_abc123..."
export GRC_TENANT_ID="org-acme"
chmod +x curl/*.sh
./curl/01_health.sh
```

### Postman
Import `GRC_Claw_Postman_Collection.json` into Postman. Set collection variables:
- `baseUrl` — API base URL
- `apiKey` — Your API key
- `tenantId` — Your tenant ID

## API Coverage

| Service | Endpoints | Examples |
|---------|-----------|----------|
| System | 3 | health, ready, metrics |
| Policies | 9 | CRUD, compile, dry-run, versions, dependencies |
| Evidence | 6 | search, submit, get, verify, export |
| Enforcement | 4 | decide, batch, get, list |
| Assessments | 6 | CRUD, findings, report |
| Compliance | 6 | frameworks, controls, posture, mappings, crosswalk, reports |
| Agents | 6 | CRUD, trust-score, policy-bindings |
| Audit | 2 | query, verify |
| Webhooks | 7 | CRUD, test, deliveries |
| Composed | 4 | dashboard, agent-360, compliance-report, executive-summary |
| GraphQL | 2 | query, mutation |

**Total: 45+ endpoints covered**

## Authentication

All API requests require:
- `Authorization: Bearer <api_key>` header
- `X-Tenant-ID: <tenant_id>` header

## Environments

| Environment | Base URL |
|-------------|----------|
| Production | `https://api.grc-claw.io` |
| Staging | `https://api.staging.grc-claw.io` |
| Development | `http://localhost:8080` |

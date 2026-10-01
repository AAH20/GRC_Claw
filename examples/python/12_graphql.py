"""
GRC_Claw Python SDK - GraphQL
==============================
Query the GraphQL endpoint for flexible data retrieval.
"""

import httpx
from grc_claw import GRCClawClient

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- GraphQL Query ---
query = """
query GetPolicies($limit: Int!) {
  policies(limit: $limit) {
    id
    name
    status
    version
    category
  }
}
"""

variables = {"limit": 10}

response = httpx.post(
    f"{client.base_url}/v1.0/graphql",
    headers={
        "Authorization": f"Bearer {client.api_key}",
        "X-Tenant-ID": client.tenant_id,
        "Content-Type": "application/json",
    },
    json={"query": query, "variables": variables},
)

data = response.json()
for policy in data["data"]["policies"]:
    print(f"  {policy['id']}: {policy['name']} ({policy['status']})")

# --- GraphQL Mutation ---
mutation = """
mutation CreatePolicy($input: PolicyInput!) {
  createPolicy(input: $input) {
    id
    name
    status
  }
}
"""

variables = {
    "input": {
        "name": "New Policy",
        "category": "privacy",
    }
}

response = httpx.post(
    f"{client.base_url}/v1.0/graphql",
    headers={
        "Authorization": f"Bearer {client.api_key}",
        "X-Tenant-ID": client.tenant_id,
        "Content-Type": "application/json",
    },
    json={"query": mutation, "variables": variables},
)

result = response.json()
print(f"Created: {result['data']['createPolicy']}")
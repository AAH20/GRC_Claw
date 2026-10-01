"""
GRC_Claw Python SDK - Client Setup & Configuration
===================================================
Demonstrates how to initialize the GRC_Claw client with various configurations.
"""

import os
from grc_claw import GRCClawClient, Environment

# --- Basic Setup ---
client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment=Environment.PRODUCTION,
)

# --- Custom Timeout & Retries ---
client_custom = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment=Environment.STAGING,
    timeout=60.0,
    max_retries=5,
)

# --- Development Environment ---
client_dev = GRCClawClient(
    api_key="grc_test_xyz789...",
    tenant_id="org-acme",
    environment=Environment.DEVELOPMENT,
)

# --- Using Environment Variables ---
client_env = GRCClawClient(
    api_key=os.environ["GRC_API_KEY"],
    tenant_id=os.environ["GRC_TENANT_ID"],
    environment=os.environ.get("GRC_ENV", "production"),
)

# --- Context Manager (auto-closes HTTP client) ---
with GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment=Environment.PRODUCTION,
) as client:
    policies, pagination = client.policies.list(limit=10)
    print(f"Found {pagination.total} policies")

print("Client setup complete!")
"""
GRC_Claw Python SDK - System & Health
======================================
Health checks, readiness, and metrics.
"""

from grc_claw import GRCClawClient

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- Health Check ---
health = client.system.health()
print(f"Status: {health.status}")
print(f"Version: {health.version}")
for component, info in health.components.items():
    print(f"  {component}: {info['status']}")

# --- Readiness Check ---
ready = client.system.ready()
print(f"Ready: {ready.ready}")
for check, info in ready.checks.items():
    print(f"  {check}: {info['status']}")

# --- Metrics (Prometheus format) ---
metrics = client.system.metrics()
print(f"Metrics:\n{metrics}")
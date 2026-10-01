"""
GRC_Claw Python SDK - Audit Trail
===================================
Query and verify audit events.
"""

from grc_claw import GRCClawClient

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- Query Audit Trail ---
events, pagination = client.audit.query(
    event_type="policy.created",
    actor_id="user-123",
    resource_type="policy",
    resource_id="pol-001",
    limit=100,
)
for e in events:
    print(f"  {e.event_id}: {e.event_type} by {e.actor.get('id')}")

# --- Verify Audit Chain ---
verification = client.audit.verify(
    from_event_id="evt-001",
    to_event_id="evt-100",
)
print(f"Verification: {verification.verification_status}")
print(f"  Events verified: {verification.events_verified}")
print(f"  Chain intact: {verification.chain_intact}")
"""
GRC_Claw Python SDK - Webhook Subscriptions
============================================
Create, manage, and test webhook subscriptions.
"""

import hmac
import hashlib
import json
from grc_claw import GRCClawClient, WebhookVerifier

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- List Subscriptions ---
subscriptions = client.webhooks.list()
for sub in subscriptions:
    print(f"  {sub.subscription_id}: {sub.url} ({len(sub.events)} events)")

# --- Create Subscription ---
subscription = client.webhooks.create(
    url="https://example.com/webhooks/grc-claw",
    events=["policy.created", "policy.updated", "enforcement.decision"],
    secret="whsec_my_webhook_secret",
    description="Production webhook for policy events",
    active=True,
    metadata={"team": "security"},
)
print(f"Subscription created: {subscription.subscription_id}")

# --- Get Subscription ---
sub = client.webhooks.get(subscription_id="sub-001")
print(f"Subscription: {sub.url}, active: {sub.active}")

# --- Update Subscription ---
updated = client.webhooks.update(
    subscription_id="sub-001",
    events=["policy.created", "policy.updated", "enforcement.decision", "evidence.verified"],
)
print(f"Updated events: {updated.events}")

# --- Test Subscription ---
test_result = client.webhooks.test(subscription_id="sub-001")
print(f"Test result: {test_result}")

# --- Get Delivery History ---
deliveries = client.webhooks.get_deliveries(
    subscription_id="sub-001",
    status="delivered",
)
for d in deliveries:
    print(f"  {d.delivery_id}: {d.event_type} -> {d.status} ({d.http_status})")

# --- Delete Subscription ---
client.webhooks.delete(subscription_id="sub-001")
print("Subscription deleted")

# --- Verify Webhook Signature (in your webhook handler) ---
def handle_webhook(request_body: str, signature_header: str, secret: str) -> bool:
    return WebhookVerifier.verify(request_body, signature_header, secret)

# Example usage in a webhook handler:
# is_valid = handle_webhook(body, headers["X-GRC-Signature"], "whsec_my_webhook_secret")
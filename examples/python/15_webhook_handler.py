"""
GRC_Claw Python SDK - Webhook Handler Example
=============================================
Complete webhook handler with signature verification.
"""

import hmac
import hashlib
import json
from flask import Flask, request, jsonify
from grc_claw import WebhookVerifier

app = Flask(__name__)
WEBHOOK_SECRET = "whsec_my_webhook_secret"

@app.route("/webhooks/grc-claw", methods=["POST"])
def handle_grc_webhook():
    # Get the signature from headers
    signature = request.headers.get("X-GRC-Signature", "")
    body = request.get_data(as_text=True)

    # Verify signature
    if not WebhookVerifier.verify(body, signature, WEBHOOK_SECRET):
        return jsonify({"error": "Invalid signature"}), 401

    # Parse the event
    event = json.loads(body)
    event_type = event.get("event_type")
    event_data = event.get("data", {})

    # Handle different event types
    handlers = {
        "policy.created": _handle_policy_created,
        "policy.updated": _handle_policy_updated,
        "enforcement.decision": _handle_enforcement_decision,
        "evidence.verified": _handle_evidence_verified,
        "assessment.completed": _handle_assessment_completed,
    }

    handler = handlers.get(event_type, _handle_unknown)
    handler(event_data)

    return jsonify({"status": "ok"}), 200

def _handle_policy_created(data):
    print(f"Policy created: {data.get('policy_id')} - {data.get('name')}")

def _handle_policy_updated(data):
    print(f"Policy updated: {data.get('policy_id')} - v{data.get('version')}")

def _handle_enforcement_decision(data):
    print(f"Enforcement: {data.get('decision_id')} -> {data.get('verdict')}")

def _handle_evidence_verified(data):
    print(f"Evidence verified: {data.get('evidence_id')}")

def _handle_assessment_completed(data):
    print(f"Assessment completed: {data.get('assessment_id')}")

def _handle_unknown(data):
    print(f"Unknown event: {data}")

if __name__ == "__main__":
    app.run(port=5000)
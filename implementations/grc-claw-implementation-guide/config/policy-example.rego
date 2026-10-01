# GRC_Claw Rego Policy
# Compatibility layer for existing OPA/Rego policies

package grcclaw

import future.keywords.if
import future.keywords.in

# Default deny
default verdict := {"effect": "deny", "reason": "No matching allow rule"}

# Block PII export
verdict := {"effect": "deny", "reason": "PII export blocked"} if {
    input.action == "export"
    input.resource.containsPii == true
}

# Allow read operations
verdict := {"effect": "allow"} if {
    input.action == "read"
}

# Require approval for high-value refunds
verdict := {"effect": "require_approval", "reason": "Refund over $500"} if {
    input.action == "refund"
    input.context.amount > 500
    not input.context.approvalTicket
}

# Rate limiting
verdict := {"effect": "throttle", "reason": "Rate limit exceeded"} if {
    input.action == "api_call"
    count(input.agent.apiCalls) > 100
    time.now_ns() - input.agent.firstCallTime < 3600000000000
}

# Allow low-value refunds for CS agents
verdict := {"effect": "allow"} if {
    input.action == "refund"
    input.context.amount <= 500
    input.agent.role == "cs-agent"
}

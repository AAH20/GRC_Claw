# GRC_Claw Cedar Policy
// Production governance policy for customer-facing agents
// Blocks PII export, requires approval for high-value refunds

permit(
    principal,
    action == Action::"export",
    resource
) when {
    !resource.containsPii &&
    principal.clearance >= "internal"
};

forbid(
    principal,
    action == Action::"export",
    resource
) when {
    resource.containsPii
};

permit(
    principal,
    action == Action::"refund",
    resource
) when {
    context.amount <= 500 &&
    principal.role == "cs-agent"
};

// High-value refunds require approval
forbid(
    principal,
    action == Action::"refund",
    resource
) when {
    context.amount > 500 &&
    !context.approvalTicket.exists
};

// Allow read operations
permit(
    principal,
    action == Action::"read",
    resource
);

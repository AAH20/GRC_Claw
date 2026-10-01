"""
GRC_Claw Python SDK - Error Handling
=====================================
Demonstrates proper error handling for all exception types.
"""

from grc_claw import (
    GRCClawClient,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    ValidationError,
    RateLimitError,
    ServerError,
)

client = GRCClawClient(
    api_key="grc_live_abc123...",
    tenant_id="org-acme",
    environment="production",
)

# --- Handle Specific Errors ---
try:
    policy = client.policies.get(policy_id="pol-nonexistent")
except NotFoundError as e:
    print(f"Not found: {e.message} (code: {e.code})")
except AuthenticationError as e:
    print(f"Auth failed: {e.message}")
except AuthorizationError as e:
    print(f"Access denied: {e.message}")
except ValidationError as e:
    print(f"Validation error: {e.message} (status: {e.status})")
except ConflictError as e:
    print(f"Conflict: {e.message} (code: {e.code})")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ServerError as e:
    print(f"Server error: {e.message} (status: {e.status})")
except GRCClawError as e:
    print(f"GRC error: {e.message} (request_id: {e.request_id})")

# --- Retry with Exponential Backoff ---
import time

def with_retry(func, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt < max_retries - 1:
                time.sleep(e.retry_after)
                continue
            raise
        except ServerError:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise
    raise Exception("Max retries exceeded")

# Usage
policy = with_retry(lambda: client.policies.get(policy_id="pol-001"))
print(f"Policy: {policy.name}")
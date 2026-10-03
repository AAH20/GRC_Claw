# Gated Communities SDK

A production-grade Python SDK for the [Gated Communities](https://gatedcommunities.io) API. Manage communities, members, users, and API keys with a fully-typed, authenticated client.

## Features

- **Full type hints** — every method and model is annotated for IDE autocomplete and static analysis
- **Pydantic v2 models** — request/response validation with clear error messages
- **Automatic retries** — exponential backoff on rate limits (429) and server errors (5xx)
- **Custom exceptions** — granular error types for authentication, authorization, validation, and more
- **Context manager support** — clean resource management with `with` statements
- **Resource namespaces** — intuitive `client.communities.list()` style access

## Installation

```bash
pip install gated-communities-sdk
```

Or install from source:

```bash
cd sdk/
pip install -e .
```

## Quick Start

```python
from gated_communities import GatedCommunitiesClient

# Initialize with an API key
client = GatedCommunitiesClient(api_key="gc_live_your_key_here")

# Or use the environment variable
# export GATED_COMMUNITIES_API_KEY="gc_live_your_key_here"
# client = GatedCommunitiesClient()

# List all communities
communities = client.communities.list()
for community in communities.data:
    print(f"{community.name} ({community.member_count} members)")

# Create a new community
from gated_communities import CommunityCreate

new_community = client.communities.create(
    CommunityCreate(
        name="My Private Community",
        slug="my-private-community",
        description="A space for trusted members",
        visibility="private",
        tags=["private", "exclusive"],
    )
)
print(f"Created community: {new_community.id}")

# Add a member
from gated_communities import MemberCreate

member = client.members.add(
    new_community.id,
    MemberCreate(user_id="usr_abc123", role="moderator"),
)
print(f"Added member: {member.id}")
```

## Authentication

The SDK uses API key authentication via Bearer tokens. You can provide your key in two ways:

1. **Direct parameter:**
   ```python
   client = GatedCommunitiesClient(api_key="gc_live_...")
   ```

2. **Environment variable:**
   ```bash
   export GATED_COMMUNITIES_API_KEY="gc_live_..."
   ```
   ```python
   client = GatedCommunitiesClient()
   ```

## Resource Reference

### Communities

| Method | Description |
|--------|-------------|
| `client.communities.list(page, per_page, visibility, tag)` | List all visible communities |
| `client.communities.get(community_id)` | Get a single community |
| `client.communities.create(payload)` | Create a new community |
| `client.communities.update(community_id, payload)` | Update a community |
| `client.communities.delete(community_id)` | Delete a community |

### Members

| Method | Description |
|--------|-------------|
| `client.members.list(community_id, page, per_page, role, status)` | List community members |
| `client.members.get(community_id, member_id)` | Get a specific member |
| `client.members.add(community_id, payload)` | Add a member |
| `client.members.update(community_id, member_id, payload)` | Update a membership |
| `client.members.remove(community_id, member_id)` | Remove a member |

### Users

| Method | Description |
|--------|-------------|
| `client.users.get(user_id)` | Get a user by ID |
| `client.users.me()` | Get the authenticated user |

### API Keys

| Method | Description |
|--------|-------------|
| `client.api_keys.list(page, per_page)` | List account API keys |
| `client.api_keys.get(key_id)` | Get a specific API key |
| `client.api_keys.revoke(key_id)` | Revoke an API key |

## Error Handling

All SDK errors inherit from `GatedCommunitiesError`:

```python
from gated_communities import (
    GatedCommunitiesClient,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

client = GatedCommunitiesClient(api_key="gc_live_...")

try:
    community = client.communities.get("comm_nonexistent")
except AuthenticationError:
    print("Invalid API key — check your credentials")
except NotFoundError:
    print("Community not found")
except RateLimitError as e:
    print(f"Rate limited — retry after {e.retry_after}s")
except ValidationError as e:
    print(f"Invalid data: {e.response_body}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Advanced Usage

### Custom HTTP Client

```python
import httpx
from gated_communities import GatedCommunitiesClient

http_client = httpx.Client(
    timeout=60.0,
    follow_redirects=True,
)

client = GatedCommunitiesClient(
    api_key="gc_live_...",
    http_client=http_client,
)
```

### Context Manager

```python
from gated_communities import GatedCommunitiesClient

with GatedCommunitiesClient(api_key="gc_live_...") as client:
    communities = client.communities.list()
    # Client is automatically closed when exiting the block
```

### Pagination

```python
from gated_communities import GatedCommunitiesClient

client = GatedCommunitiesClient(api_key="gc_live_...")

page = 1
while True:
    result = client.communities.list(page=page, per_page=50)
    for community in result.data:
        print(community.name)
    if not result.has_more:
        break
    page += 1
```

### Custom Base URL

```python
client = GatedCommunitiesClient(
    api_key="gc_live_...",
    base_url="https://api.staging.gatedcommunities.io/v1",
)
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | `None` | API key (or use env var) |
| `base_url` | `https://api.gatedcommunities.io/v1` | API base URL |
| `timeout` | `30.0` | Request timeout in seconds |
| `max_retries` | `3` | Max retry attempts |
| `retry_delay` | `1.0` | Initial retry delay (doubles each attempt) |
| `http_client` | `None` | Custom `httpx.Client` instance |

## Requirements

- Python 3.10+
- `httpx` >= 0.27
- `pydantic` >= 2.0

## License

MIT

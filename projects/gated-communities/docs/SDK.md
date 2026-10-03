# SDK Documentation

## Python SDK

### Installation
pip install gated-communities-sdk

### Quick Start
```python
from gated_communities import GatedCommunitiesClient

client = GatedCommunitiesClient(
    api_key="your-api-key",
    base_url="https://api.gated-communities.example.com"
)

# List tiers
tiers = client.tiers.list()

# Create a tier
tier = client.tiers.create(
    name="Gold",
    level="gold",
    price=9.99
)

# Get members
members = client.members.list(community_id="community-123")
```

### Authentication
The SDK supports API key authentication:
client = GatedCommunitiesClient(api_key="your-api-key")

### Error Handling
```python
from gated_communities.exceptions import GatedCommunitiesError

try:
    tiers = client.tiers.list()
except GatedCommunitiesError as e:
    print(f"Error: {e.message}")
```

## JavaScript/TypeScript SDK

### Installation
npm install @gated-communities/sdk

### Quick Start
```typescript
import { GatedCommunitiesClient } from '@gated-communities/sdk';

const client = new GatedCommunitiesClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.gated-communities.example.com'
});

// List tiers
const tiers = await client.tiers.list();

// Create a tier
const tier = await client.tiers.create({
  name: 'Gold',
  level: 'gold',
  price: 9.99
});
```

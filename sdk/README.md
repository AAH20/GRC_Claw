# GRC Marketing SDK & CLI

Production-grade Python and TypeScript SDKs plus a CLI for the GRC Marketing API. Manage campaigns, leads, journeys, and analytics from code or the terminal.

## Project Structure

```
sdk/
├── python/                  # Python SDK
│   ├── grc_marketing/
│   │   ├── __init__.py      # Main entry point (GRCMarketing class)
│   │   ├── client.py        # Low-level HTTP API client
│   │   ├── auth.py          # Authentication (API key + OAuth2)
│   │   ├── campaigns.py     # Campaign operations
│   │   ├── leads.py         # Lead operations
│   │   ├── journeys.py      # Journey operations
│   │   ├── analytics.py     # Analytics operations
│   │   ├── errors.py        # Error hierarchy
│   │   └── types.py         # Type definitions & dataclasses
│   └── pyproject.toml
├── typescript/              # TypeScript SDK
│   ├── src/
│   │   ├── index.ts         # Main entry point (GRCMarketing class)
│   │   ├── client.ts        # Low-level HTTP API client
│   │   ├── auth.ts          # Authentication (API key + OAuth2)
│   │   ├── campaigns.ts     # Campaign operations
│   │   ├── leads.ts         # Lead operations
│   │   ├── journeys.ts      # Journey operations
│   │   ├── analytics.ts     # Analytics operations
│   │   ├── errors.ts        # Error hierarchy
│   │   └── types.ts         # Type definitions
│   ├── package.json
│   └── tsconfig.json
└── cli/                     # Python CLI
    ├── grc-marketing-cli/
    │   ├── __init__.py
    │   ├── main.py          # CLI entry point & auth commands
    │   ├── campaigns.py     # Campaign commands
    │   ├── leads.py         # Lead commands
    │   ├── journeys.py      # Journey commands
    │   └── analytics.py     # Analytics commands
    └── pyproject.toml
```

## Installation

### Python SDK

```bash
cd python
pip install -e .
```

### TypeScript SDK

```bash
cd typescript
npm install
npm run build
```

### CLI

```bash
cd cli
pip install -e .
```

## Quick Start

### Python SDK

```python
from grc_marketing import GRCMarketing

# Initialize with API key
sdk = GRCMarketing(
    base_url="https://api.grc.example.com",
    api_key="your-api-key",
)

# Or use OAuth2
sdk = GRCMarketing(
    base_url="https://api.grc.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
)

# Authenticate
sdk.authenticate()

# Campaigns
campaigns = sdk.campaigns.list(status="active")
campaign = sdk.campaigns.get("camp_123")
new_campaign = sdk.campaigns.create({
    "name": "Summer Sale",
    "channel": "email",
    "budget": 5000.0,
})
sdk.campaigns.activate("camp_123")

# Leads
leads = sdk.leads.list(status="new")
lead = sdk.leads.create({
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
})
sdk.leads.qualify("lead_456")

# Journeys
journeys = sdk.journeys.list()
journey = sdk.journeys.create({
    "name": "Onboarding",
    "steps": [{"type": "email", "delay": 0}],
})

# Analytics
report = sdk.analytics.get_campaign_performance(
    start_date="2024-01-01",
    end_date="2024-01-31",
)
```

### TypeScript SDK

```typescript
import { GRCMarketing } from "@grc/marketing";

const sdk = new GRCMarketing({
  baseUrl: "https://api.grc.example.com",
  apiKey: "your-api-key",
});

await sdk.authenticate();

// Campaigns
const campaigns = await sdk.campaigns.list({ status: "active" });
const campaign = await sdk.campaigns.get("camp_123");
await sdk.campaigns.activate("camp_123");

// Leads
const leads = await sdk.leads.list({ status: "new" });
await sdk.leads.qualify("lead_456");

// Analytics
const report = await sdk.analytics.getCampaignPerformance({
  startDate: "2024-01-01",
  endDate: "2024-01-31",
});
```

### CLI

```bash
# Authenticate
grc-marketing auth login

# Campaigns
grc-marketing campaigns list --status active
grc-marketing campaigns get camp_123
grc-marketing campaigns create --name "Summer Sale" --channel email --budget 5000
grc-marketing campaigns activate camp_123
grc-marketing campaigns pause camp_123
grc-marketing campaigns complete camp_123
grc-marketing campaigns archive camp_123
grc-marketing campaigns delete camp_123

# Leads
grc-marketing leads list --status new
grc-marketing leads get lead_456
grc-marketing leads create --email user@example.com --first-name Jane --last-name Doe
grc-marketing leads qualify lead_456
grc-marketing leads convert lead_456
grc-marketing leads mark-lost lead_456

# Journeys
grc-marketing journeys list
grc-marketing journeys create --name "Onboarding" --steps '[{"type":"email"}]'
grc-marketing journeys activate journey_789

# Analytics
grc-marketing analytics report --start-date 2024-01-01 --end-date 2024-01-31
grc-marketing analytics campaign-performance --start-date 2024-01-01
grc-marketing analytics lead-funnel
grc-marketing analytics channel-performance
grc-marketing analytics journey-analytics journey_789
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GRC_BASE_URL` | API base URL |
| `GRC_API_KEY` | API key for authentication |

### CLI Config File

The CLI stores credentials at `~/.config/grc-marketing/config.json`.

## Error Handling

Both SDKs provide a rich error hierarchy:

```python
from grc_marketing import (
    AuthenticationError,    # 401
    AuthorizationError,     # 403
    NotFoundError,          # 404
    ValidationError,       # 422
    RateLimitError,         # 429
    ServerError,            # 5xx
    NetworkError,           # Connection issues
    TimeoutError,           # Request timeout
    ConfigurationError,     # SDK misconfiguration
)
```

```typescript
import {
  AuthenticationError,    // 401
  AuthorizationError,     // 403
  NotFoundError,          // 404
  ValidationError,       // 422
  RateLimitError,         // 429
  ServerError,            // 5xx
  NetworkError,           // Connection issues
  TimeoutError,           // Request timeout
  ConfigurationError,     // SDK misconfiguration
} from "@grc/marketing";
```

## API Reference

### Campaigns

| Method | Description |
|--------|-------------|
| `list(page, per_page, status, channel, sort_by, sort_order)` | List campaigns |
| `get(campaign_id)` | Get a campaign by ID |
| `create(payload)` | Create a new campaign |
| `update(campaign_id, payload)` | Update a campaign |
| `delete(campaign_id)` | Delete a campaign |
| `activate(campaign_id)` | Activate a campaign |
| `pause(campaign_id)` | Pause a campaign |
| `complete(campaign_id)` | Mark as completed |
| `archive(campaign_id)` | Archive a campaign |

### Leads

| Method | Description |
|--------|-------------|
| `list(page, per_page, status, source, sort_by, sort_order)` | List leads |
| `get(lead_id)` | Get a lead by ID |
| `create(payload)` | Create a new lead |
| `update(lead_id, payload)` | Update a lead |
| `delete(lead_id)` | Delete a lead |
| `qualify(lead_id)` | Mark as qualified |
| `convert(lead_id)` | Mark as converted |
| `mark_lost(lead_id)` | Mark as lost |

### Journeys

| Method | Description |
|--------|-------------|
| `list(page, per_page, status, sort_by, sort_order)` | List journeys |
| `get(journey_id)` | Get a journey by ID |
| `create(payload)` | Create a new journey |
| `update(journey_id, payload)` | Update a journey |
| `delete(journey_id)` | Delete a journey |
| `activate(journey_id)` | Activate a journey |
| `pause(journey_id)` | Pause a journey |
| `complete(journey_id)` | Mark as completed |

### Analytics

| Method | Description |
|--------|-------------|
| `get_report(params)` | Get custom analytics report |
| `get_campaign_performance(params)` | Campaign performance metrics |
| `get_lead_funnel(params)` | Lead funnel analytics |
| `get_channel_performance(params)` | Channel performance metrics |
| `get_journey_analytics(journey_id, params)` | Journey-specific analytics |

## License

MIT

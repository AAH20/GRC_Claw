# GRC_Claw Python SDK

Python SDK for the GRC_Claw compliance automation platform. Scan codebases, run CMMC assessments, and track trust scores from Python or the CLI.

## Installation

```bash
pip install grc-claw
```

## Quick Start

### Python API

```python
from grc_claw import GRCClient

client = GRCClient(api_key="your-api-key")

# Scan a directory
result = client.scan("/path/to/project", frameworks=["CMMC", "SOC2"])
print(f"Found {result['total_findings']} issues")

# Run CMMC assessment
assessment = client.cmmc_assess("/path/to/project", level=2)
print(f"Score: {assessment['overall_score']}%")

# Get trust score
trust = client.trust_score("org-123", "organization")
print(f"Trust: {trust['score']}/100")

# List frameworks
frameworks = client.list_frameworks()
for fw in frameworks:
    print(f"{fw['name']}: {fw['version']}")
```

### Context Manager

```python
with GRCClient(api_key="your-api-key") as client:
    result = client.scan("/path/to/project")
```

## CLI Usage

Set your API key as an environment variable:

```bash
export GRC_CLAW_API_KEY="your-api-key"
```

### Commands

```bash
# Scan a directory
grc scan /path/to/project --frameworks CMMC SOC2

# CMMC assessment
grc cmmc /path/to/project --level 2

# Get trust score
grc trust org-123 --entity-type organization

# List frameworks
grc frameworks

# List controls
grc controls --framework CMMC
```

### CLI Options

```bash
grc --api-key KEY        # Provide API key directly
grc --base-url URL       # Custom API endpoint
grc --timeout SECONDS    # Request timeout
```

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `GRC_CLAW_API_KEY` | Your API key |

## Rate Limiting

The SDK enforces client-side rate limiting (60 requests/minute) and automatically retries on 429 responses with exponential backoff.

## Error Handling

```python
from grc_claw import GRCClient, GRCError, AuthenticationError, RateLimitError

try:
    client = GRCClient(api_key="invalid")
except AuthenticationError as e:
    print(f"Auth failed: {e.message}")

try:
    result = client.scan("/path")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except GRCError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## License

MIT

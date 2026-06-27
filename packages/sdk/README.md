# @grc-claw/sdk

Compliance-as-Code SDK with `grcfile.yaml` support and CLI primitives for the GRC_Claw platform.

## Installation

```sh
npm install @grc-claw/sdk
```

## Quick Start

```ts
import { GRCClient } from '@grc-claw/sdk';

const client = new GRCClient({ apiUrl: 'https://a2zsoc.com', apiKey: process.env.GRC_API_KEY });
const controls = await client.controls.list({ orgSlug: 'acme-corp', framework: 'soc2' });
```

## License

MIT

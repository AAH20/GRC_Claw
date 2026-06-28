# Contributing to GRC_Claw

## Adding a connector

1. Create `packages/cloud-connectors/src/<service>.ts`
2. Export from `packages/cloud-connectors/src/index.ts`
3. Wire into `api/platform/[...path].ts` integrations handler
4. Add connector card to integrations page

## Adding framework mappings

Mappings live in the A2Z SOC database (27,596 rows). To propose additions:
1. Open an issue with the framework name and control IDs
2. Include the source document (NIST SP, ISO standard, etc.)
3. We'll add to the crosswalk corpus and expose via the API

## Adding compliance rules (VS Code extension)

Add to `packages/vscode-extension/src/extension.ts` in the SCAN_RULES array.
Each rule needs: pattern (RegExp), message, severity (DiagnosticSeverity), frameworks ([])

## License
MIT. All contributions are MIT licensed.

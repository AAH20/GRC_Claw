# GRC_Claw Development Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Building](#building)
- [Testing](#testing)
- [Docker Development](#docker-development)
- [Code Style](#code-style)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | >= 20.0.0 | Runtime |
| npm | >= 10.0.0 | Package manager |
| Docker | >= 24.0.0 | Containerization |
| Docker Compose | >= 2.20.0 | Multi-container orchestration |
| Git | >= 2.40.0 | Version control |
| VS Code | Latest | Recommended editor |

### Verify Installation

```bash
node --version    # v20.x.x or higher
npm --version     # 10.x.x or higher
docker --version  # 24.x.x or higher
docker compose version  # 2.20.x or higher
```

---

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/your-org/GRC_Claw.git
cd GRC_Claw
npm install
```

### 2. Build All Packages

```bash
npm run build
```

### 3. Run Tests

```bash
npm test                    # Ingest package tests
npm run test:all           # Build all packages
npm run test:comprehensive # Full test suite
```

### 4. Start Development Services

```bash
# Start the gateway
npm run gateway

# Start the console (in another terminal)
npm run console

# Or use Docker Compose for all services
docker compose -f deploy/docker-compose.yml up
```

---

## Project Structure

```
GRC_Claw/
├── apps/                    # Application entry points
│   ├── console/            # Web console UI
│   └── gateway/            # API gateway
├── packages/               # Shared libraries (89 packages)
│   ├── ingest/             # Data ingestion
│   ├── evidence/           # Evidence collection
│   ├── compliance-orchestrator/  # Core orchestration
│   ├── mcp-server/         # MCP protocol server
│   └── ...                 # 85+ more packages
├── deploy/                 # Deployment configurations
│   ├── Dockerfile          # Main deployment image
│   └── docker-compose.yml  # Multi-service orchestration
├── deployment/             # Service-specific Dockerfiles (27 total)
│   ├── grc-claw-api/
│   ├── grc-claw-deployment/
│   │   ├── docker/         # Docker images
│   │   └── dockerfiles/    # Alternative Dockerfiles
│   └── ...
├── scripts/                # Build and test scripts
├── examples/               # Usage examples
├── docs/                   # Documentation
├── specs/                  # Specifications
├── schemas/                # JSON schemas
├── .devcontainer/          # Development container config
├── package.json            # Root workspace config
├── tsconfig.json           # TypeScript project references
└── tsconfig.base.json      # Shared TS config
```

---

## Development Workflow

### Branch Naming

```
feature/<description>     # New features
bugfix/<description>      # Bug fixes
hotfix/<description>      # Critical fixes
refactor/<description>   # Code refactoring
docs/<description>        # Documentation
test/<description>        # Test additions
```

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new compliance rule engine
fix: resolve evidence collector timeout
docs: update API documentation
test: add integration tests for PDP
refactor: simplify policy evaluation logic
chore: update dependencies
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commits
3. Ensure all tests pass: `npm run test:comprehensive`
4. Update documentation if needed
5. Open a PR with a clear description
6. Address review feedback
7. Squash merge when approved

---

## Building

### Build All Packages

```bash
npm run build
```

This uses TypeScript project references to build all 89 packages in dependency order.

### Build Specific Package

```bash
npm run build -w @grc-claw/<package-name>
```

### Build Console

```bash
npm run build:console
```

### Clean Build

```bash
# Remove all build artifacts
find . -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.tsbuildinfo" -delete

# Rebuild
npm run build
```

---

## Testing

### Run All Tests

```bash
npm run test:comprehensive
```

### Run Package-Specific Tests

```bash
# Ingest package
npm test

# Specific package
npm run test -w @grc-claw/<package-name>

# All test scripts
npm run test:orchestrator
npm run test:mcp
npm run test:skills
# ... see package.json for full list
```

### Test Coverage

```bash
# Generate coverage report
npx vitest run --coverage

# View coverage
open coverage/index.html
```

### Writing Tests

Tests use Vitest and are co-located with source files:

```typescript
// packages/example/src/example.test.ts
import { describe, it, expect } from 'vitest';
import { myFunction } from './my-function.js';

describe('myFunction', () => {
  it('should return expected value', () => {
    expect(myFunction('input')).toBe('expected');
  });
});
```

---

## Docker Development

### Build All Docker Images

```bash
# Build main deployment image
docker build -t grc-claw:latest -f deploy/Dockerfile .

# Build specific service
docker build -t grc-claw-policy-api:latest \
  -f deployment/grc-claw-deployment/docker/policy-api/Dockerfile .
```

### Docker Compose

```bash
# Start all services
docker compose -f deploy/docker-compose.yml up -d

# View logs
docker compose -f deploy/docker-compose.yml logs -f

# Stop all services
docker compose -f deploy/docker-compose.yml down

# Rebuild and restart
docker compose -f deploy/docker-compose.yml up -d --build
```

### Available Docker Images (27 total)

| Service | Dockerfile Path |
|---------|----------------|
| Main API | `deploy/Dockerfile` |
| Agent Identity | `deployment/.../agent-identity/Dockerfile` |
| Policy API | `deployment/.../policy-api/Dockerfile` |
| Approval Workflow | `deployment/.../approval-workflow/Dockerfile` |
| PEP Gateway | `deployment/.../pep-gateway/Dockerfile` |
| Evidence Collector | `deployment/.../evidence-collector/Dockerfile` |
| Analytics Engine | `deployment/.../analytics-engine/Dockerfile` |
| PDP Service | `deployment/.../pdp-service/Dockerfile` |
| Discovery Engine | `deployment/.../discovery-engine/Dockerfile` |
| Risk Assessment | `deployment/.../risk-assessment/Dockerfile` |
| OTel Collector | `deployment/.../otel-collector/Dockerfile` |
| Reporting Engine | `deployment/.../reporting-engine/Dockerfile` |
| Compliance Mapping | `deployment/.../compliance-mapping/Dockerfile` |

---

## Code Style

### TypeScript

- **Target**: ES2022
- **Module**: NodeNext
- **Strict mode**: Enabled
- **Style**: 2-space indentation, single quotes, semicolons

### Linting

```bash
# Lint all files
npx eslint .

# Lint specific package
npx eslint packages/<name>/src/

# Auto-fix
npx eslint . --fix
```

### Formatting

```bash
# Format all files
npx prettier --write .

# Check formatting
npx prettier --check .
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
cp .devcontainer/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Or use Husky:

```bash
npx husky install
npx husky add .husky/pre-commit "bash .devcontainer/pre-commit"
```

---

## Debugging

### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Gateway",
      "program": "${workspaceFolder}/apps/gateway/src/index.ts",
      "preLaunchTask": "npm: build",
      "outFiles": ["${workspaceFolder}/**/dist/**/*.js"],
      "env": { "NODE_ENV": "development" }
    },
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Tests",
      "program": "${workspaceFolder}/node_modules/vitest/vitest.mjs",
      "args": ["run", "${relativeFile}"],
      "console": "integratedTerminal"
    }
  ]
}
```

### Docker Debugging

```bash
# Build with debug symbols
docker build -t grc-claw:debug -f deploy/Dockerfile --build-arg NODE_ENV=development .

# Run with debug port exposed
docker run -p 9229:9229 -e NODE_ENV=development grc-claw:debug

# Attach debugger from VS Code
# Use "Attach to Node/Chrome" configuration
```

---

## Common Tasks

### Add a New Package

1. Create directory: `packages/<name>/`
2. Create `package.json`:

```json
{
  "name": "@grc-claw/<name>",
  "version": "1.0.0",
  "private": true,
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "vitest run"
  }
}
```

3. Create `tsconfig.json`:

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src/**/*"]
}
```

4. Add to root `tsconfig.json` references
5. Add to root `package.json` workspaces (if not using glob)
6. Run `npm install`

### Add a New Docker Service

1. Create `deployment/<service>/Dockerfile`
2. Add to `deploy/docker-compose.yml`
3. Add build script to root `package.json`
4. Update this documentation

### Update Dependencies

```bash
# Check for outdated packages
npm outdated

# Update all packages
npm update

# Update specific package
npm update <package-name>

# Update to latest (breaking changes)
npm install <package-name>@latest
```

### Generate Changeset

```bash
npx changeset
# Select packages, bump version, describe changes
npx changeset version
npx changeset publish
```

---

## IDE Setup

### VS Code Extensions

Install recommended extensions:

```bash
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension ms-vscode.vscode-typescript-next
code --install-extension redhat.vscode-yaml
code --install-extension ms-azuretools.vscode-docker
code --install-extension github.copilot
code --install-extension eamodio.gitlens
```

### VS Code Settings

Settings are pre-configured in `.vscode/settings.json`:
- TypeScript SDK points to workspace version
- Format on save enabled
- ESLint auto-fix on save
- Prettier as default formatter

### Recommended VS Code Settings

Add to your user settings for better experience:

```json
{
  "editor.quickSuggestions": {
    "strings": true
  },
  "typescript.suggest.autoImports": true,
  "javascript.suggest.autoImports": true,
  "editor.suggestSelection": "first",
  "editor.acceptSuggestionOnEnter": "on"
}
```

---

## Architecture Overview

### Core Components

1. **Gateway** (`packages/gateway`): Supervised control-plane gateway daemon
2. **Core** (`packages/core`): Domain types and GRCEngineFacade
3. **SDK** (`packages/sdk`): Compliance-as-Code SDK with grcfile.yaml support
4. **CLI** (`packages/cli`): Command-line interface
5. **MCP Server** (`packages/mcp-server`): Model Context Protocol server

### Key Packages

- **Evidence**: Evidence collection and management
- **Agent Identity**: Agent identity and trust management
- **Compliance Orchestrator**: Orchestration of compliance workflows
- **Policy Management**: Policy definition and enforcement
- **Risk Assessment**: Risk quantification and assessment
- **Audit Management**: Audit trail and reporting
- **Incident Response**: Incident management workflows
- **Persistence**: Data persistence layer
- **Observability**: Monitoring, logging, and tracing

### Communication

- **REST API**: Gateway exposes REST API on port 18791
- **gRPC**: Inter-service communication on port 50051
- **MCP**: Model Context Protocol for AI agent integration

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Console   │────▶│   Gateway   │────▶│   Core      │
│   (Web UI)  │     │   (REST)    │     │   Engine    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Services   │
                    │  (gRPC)     │
                    └─────────────┘
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues and solutions.

---

## Getting Help

- **Documentation**: [README.md](../README.md)
- **Architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

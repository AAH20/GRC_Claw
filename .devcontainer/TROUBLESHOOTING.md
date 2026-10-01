# GRC_Claw Troubleshooting Guide

## Table of Contents

- [Installation Issues](#installation-issues)
- [Build Issues](#build-issues)
- [Test Issues](#test-issues)
- [Docker Issues](#docker-issues)
- [Runtime Issues](#runtime-issues)
- [Performance Issues](#performance-issues)
- [IDE Issues](#ide-issues)
- [Getting Help](#getting-help)

---

## Installation Issues

### `npm install` fails with peer dependency errors

**Symptom:**
```
npm ERR! ERESOLVE unable to resolve dependency tree
```

**Solution:**
```bash
# Use legacy peer deps resolution
npm install --legacy-peer-deps

# Or use npm v10+ which handles this better
npm install
```

### `node-gyp` build failures

**Symptom:**
```
gyp ERR! stack Error: `gyp` failed with exit code: 1
```

**Solution:**
```bash
# macOS: Install Xcode Command Line Tools
xcode-select --install

# Install build essentials
npm install -g node-gyp

# Rebuild native modules
npm rebuild
```

### Node version mismatch

**Symptom:**
```
Error: Node.js version >= 20.0.0 is required
```

**Solution:**
```bash
# Check current version
node --version

# Install Node 20+ using nvm
nvm install 20
nvm use 20

# Or using Homebrew
brew install node@20
brew link node@20 --force
```

---

## Build Issues

### TypeScript compilation errors

**Symptom:**
```
error TS2307: Cannot find module '@grc-claw/<package>'
```

**Solution:**
```bash
# Build all packages in dependency order
npm run build

# If specific package fails, build it first
npm run build -w @grc-claw/<dependency-package>

# Clean and rebuild
find . -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.tsbuildinfo" -delete
npm run build
```

### `tsc -b` fails with project reference errors

**Symptom:**
```
error TS6306: Referenced project must have setting "composite": true
```

**Solution:**
```bash
# Ensure all tsconfig.json files extend tsconfig.base.json
# and have composite: true for referenced projects

# Verify tsconfig.json references
cat tsconfig.json

# Rebuild from clean state
rm -rf node_modules/.cache
npm run build
```

### Out of memory during build

**Symptom:**
```
JavaScript heap out of memory
```

**Solution:**
```bash
# Increase Node memory limit
export NODE_OPTIONS="--max-old-space-size=4096"

# Or for one-time build
NODE_OPTIONS="--max-old-space-size=4096" npm run build
```

### Module resolution errors

**Symptom:**
```
Error: Cannot find module './dist/index.js'
```

**Solution:**
```bash
# Ensure package is built
npm run build -w @grc-claw/<package>

# Check package.json exports field
cat packages/<package>/package.json

# Verify dist directory exists
ls packages/<package>/dist/
```

---

## Test Issues

### Tests fail with timeout

**Symptom:**
```
Error: Test timed out after 5000ms
```

**Solution:**
```bash
# Increase timeout in vitest config
# vitest.config.ts
export default defineConfig({
  test: {
    testTimeout: 30000,
    hookTimeout: 30000
  }
});

# Or for specific test
it('slow test', async () => {
  // ...
}, 30000);
```

### Tests fail with module not found

**Symptom:**
```
Error: Cannot find module '@grc-claw/<package>'
```

**Solution:**
```bash
# Build packages before testing
npm run build

# Run tests with tsx for direct TS execution
npx vitest run --config vitest.config.ts
```

### Tests pass locally but fail in CI

**Symptom:**
Tests fail in GitHub Actions but pass on local machine.

**Solution:**
```bash
# Run tests in CI mode
CI=true npm run test:comprehensive

# Check for environment-specific issues
echo $NODE_ENV
echo $CI

# Ensure all dependencies are installed
npm ci
```

### Vitest watch mode issues

**Symptom:**
Tests don't re-run on file changes.

**Solution:**
```bash
# Clear vitest cache
rm -rf node_modules/.vitest

# Restart vitest
npx vitest --watch
```

---

## Docker Issues

### Docker build fails

**Symptom:**
```
failed to solve: rpc error: code = Unknown desc = executor failed running
```

**Solution:**
```bash
# Clean Docker build cache
docker builder prune -f

# Build with no cache
docker build --no-cache -t grc-claw:latest -f deploy/Dockerfile .

# Check Dockerfile syntax
docker build --check -f deploy/Dockerfile .
```

### Docker Compose services won't start

**Symptom:**
```
Error response from daemon: driver failed programming external connectivity
```

**Solution:**
```bash
# Check if ports are in use
lsof -i :3000
lsof -i :8080

# Stop conflicting services
docker compose -f deploy/docker-compose.yml down

# Or use different ports in docker-compose.yml
```

### Docker container exits immediately

**Symptom:**
Container starts then stops with exit code 1.

**Solution:**
```bash
# Check logs
docker logs <container-id>

# Run interactively to see error
docker run -it --entrypoint /bin/sh grc-claw:latest

# Check entrypoint script
cat deploy/Dockerfile | grep ENTRYPOINT
```

### Docker volume permission issues

**Symptom:**
```
EACCES: permission denied, open '/data/file'
```

**Solution:**
```bash
# Fix volume permissions
docker run --rm -v grc-claw-data:/data alpine chown -R node:node /data

# Or in docker-compose.yml, add user: node
```

### Docker network issues

**Symptom:**
```
Error: Cannot connect to the Docker daemon
```

**Solution:**
```bash
# Check Docker is running
docker info

# Restart Docker (macOS)
killall Docker && open /Applications/Docker.app

# Or using Homebrew
brew services restart docker
```

---

## Runtime Issues

### Gateway won't start

**Symptom:**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solution:**
```bash
# Find process using port
lsof -i :3000

# Kill process
kill -9 <PID>

# Or use different port
PORT=3001 npm run gateway
```

### MCP Server connection issues

**Symptom:**
```
Error: Connection refused to MCP server
```

**Solution:**
```bash
# Check if MCP server is running
curl http://localhost:8081/health

# Start MCP server
npm run start -w @grc-claw/mcp-server

# Check MCP server logs
docker logs grc-claw-mcp
```

### Memory leaks / high memory usage

**Symptom:**
Process memory grows unbounded.

**Solution:**
```bash
# Run with memory limit
NODE_OPTIONS="--max-old-space-size=2048" npm run gateway

# Generate heap snapshot
kill -USR2 <PID>

# Analyze with Chrome DevTools
# Open chrome://inspect and take heap snapshot
```

### Database connection issues

**Symptom:**
```
Error: connect ECONNREFUSED 127.0.0.1:5432
```

**Solution:**
```bash
# Check if database is running
docker ps | grep postgres

# Start database
docker compose -f deploy/docker-compose.yml up -d postgres

# Check connection string
echo $DATABASE_URL
```

---

## Performance Issues

### Slow build times

**Symptom:**
`npm run build` takes too long.

**Solution:**
```bash
# Use incremental builds (default with tsc -b)
npm run build

# Parallelize builds
NODE_OPTIONS="--max-old-space-size=4096" npm run build

# Use SWC for faster compilation (if configured)
npm run build:fast
```

### Slow test execution

**Symptom:**
Tests take too long to run.

**Solution:**
```bash
# Run tests in parallel
npx vitest run --maxWorkers=4

# Run only changed tests
npx vitest run --changed

# Run specific test file
npx vitest run packages/<name>/src/<file>.test.ts
```

### Docker build too slow

**Symptom:**
Docker builds take too long.

**Solution:**
```bash
# Use BuildKit
DOCKER_BUILDKIT=1 docker build -t grc-claw:latest -f deploy/Dockerfile .

# Use cache mounts
# In Dockerfile:
# RUN --mount=type=cache,target=/root/.npm npm ci

# Multi-stage builds to reduce final image size
# See deploy/Dockerfile for example
```

---

## IDE Issues

### VS Code TypeScript server crashes

**Symptom:**
```
The TypeScript language service died 5 times
```

**Solution:**
```bash
# Restart TS server
# VS Code: Cmd+Shift+P -> "TypeScript: Restart TS Server"

# Increase memory
# Add to VS Code settings:
# "typescript.tsserver.maxTsServerMemory": 4096

# Or in workspace settings
echo '{"typescript.tsserver.maxTsServerMemory": 4096}' >> .vscode/settings.json
```

### ESLint not working

**Symptom:**
ESLint errors not shown in editor.

**Solution:**
```bash
# Ensure ESLint extension is installed
# dbaeumer.vscode-eslint

# Check ESLint config
cat .eslintrc.cjs

# Run ESLint manually
npx eslint . --ext .ts,.tsx

# Restart ESLint server
# VS Code: Cmd+Shift+P -> "ESLint: Restart ESLint Server"
```

### Prettier not formatting on save

**Symptom:**
Files not formatted when saved.

**Solution:**
```bash
# Check VS Code settings
# "editor.formatOnSave": true
# "editor.defaultFormatter": "esbenp.prettier-vscode"

# Ensure Prettier config exists
cat .prettierrc

# Run Prettier manually
npx prettier --write .
```

### Git integration issues

**Symptom:**
Git changes not shown in VS Code.

**Solution:**
```bash
# Check Git is installed
git --version

# Refresh Git state
# VS Code: Cmd+Shift+P -> "Git: Refresh"

# Check .gitignore
cat .gitignore
```

---

## Getting Help

If you're still experiencing issues:

1. **Check existing issues**: [GitHub Issues](https://github.com/your-org/GRC_Claw/issues)
2. **Search discussions**: [GitHub Discussions](https://github.com/your-org/GRC_Claw/discussions)
3. **Review documentation**: [README.md](../README.md)
4. **Check architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md)
5. **Ask for help**: Open a new issue with:
   - Your OS and version
   - Node.js version (`node --version`)
   - Docker version (`docker --version`)
   - Full error message
   - Steps to reproduce
   - What you've tried so far

---

## Quick Diagnostic Commands

```bash
# System info
echo "=== System ===" && uname -a
echo "=== Node ===" && node --version
echo "=== npm ===" && npm --version
echo "=== Docker ===" && docker --version
echo "=== Git ===" && git --version

# Project info
echo "=== Project ===" && pwd
echo "=== Branch ===" && git branch --show-current
echo "=== Status ===" && git status --short

# Dependencies
echo "=== Outdated ===" && npm outdated
echo "=== Installed ===" && npm list --depth=0

# Build status
echo "=== Build artifacts ===" && find . -name "dist" -type d | wc -l
echo "=== TypeScript errors ===" && npx tsc --noEmit 2>&1 | head -20

# Docker status
echo "=== Containers ===" && docker ps -a
echo "=== Images ===" && docker images | grep grc-claw
echo "=== Volumes ===" && docker volume ls | grep grc-claw
```

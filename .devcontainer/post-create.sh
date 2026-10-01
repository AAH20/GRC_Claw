#!/usr/bin/env bash
set -euo pipefail

echo "🐾 GRC_Claw DevContainer Setup"
echo "==============================="

# Ensure correct ownership
sudo chown -R node:node /workspaces/GRC_Claw 2>/dev/null || true

# Install dependencies
echo "📦 Installing dependencies..."
npm ci --ignore-scripts

# Build all packages
echo "🔨 Building all packages..."
npm run build

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
if command -v pre-commit &>/dev/null; then
  pre-commit install --install-hooks
else
  echo "⚠️  pre-commit not found, skipping hook installation"
  echo "   Install with: pip install pre-commit"
fi

# Verify setup
echo "✅ Verifying setup..."
node --version
npm --version
npx tsc --version

echo ""
echo "🎉 GRC_Claw development environment ready!"
echo ""
echo "Quick start:"
echo "  npm run build          # Build all packages"
echo "  npm test               # Run tests"
echo "  npm run gateway        # Start gateway"
echo "  npm run console        # Start console"
echo "  npm run doctor         # Run diagnostics"
echo ""

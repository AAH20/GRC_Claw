# GRC_Claw Unified Build & Deployment Makefile
# Usage: make [target] [VARS]

SHELL := /bin/bash
ROOT := $(shell cd "$(dir $(lastword $(MAKEFILE_LIST)))/.." && pwd)
SCRIPTS := $(ROOT)/scripts
DOCKER_DIR := $(ROOT)/deploy
COMPOSE_FILE := $(DOCKER_DIR)/docker-compose.yml
IMAGE_REGISTRY ?= ghcr.io/grc-claw
IMAGE_TAG ?= $(shell git -C $(ROOT) rev-parse --short HEAD 2>/dev/null || echo "latest")
GATEWAY_PORT ?= 18791
GATEWAY_TOKEN ?= grc-test-token

.PHONY: help build test scan deploy validate rollback clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Build ──────────────────────────────────────────────────────────────────

build: ## Build all Docker images
	@echo "▶ Building GRC_Claw images (tag: $(IMAGE_TAG))"
	docker build -t $(IMAGE_REGISTRY)/gateway:$(IMAGE_TAG) \
		-f $(DOCKER_DIR)/Dockerfile $(ROOT)
	@for svc in $(ROOT)/deployment/grc-claw-deployment/docker/*/; do \
		name=$$(basename $$svc); \
		if [ -f $$svc/Dockerfile ]; then \
			echo "  → $$name"; \
			docker build -t $(IMAGE_REGISTRY)/$$name:$(IMAGE_TAG) \
				-f $$svc/Dockerfile $$svc || exit 1; \
		fi; \
	done
	@echo "✓ Build complete"

build-ts: ## Build TypeScript packages
	cd $(ROOT) && npm run build

# ── Test ───────────────────────────────────────────────────────────────────

test: ## Run all tests (unit + integration)
	@echo "▶ Running test suite..."
	cd $(ROOT) && bash scripts/test.sh
	cd $(ROOT) && bash scripts/test-comprehensive.sh

test-unit: ## Run unit tests only
	cd $(ROOT) && npm run test -w @grc-claw/ingest

test-integration: ## Run integration tests (requires running gateway)
	cd $(ROOT) && bash scripts/test.sh

# ── Scan ───────────────────────────────────────────────────────────────────

scan: build ## Scan all images for vulnerabilities
	@echo "▶ Scanning images..."
	bash $(SCRIPTS)/scan-images.sh $(IMAGE_REGISTRY) $(IMAGE_TAG)

scan-trivy: ## Scan with Trivy only
	@command -v trivy >/dev/null || { echo "trivy not installed"; exit 1; }
	trivy image --severity HIGH,CRITICAL $(IMAGE_REGISTRY)/gateway:$(IMAGE_TAG)

scan-grype: ## Scan with Grype only
	@command -v grype >/dev/null || { echo "grype not installed"; exit 1; }
	grype $(IMAGE_REGISTRY)/gateway:$(IMAGE_TAG)

# ── Deploy ─────────────────────────────────────────────────────────────────

deploy: build scan validate ## Full deploy pipeline: build → scan → validate
	@echo "▶ Deploying GRC_Claw stack..."
	docker compose -f $(COMPOSE_FILE) up -d --remove-orphans
	@echo "✓ Deploy complete. Gateway: http://127.0.0.1:$(GATEWAY_PORT)"

deploy-fast: build ## Deploy without scan (dev only)
	docker compose -f $(COMPOSE_FILE) up -d --remove-orphans

# ── Validate ───────────────────────────────────────────────────────────────

validate: ## Validate deployment health
	@echo "▶ Validating deployment..."
	bash $(SCRIPTS)/validate-deployment.sh $(GATEWAY_PORT) $(GATEWAY_TOKEN)

# ── Rollback ───────────────────────────────────────────────────────────────

rollback: ## Rollback to previous image tag
	@echo "▶ Rolling back..."
	bash $(SCRIPTS)/rollback.sh $(IMAGE_REGISTRY) $(IMAGE_TAG)

# ── Clean ──────────────────────────────────────────────────────────────────

clean: ## Remove all containers and prune
	@echo "▶ Cleaning up..."
	docker compose -f $(COMPOSE_FILE) down --remove-orphans
	docker image prune -f --filter "label=grc-claw"
	@echo "✓ Clean complete"

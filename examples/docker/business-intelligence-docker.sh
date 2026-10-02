#!/usr/bin/env bash
# =============================================================================
# Business Intelligence Docker Example
# =============================================================================
# Description: BI dashboards and data-driven decision support
#
# This script provides a complete Docker workflow for running the Business Intelligence
# tool in a containerized environment. It includes:
#   - Docker image build
#   - Container run with proper configuration
#   - Docker Compose orchestration
#
# Usage:
#   ./business-intelligence-docker.sh build    # Build the Docker image
#   ./business-intelligence-docker.sh run      # Run the container
#   ./business-intelligence-docker.sh compose  # Start with Docker Compose
#   ./business-intelligence-docker.sh stop     # Stop compose services
#   ./business-intelligence-docker.sh clean    # Remove containers and images
# =============================================================================

set -euo pipefail

# -- Configuration ------------------------------------------------------------
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly IMAGE_NAME="grc-business-intelligence"
readonly IMAGE_TAG="latest"
readonly CONTAINER_NAME="grc-business-intelligence"
readonly COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.business-intelligence.yml"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# -- Helper Functions ---------------------------------------------------------

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

check_docker() {
    if ! command -v docker &>/dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    if ! docker info &>/dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    log_info "Docker is available"
}

check_compose() {
    if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    log_info "Docker Compose is available"
}

# -- Dockerfile Generation ----------------------------------------------------

generate_dockerfile() {
    log_info "Generating Dockerfile..."
    cat > "${SCRIPT_DIR}/Dockerfile.business-intelligence" << 'DOCKERFILE_EOF'
FROM python:3.11-slim

LABEL maintainer="GRC Claw"
LABEL description="BI dashboards and data-driven decision support"

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r grc && useradd -r -g grc -d /app -s /sbin/nologin grc

WORKDIR /app

# Install Python dependencies
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy application code
COPY --chown=grc:grc . .

# Switch to non-root user
USER grc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

ENTRYPOINT ["python", "-m", "business_intelligence"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
DOCKERFILE_EOF
    log_info "Dockerfile generated: Dockerfile.business-intelligence"
}

# -- Docker Compose File Generation -------------------------------------------

generate_compose() {
    log_info "Generating Docker Compose file..."
    cat > "${COMPOSE_FILE}" << 'COMPOSE_EOF'
version: "3.8"

services:
  business-intelligence:
    build:
      context: .
      dockerfile: Dockerfile.business-intelligence
    image: grc-business-intelligence:business-intelligence
    container_name: grc-business-intelligence
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - LOG_LEVEL=info
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/grc_business-intelligence
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    networks:
      - grc-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  redis:
    image: redis:7-alpine
    container_name: grc-business-intelligence-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - grc-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  postgres:
    image: postgres:15-alpine
    container_name: grc-business-intelligence-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: grc
      POSTGRES_PASSWORD: grc
      POSTGRES_DB: grc_business-intelligence
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - grc-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U grc -d grc_business-intelligence"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis-data:
  postgres-data:

networks:
  grc-network:
    driver: bridge
COMPOSE_EOF
    log_info "Compose file generated: ${COMPOSE_FILE}"
}

# -- Build Command ------------------------------------------------------------

cmd_build() {
    log_info "Building Docker image: grc-business-intelligence:business-intelligence"
    check_docker
    generate_dockerfile
    generate_compose

    docker build \
        --tag "grc-business-intelligence:@" \
        --file "${SCRIPT_DIR}/Dockerfile.business-intelligence" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        "${SCRIPT_DIR}"

    log_info "Build complete: grc-business-intelligence:business-intelligence"
    docker images "grc-business-intelligence" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
}

# -- Run Command --------------------------------------------------------------

cmd_run() {
    log_info "Running container: grc-business-intelligence"
    check_docker

    # Remove existing container if present
    if docker ps -a --format '{{.Names}}' | grep -q "^grc-business-intelligence$"; then
        log_warn "Removing existing container: grc-business-intelligence"
        docker rm -f "grc-business-intelligence"
    fi

    docker run \
        --detach \
        --name "grc-business-intelligence" \
        --publish "8080:8080" \
        --env LOG_LEVEL=info \
        --env ENVIRONMENT=production \
        --restart unless-stopped \
        --health-cmd="curl -f http://localhost:8080/health || exit 1" \
        --health-interval="30s" \
        --health-timeout="10s" \
        --health-retries="3" \
        "grc-business-intelligence:business-intelligence"

    log_info "Container started: grc-business-intelligence"
    log_info "Health check:"
    docker ps --filter "name=grc-business-intelligence" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    log_info "Logs (last 20 lines):"
    docker logs --tail 20 "grc-business-intelligence" || true
}

# -- Compose Command ----------------------------------------------------------

cmd_compose() {
    log_info "Starting services with Docker Compose..."
    check_docker
    check_compose
    generate_dockerfile
    generate_compose

    if command -v docker-compose &>/dev/null; then
        docker-compose -f "${COMPOSE_FILE}" up --build --detach
    else
        docker compose -f "${COMPOSE_FILE}" up --build --detach
    fi

    log_info "Services started. Status:"
    if command -v docker-compose &>/dev/null; then
        docker-compose -f "${COMPOSE_FILE}" ps
    else
        docker compose -f "${COMPOSE_FILE}" ps
    fi
}

# -- Stop Command -------------------------------------------------------------

cmd_stop() {
    log_info "Stopping services..."
    check_docker

    if command -v docker-compose &>/dev/null; then
        docker-compose -f "${COMPOSE_FILE}" down
    else
        docker compose -f "${COMPOSE_FILE}" down
    fi

    log_info "Services stopped"
}

# -- Clean Command ------------------------------------------------------------

cmd_clean() {
    log_info "Cleaning up containers and images..."
    check_docker

    # Stop and remove containers
    if command -v docker-compose &>/dev/null; then
        docker-compose -f "${COMPOSE_FILE}" down --volumes --remove-orphans 2>/dev/null || true
    else
        docker compose -f "${COMPOSE_FILE}" down --volumes --remove-orphans 2>/dev/null || true
    fi

    # Remove image
    docker rmi "grc-business-intelligence:business-intelligence" 2>/dev/null || true

    # Remove generated files
    rm -f "${SCRIPT_DIR}/Dockerfile.business-intelligence" "${COMPOSE_FILE}"

    log_info "Cleanup complete"
}

# -- Main ---------------------------------------------------------------------

usage() {
    cat <<EOF
Usage: ./${SCRIPT_NAME} <command>

Commands:
  build    Build the Docker image
  run      Run the container
  compose  Start with Docker Compose
  stop     Stop compose services
  clean    Remove containers and images

Examples:
  ./${SCRIPT_NAME} build
  ./${SCRIPT_NAME} run
  ./${SCRIPT_NAME} compose
EOF
}

main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi

    local command="$1"
    shift

    case "${command}" in
        build)   cmd_build   "$@" ;;
        run)     cmd_run     "$@" ;;
        compose)  cmd_compose  "$@" ;;
        stop)    cmd_stop    "$@" ;;
        clean)   cmd_clean   "$@" ;;
        help|-h|--help) usage ;;
        *)
            log_error "Unknown command: ${command}"
            usage
            exit 1
            ;;
    esac
}

main "$@"

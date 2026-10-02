#!/usr/bin/env bash
# =============================================================================
# Marketing Compliance Docker Example
# =============================================================================
# Description: Ensures marketing materials meet regulatory requirements
#
# This script provides a complete Docker workflow for running the Marketing Compliance
# tool in a containerized environment. It includes:
#   - Docker image build
#   - Container run with proper configuration
#   - Docker Compose orchestration
#
# Usage:
#   ./marketing-compliance-docker.sh build    # Build the Docker image
#   ./marketing-compliance-docker.sh run      # Run the container
#   ./marketing-compliance-docker.sh compose  # Start with Docker Compose
#   ./marketing-compliance-docker.sh stop     # Stop compose services
#   ./marketing-compliance-docker.sh clean    # Remove containers and images
# =============================================================================

set -euo pipefail

# -- Configuration ------------------------------------------------------------
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly IMAGE_NAME="grc-marketing-compliance"
readonly IMAGE_TAG="latest"
readonly CONTAINER_NAME="grc-marketing-compliance"
readonly COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.marketing-compliance.yml"

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
    cat > "${SCRIPT_DIR}/Dockerfile.marketing-compliance" << 'DOCKERFILE_EOF'
FROM python:3.11-slim

LABEL maintainer="GRC Claw"
LABEL description="Ensures marketing materials meet regulatory requirements"

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

ENTRYPOINT ["python", "-m", "marketing_compliance"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
DOCKERFILE_EOF
    log_info "Dockerfile generated: Dockerfile.marketing-compliance"
}

# -- Docker Compose File Generation -------------------------------------------

generate_compose() {
    log_info "Generating Docker Compose file..."
    cat > "${COMPOSE_FILE}" << 'COMPOSE_EOF'
version: "3.8"

services:
  marketing-compliance:
    build:
      context: .
      dockerfile: Dockerfile.marketing-compliance
    image: grc-marketing-compliance:marketing-compliance
    container_name: grc-marketing-compliance
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - LOG_LEVEL=info
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/grc_marketing-compliance
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
    container_name: grc-marketing-compliance-redis
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
    container_name: grc-marketing-compliance-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: grc
      POSTGRES_PASSWORD: grc
      POSTGRES_DB: grc_marketing-compliance
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - grc-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U grc -d grc_marketing-compliance"]
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
    log_info "Building Docker image: grc-marketing-compliance:marketing-compliance"
    check_docker
    generate_dockerfile
    generate_compose

    docker build \
        --tag "grc-marketing-compliance:@" \
        --file "${SCRIPT_DIR}/Dockerfile.marketing-compliance" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        "${SCRIPT_DIR}"

    log_info "Build complete: grc-marketing-compliance:marketing-compliance"
    docker images "grc-marketing-compliance" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
}

# -- Run Command --------------------------------------------------------------

cmd_run() {
    log_info "Running container: grc-marketing-compliance"
    check_docker

    # Remove existing container if present
    if docker ps -a --format '{{.Names}}' | grep -q "^grc-marketing-compliance$"; then
        log_warn "Removing existing container: grc-marketing-compliance"
        docker rm -f "grc-marketing-compliance"
    fi

    docker run \
        --detach \
        --name "grc-marketing-compliance" \
        --publish "8080:8080" \
        --env LOG_LEVEL=info \
        --env ENVIRONMENT=production \
        --restart unless-stopped \
        --health-cmd="curl -f http://localhost:8080/health || exit 1" \
        --health-interval="30s" \
        --health-timeout="10s" \
        --health-retries="3" \
        "grc-marketing-compliance:marketing-compliance"

    log_info "Container started: grc-marketing-compliance"
    log_info "Health check:"
    docker ps --filter "name=grc-marketing-compliance" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    log_info "Logs (last 20 lines):"
    docker logs --tail 20 "grc-marketing-compliance" || true
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
    docker rmi "grc-marketing-compliance:marketing-compliance" 2>/dev/null || true

    # Remove generated files
    rm -f "${SCRIPT_DIR}/Dockerfile.marketing-compliance" "${COMPOSE_FILE}"

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

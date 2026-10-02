#!/usr/bin/env bash
# =============================================================================
# GRC Claw — Redis Initialization Script
# =============================================================================
# Configures Redis with optimal settings for the GRC Claw platform.
# This script runs after Redis is started.
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

readonly REDIS_HOST="${REDIS_HOST:-localhost}"
readonly REDIS_PORT="${REDIS_PORT:-6379}"
readonly REDIS_PASSWORD="${REDIS_PASSWORD:-}"
readonly LOG_PREFIX="[init-redis]"

# =============================================================================
# Logging Functions
# =============================================================================

log_info() {
    echo "${LOG_PREFIX} [INFO] $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*"
}

log_warn() {
    echo "${LOG_PREFIX} [WARN] $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*" >&2
}

log_error() {
    echo "${LOG_PREFIX} [ERROR] $(date -u +"%Y-%m-%dT%H:%M:%SZ") $*" >&2
}

# =============================================================================
# Utility Functions
# =============================================================================

check_redis_available() {
    local max_attempts=30
    local attempt=1

    log_info "Waiting for Redis to be available at ${REDIS_HOST}:${REDIS_PORT}..."

    while [[ ${attempt} -le ${max_attempts} ]]; do
        if redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ${REDIS_PASSWORD:+-a "${REDIS_PASSWORD}"} ping &>/dev/null; then
            log_info "Redis is available."
            return 0
        fi
        log_warn "Attempt ${attempt}/${max_attempts}: Redis not ready. Retrying in 2s..."
        sleep 2
        ((attempt++))
    done

    log_error "Redis did not become available after ${max_attempts} attempts."
    return 1
}

redis_cmd() {
    local args=()
    [[ -n "${REDIS_PASSWORD}" ]] && args+=(-a "${REDIS_PASSWORD}")
    redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" "${args[@]}" "$@"
}

# =============================================================================
# Configuration Steps
# =============================================================================

configure_memory_policy() {
    log_info "Configuring memory eviction policy..."
    redis_cmd CONFIG SET maxmemory-policy allkeys-lru
    redis_cmd CONFIG SET maxmemory 256mb
}

configure_persistence() {
    log_info "Configuring persistence..."
    redis_cmd CONFIG SET save "900 1 300 10 60 10000"
    redis_cmd CONFIG SET appendonly yes
    redis_cmd CONFIG SET appendfsync everysec
}

configure_network() {
    log_info "Configuring network settings..."
    redis_cmd CONFIG SET timeout 300
    redis_cmd CONFIG SET tcp-keepalive 60
    redis_cmd CONFIG SET maxclients 10000
}

configure_safety() {
    log_info "Configuring safety settings..."
    redis_cmd CONFIG SET protected-mode yes
    redis_cmd CONFIG SET bind 0.0.0.0
}

create_namespaces() {
    log_info "Creating key namespaces..."

    # Namespace prefixes for different data types:
    #   agent:{id}       — Agent state and configuration
    #   campaign:{id}    — Campaign data and metrics
    #   session:{token}  — User sessions
    #   cache:{key}      — General cache entries
    #   rate:{service}   — Rate limiting counters
    #   lock:{resource}  — Distributed locks

    # Set namespace metadata (using Redis hashes for tracking)
    redis_cmd HSET grc:namespaces agent "Agent state and configuration"
    redis_cmd HSET grc:namespaces campaign "Campaign data and metrics"
    redis_cmd HSET grc:namespaces session "User sessions"
    redis_cmd HSET grc:namespaces cache "General cache entries"
    redis_cmd HSET grc:namespaces rate "Rate limiting counters"
    redis_cmd HSET grc:namespaces lock "Distributed locks"
}

configure_keyspace_notifications() {
    log_info "Configuring keyspace notifications..."
    redis_cmd CONFIG SET notify-keyspace-events "Exg"
}

warm_up() {
    log_info "Warming up Redis..."
    redis_cmd PING
    redis_cmd DBSIZE
}

# =============================================================================
# Main
# =============================================================================

main() {
    log_info "Starting Redis initialization..."

    check_redis_available

    configure_memory_policy
    configure_persistence
    configure_network
    configure_safety
    create_namespaces
    configure_keyspace_notifications
    warm_up

    log_info "Redis initialization complete."
    log_info "Redis server info:"
    redis_cmd INFO server
}

main "$@"

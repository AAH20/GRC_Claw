#!/usr/bin/env bash
# =============================================================================
# GRC Claw — Kafka Initialization Script
# =============================================================================
# Creates all required Kafka topics with appropriate configurations.
# This script runs after Kafka broker is healthy.
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

readonly KAFKA_BOOTSTRAP_SERVER="${KAFKA_BOOTSTRAP_SERVER:-localhost:9092}"
readonly KAFKA_TOPICS_CONFIG="${KAFKA_TOPICS_CONFIG:-/etc/kafka/topics.yaml}"
readonly LOG_PREFIX="[init-kafka]"

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

check_kafka_available() {
    local max_attempts=30
    local attempt=1

    log_info "Waiting for Kafka to be available at ${KAFKA_BOOTSTRAP_SERVER}..."

    while [[ ${attempt} -le ${max_attempts} ]]; do
        if kafka-broker-api-versions --bootstrap-server "${KAFKA_BOOTSTRAP_SERVER}" &>/dev/null; then
            log_info "Kafka is available."
            return 0
        fi
        log_warn "Attempt ${attempt}/${max_attempts}: Kafka not ready yet. Retrying in 2s..."
        sleep 2
        ((attempt++))
    done

    log_error "Kafka did not become available after ${max_attempts} attempts."
    return 1
}

topic_exists() {
    local topic_name="$1"
    kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP_SERVER}" --list | grep -qx "${topic_name}"
}

create_topic() {
    local topic_name="$1"
    local partitions="${2:-3}"
    local replication="${3:-1}"
    local retention_ms="${4:-604800000}"
    local cleanup_policy="${5:-delete}"

    if topic_exists "${topic_name}"; then
        log_warn "Topic '${topic_name}' already exists. Skipping."
        return 0
    fi

    log_info "Creating topic '${topic_name}' (partitions=${partitions}, replication=${replication}, retention=${retention_ms}ms)..."

    kafka-topics \
        --bootstrap-server "${KAFKA_BOOTSTRAP_SERVER}" \
        --create \
        --topic "${topic_name}" \
        --partitions "${partitions}" \
        --replication-factor "${replication}" \
        --config "retention.ms=${retention_ms}" \
        --config "cleanup.policy=${cleanup_policy}" \
        --config "min.insync.replicas=1" \
        --config "compression.type=producer"

    log_info "Topic '${topic_name}' created successfully."
}

# =============================================================================
# Topic Definitions
# =============================================================================

create_agent_events_topic() {
    create_topic "grc.agent.events" 6 1 604800000 "delete"
}

create_campaign_events_topic() {
    create_topic "grc.campaign.events" 6 1 604800000 "delete"
}

create_audit_log_topic() {
    create_topic "grc.audit.log" 3 1 2592000000 "delete"
}

create_metrics_topic() {
    create_topic "grc.metrics" 3 1 86400000 "delete"
}

create_notifications_topic() {
    create_topic "grc.notifications" 3 1 604800000 "delete"
}

create_dlq_topic() {
    create_topic "grc.dlq" 3 1 2592000000 "delete"
}

# =============================================================================
# Main
# =============================================================================

main() {
    log_info "Starting Kafka topic initialization..."

    check_kafka_available

    create_agent_events_topic
    create_campaign_events_topic
    create_audit_log_topic
    create_metrics_topic
    create_notifications_topic
    create_dlq_topic

    log_info "Kafka topic initialization complete."
    log_info "Listing all topics:"
    kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP_SERVER}" --list
}

main "$@"

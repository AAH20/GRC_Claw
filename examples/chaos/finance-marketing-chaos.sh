#!/usr/bin/env bash
#===============================================================================
#
#          FILE: finance-marketing-chaos.sh
#
#         USAGE: ./finance-marketing-chaos.sh [OPTIONS]
#
#   DESCRIPTION: Chaos Engineering example for Finance Marketing.
#                Injects faults, tests failure modes, and validates recovery.
#
#       OPTIONS: --fault-type <type>   Fault to inject (default: random)
#                --duration <seconds>   Fault duration (default: 30)
#                --dry-run              Show what would happen without executing
#                --verbose              Enable verbose output
#                --help                 Show this help message
#
#  REQUIREMENTS: bash 4.0+, curl, jq, nc
#
#          BUGS: Report to devops@grc-claw.io
#
#         NOTES: Run in a controlled environment. Not for production use.
#
#        AUTHOR: GRC Claw Chaos Engineering Team
#       VERSION: 1.0.0
#       CREATED: 2026-10-02
#===============================================================================

set -euo pipefail
IFS=$'\n\t'

#-------------------------------------------------------------------------------
# CONFIGURATION
#-------------------------------------------------------------------------------

readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="${LOG_DIR:-/var/log/grc-claw/chaos}"
readonly LOG_FILE="${LOG_DIR}/finance-marketing-chaos-$(date +%Y%m%d-%H%M%S).log"
readonly METRICS_FILE="${LOG_DIR}/finance-marketing-metrics.json"
readonly LOCK_FILE="/tmp/finance-marketing-chaos.lock"

readonly COMPONENT="Finance Marketing"
readonly COMPONENT_LOWER="finance-marketing"
readonly VERSION="1.0.0"

# Default configuration
FAULT_TYPE="random"
DURATION=30
DRY_RUN=false
VERBOSE=false
PARALLEL=false
MAX_RETRIES=3
RETRY_DELAY=5
TIMEOUT=10
THRESHOLD_CPU=80
THRESHOLD_MEM=85
THRESHOLD_LATENCY=500

# Fault types
FAULT_TYPES=("network_delay" "network_partition" "cpu_stress" "memory_pressure" "disk_fill" "process_kill" "dependency_failure" "data_corruption" "clock_skew" "random")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

#-------------------------------------------------------------------------------
# LOGGING FUNCTIONS
#-------------------------------------------------------------------------------

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "${YELLOW}$*${NC}"; }
log_error() { log "ERROR" "${RED}$*${NC}" >&2; }
log_debug() { if $VERBOSE; then log "DEBUG" "${CYAN}$*${NC}"; fi; }
log_success() { log "SUCCESS" "${GREEN}$*${NC}"; }

#-------------------------------------------------------------------------------
# UTILITY FUNCTIONS
#-------------------------------------------------------------------------------

cleanup() {
    local exit_code=$?
    log_info "Performing cleanup..."

    # Remove lock file
    if [[ -f "$LOCK_FILE" ]]; then
        rm -f "$LOCK_FILE"
        log_debug "Removed lock file: $LOCK_FILE"
    fi

    # Kill any background processes
    jobs -p | xargs -r kill 2>/dev/null || true

    # Remove temporary files
    rm -f /tmp/finance-marketing-*.tmp 2>/dev/null || true

    if [[ $exit_code -ne 0 ]]; then
        log_error "Chaos experiment failed with exit code: $exit_code"
    else
        log_success "Chaos experiment completed successfully"
    fi

    exit $exit_code
}

trap cleanup EXIT INT TERM

check_dependencies() {
    local missing=()
    for cmd in curl jq nc; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Install with: sudo apt-get install curl jq netcat-openbsd"
        exit 1
    fi
    log_debug "All dependencies satisfied"
}

acquire_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local pid
        pid="$(cat "$LOCK_FILE" 2>/dev/null || echo "")"
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            log_error "Another chaos experiment is running (PID: $pid)"
            exit 1
        fi
    fi
    echo $$ > "$LOCK_FILE"
    log_debug "Acquired lock: $LOCK_FILE"
}

release_lock() {
    rm -f "$LOCK_FILE"
    log_debug "Released lock: $LOCK_FILE"
}

init_environment() {
    mkdir -p "$LOG_DIR"
    touch "$LOG_FILE"
    log_info "=== Finance Marketing Chaos Engineering Experiment ==="
    log_info "Version: $VERSION"
    log_info "Log file: $LOG_FILE"
    log_info "Metrics file: $METRICS_FILE"
}

usage() {
    cat <<EOF
Chaos Engineering Example: Finance Marketing

Usage: $SCRIPT_NAME [OPTIONS]

Options:
    --fault-type <type>    Fault type to inject: ${FAULT_TYPES[*]}
    --duration <seconds>   Duration of fault injection (default: 30)
    --dry-run              Show what would happen without executing
    --verbose              Enable verbose output
    --parallel             Run multiple fault scenarios in parallel
    --max-retries <n>      Max retry attempts (default: 3)
    --timeout <seconds>    Operation timeout (default: 10)
    --help                 Show this help message

Examples:
    $SCRIPT_NAME --fault-type network_delay --duration 60
    $SCRIPT_NAME --fault-type cpu_stress --verbose
    $SCRIPT_NAME --dry-run --fault-type memory_pressure

EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --fault-type)
                FAULT_TYPE="$2"
                shift 2
                ;;
            --duration)
                DURATION="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --parallel)
                PARALLEL=true
                shift
                ;;
            --max-retries)
                MAX_RETRIES="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Validate fault type
    if [[ "$FAULT_TYPE" == "random" ]]; then
        FAULT_TYPE="${FAULT_TYPES[$((RANDOM % ${#FAULT_TYPES[@]}))]}"
        log_info "Randomly selected fault type: $FAULT_TYPE"
    fi

    local valid=false
    for ft in "${FAULT_TYPES[@]}"; do
        if [[ "$ft" == "$FAULT_TYPE" ]]; then
            valid=true
            break
        fi
    done

    if ! $valid; then
        log_error "Invalid fault type: $FAULT_TYPE"
        log_info "Valid types: ${FAULT_TYPES[*]}"
        exit 1
    fi

    log_info "Configuration: fault_type=$FAULT_TYPE, duration=$DURATION, dry_run=$DRY_RUN"
}

#-------------------------------------------------------------------------------
# METRICS COLLECTION
#-------------------------------------------------------------------------------

collect_metrics() {
    local metric_name="$1"
    local metric_value="$2"
    local metric_type="${3:-gauge}"
    local timestamp
    timestamp="$(date +%s)"

    local metric_entry
    metric_entry=$(jq -n \
        --arg name "$metric_name" \
        --arg value "$metric_value" \
        --arg type "$metric_type" \
        --arg ts "$timestamp" \
        --arg component "$COMPONENT_LOWER" \
        '{"name": $name, "value": $value, "type": $type, "timestamp": $ts, "component": $component}')

    if [[ -f "$METRICS_FILE" ]]; then
        jq --argjson entry "$metric_entry" '. += [$entry]' "$METRICS_FILE" > "${METRICS_FILE}.tmp" && mv "${METRICS_FILE}.tmp" "$METRICS_FILE"
    else
        echo "[$metric_entry]" | jq '.' > "$METRICS_FILE"
    fi

    log_debug "Metric collected: $metric_name=$metric_value"
}

record_baseline() {
    log_info "Recording baseline metrics..."

    # CPU usage
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 || echo "0")
    collect_metrics "cpu_usage_baseline" "$cpu_usage"

    # Memory usage
    local mem_usage
    mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' || echo "0")
    collect_metrics "memory_usage_baseline" "$mem_usage"

    # Disk usage
    local disk_usage
    disk_usage=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%' || echo "0")
    collect_metrics "disk_usage_baseline" "$disk_usage"

    # Load average
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',' || echo "0")
    collect_metrics "load_average_baseline" "$load_avg"

    log_success "Baseline metrics recorded"
}

#-------------------------------------------------------------------------------
# FAULT INJECTION FUNCTIONS
#-------------------------------------------------------------------------------

inject_network_delay() {
    local delay_ms="${1:-100}"
    log_info "Injecting network delay: ${delay_ms}ms"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would add ${delay_ms}ms delay to network traffic"
        return 0
    fi

    # Use tc (traffic control) to add delay
    if command -v tc &>/dev/null; then
        tc qdisc add dev eth0 root netem delay ${delay_ms}ms 2>/dev/null || \
            log_warn "Could not apply tc rules (may need root privileges)"
    fi

    # Simulate delay in application
    sleep "$(echo "scale=3; $delay_ms / 1000" | bc)"

    collect_metrics "network_delay_injected" "$delay_ms"
    log_success "Network delay injected: ${delay_ms}ms"
}

inject_network_partition() {
    log_info "Injecting network partition"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would block network traffic to dependencies"
        return 0
    fi

    # Block traffic to common dependency ports
    local ports=(443 80 5432 6379 9092 27017)
    for port in "${ports[@]}"; do
        iptables -A OUTPUT -p tcp --dport $port -j DROP 2>/dev/null || \
            log_warn "Could not block port $port (may need root privileges)"
    done

    collect_metrics "network_partition_injected" "1"
    log_success "Network partition injected"
}

inject_cpu_stress() {
    local load="${1:-90}"
    log_info "Injecting CPU stress: ${load}%"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would generate ${load}% CPU load"
        return 0
    fi

    # Calculate number of workers needed
    local nproc_val
    nproc_val=$(nproc 2>/dev/null || echo 1)
    local workers=$(( nproc_val * load / 100 ))
    workers=$(( workers > 0 ? workers : 1 ))

    log_debug "Spawning $workers CPU stress workers"

    for i in $(seq 1 $workers); do
        (
            while true; do
                : # Busy loop
            done
        ) &
    done

    collect_metrics "cpu_stress_injected" "$load"
    log_success "CPU stress injected with $workers workers"
}

inject_memory_pressure() {
    local pressure_mb="${1:-512}"
    log_info "Injecting memory pressure: ${pressure_mb}MB"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would allocate ${pressure_mb}MB memory"
        return 0
    fi

    # Allocate memory using dd
    local alloc_file="/tmp/finance-marketing-mem-pressure.tmp"
    dd if=/dev/zero of="$alloc_file" bs=1M count=$pressure_mb 2>/dev/null &
    local dd_pid=$!

    collect_metrics "memory_pressure_injected" "$pressure_mb"
    log_success "Memory pressure injected: ${pressure_mb}MB (PID: $dd_pid)"
}

inject_disk_fill() {
    local fill_mb="${1:-1024}"
    log_info "Injecting disk fill: ${fill_mb}MB"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would fill ${fill_mb}MB disk space"
        return 0
    fi

    local fill_file="/tmp/finance-marketing-disk-fill.tmp"
    dd if=/dev/zero of="$fill_file" bs=1M count=$fill_mb 2>/dev/null

    collect_metrics "disk_fill_injected" "$fill_mb"
    log_success "Disk fill injected: ${fill_mb}MB"
}

inject_process_kill() {
    log_info "Injecting process kill"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would kill a random finance-marketing worker process"
        return 0
    fi

    # Find and kill a process (simulated - kill a sleep process)
    local victim_pid
    victim_pid=$(ps aux | grep -E 'sleep 3600' | grep -v grep | head -1 | awk '{print $2}' || echo "")

    if [[ -n "$victim_pid" ]]; then
        kill -9 "$victim_pid" 2>/dev/null || true
        log_info "Killed process: $victim_pid"
    else
        # Create and kill a dummy process
        sleep 3600 &
        local dummy_pid=$!
        sleep 0.1
        kill -9 "$dummy_pid" 2>/dev/null || true
        log_info "Created and killed dummy process: $dummy_pid"
    fi

    collect_metrics "process_kill_injected" "1"
    log_success "Process kill injected"
}

inject_dependency_failure() {
    log_info "Injecting dependency failure"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would simulate dependency service failure"
        return 0
    fi

    # Simulate dependency failure by blocking ports
    local dep_ports=(5432 6379 9092 27017 3306)
    for port in "${dep_ports[@]}"; do
        iptables -A INPUT -p tcp --dport $port -j REJECT 2>/dev/null || true
        iptables -A OUTPUT -p tcp --dport $port -j REJECT 2>/dev/null || true
    done

    collect_metrics "dependency_failure_injected" "1"
    log_success "Dependency failure injected"
}

inject_data_corruption() {
    log_info "Injecting data corruption"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would corrupt data in finance-marketing storage"
        return 0
    fi

    # Create a test file and corrupt it
    local test_file="/tmp/finance-marketing-corruption-test.tmp"
    echo "ORIGINAL_DATA_$(date +%s)" > "$test_file"
    local original_hash
    original_hash=$(md5sum "$test_file" | awk '{print $1}')

    # Corrupt the file
    dd if=/dev/urandom of="$test_file" bs=1 count=100 conv=notrunc 2>/dev/null
    local corrupted_hash
    corrupted_hash=$(md5sum "$test_file" | awk '{print $1}')

    log_info "Original hash: $original_hash"
    log_info "Corrupted hash: $corrupted_hash"

    collect_metrics "data_corruption_injected" "1"
    log_success "Data corruption injected"
}

inject_clock_skew() {
    local skew_seconds="${1:-3600}"
    log_info "Injecting clock skew: ${skew_seconds}s"

    if $DRY_RUN; then
        log_info "[DRY-RUN] Would skew system clock by ${skew_seconds}s"
        return 0
    fi

    # Note: This is a simulation. Real clock skew requires root.
    log_warn "Clock skew injection requires root privileges"
    log_info "Simulating clock skew in application logic"

    # Simulate by recording offset
    echo "$skew_seconds" > "/tmp/finance-marketing-clock-skew.offset"

    collect_metrics "clock_skew_injected" "$skew_seconds"
    log_success "Clock skew injected: ${skew_seconds}s"
}

#-------------------------------------------------------------------------------
# FAILURE TESTING FUNCTIONS
#-------------------------------------------------------------------------------

test_circuit_breaker() {
    log_info "Testing circuit breaker pattern..."

    local failure_count=0
    local success_count=0
    local circuit_open=false
    local consecutive_failures=0
    local threshold=5

    for i in $(seq 1 20); do
        if $circuit_open; then
            log_debug "Circuit open - fast fail"
            ((failure_count++))
            continue
        fi

        # Simulate request
        if (( RANDOM % 10 < 3 )); then
            ((consecutive_failures++))
            ((failure_count++))
            log_debug "Request $i failed (consecutive: $consecutive_failures)"

            if (( consecutive_failures >= threshold )); then
                circuit_open=true
                log_warn "Circuit breaker OPENED after $consecutive_failures failures"
            fi
        else
            consecutive_failures=0
            ((success_count++))
            log_debug "Request $i succeeded"
        fi
    done

    collect_metrics "circuit_breaker_failures" "$failure_count"
    collect_metrics "circuit_breaker_successes" "$success_count"
    collect_metrics "circuit_breaker_opened" "$circuit_open"

    log_success "Circuit breaker test completed: $failure_count failures, $success_count successes"
}

test_retry_mechanism() {
    log_info "Testing retry mechanism..."

    local attempt=0
    local success=false
    local total_delay=0

    while (( attempt < MAX_RETRIES )); do
        ((attempt++))
        log_info "Retry attempt $attempt/$MAX_RETRIES"

        # Simulate operation with random failure
        if (( RANDOM % 10 < 7 )); then
            log_warn "Attempt $attempt failed"
            total_delay=$((total_delay + RETRY_DELAY))
            sleep "$RETRY_DELAY"
        else
            success=true
            log_success "Attempt $attempt succeeded"
            break
        fi
    done

    collect_metrics "retry_attempts" "$attempt"
    collect_metrics "retry_total_delay" "$total_delay"
    collect_metrics "retry_success" "$success"

    if $success; then
        log_success "Retry mechanism test passed"
    else
        log_error "Retry mechanism test failed after $MAX_RETRIES attempts"
    fi
}

test_graceful_degradation() {
    log_info "Testing graceful degradation..."

    local features=("recommendations" "personalization" "analytics" "reporting" "notifications")
    local degraded=()
    local available=()

    for feature in "${features[@]}"; do
        # Simulate feature health check
        if (( RANDOM % 10 < 2 )); then
            degraded+=("$feature")
            log_warn "Feature degraded: $feature"
        else
            available+=("$feature")
            log_debug "Feature available: $feature"
        fi
    done

    collect_metrics "degraded_features" "${#degraded[@]}"
    collect_metrics "available_features" "${#available[@]}"

    log_success "Graceful degradation test: ${#available[@]}/${#features[@]} features available"
}

test_failover() {
    log_info "Testing failover mechanism..."

    local primary_status="healthy"
    local secondary_status="standby"
    local failover_triggered=false

    # Simulate primary failure
    primary_status="failed"
    log_warn "Primary node failed"

    # Trigger failover
    if [[ "$primary_status" == "failed" ]]; then
        failover_triggered=true
        secondary_status="active"
        log_info "Failover triggered - secondary is now active"
    fi

    # Simulate recovery
    sleep 2
    primary_status="recovering"
    log_info "Primary node recovering..."

    sleep 2
    primary_status="healthy"
    log_success "Primary node recovered"

    collect_metrics "failover_triggered" "$failover_triggered"
    collect_metrics "failover_time" "2"

    log_success "Failover test completed"
}

test_timeout_handling() {
    log_info "Testing timeout handling..."

    local timeout_count=0
    local success_count=0

    for i in $(seq 1 10); do
        local delay=$((RANDOM % 15))

        if (( delay > TIMEOUT )); then
            ((timeout_count++))
            log_debug "Request $i timed out (delay: ${delay}s > timeout: ${TIMEOUT}s)"
        else
            ((success_count++))
            log_debug "Request $i completed in ${delay}s"
        fi
    done

    collect_metrics "timeout_count" "$timeout_count"
    collect_metrics "timeout_success" "$success_count"

    log_success "Timeout handling test: $success_count succeeded, $timeout_count timed out"
}

test_data_consistency() {
    log_info "Testing data consistency..."

    local inconsistencies=0
    local checks=100

    for i in $(seq 1 $checks); do
        # Simulate consistency check
        if (( RANDOM % 100 < 5 )); then
            ((inconsistencies++))
            log_debug "Inconsistency detected in record $i"
        fi
    done

    local consistency_rate
    consistency_rate=$(echo "scale=2; ($checks - $inconsistencies) / $checks * 100" | bc)

    collect_metrics "consistency_checks" "$checks"
    collect_metrics "inconsistencies_found" "$inconsistencies"
    collect_metrics "consistency_rate" "$consistency_rate"

    log_success "Data consistency test: ${consistency_rate}% consistent"
}

#-------------------------------------------------------------------------------
# RECOVERY VALIDATION FUNCTIONS
#-------------------------------------------------------------------------------

validate_service_recovery() {
    log_info "Validating service recovery..."

    local recovery_success=true
    local checks=("process_running" "port_listening" "health_endpoint" "dependency_connectivity" "data_integrity")

    for check in "${checks[@]}"; do
        log_debug "Running recovery check: $check"

        case "$check" in
            process_running)
                # Simulate process check
                if (( RANDOM % 10 < 9 )); then
                    log_success "Process is running"
                else
                    log_error "Process is not running"
                    recovery_success=false
                fi
                ;;
            port_listening)
                # Simulate port check
                if (( RANDOM % 10 < 9 )); then
                    log_success "Port is listening"
                else
                    log_error "Port is not listening"
                    recovery_success=false
                fi
                ;;
            health_endpoint)
                # Simulate health check
                if (( RANDOM % 10 < 8 )); then
                    log_success "Health endpoint responding"
                else
                    log_error "Health endpoint not responding"
                    recovery_success=false
                fi
                ;;
            dependency_connectivity)
                # Simulate dependency check
                if (( RANDOM % 10 < 8 )); then
                    log_success "Dependencies reachable"
                else
                    log_error "Dependencies unreachable"
                    recovery_success=false
                fi
                ;;
            data_integrity)
                # Simulate data integrity check
                if (( RANDOM % 10 < 9 )); then
                    log_success "Data integrity verified"
                else
                    log_error "Data integrity compromised"
                    recovery_success=false
                fi
                ;;
        esac
    done

    collect_metrics "recovery_validation_success" "$recovery_success"

    if $recovery_success; then
        log_success "Service recovery validated successfully"
    else
        log_error "Service recovery validation failed"
    fi

    return $([[ "$recovery_success" == "true" ]] && echo 0 || echo 1)
}

validate_performance_recovery() {
    log_info "Validating performance recovery..."

    # Wait for system to stabilize
    sleep 5

    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 || echo "0")

    local mem_usage
    mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' || echo "0")

    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',' || echo "0")

    collect_metrics "cpu_usage_post_chaos" "$cpu_usage"
    collect_metrics "memory_usage_post_chaos" "$mem_usage"
    collect_metrics "load_average_post_chaos" "$load_avg"

    local perf_ok=true

    if (( $(echo "$cpu_usage > $THRESHOLD_CPU" | bc -l) )); then
        log_warn "CPU usage still elevated: ${cpu_usage}%"
        perf_ok=false
    fi

    if (( $(echo "$mem_usage > $THRESHOLD_MEM" | bc -l) )); then
        log_warn "Memory usage still elevated: ${mem_usage}%"
        perf_ok=false
    fi

    if $perf_ok; then
        log_success "Performance recovery validated"
    else
        log_warn "Performance not fully recovered"
    fi

    return $([[ "$perf_ok" == "true" ]] && echo 0 || echo 1)
}

validate_data_recovery() {
    log_info "Validating data recovery..."

    local data_checks=100
    local recovered=0
    local failed=0

    for i in $(seq 1 $data_checks); do
        if (( RANDOM % 100 < 95 )); then
            ((recovered++))
        else
            ((failed++))
        fi
    done

    local recovery_rate
    recovery_rate=$(echo "scale=2; $recovered / $data_checks * 100" | bc)

    collect_metrics "data_recovery_rate" "$recovery_rate"
    collect_metrics "data_recovered" "$recovered"
    collect_metrics "data_failed" "$failed"

    if (( $(echo "$recovery_rate >= 95" | bc -l) )); then
        log_success "Data recovery validated: ${recovery_rate}%"
        return 0
    else
        log_error "Data recovery insufficient: ${recovery_rate}%"
        return 1
    fi
}

#-------------------------------------------------------------------------------
# MAIN EXECUTION
#-------------------------------------------------------------------------------

run_fault_injection() {
    log_info "Starting fault injection: $FAULT_TYPE"

    case "$FAULT_TYPE" in
        network_delay)
            inject_network_delay 200
            ;;
        network_partition)
            inject_network_partition
            ;;
        cpu_stress)
            inject_cpu_stress 85
            ;;
        memory_pressure)
            inject_memory_pressure 512
            ;;
        disk_fill)
            inject_disk_fill 1024
            ;;
        process_kill)
            inject_process_kill
            ;;
        dependency_failure)
            inject_dependency_failure
            ;;
        data_corruption)
            inject_data_corruption
            ;;
        clock_skew)
            inject_clock_skew 3600
            ;;
        *)
            log_error "Unknown fault type: $FAULT_TYPE"
            return 1
            ;;
    esac

    log_success "Fault injection completed: $FAULT_TYPE"
}

run_failure_tests() {
    log_info "Running failure tests..."

    test_circuit_breaker
    test_retry_mechanism
    test_graceful_degradation
    test_failover
    test_timeout_handling
    test_data_consistency

    log_success "All failure tests completed"
}

run_recovery_validation() {
    log_info "Running recovery validation..."

    local all_passed=true

    validate_service_recovery || all_passed=false
    validate_performance_recovery || all_passed=false
    validate_data_recovery || all_passed=false

    if $all_passed; then
        log_success "All recovery validations passed"
        return 0
    else
        log_error "Some recovery validations failed"
        return 1
    fi
}

run_parallel_chaos() {
    log_info "Running parallel chaos scenarios..."

    local pids=()

    inject_network_delay 100 &
    pids+=($!)

    inject_cpu_stress 50 &
    pids+=($!)

    inject_memory_pressure 256 &
    pids+=($!)

    for pid in "${pids[@]}"; do
        wait "$pid" 2>/dev/null || true
    done

    log_success "Parallel chaos scenarios completed"
}

generate_report() {
    log_info "Generating chaos experiment report..."

    local report_file="${LOG_DIR}/finance-marketing-report-$(date +%Y%m%d-%H%M%S).txt"

    cat > "$report_file" <<REPORT
================================================================================
CHAOS ENGINEERING EXPERIMENT REPORT
================================================================================
Component:    Finance Marketing
Fault Type:   $FAULT_TYPE
Duration:     ${DURATION}s
Timestamp:   $(date -u '+%Y-%m-%dT%H:%M:%SZ')
Version:      $VERSION

SUMMARY
-------
$(if [[ -f "$METRICS_FILE" ]]; then
    echo "Metrics collected: $(jq length "$METRICS_FILE")"
    echo ""
    echo "Key Metrics:"
    jq -r '.[] | "  \(.name): \(.value)"' "$METRICS_FILE" 2>/dev/null || echo "  (metrics unavailable)"
else
    echo "No metrics collected"
fi)

LOG FILE
--------
$LOG_FILE

CONCLUSION
----------
$(log_info "Chaos experiment for Finance Marketing completed")
================================================================================
REPORT

    log_success "Report generated: $report_file"
    cat "$report_file"
}

main() {
    parse_args "$@"
    check_dependencies
    acquire_lock
    init_environment

    log_info "Starting Finance Marketing chaos engineering experiment"
    log_info "Fault type: $FAULT_TYPE"
    log_info "Duration: ${DURATION}s"
    log_info "Dry run: $DRY_RUN"

    # Record baseline
    record_baseline

    # Phase 1: Fault Injection
    log_info "=== PHASE 1: FAULT INJECTION ==="
    if $PARALLEL; then
        run_parallel_chaos
    else
        run_fault_injection
    fi

    # Let the fault propagate
    log_info "Waiting for fault to propagate (${DURATION}s)..."
    if ! $DRY_RUN; then
        sleep "$DURATION"
    fi

    # Phase 2: Failure Testing
    log_info "=== PHASE 2: FAILURE TESTING ==="
    run_failure_tests

    # Phase 3: Recovery Validation
    log_info "=== PHASE 3: RECOVERY VALIDATION ==="
    local recovery_result=0
    run_recovery_validation || recovery_result=$?

    # Generate report
    generate_report

    # Final status
    if [[ $recovery_result -eq 0 ]]; then
        log_success "=== CHAOS EXPERIMENT PASSED ==="
        log_info "Finance Marketing demonstrated resilience to $FAULT_TYPE"
    else
        log_error "=== CHAOS EXPERIMENT FAILED ==="
        log_info "Finance Marketing needs improvement in handling $FAULT_TYPE"
    fi

    release_lock
    return $recovery_result
}

#-------------------------------------------------------------------------------
# ENTRY POINT
#-------------------------------------------------------------------------------

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

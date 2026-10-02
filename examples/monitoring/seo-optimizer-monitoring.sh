#!/usr/bin/env bash
# =============================================================================
# seo-optimizer-monitoring.sh
# SEO Optimizer - monitors search rankings, organic traffic, and technical SEO health
# =============================================================================
# Production-grade monitoring script with metrics collection, alerting,
# and dashboard setup for the seo-optimizer project.
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
PROJECT_NAME="seo-optimizer"
METRICS_DIR="${METRICS_DIR:-/var/lib/${PROJECT_NAME}/metrics}"
ALERTS_DIR="${ALERTS_DIR:-/var/lib/${PROJECT_NAME}/alerts}"
DASHBOARD_DIR="${DASHBOARD_DIR:-/var/lib/${PROJECT_NAME}/dashboard}"
LOG_DIR="${LOG_DIR:-/var/log/${PROJECT_NAME}/monitoring}"
CONFIG_FILE="${CONFIG_FILE:-/etc/${PROJECT_NAME}/monitoring.conf}"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"
ALERT_EMAIL="${ALERT_EMAIL:-}"
PROMETHEUS_PUSHGATEWAY="${PROMETHEUS_PUSHGATEWAY:-}"
DATADOG_API_KEY="${DATADOG_API_KEY:-}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
PAGERDUTY_KEY="${PAGERDUTY_KEY:-}"
COLLECTION_INTERVAL="${COLLECTION_INTERVAL:-60}"
ALERT_COOLDOWN="${ALERT_COOLDOWN:-300}"
RETENTION_DAYS="${RETENTION_DAYS:-90}"
VERBOSITY="${VERBOSITY:-1}"

# -----------------------------------------------------------------------------
# Color codes for terminal output
# -----------------------------------------------------------------------------
RED="\033[0;31m"
YELLOW="\033[1;33m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# -----------------------------------------------------------------------------
# Logging functions
# -----------------------------------------------------------------------------
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "[${timestamp}] [${level}] ${message}" >> "${LOG_DIR}/monitoring.log" 2>/dev/null || true
    if [[ "${VERBOSITY}" -ge 1 ]]; then
        case "${level}" in
            ERROR)   echo -e "${RED}[${timestamp}] [${level}] ${message}${NC}" >&2 ;;
            WARNING) echo -e "${YELLOW}[${timestamp}] [${level}] ${message}${NC}" >&2 ;;
            INFO)    echo -e "${GREEN}[${timestamp}] [${level}] ${message}${NC}" ;;
            DEBUG)   [[ "${VERBOSITY}" -ge 2 ]] && echo -e "${BLUE}[${timestamp}] [${level}] ${message}${NC}" ;;
        esac
    fi
}

log_info()  { log "INFO" "$@"; }
log_warn()  { log "WARNING" "$@"; }
log_error() { log "ERROR" "$@"; }
log_debug() { log "DEBUG" "$@"; }

# -----------------------------------------------------------------------------
# Error handling
# -----------------------------------------------------------------------------
error_exit() {
    log_error "$1"
    exit "${2:-1}"
}

cleanup() {
    log_debug "Cleaning up temporary files..."
    rm -f "${METRICS_DIR}/.tmp_"* 2>/dev/null || true
}

trap cleanup EXIT
trap "error_exit \"Script interrupted\" 130" INT TERM

# -----------------------------------------------------------------------------
# Initialization
# -----------------------------------------------------------------------------
init_directories() {
    local dirs=("${METRICS_DIR}" "${ALERTS_DIR}" "${DASHBOARD_DIR}" "${LOG_DIR}")
    for dir in "${dirs[@]}"; do
        if [[ ! -d "${dir}" ]]; then
            mkdir -p "${dir}" || error_exit "Failed to create directory: ${dir}"
            log_info "Created directory: ${dir}"
        fi
    done
}

load_config() {
    if [[ -f "${CONFIG_FILE}" ]]; then
        # shellcheck source=/dev/null
        source "${CONFIG_FILE}"
        log_info "Loaded configuration from ${CONFIG_FILE}"
    else
        log_warn "Configuration file not found: ${CONFIG_FILE}, using defaults"
    fi
}

# -----------------------------------------------------------------------------
# Metrics Collection
# -----------------------------------------------------------------------------
collect_metrics() {
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    local metrics_file="${METRICS_DIR}/metrics_$(date -u +%Y%m%d_%H%M%S).json"

    log_info "Starting metrics collection cycle..."

    # Initialize metrics JSON
    cat > "${metrics_file}" <<METRICS_EOF
{
    "project": "${PROJECT_NAME}",
    "timestamp": "${timestamp}",
    "metrics": {
        "__PLACEHOLDER__": true
    }
}
METRICS_EOF

    # Collect each metric
    collect_organic_traffic "${metrics_file}"
    collect_keyword_rankings "${metrics_file}"
    collect_backlink_count "${metrics_file}"
    collect_page_speed "${metrics_file}"
    collect_crawl_errors "${metrics_file}"
    collect_indexing_rate "${metrics_file}"
    collect_domain_authority "${metrics_file}"
    collect_click_through_rate "${metrics_file}"

    # Remove placeholder and close JSON
    sed -i.bak "s/\"__PLACEHOLDER__\": true//" "${metrics_file}" && rm -f "${metrics_file}.bak"

    log_info "Metrics collection complete: ${metrics_file}"
    echo "${metrics_file}"
}

collect_organic_traffic() {
    local metrics_file="$1"
    local value
    value=$(get_organic_traffic_value)
    if [[ -n "${value}" ]]; then
        local entry="\"organic_traffic\": {\"value\": \"${value}\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
        # Insert into JSON (before closing brace)
        sed -i.bak "s/}$/${entry},}/" "${metrics_file}" && rm -f "${metrics_file}.bak"
    else
        log_warn "Failed to collect metric: organic_traffic"
    fi
}

collect_keyword_rankings() {
    local metrics_file="$1"
    local value
    value=$(get_keyword_rankings_value)
    if [[ -n "${value}" ]]; then
        local entry="\"keyword_rankings\": {\"value\": \"${value}\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
        # Insert into JSON (before closing brace)
        sed -i.bak "s/}$/${entry},}/" "${metrics_file}" && rm -f "${metrics_file}.bak"
    else
        log_warn "Failed to collect metric: keyword_rankings"
    fi
}

collect_backlink_count() {
    local metrics_file="$1"
    local value
    value=$(get_backlink_count_value)
    if [[ -n "${value}" ]]; then
        local entry="\"backlink_count\": {\"value\": \"${value}\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
        # Insert into JSON (before closing brace)
        sed -i.bak "s/}$/${entry},}/" "${metrics_file}" && rm -f "${metrics_file}.bak"
    else
        log_warn "Failed to collect metric: backlink_count"
    fi
}

collect_page_speed() {
    local metrics_file="$1"
    local value
    value=$(get_page_speed_value)
    if [[ -n "${value}" ]]; then
        local entry="\"page_speed\": {\"value\": \"${value}\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
        # Insert into JSON (before closing brace)
        sed -i.bak "s/}$/${entry},}/" "${metrics_file}" && rm -f "${metrics_file}.bak"
    else
        log_warn "Failed to collect metric: page_speed"
    fi
}

collect_crawl_errors() {
    local metrics_file="$1"
    local value
    value=$(get_crawl_errors_value)
    if [[ -n "${value}" ]]; then
        local entry="\"crawl_errors\": {\"value\": \"${value}\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
        # Insert into JSON (before closing brace)
        sed -i.bak "s/}$/${entry},}/" "${metrics_file}" && rm -f "${metrics_file}.bak"
    else
        log_warn "Failed to collect metric: crawl_errors"
    fi
}

collect_indexing_rate() {
    local metrics_file="$1"
    local value
    value=$(get_indexing_rate_value)
    if [[ -n "${value}" ]]; then
        local entry="\"indexing_rate\": {\"value\": \"${value}\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
        # Insert into JSON (before closing brace)
        sed -i.bak "s/}$/${entry},}/" "${metrics_file}" && rm -f "${metrics_file}.bak"
    else
        log_warn "Failed to collect metric: indexing_rate"
    fi
}

collect_domain_authority() {
    local metrics_file="$1"
    local value
    value=$(get_domain_authority_value)
    if [[ -n "${value}" ]]; then
        local entry="\"domain_authority\": {\"value\": \"${value}\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
        # Insert into JSON (before closing brace)
        sed -i.bak "s/}$/${entry},}/" "${metrics_file}" && rm -f "${metrics_file}.bak"
    else
        log_warn "Failed to collect metric: domain_authority"
    fi
}

collect_click_through_rate() {
    local metrics_file="$1"
    local value
    value=$(get_click_through_rate_value)
    if [[ -n "${value}" ]]; then
        local entry="\"click_through_rate\": {\"value\": \"${value}\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
        # Insert into JSON (before closing brace)
        sed -i.bak "s/}$/${entry},}/" "${metrics_file}" && rm -f "${metrics_file}.bak"
    else
        log_warn "Failed to collect metric: click_through_rate"
    fi
}



get_organic_traffic_value() {
    # TODO: Implement actual organic_traffic collection logic
    # This is a placeholder that returns a simulated value
    # Replace with actual API calls, database queries, or log parsing
    echo "0"
}

get_keyword_rankings_value() {
    # TODO: Implement actual keyword_rankings collection logic
    # This is a placeholder that returns a simulated value
    # Replace with actual API calls, database queries, or log parsing
    echo "0"
}

get_backlink_count_value() {
    # TODO: Implement actual backlink_count collection logic
    # This is a placeholder that returns a simulated value
    # Replace with actual API calls, database queries, or log parsing
    echo "0"
}

get_page_speed_value() {
    # TODO: Implement actual page_speed collection logic
    # This is a placeholder that returns a simulated value
    # Replace with actual API calls, database queries, or log parsing
    echo "0"
}

get_crawl_errors_value() {
    # TODO: Implement actual crawl_errors collection logic
    # This is a placeholder that returns a simulated value
    # Replace with actual API calls, database queries, or log parsing
    echo "0"
}

get_indexing_rate_value() {
    # TODO: Implement actual indexing_rate collection logic
    # This is a placeholder that returns a simulated value
    # Replace with actual API calls, database queries, or log parsing
    echo "0"
}

get_domain_authority_value() {
    # TODO: Implement actual domain_authority collection logic
    # This is a placeholder that returns a simulated value
    # Replace with actual API calls, database queries, or log parsing
    echo "0"
}

get_click_through_rate_value() {
    # TODO: Implement actual click_through_rate collection logic
    # This is a placeholder that returns a simulated value
    # Replace with actual API calls, database queries, or log parsing
    echo "0"
}



# -----------------------------------------------------------------------------
# Alerting
# -----------------------------------------------------------------------------
check_alerts() {
    local metrics_file="$1"
    local alert_triggered=false
    local alert_timestamp
    alert_timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    log_info "Checking alert conditions..."

    # Alert: Organic traffic dropped below 1000 daily visits
    check_single_alert "${metrics_file}" "organic_traffic" "<" "1000" "warning" "Organic traffic dropped below 1000 daily visits" "${alert_timestamp}"
    if [[ $? -eq 0 ]]; then
        alert_triggered=true
    fi

    # Alert: Crawl errors above 50 - technical SEO issue
    check_single_alert "${metrics_file}" "crawl_errors" ">" "50" "critical" "Crawl errors above 50 - technical SEO issue" "${alert_timestamp}"
    if [[ $? -eq 0 ]]; then
        alert_triggered=true
    fi

    # Alert: Page speed above 3 seconds - Core Web Vitals issue
    check_single_alert "${metrics_file}" "page_speed" ">" "3.0" "warning" "Page speed above 3 seconds - Core Web Vitals issue" "${alert_timestamp}"
    if [[ $? -eq 0 ]]; then
        alert_triggered=true
    fi

    # Alert: Indexing rate below 80% - pages not being indexed
    check_single_alert "${metrics_file}" "indexing_rate" "<" "0.8" "critical" "Indexing rate below 80% - pages not being indexed" "${alert_timestamp}"
    if [[ $? -eq 0 ]]; then
        alert_triggered=true
    fi



    if [[ "${alert_triggered}" == "true" ]]; then
        log_warn "One or more alerts triggered during this cycle"
    fi
}

check_single_alert() {
    local metrics_file="$1"
    local metric_name="$2"
    local condition="$3"
    local threshold="$4"
    local severity="$5"
    local message="$6"
    local timestamp="$7"

    local value
    value=$(jq -r ".metrics.${metric_name}.value // \"null\"" "${metrics_file}" 2>/dev/null || echo "null")

    if [[ "${value}" == "null" ]]; then
        log_warn "Metric ${metric_name} not found in metrics file"
        return 1
    fi

    local alert_file="${ALERTS_DIR}/alert_${metric_name}_$(date -u +%Y%m%d_%H%M%S).json"
    local cooldown_file="${ALERTS_DIR}/.cooldown_${metric_name}"

    # Check cooldown
    if [[ -f "${cooldown_file}" ]]; then
        local last_alert
        last_alert=$(cat "${cooldown_file}")
        local now
        now=$(date +%s)
        if (( now - last_alert < ALERT_COOLDOWN )); then
            log_debug "Alert for ${metric_name} is in cooldown period"
            return 1
        fi
    fi

    # Evaluate condition
    local triggered=false
    case "${condition}" in
        "<")  if (( $(echo "${value} < ${threshold}" | bc -l) )); then triggered=true ;;
        ">")  if (( $(echo "${value} > ${threshold}" | bc -l) )); then triggered=true ;;
        "==") if (( $(echo "${value} == ${threshold}" | bc -l) )); then triggered=true ;;
        "!=") if (( $(echo "${value} != ${threshold}" | bc -l) )); then triggered=true ;;
        "<=") if (( $(echo "${value} <= ${threshold}" | bc -l) )); then triggered=true ;;
        ">=") if (( $(echo "${value} >= ${threshold}" | bc -l) )); then triggered=true ;;
        *)   log_error "Unknown condition: ${condition}"; return 1 ;;
    esac

    if [[ "${triggered}" == "true" ]]; then
        log_warn "ALERT [${severity}]: ${message} (value=${value}, threshold=${threshold})"

        # Write alert record
        cat > "${alert_file}" <<ALERT_EOF
{
    "project": "${PROJECT_NAME}",
    "timestamp": "${timestamp}",
    "metric": "${metric_name}",
    "value": "${value}",
    "condition": "${condition}",
    "threshold": "${threshold}",
    "severity": "${severity}",
    "message": "${message}"
}
ALERT_EOF

        # Update cooldown
        date +%s > "${cooldown_file}"

        # Send notifications
        send_notification "${severity}" "${message}" "${metric_name}" "${value}" "${threshold}"

        return 0
    fi

    return 1
}

send_notification() {
    local severity="$1"
    local message="$2"
    local metric="$3"
    local value="$4"
    local threshold="$5"

    log_info "Sending notification: [${severity}] ${message}"

    # Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL}" ]]; then
        send_slack_notification "${severity}" "${message}" "${metric}" "${value}" "${threshold}"
    fi

    # Email notification
    if [[ -n "${ALERT_EMAIL}" ]]; then
        send_email_notification "${severity}" "${message}" "${metric}" "${value}" "${threshold}"
    fi

    # PagerDuty notification for critical alerts
    if [[ "${severity}" == "critical" && -n "${PAGERDUTY_KEY}" ]]; then
        send_pagerduty_notification "${severity}" "${message}" "${metric}" "${value}" "${threshold}"
    fi

    # Generic webhook
    if [[ -n "${ALERT_WEBHOOK}" ]]; then
        send_webhook_notification "${severity}" "${message}" "${metric}" "${value}" "${threshold}"
    fi
}

send_slack_notification() {
    local severity="$1"
    local message="$2"
    local metric="$3"
    local value="$4"
    local threshold="$5"

    local color="danger"
    case "${severity}" in
        critical) color="danger" ;;
        warning)  color="warning" ;;
        info)     color="good" ;;
    esac

    local payload
    payload=$(cat <<PAYLOAD_EOF
{
    "attachments": [{
        "color": "${color}",
        "title": "Monitoring Alert - ${PROJECT_NAME}",
        "fields": [
            {"title": "Severity", "value": "${severity}", "short": true},
            {"title": "Metric", "value": "${metric}", "short": true},
            {"title": "Value", "value": "${value}", "short": true},
            {"title": "Threshold", "value": "${threshold}", "short": true},
            {"title": "Message", "value": "${message}", "short": false}
        ],
        "ts": $(date +%s)
    }]
}
PAYLOAD_EOF
)

    curl -s -X POST -H "Content-Type: application/json" \
         -d "${payload}" "${SLACK_WEBHOOK_URL}" > /dev/null 2>&1 || \
        log_warn "Failed to send Slack notification"
}

send_email_notification() {
    local severity="$1"
    local message="$2"
    local metric="$3"
    local value="$4"
    local threshold="$5"

    local subject="[${severity}] ${PROJECT_NAME} Alert: ${metric}"
    local body
    body=$(cat <<BODY_EOF
Monitoring Alert for ${PROJECT_NAME}

Severity: ${severity}
Metric: ${metric}
Value: ${value}
Threshold: ${threshold}
Message: ${message}
Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
BODY_EOF
)

    echo "${body}" | mail -s "${subject}" "${ALERT_EMAIL}" 2>/dev/null || \
        log_warn "Failed to send email notification"
}

send_pagerduty_notification() {
    local severity="$1"
    local message="$2"
    local metric="$3"
    local value="$4"
    local threshold="$5"

    local payload
    payload=$(cat <<PAYLOAD_EOF
{
    "routing_key": "${PAGERDUTY_KEY}",
    "event_action": "trigger",
    "payload": {
        "summary": "${message}",
        "severity": "critical",
        "source": "${PROJECT_NAME}",
        "custom_details": {
            "metric": "${metric}",
            "value": "${value}",
            "threshold": "${threshold}"
        }
    }
}
PAYLOAD_EOF
)

    curl -s -X POST -H "Content-Type: application/json" \
         -d "${payload}" "https://events.pagerduty.com/v2/enqueue" > /dev/null 2>&1 || \
        log_warn "Failed to send PagerDuty notification"
}

send_webhook_notification() {
    local severity="$1"
    local message="$2"
    local metric="$3"
    local value="$4"
    local threshold="$5"

    local payload
    payload=$(cat <<PAYLOAD_EOF
{
    "project": "${PROJECT_NAME}",
    "severity": "${severity}",
    "metric": "${metric}",
    "value": "${value}",
    "threshold": "${threshold}",
    "message": "${message}",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
PAYLOAD_EOF
)

    curl -s -X POST -H "Content-Type: application/json" \
         -d "${payload}" "${ALERT_WEBHOOK}" > /dev/null 2>&1 || \
        log_warn "Failed to send webhook notification"
}

# -----------------------------------------------------------------------------
# Dashboard Setup
# -----------------------------------------------------------------------------
setup_dashboard() {
    log_info "Setting up dashboard..."

    # Generate Grafana dashboard JSON
    generate_grafana_dashboard

    # Generate HTML dashboard
    generate_html_dashboard

    # Setup Prometheus metrics endpoint
    setup_prometheus_endpoint

    log_info "Dashboard setup complete"
}

generate_grafana_dashboard() {
    local dashboard_file="${DASHBOARD_DIR}/grafana_dashboard.json"

    log_info "Generating Grafana dashboard: ${dashboard_file}"

    cat > "${dashboard_file}" <<GRAFANA_EOF
{
    "dashboard": {
        "title": "${PROJECT_NAME} Monitoring Dashboard",
        "uid": "${PROJECT_NAME}-monitoring",
        "timezone": "UTC",
        "refresh": "30s",
        "panels": [
            __PANELS_PLACEHOLDER__
        ],
        "time": {
            "from": "now-6h",
            "to": "now"
        },
        "schemaVersion": 39,
        "version": 1
    },
    "overwrite": true
}
GRAFANA_EOF

    # Generate panel definitions
    local panels=""
    panels+='{"title": "Ranking Tracker", "type": "timeseries", "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}, "targets": [{"expr": "{project=\"seo-optimizer\"}", "legendFormat": "Ranking Tracker"}]},'
    panels+='{"title": "Organic Traffic", "type": "timeseries", "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}, "targets": [{"expr": "{project=\"seo-optimizer\"}", "legendFormat": "Organic Traffic"}]},'
    panels+='{"title": "Technical SEO Health", "type": "timeseries", "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}, "targets": [{"expr": "{project=\"seo-optimizer\"}", "legendFormat": "Technical SEO Health"}]},'
    panels+='{"title": "Backlink Profile", "type": "timeseries", "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}, "targets": [{"expr": "{project=\"seo-optimizer\"}", "legendFormat": "Backlink Profile"}]},'
    panels+='{"title": "Page Speed Metrics", "type": "timeseries", "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}, "targets": [{"expr": "{project=\"seo-optimizer\"}", "legendFormat": "Page Speed Metrics"}]}'

    # Insert panels into dashboard JSON
    sed -i.bak "s/__PANELS_PLACEHOLDER__/${panels}/" "${dashboard_file}" && rm -f "${dashboard_file}.bak"

    log_info "Grafana dashboard generated: ${dashboard_file}"
}

generate_html_dashboard() {
    local html_file="${DASHBOARD_DIR}/index.html"

    log_info "Generating HTML dashboard: ${html_file}"

    cat > "${html_file}" <<HTML_EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${PROJECT_NAME} Monitoring Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; }
        .header { background: #16213e; padding: 1rem 2rem; border-bottom: 2px solid #0f3460; }
        .header h1 { font-size: 1.5rem; color: #e94560; }
        .header .status { display: inline-block; margin-left: 1rem; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem; }
        .status.ok { background: #00b894; color: #fff; }
        .status.warning { background: #fdcb6e; color: #2d3436; }
        .status.critical { background: #e94560; color: #fff; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; padding: 1rem; }
        .card { background: #16213e; border-radius: 8px; padding: 1rem; border: 1px solid #0f3460; }
        .card h3 { color: #e94560; margin-bottom: 0.5rem; font-size: 1rem; }
        .metric { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #0f3460; }
        .metric:last-child { border-bottom: none; }
        .metric .label { color: #a0a0a0; }
        .metric .value { font-weight: bold; }
        .metric .value.ok { color: #00b894; }
        .metric .value.warning { color: #fdcb6e; }
        .metric .value.critical { color: #e94560; }
        .footer { text-align: center; padding: 1rem; color: #666; font-size: 0.875rem; }
        .refresh-info { text-align: center; padding: 0.5rem; color: #888; font-size: 0.75rem; }
    </style>
</head>
<body>
    <div class="header">
        <h1>${PROJECT_NAME} Monitoring Dashboard</h1>
        <span class="status ok" id="overall-status">HEALTHY</span>
    </div>
    <div class="refresh-info">Last refreshed: <span id="last-refresh">Never</span> | Auto-refresh: 30s</div>
    <div class="grid" id="metrics-grid">
        <!-- Metrics cards will be populated by JavaScript -->
    </div>
    <div class="footer">
        <p>${PROJECT_NAME} Monitoring System &copy; $(date +%Y)</p>
    </div>
    <script>
        const METRICS_API = '/api/metrics';
        const REFRESH_INTERVAL = 30000;

        async function fetchMetrics() {
            try {
                const response = await fetch(METRICS_API);
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to fetch metrics:', error);
                document.getElementById('overall-status').className = 'status critical';
                document.getElementById('overall-status').textContent = 'ERROR';
            }
        }

        function updateDashboard(data) {
            const grid = document.getElementById('metrics-grid');
            grid.innerHTML = '';

            if (!data.metrics) {
                grid.innerHTML = '<div class="card"><p>No metrics available</p></div>';
                return;
            }

            for (const [name, metric] of Object.entries(data.metrics)) {
                const card = document.createElement('div');
                card.className = 'card';

                const statusClass = metric.value < metric.threshold ? 'critical' :
                                  metric.value < metric.threshold * 1.2 ? 'warning' : 'ok';

                card.innerHTML = '<h3>' + name + '</h3>' +
                    '<div class="metric">' +
                        '<span class="label">Value</span>' +
                        '<span class="value ' + statusClass + '">' + metric.value + '</span>' +
                    '</div>' +
                    '<div class="metric">' +
                        '<span class="label">Threshold</span>' +
                        '<span class="value">' + (metric.threshold || 'N/A') + '</span>' +
                    '</div>' +
                    '<div class="metric">' +
                        '<span class="label">Last Updated</span>' +
                        '<span class="value">' + (metric.timestamp || 'N/A') + '</span>' +
                    '</div>';

                grid.appendChild(card);
            }

            document.getElementById('last-refresh').textContent = new Date().toLocaleString();
        }

        // Initial fetch and periodic refresh
        fetchMetrics();
        setInterval(fetchMetrics, REFRESH_INTERVAL);
    </script>
</body>
</html>
HTML_EOF

    log_info "HTML dashboard generated: ${html_file}"
}

setup_prometheus_endpoint() {
    local prometheus_file="${DASHBOARD_DIR}/prometheus_metrics.txt"

    log_info "Setting up Prometheus metrics endpoint..."

    cat > "${prometheus_file}" <<PROMETHEUS_EOF
# HELP ${PROJECT_NAME}_info Project information
# TYPE ${PROJECT_NAME}_info gauge
${PROJECT_NAME}_info{project="${PROJECT_NAME}"} 1

# HELP ${PROJECT_NAME}_metrics_collected_total Total metrics collected
# TYPE ${PROJECT_NAME}_metrics_collected_total counter
${PROJECT_NAME}_metrics_collected_total 0

# HELP ${PROJECT_NAME}_alerts_triggered_total Total alerts triggered
# TYPE ${PROJECT_NAME}_alerts_triggered_total counter
${PROJECT_NAME}_alerts_triggered_total 0

# HELP ${PROJECT_NAME}_collection_duration_seconds Metrics collection duration
# TYPE ${PROJECT_NAME}_collection_duration_seconds gauge
${PROJECT_NAME}_collection_duration_seconds 0
PROMETHEUS_EOF

    log_info "Prometheus metrics endpoint configured: ${prometheus_file}"
}

# -----------------------------------------------------------------------------
# Metrics Retention
# -----------------------------------------------------------------------------
cleanup_old_metrics() {
    log_info "Cleaning up metrics older than ${RETENTION_DAYS} days..."

    find "${METRICS_DIR}" -name "metrics_*.json" -type f -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true
    find "${ALERTS_DIR}" -name "alert_*.json" -type f -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true

    log_info "Old metrics cleanup complete"
}

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
health_check() {
    log_info "Performing health check..."

    local healthy=true

    # Check required directories
    for dir in "${METRICS_DIR}" "${ALERTS_DIR}" "${DASHBOARD_DIR}" "${LOG_DIR}"; do
        if [[ ! -d "${dir}" ]]; then
            log_error "Directory missing: ${dir}"
            healthy=false
        fi
    done

    # Check required tools
    for tool in jq curl bc; do
        if ! command -v "${tool}" &> /dev/null; then
            log_warn "Optional tool not found: ${tool}"
        fi
    done

    # Check disk space
    local disk_usage
    disk_usage=$(df -h "${METRICS_DIR}" | awk 'NR==2 {print $5}' | tr -d '%')
    if [[ "${disk_usage}" -gt 90 ]]; then
        log_warn "Disk usage above 90%: ${disk_usage}%"
        healthy=false
    fi

    if [[ "${healthy}" == "true" ]]; then
        log_info "Health check passed"
        return 0
    else
        log_error "Health check failed"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Push Metrics to External Systems
# -----------------------------------------------------------------------------
push_metrics() {
    local metrics_file="$1"

    # Push to Prometheus Pushgateway
    if [[ -n "${PROMETHEUS_PUSHGATEWAY}" ]]; then
        push_to_prometheus "${metrics_file}"
    fi

    # Push to Datadog
    if [[ -n "${DATADOG_API_KEY}" ]]; then
        push_to_datadog "${metrics_file}"
    fi
}

push_to_prometheus() {
    local metrics_file="$1"

    log_debug "Pushing metrics to Prometheus Pushgateway..."

    local prometheus_data=""
    prometheus_data=$(jq -r \
        ".metrics | to_entries | map("
            "# HELP \(.key) \(.key) metric for ${PROJECT_NAME}",
            "# TYPE \(.key) gauge",
            "${PROJECT_NAME}_\\(.key){project=\\"${PROJECT_NAME}\\"} \\(.value.value)"
        ) | .[]" "${metrics_file}" 2>/dev/null) || true

    if [[ -n "${prometheus_data}" ]]; then
        echo "${prometheus_data}" | curl -s -X POST \
             --data-binary @- \
             "${PROMETHEUS_PUSHGATEWAY}/metrics/job/${PROJECT_NAME}/instance/localhost" \
             > /dev/null 2>&1 || \
            log_warn "Failed to push metrics to Prometheus"
    fi
}

push_to_datadog() {
    local metrics_file="$1"

    log_debug "Pushing metrics to Datadog..."

    local series
    series=$(jq -r \
        ".metrics | to_entries | map({
            "metric": "${PROJECT_NAME}.\(.key)",
            "points": [[$(date +%s), (.value.value | tonumber)]],
            "type": "gauge",
            "host": "localhost",
            "tags": ["project:${PROJECT_NAME}"]
        }) | .[]" "${metrics_file}" 2>/dev/null) || true

    if [[ -n "${series}" ]]; then
        local payload
        payload="{\"series\": ${series}}"
        curl -s -X POST -H "Content-Type: application/json" \
             -H "DD-API-KEY: ${DATADOG_API_KEY}" \
             -d "${payload}" "https://api.datadoghq.com/api/v1/series" \
             > /dev/null 2>&1 || \
            log_warn "Failed to push metrics to Datadog"
    fi
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
show_usage() {
    cat <<USAGE_EOF
Usage: $0 [OPTIONS] COMMAND

Commands:
  collect    Collect metrics
  alerts     Check alert conditions
  dashboard  Setup monitoring dashboard
  push       Push metrics to external systems
  cleanup    Clean up old metrics
  health     Perform health check
  run        Full monitoring cycle (collect + alerts + push)
  daemon     Run as daemon with periodic collection

Options:
  -c, --config FILE    Configuration file path
  -v, --verbose        Verbose output
  -q, --quiet          Quiet output
  -h, --help           Show this help message

Environment Variables:
  METRICS_DIR              Metrics storage directory
  ALERTS_DIR               Alerts storage directory
  DASHBOARD_DIR            Dashboard output directory
  LOG_DIR                  Log directory
  ALERT_WEBHOOK            Generic webhook URL for alerts
  ALERT_EMAIL             Email address for alerts
  SLACK_WEBHOOK_URL        Slack webhook URL
  PAGERDUTY_KEY            PagerDuty integration key
  PROMETHEUS_PUSHGATEWAY   Prometheus Pushgateway URL
  DATADOG_API_KEY          Datadog API key
  COLLECTION_INTERVAL      Metrics collection interval in seconds
  ALERT_COOLDOWN           Alert cooldown period in seconds
  RETENTION_DAYS           Metrics retention period in days

Examples:
  $0 collect
  $0 run
  $0 daemon
  $0 dashboard
  $0 health
USAGE_EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSITY=2
                shift
                ;;
            -q|--quiet)
                VERBOSITY=0
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            collect|alerts|dashboard|push|cleanup|health|run|daemon)
                COMMAND="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

run_daemon() {
    log_info "Starting ${PROJECT_NAME} monitoring daemon..."
    log_info "Collection interval: ${COLLECTION_INTERVAL}s"

    while true; do
        log_debug "Starting monitoring cycle..."

        local metrics_file
        metrics_file=$(collect_metrics)

        if [[ -n "${metrics_file}" && -f "${metrics_file}" ]]; then
            check_alerts "${metrics_file}"
            push_metrics "${metrics_file}"
        fi

        # Cleanup old metrics every 24 hours
        if [[ $(date +%H%M) == "0000" ]]; then
            cleanup_old_metrics
        fi

        log_debug "Sleeping for ${COLLECTION_INTERVAL} seconds..."
        sleep "${COLLECTION_INTERVAL}"
    done
}

main() {
    parse_args "$@"

    # Initialize
    init_directories
    load_config

    # Execute command
    case "${COMMAND:-run}" in
        collect)
            collect_metrics
            ;;
        alerts)
            local latest_metrics
            latest_metrics=$(ls -t "${METRICS_DIR}"/metrics_*.json 2>/dev/null | head -1)
            if [[ -n "${latest_metrics}" ]]; then
                check_alerts "${latest_metrics}"
            else
                log_error "No metrics files found"
                exit 1
            fi
            ;;
        dashboard)
            setup_dashboard
            ;;
        push)
            local latest_metrics
            latest_metrics=$(ls -t "${METRICS_DIR}"/metrics_*.json 2>/dev/null | head -1)
            if [[ -n "${latest_metrics}" ]]; then
                push_metrics "${latest_metrics}"
            else
                log_error "No metrics files found"
                exit 1
            fi
            ;;
        cleanup)
            cleanup_old_metrics
            ;;
        health)
            health_check
            ;;
        run)
            local metrics_file
            metrics_file=$(collect_metrics)
            if [[ -n "${metrics_file}" && -f "${metrics_file}" ]]; then
                check_alerts "${metrics_file}"
                push_metrics "${metrics_file}"
            fi
            ;;
        daemon)
            run_daemon
            ;;
        *)
            log_error "Unknown command: ${COMMAND}"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"

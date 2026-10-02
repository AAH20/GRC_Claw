#!/usr/bin/env bash
# =============================================================================
# Video Marketing CLI Example
# =============================================================================
# Production-grade Bash CLI demonstrating authentication, CRUD operations,
# error handling, and best practices for the Video Marketing API.
#
# Usage:
#   ./video-marketing-cli.sh <command> [options]
#
# Commands:
#   auth              Authenticate and obtain access token
#   list              List all video-campaigns
#   get               Get a specific video-campaign by ID
#   create            Create a new video-campaign
#   update            Update an existing video-campaign
#   delete            Delete a video-campaign
#   search            Search video-campaigns with filters
#   batch             Batch operations (create/update multiple)
#   health            Check API health status
#
# Environment Variables:
#   GRC_API_KEY       API key for authentication (required)
#   GRC_API_SECRET    API secret for authentication (required)
#   GRC_API_BASE_URL  API base URL (default: https://api.grcclaw.com/v1)
#   GRC_OUTPUT_FORMAT Output format: json|table (default: json)
#   GRC_DEBUG         Enable debug mode: true|false (default: false)
#   GRC_RETRY_COUNT   Number of retries for failed requests (default: 3)
#   GRC_TIMEOUT       Request timeout in seconds (default: 30)
#
# Examples:
#   export GRC_API_KEY="your-api-key"
#   export GRC_API_SECRET="your-api-secret"
#   ./video-marketing-cli.sh auth
#   ./video-marketing-cli.sh list --limit 20
#   ./video-marketing-cli.sh get --id "12345"
#   ./video-marketing-cli.sh create --name "Q4 Campaign" --budget 5000
#   ./video-marketing-cli.sh update --id "12345" --status active
#   ./video-marketing-cli.sh delete --id "12345"
#   ./video-marketing-cli.sh search --query "enterprise" --sort-by created_at
#   ./video-marketing-cli.sh batch --file ./batch_data.json
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# --- Constants ---------------------------------------------------------------
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VERSION="1.0.0"
readonly DEFAULT_API_BASE="https://api.grcclaw.com/v1"
readonly DEFAULT_TIMEOUT=30
readonly DEFAULT_RETRY_COUNT=3
readonly DEFAULT_OUTPUT_FORMAT="json"
readonly TOKEN_CACHE_FILE="${TMPDIR:-/tmp}/${SCRIPT_NAME%.sh}.token"
readonly LOG_FILE="${TMPDIR:-/tmp}/${SCRIPT_NAME%.sh}.log"

# --- Color Codes (disabled if not TTY) ---------------------------------------
if [[ -t 1 ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly CYAN='\033[0;36m'
    readonly NC='\033[0m' # No Color
    readonly BOLD='\033[1m'
else
    readonly RED=''
    readonly GREEN=''
    readonly YELLOW=''
    readonly BLUE=''
    readonly CYAN=''
    readonly NC=''
    readonly BOLD=''
fi

# --- Logging -----------------------------------------------------------------
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"

    case "$level" in
        ERROR)   echo -e "${RED}[ERROR]${NC} $message" >&2 ;;
        WARN)    echo -e "${YELLOW}[WARN]${NC}  $message" >&2 ;;
        INFO)    echo -e "${GREEN}[INFO]${NC}  $message" ;;
        DEBUG)   [[ "${GRC_DEBUG:-false}" == "true" ]] && echo -e "${CYAN}[DEBUG]${NC} $message" ;;
    esac
}

# --- Cleanup -----------------------------------------------------------------
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log ERROR "Script exited with code $exit_code"
    fi
    # Remove token cache on exit if it's expired
    if [[ -f "$TOKEN_CACHE_FILE" ]]; then
        local token_expiry
        token_expiry="$(cat "${TOKEN_CACHE_FILE}.expiry" 2>/dev/null || echo 0)"
        if [[ "$(date +%s)" -ge "$token_expiry" ]]; then
            rm -f "$TOKEN_CACHE_FILE" "${TOKEN_CACHE_FILE}.expiry"
            log DEBUG "Removed expired token cache"
        fi
    fi
    exit $exit_code
}
trap cleanup EXIT INT TERM

# --- Configuration -----------------------------------------------------------
load_config() {
    GRC_API_BASE_URL="${GRC_API_BASE_URL:-$DEFAULT_API_BASE}"
    GRC_OUTPUT_FORMAT="${GRC_OUTPUT_FORMAT:-$DEFAULT_OUTPUT_FORMAT}"
    GRC_RETRY_COUNT="${GRC_RETRY_COUNT:-$DEFAULT_RETRY_COUNT}"
    GRC_TIMEOUT="${GRC_TIMEOUT:-$DEFAULT_TIMEOUT}"
    GRC_DEBUG="${GRC_DEBUG:-false}"

    # Validate output format
    if [[ "$GRC_OUTPUT_FORMAT" != "json" && "$GRC_OUTPUT_FORMAT" != "table" ]]; then
        log ERROR "Invalid output format: $GRC_OUTPUT_FORMAT (must be json or table)"
        exit 1
    fi

    # Validate retry count
    if ! [[ "$GRC_RETRY_COUNT" =~ ^[0-9]+$ ]]; then
        log ERROR "Invalid retry count: $GRC_RETRY_COUNT"
        exit 1
    fi

    # Validate timeout
    if ! [[ "$GRC_TIMEOUT" =~ ^[0-9]+$ ]]; then
        log ERROR "Invalid timeout: $GRC_TIMEOUT"
        exit 1
    fi
}

# --- Dependency Check --------------------------------------------------------
check_dependencies() {
    local missing=()
    for cmd in curl jq date; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log ERROR "Missing required dependencies: ${missing[*]}"
        log ERROR "Install with: brew install ${missing[*]}"
        exit 1
    fi
}

# --- Authentication -----------------------------------------------------------
authenticate() {
    if [[ -z "${GRC_API_KEY:-}" ]]; then
        log ERROR "GRC_API_KEY environment variable is required"
        log ERROR "Export it with: export GRC_API_KEY=\"your-api-key\""
        exit 1
    fi

    if [[ -z "${GRC_API_SECRET:-}" ]]; then
        log ERROR "GRC_API_SECRET environment variable is required"
        log ERROR "Export it with: export GRC_API_SECRET=\"your-api-secret\""
        exit 1
    fi

    # Check cached token
    if [[ -f "$TOKEN_CACHE_FILE" ]]; then
        local token_expiry
        token_expiry="$(cat "${TOKEN_CACHE_FILE}.expiry" 2>/dev/null || echo 0)"
        if [[ "$(date +%s)" -lt "$token_expiry" ]]; then
            log DEBUG "Using cached token (expires in $(( token_expiry - $(date +%s) ))s)"
            return 0
        fi
    fi

    log INFO "Authenticating with GRC Claw API..."

    local response
    local http_code
    local temp_file
    temp_file="$(mktemp)"

    http_code=$(curl -s -w "%{{http_code}}" -o "$temp_file" \
        --max-time "$GRC_TIMEOUT" \
        -X POST "${GRC_API_BASE_URL}/auth/token" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: ${GRC_API_KEY}" \
        -H "X-API-Secret: ${GRC_API_SECRET}" \
        -d '{
            "grant_type": "client_credentials",
            "scope": "video-campaigns:read video-campaigns:write"
        }' 2>/dev/null) || true

    response="$(cat "$temp_file")"
    rm -f "$temp_file"

    if [[ "$http_code" != "200" ]]; then
        log ERROR "Authentication failed (HTTP $http_code)"
        log ERROR "Response: $response"
        exit 1
    fi

    local access_token
    access_token="$(echo "$response" | jq -r '.access_token // empty')"
    if [[ -z "$access_token" || "$access_token" == "null" ]]; then
        log ERROR "No access token in response"
        exit 1
    fi

    local expires_in
    expires_in="$(echo "$response" | jq -r '.expires_in // 3600')"

    # Cache token
    echo "$access_token" > "$TOKEN_CACHE_FILE"
    echo $(( $(date +%s) + expires_in - 60 )) > "${TOKEN_CACHE_FILE}.expiry"
    chmod 600 "$TOKEN_CACHE_FILE" "${TOKEN_CACHE_FILE}.expiry"

    log INFO "Authentication successful (expires in ${expires_in}s)"
}

get_auth_token() {
    if [[ ! -f "$TOKEN_CACHE_FILE" ]]; then
        authenticate
    fi
    cat "$TOKEN_CACHE_FILE"
}

# --- HTTP Request Helper -----------------------------------------------------
api_request() {
    local method="$1"
    local endpoint="$2"
    shift 2
    local data="${1:-}"

    local token
    token="$(get_auth_token)"

    local url="${GRC_API_BASE_URL}${endpoint}"
    local temp_file
    temp_file="$(mktemp)"
    local http_code
    local retry=0
    local max_retries="$GRC_RETRY_COUNT"

    while [[ $retry -le $max_retries ]]; do
        local curl_args=(
            -s -w "\n%{{http_code}}"
            --max-time "$GRC_TIMEOUT"
            -X "$method"
            -H "Authorization: Bearer $token"
            -H "Content-Type: application/json"
            -H "Accept: application/json"
            -H "X-Request-Id: $(uuidgen 2>/dev/null || date +%s%N)"
        )

        if [[ -n "$data" && "$method" != "GET" && "$method" != "DELETE" ]]; then
            curl_args+=(-d "$data")
        fi

        http_code=$(curl "${curl_args[@]}" "$url" 2>/dev/null | tail -1)
        local body
        body="$(curl "${curl_args[@]}" "$url" 2>/dev/null | sed '$d')"

        case "$http_code" in
            2[0-9][0-9])
                echo "$body"
                rm -f "$temp_file"
                return 0
                ;;
            401)
                log WARN "Token expired, re-authenticating..."
                rm -f "$TOKEN_CACHE_FILE" "${TOKEN_CACHE_FILE}.expiry"
                token="$(get_auth_token)"
                retry=$((retry + 1))
                ;;
            429)
                local retry_after
                retry_after="$(echo "$body" | jq -r '.retry_after // 5')"
                log WARN "Rate limited, waiting ${retry_after}s..."
                sleep "$retry_after"
                retry=$((retry + 1))
                ;;
            5[0-9][0-9])
                retry=$((retry + 1))
                if [[ $retry -le $max_retries ]]; then
                    local wait_time=$((2 ** retry))
                    log WARN "Server error (HTTP $http_code), retry $retry/$max_retries in ${wait_time}s..."
                    sleep "$wait_time"
                else
                    log ERROR "Server error after $max_retries retries (HTTP $http_code)"
                    log ERROR "Response: $body"
                    rm -f "$temp_file"
                    return 1
                fi
                ;;
            *)
                log ERROR "Request failed (HTTP $http_code)"
                log ERROR "Response: $body"
                rm -f "$temp_file"
                return 1
                ;;
        esac
    done

    rm -f "$temp_file"
    return 1
}

# --- Output Formatting -------------------------------------------------------
format_output() {
    local data="$1"
    if [[ "$GRC_OUTPUT_FORMAT" == "json" ]]; then
        echo "$data" | jq '.' 2>/dev/null || echo "$data"
    else
        # Table format
        echo "$data" | jq -r '
            if type == "array" then
                if length == 0 then "No results found."
                else
                    (.[0] | keys_unsorted | join("\t")),
                    (.[] | [.[] | tostring] | join("\t"))
                end
            elif type == "object" then
                to_entries[] | "\(.key)\t\(.value)"
            else
                tostring
            end
        ' 2>/dev/null || echo "$data"
    fi
}

# --- Input Validation --------------------------------------------------------
validate_required() {
    local field_name="$1"
    local field_value="${2:-}"
    if [[ -z "$field_value" ]]; then
        log ERROR "Missing required parameter: --${field_name//_/-}"
        return 1
    fi
}

validate_id() {
    local id="$1"
    if [[ ! "$id" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        log ERROR "Invalid ID format: $id"
        return 1
    fi
}

# --- CRUD Operations --------------------------------------------------------

# List video-campaigns
cmd_list() {
    local limit="${1:-50}"
    local offset="${2:-0}"
    local sort_by="${3:-created_at}"
    local sort_order="${4:-desc}"

    log INFO "Listing video-campaigns (limit=$limit, offset=$offset)..."

    local query_params
    query_params="limit=${limit}&offset=${offset}&sort_by=${sort_by}&sort_order=${sort_order}"

    local response
    if ! response="$(api_request "GET" "/video-campaigns?${query_params}")"; then
        log ERROR "Failed to list video-campaigns"
        return 1
    fi

    format_output "$response"
}

# Get a specific video-campaign
cmd_get() {
    local id="${1:-}"
    validate_required "id" "$id" || return 1
    validate_id "$id" || return 1

    log INFO "Getting video-campaign with ID: $id"

    local response
    if ! response="$(api_request "GET" "/video-campaigns/${id}")"; then
        log ERROR "Failed to get video-campaign with ID: $id"
        return 1
    fi

    format_output "$response"
}

# Create a new video-campaign
cmd_create() {
    local name="${1:-}"
    local description="${2:-}"
    local status="${3:-draft}"
    local metadata="${4:-{}}"

    validate_required "name" "$name" || return 1

    log INFO "Creating new video-campaign: $name"

    local payload
    payload="$(jq -n \
        --arg name "$name" \
        --arg description "$description" \
        --arg status "$status" \
        --argjson metadata "$metadata" \
        --arg created_at "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        '{
            name: $name,
            description: $description,
            status: $status,
            metadata: $metadata,
            created_at: $created_at
        }')"

    local response
    if ! response="$(api_request "POST" "/video-campaigns" "$payload")"; then
        log ERROR "Failed to create video-campaign"
        return 1
    fi

    log INFO "video-campaign created successfully"
    format_output "$response"
}

# Update an existing video-campaign
cmd_update() {
    local id="${1:-}"
    local name="${2:-}"
    local description="${3:-}"
    local status="${4:-}"
    local metadata="${5:-}"

    validate_required "id" "$id" || return 1
    validate_id "$id" || return 1

    log INFO "Updating video-campaign with ID: $id"

    # Build payload with only provided fields
    local payload
    payload="$(jq -n \
        --arg name "$name" \
        --arg description "$description" \
        --arg status "$status" \
        --arg metadata "$metadata" \
        --arg updated_at "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        '{
            (if $name != "" then {name: $name} else {} end),
            (if $description != "" then {description: $description} else {} end),
            (if $status != "" then {status: $status} else {} end),
            (if $metadata != "" then {metadata: $metadata} else {} end),
            updated_at: $updated_at
        }')"

    local response
    if ! response="$(api_request "PUT" "/video-campaigns/${id}" "$payload")"; then
        log ERROR "Failed to update video-campaign with ID: $id"
        return 1
    fi

    log INFO "video-campaign updated successfully"
    format_output "$response"
}

# Delete a video-campaign
cmd_delete() {
    local id="${1:-}"
    local force="${2:-false}"

    validate_required "id" "$id" || return 1
    validate_id "$id" || return 1

    if [[ "$force" != "true" ]]; then
        log WARN "About to delete video-campaign with ID: $id"
        read -r -p "Are you sure? [y/N] " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log INFO "Deletion cancelled"
            return 0
        fi
    fi

    log INFO "Deleting video-campaign with ID: $id"

    if ! api_request "DELETE" "/video-campaigns/${id}" >/dev/null; then
        log ERROR "Failed to delete video-campaign with ID: $id"
        return 1
    fi

    log INFO "video-campaign deleted successfully"
}

# Search video-campaigns
cmd_search() {
    local query="${1:-}"
    local filters="${2:-{}}"
    local sort_by="${3:-relevance}"
    local limit="${4:-20}"

    log INFO "Searching video-campaigns for: $query"

    local payload
    payload="$(jq -n \
        --arg query "$query" \
        --argjson filters "$filters" \
        --arg sort_by "$sort_by" \
        --argjson limit "$limit" \
        '{
            query: $query,
            filters: $filters,
            sort_by: $sort_by,
            limit: $limit
        }')"

    local response
    if ! response="$(api_request "POST" "/video-campaigns/search" "$payload")"; then
        log ERROR "Search failed"
        return 1
    fi

    format_output "$response"
}

# Batch operations
cmd_batch() {
    local file="${1:-}"
    local operation="${2:-create}"
    local continue_on_error="${3:-false}"

    validate_required "file" "$file" || return 1

    if [[ ! -f "$file" ]]; then
        log ERROR "Batch file not found: $file"
        return 1
    fi

    log INFO "Starting batch $operation from file: $file"

    local total
    total="$(jq 'length' "$file")"
    local success=0
    local failed=0
    local results=()

    for i in $(seq 0 $((total - 1))); do
        local item
        item="$(jq ".[$i]" "$file")"
        local item_id
        item_id="$(echo "$item" | jq -r '.id // .name // "item_$i"')"

        log INFO "Processing $((i + 1))/$total: $item_id"

        local response
        if response="$(api_request "POST" "/video-campaigns/batch/${operation}" "$item")"; then
            success=$((success + 1))
            results+=("$(jq -n --arg id "$item_id" --arg status "success" '{id: $id, status: $status}')")
        else
            failed=$((failed + 1))
            results+=("$(jq -n --arg id "$item_id" --arg status "failed" '{id: $id, status: $status}')")
            if [[ "$continue_on_error" != "true" ]]; then
                log ERROR "Batch operation halted due to error (use --continue-on-error to override)"
                break
            fi
        fi

        # Rate limiting
        sleep 0.1
    done

    log INFO "Batch complete: $success succeeded, $failed failed out of $total"

    # Output summary
    jq -n \
        --argjson total "$total" \
        --argjson success "$success" \
        --argjson failed "$failed" \
        --argjson results "$(printf '%s\n' "${results[@]}" | jq -s '.')" \
        '{total: $total, success: $success, failed: $failed, results: $results}'
}

# Health check
cmd_health() {
    log INFO "Checking API health..."

    local response
    if response="$(api_request "GET" "/health")"; then
        format_output "$response"
    else
        log ERROR "Health check failed"
        return 1
    fi
}

# --- Usage -------------------------------------------------------------------
usage() {
    cat <<EOF
${BOLD}Video Marketing CLI v${VERSION}${NC}

${BOLD}USAGE:${NC}
    $SCRIPT_NAME <command> [options]

${BOLD}COMMANDS:${NC}
    auth                    Authenticate with the API
    list [limit] [offset]   List video-campaigns
    get --id <id>           Get a video-campaign by ID
    create [options]        Create a new video-campaign
    update [options]        Update an existing video-campaign
    delete --id <id>        Delete a video-campaign
    search [options]        Search video-campaigns
    batch [options]         Batch operations
    health                  Check API health status
    help                    Show this help message

${BOLD}CREATE OPTIONS:${NC}
    --name <name>           video-campaign name (required)
    --description <desc>    Description
    --status <status>       Status (default: draft)
    --metadata <json>       Additional metadata as JSON

${BOLD}UPDATE OPTIONS:${NC}
    --id <id>               video-campaign ID (required)
    --name <name>           New name
    --description <desc>    New description
    --status <status>       New status
    --metadata <json>       Metadata as JSON

${BOLD}SEARCH OPTIONS:${NC}
    --query <query>         Search query
    --filters <json>        Filter criteria as JSON
    --sort-by <field>       Sort field (default: relevance)
    --limit <n>             Results limit (default: 20)

${BOLD}BATCH OPTIONS:${NC}
    --file <path>           JSON file with items (required)
    --operation <op>        Operation: create|update|delete (default: create)
    --continue-on-error     Continue on individual item failure

${BOLD}EXAMPLES:${NC}
    # Authenticate
    export GRC_API_KEY="your-key"
    export GRC_API_SECRET="your-secret"
    $SCRIPT_NAME auth

    # List video-campaigns
    $SCRIPT_NAME list 20 0

    # Get a specific video-campaign
    $SCRIPT_NAME get --id "abc123"

    # Create a new video-campaign
    $SCRIPT_NAME create --name "New video-campaign" --status active

    # Update a video-campaign
    $SCRIPT_NAME update --id "abc123" --status completed

    # Delete a video-campaign
    $SCRIPT_NAME delete --id "abc123" --force

    # Search
    $SCRIPT_NAME search --query "enterprise" --limit 10

    # Batch create from file
    $SCRIPT_NAME batch --file ./items.json --operation create

${BOLD}ENVIRONMENT:${NC}
    GRC_API_KEY             API key (required)
    GRC_API_SECRET          API secret (required)
    GRC_API_BASE_URL        API base URL (default: $DEFAULT_API_BASE)
    GRC_OUTPUT_FORMAT       Output format: json|table (default: json)
    GRC_DEBUG               Enable debug logging (default: false)
    GRC_RETRY_COUNT         Retry attempts for failures (default: 3)
    GRC_TIMEOUT             Request timeout in seconds (default: 30)

EOF
}

# --- Argument Parsing --------------------------------------------------------
parse_global_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --output|-o)
                GRC_OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --debug|-d)
                GRC_DEBUG=true
                shift
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            --version|-v)
                echo "$SCRIPT_NAME v$VERSION"
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done
}

parse_create_args() {
    CREATE_NAME=""
    CREATE_DESCRIPTION=""
    CREATE_STATUS="draft"
    CREATE_METADATA="{}"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name)       CREATE_NAME="$2"; shift 2 ;;
            --description) CREATE_DESCRIPTION="$2"; shift 2 ;;
            --status)     CREATE_STATUS="$2"; shift 2 ;;
            --metadata)   CREATE_METADATA="$2"; shift 2 ;;
            *)            log ERROR "Unknown option: $1"; return 1 ;;
        esac
    done
}

parse_update_args() {
    UPDATE_ID=""
    UPDATE_NAME=""
    UPDATE_DESCRIPTION=""
    UPDATE_STATUS=""
    UPDATE_METADATA=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id)         UPDATE_ID="$2"; shift 2 ;;
            --name)       UPDATE_NAME="$2"; shift 2 ;;
            --description) UPDATE_DESCRIPTION="$2"; shift 2 ;;
            --status)     UPDATE_STATUS="$2"; shift 2 ;;
            --metadata)   UPDATE_METADATA="$2"; shift 2 ;;
            *)            log ERROR "Unknown option: $1"; return 1 ;;
        esac
    done
}

parse_search_args() {
    SEARCH_QUERY=""
    SEARCH_FILTERS="{}"
    SEARCH_SORT_BY="relevance"
    SEARCH_LIMIT=20

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --query)    SEARCH_QUERY="$2"; shift 2 ;;
            --filters)  SEARCH_FILTERS="$2"; shift 2 ;;
            --sort-by)  SEARCH_SORT_BY="$2"; shift 2 ;;
            --limit)    SEARCH_LIMIT="$2"; shift 2 ;;
            *)          log ERROR "Unknown option: $1"; return 1 ;;
        esac
    done
}

parse_batch_args() {
    BATCH_FILE=""
    BATCH_OPERATION="create"
    BATCH_CONTINUE_ON_ERROR="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --file)              BATCH_FILE="$2"; shift 2 ;;
            --operation)         BATCH_OPERATION="$2"; shift 2 ;;
            --continue-on-error) BATCH_CONTINUE_ON_ERROR="true"; shift ;;
            *)                   log ERROR "Unknown option: $1"; return 1 ;;
        esac
    done
}

# --- Main --------------------------------------------------------------------
main() {
    check_dependencies
    load_config

    local command="${1:-help}"
    shift || true

    case "$command" in
        auth)
            authenticate
            ;;
        list)
            parse_global_args "$@" || true
            cmd_list "${1:-50}" "${2:-0}" "${3:-created_at}" "${4:-desc}"
            ;;
        get)
            parse_global_args "$@"
            local id=""
            while [[ $# -gt 0 ]]; do
                case "$1" in
                    --id) id="$2"; shift 2 ;;
                    *) shift ;;
                esac
            done
            cmd_get "$id"
            ;;
        create)
            parse_global_args "$@"
            parse_create_args "$@"
            cmd_create "$CREATE_NAME" "$CREATE_DESCRIPTION" "$CREATE_STATUS" "$CREATE_METADATA"
            ;;
        update)
            parse_global_args "$@"
            parse_update_args "$@"
            cmd_update "$UPDATE_ID" "$UPDATE_NAME" "$UPDATE_DESCRIPTION" "$UPDATE_STATUS" "$UPDATE_METADATA"
            ;;
        delete)
            parse_global_args "$@"
            local id=""
            local force="false"
            while [[ $# -gt 0 ]]; do
                case "$1" in
                    --id)    id="$2"; shift 2 ;;
                    --force) force="true"; shift ;;
                    *) shift ;;
                esac
            done
            cmd_delete "$id" "$force"
            ;;
        search)
            parse_global_args "$@"
            parse_search_args "$@"
            cmd_search "$SEARCH_QUERY" "$SEARCH_FILTERS" "$SEARCH_SORT_BY" "$SEARCH_LIMIT"
            ;;
        batch)
            parse_global_args "$@"
            parse_batch_args "$@"
            cmd_batch "$BATCH_FILE" "$BATCH_OPERATION" "$BATCH_CONTINUE_ON_ERROR"
            ;;
        health)
            parse_global_args "$@"
            cmd_health
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log ERROR "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"

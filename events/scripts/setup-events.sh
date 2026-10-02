#!/usr/bin/env bash
# Setup script for the event-driven integration system.
# Initializes directories, validates dependencies, and prepares the environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVENTS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$EVENTS_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python() {
    log_info "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python version: $PYTHON_VERSION"

    # Check minimum version (3.9+)
    python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)' || {
        log_error "Python 3.9 or higher is required."
        exit 1
    }
}

# Check pip
check_pip() {
    log_info "Checking pip installation..."
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not installed."
        exit 1
    fi
    log_info "pip is available"
}

# Create necessary directories
create_directories() {
    log_info "Creating event system directories..."

    mkdir -p "$EVENTS_DIR"/{scripts,tests}
    mkdir -p "$PROJECT_ROOT"/data/events
    mkdir -p "$PROJECT_ROOT"/logs/events

    log_info "Directories created successfully"
}

# Verify module structure
verify_structure() {
    log_info "Verifying event system module structure..."

    local required_files=(
        "__init__.py"
        "bus.py"
        "schema.py"
        "router.py"
        "sourcing.py"
        "replay.py"
        "subscriber.py"
        "publisher.py"
        "store.py"
        "metrics.py"
    )

    local missing=0
    for file in "${required_files[@]}"; do
        if [[ ! -f "$EVENTS_DIR/$file" ]]; then
            log_error "Missing required file: $file"
            missing=$((missing + 1))
        fi
    done

    if [[ $missing -gt 0 ]]; then
        log_error "$missing required file(s) missing"
        exit 1
    fi

    log_info "All required files present"
}

# Run syntax check
syntax_check() {
    log_info "Running syntax check on event modules..."

    local failed=0
    for file in "$EVENTS_DIR"/*.py; do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            log_error "Syntax error in: $(basename "$file")"
            failed=$((failed + 1))
        fi
    done

    if [[ $failed -gt 0 ]]; then
        log_error "$failed file(s) with syntax errors"
        exit 1
    fi

    log_info "Syntax check passed"
}

# Run import test
import_test() {
    log_info "Running import test..."

    cd "$PROJECT_ROOT"
    if ! python3 -c "from events import EventBus, Event, EventRouter, EventStore; print('Import successful')" 2>/dev/null; then
        log_warn "Import test failed - this may be expected if running outside the project context"
    else
        log_info "Import test passed"
    fi
}

# Print summary
print_summary() {
    echo ""
    log_info "Event-driven integration system setup complete!"
    echo ""
    echo "Module location: $EVENTS_DIR"
    echo "Data directory:  $PROJECT_ROOT/data/events"
    echo "Log directory:   $PROJECT_ROOT/logs/events"
    echo ""
    echo "Quick start:"
    echo "  cd $PROJECT_ROOT"
    echo "  python3 -c 'from events import EventBus, Event; bus = EventBus(); ...'"
    echo ""
}

# Main execution
main() {
    log_info "Setting up event-driven integration system..."
    echo ""

    check_python
    check_pip
    create_directories
    verify_structure
    syntax_check
    import_test
    print_summary
}

main "$@"

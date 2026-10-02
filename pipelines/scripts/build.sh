#!/usr/bin/env bash
# build.sh — Build and push a Docker image.
#
# Usage:
#   ./scripts/build.sh --image IMAGE_NAME --tag TAG [--push] [--platforms PLATFORMS]
#
# Options:
#   --image IMAGE_NAME    Docker image name (e.g., myapp).
#   --tag TAG             Docker image tag (e.g., latest, v1.0.0, sha-abc123).
#   --push                Push the image to the registry after building.
#   --platforms PLATFORMS Comma-separated target platforms (default: linux/amd64).
#   --dockerfile PATH     Path to Dockerfile (default: ./Dockerfile).
#   --context PATH        Build context path (default: .).
#   --build-arg KEY=VAL   Pass build arguments (can be used multiple times).
#   --cache               Enable BuildKit cache.
#   --no-cache            Disable build cache.
#
# Exit codes:
#   0  Build (and push) succeeded.
#   1  Build or push failed.

set -euo pipefail

# ── Colors for output ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Logging helpers ─────────────────────────────────────────────────────────
log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $*"; }

# ── Argument parsing ────────────────────────────────────────────────────────
IMAGE_NAME=""
IMAGE_TAG=""
PUSH=false
PLATFORMS="linux/amd64"
DOCKERFILE="./Dockerfile"
CONTEXT="."
BUILD_ARGS=()
USE_CACHE=true

for arg in "$@"; do
    case "$arg" in
        --image)
            shift
            IMAGE_NAME="${1:-}"
            ;;
        --tag)
            shift
            IMAGE_TAG="${1:-}"
            ;;
        --push)
            PUSH=true
            ;;
        --platforms)
            shift
            PLATFORMS="${1:-linux/amd64}"
            ;;
        --dockerfile)
            shift
            DOCKERFILE="${1:-./Dockerfile}"
            ;;
        --context)
            shift
            CONTEXT="${1:-.}"
            ;;
        --build-arg)
            shift
            BUILD_ARGS+=("--build-arg" "${1:-}")
            ;;
        --cache)
            USE_CACHE=true
            ;;
        --no-cache)
            USE_CACHE=false
            ;;
        -h|--help)
            grep '^#' "$0" | head -n 14 | sed 's/^# //'
            exit 0
            ;;
        *)
            log_error "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# ── Validate required arguments ──────────────────────────────────────────────
if [[ -z "$IMAGE_NAME" ]]; then
    log_error "--image is required."
    exit 1
fi

if [[ -z "$IMAGE_TAG" ]]; then
    log_warn "No --tag specified, using 'latest'."
    IMAGE_TAG="latest"
fi

# ── Determine project root ──────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$PROJECT_ROOT"

# ── Check dependencies ──────────────────────────────────────────────────────
check_dependency() {
    local cmd="$1"
    if ! command -v "$cmd" &>/dev/null; then
        log_error "'$cmd' is not installed."
        exit 1
    fi
}

log_info "Checking dependencies..."
check_dependency docker

# ── Verify Dockerfile exists ─────────────────────────────────────────────────
if [[ ! -f "$DOCKERFILE" ]]; then
    log_error "Dockerfile not found at: $DOCKERFILE"
    exit 1
fi

# ── Build Docker image ──────────────────────────────────────────────────────
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
log_info "Building Docker image: $FULL_IMAGE_NAME"
log_info "  Dockerfile: $DOCKERFILE"
log_info "  Context:    $CONTEXT"
log_info "  Platforms:  $PLATFORMS"

BUILDKIT_ARGS=(
    "build"
    "--file" "$DOCKERFILE"
    "--tag" "$FULL_IMAGE_NAME"
    "--platform" "$PLATFORMS"
    "--provenance" "mode=max"
    "--sbom" "true"
)

# Add build arguments
for ba in "${BUILD_ARGS[@]}"; do
    BUILDKIT_ARGS+=("$ba")
done

# Cache options
if [[ "$USE_CACHE" == true ]]; then
    BUILDKIT_ARGS+=("--cache-from" "type=local,src=.buildx-cache")
    BUILDKIT_ARGS+=("--cache-to" "type=local,dest=.buildx-cache-new,mode=max")
fi

# Push option
if [[ "$PUSH" == true ]]; then
    BUILDKIT_ARGS+=("--push")
    log_info "Image will be pushed after build."
else
    BUILDKIT_ARGS+=("--load")
    log_info "Image will be loaded locally (no push)."
fi

BUILD_EXIT_CODE=0
docker buildx "${BUILDKIT_ARGS[@]}" "$CONTEXT" || BUILD_EXIT_CODE=$?

if [[ "$BUILD_EXIT_CODE" -ne 0 ]]; then
    log_error "Docker build failed with exit code: $BUILD_EXIT_CODE"
    exit 1
fi

log_success "Docker image built successfully: $FULL_IMAGE_NAME"

# ── Push Docker image ───────────────────────────────────────────────────────
if [[ "$PUSH" == true ]]; then
    log_info "Pushing Docker image: $FULL_IMAGE_NAME"

    PUSH_EXIT_CODE=0
    docker push "$FULL_IMAGE_NAME" || PUSH_EXIT_CODE=$?

    if [[ "$PUSH_EXIT_CODE" -ne 0 ]]; then
        log_error "Docker push failed with exit code: $PUSH_EXIT_CODE"
        exit 1
    fi

    log_success "Docker image pushed successfully: $FULL_IMAGE_NAME"
fi

# ── Output image digest ─────────────────────────────────────────────────────
IMAGE_DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "$FULL_IMAGE_NAME" 2>/dev/null || echo "N/A")
log_info "Image digest: $IMAGE_DIGEST"

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════"
log_success "Build completed successfully!"
log_info "Image: $FULL_IMAGE_NAME"
log_info "Digest: $IMAGE_DIGEST"
echo "══════════════════════════════════════════════════════════════"
exit 0

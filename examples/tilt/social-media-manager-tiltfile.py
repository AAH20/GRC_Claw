"""
Tiltfile for Social Media Manager Service
==========================================
Build, deploy, and live-update configuration for the social media management
microservice. Manages posting, scheduling, and analytics across multiple
social platforms.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "social-media-manager"
IMAGE_NAME = "grc-claw/social-media-manager"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8084
REMOTE_PORT = 8084

# ---------------------------------------------------------------------------
# Docker Build
# ---------------------------------------------------------------------------
docker_build(
    ref=IMAGE_NAME,
    context=".",
    dockerfile=DOCKERFILE,
    build_args={
        "PYTHON_VERSION": "3.11",
        "ENVIRONMENT": "production",
    },
    live_update=[
        sync("./src", "/app/src"),
        sync("./platforms", "/app/platforms"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/social-media-manager"))

k8s_resource(
    workload="social-media-manager",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["social", "media", "scheduling"],
    resource_deps=["social-db", "redis-cache", "media-storage"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="social-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=social_media postgres:15",
    serve_cmd="pg_isready -h localhost -p 5432",
    readiness_probe=probe(period_secs=5, failure_threshold=12),
    labels=["database"],
)

local_resource(
    name="redis-cache",
    cmd="docker run --rm -p 6379:6379 redis:7-alpine",
    serve_cmd="redis-cli ping",
    readiness_probe=probe(period_secs=5, failure_threshold=12),
    labels=["cache"],
)

local_resource(
    name="media-storage",
    cmd="docker run --rm -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ':9001'",
    serve_cmd="curl -s http://localhost:9000/minio/health/live",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["storage", "minio"],
)

local_resource(
    name="seed-platforms",
    cmd="python scripts/seed_platforms.py",
    deps=["./scripts/seed_platforms.py", "./data/platforms.yaml"],
    labels=["seed", "data"],
    resource_deps=["social-db"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./platforms")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="social-media-manager",
    probes={
        "readiness": probe(
            http_get=probe_http_get(port=REMOTE_PORT, path="/health/ready"),
            period_secs=10,
            failure_threshold=3,
        ),
        "liveness": probe(
            http_get=probe_http_get(port=REMOTE_PORT, path="/health/live"),
            period_secs=15,
            failure_threshold=3,
        ),
    },
)

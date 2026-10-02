"""
Tiltfile for PPC Manager Service
=================================
Build, deploy, and live-update configuration for the PPC (Pay-Per-Click)
management microservice. Manages ad campaigns across Google Ads, Bing Ads,
and social platforms with automated bidding and budget optimization.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "ppc-manager"
IMAGE_NAME = "grc-claw/ppc-manager"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8086
REMOTE_PORT = 8086

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
        sync("./adapters", "/app/adapters"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/ppc-manager"))

k8s_resource(
    workload="ppc-manager",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["ppc", "advertising", "bidding"],
    resource_deps=["ppc-db", "redis-cache", "api-gateway"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="ppc-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=ppc postgres:15",
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
    name="api-gateway",
    cmd="docker run --rm -p 8080:8080 -e GOOGLE_ADS_API_KEY=$GOOGLE_ADS_API_KEY -e BING_ADS_API_KEY=$BING_ADS_API_KEY envoyproxy/envoy:v1.28",
    serve_cmd="curl -s http://localhost:8080/ready",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["gateway", "api"],
)

local_resource(
    name="sync-campaigns",
    cmd="python scripts/sync_campaigns.py",
    deps=["./scripts/sync_campaigns.py"],
    labels=["sync", "campaigns"],
    resource_deps=["ppc-db", "api-gateway"],
    trigger_mode=TRIGGER_MODE_AUTO,
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./adapters")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="ppc-manager",
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

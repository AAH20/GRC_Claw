"""
Tiltfile for Campaign Optimizer Service
========================================
Build, deploy, and live-update configuration for the campaign optimizer
microservice. Handles A/B testing, bid management, and campaign performance
optimization.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "campaign-optimizer"
IMAGE_NAME = "grc-claw/campaign-optimizer"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8080
REMOTE_PORT = 8080

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
        sync("./config", "/app/config"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/campaign-optimizer"))

k8s_resource(
    workload="campaign-optimizer",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["optimization", "campaigns"],
    resource_deps=["campaign-db", "redis-cache"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="campaign-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=campaigns postgres:15",
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
    name="seed-campaigns",
    cmd="python scripts/seed_campaigns.py",
    deps=["./scripts/seed_campaigns.py", "./data/campaigns.json"],
    labels=["seed", "data"],
    resource_deps=["campaign-db"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./config")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="campaign-optimizer",
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

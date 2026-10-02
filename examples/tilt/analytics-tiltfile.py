"""
Tiltfile for Analytics Service
===============================
Build, deploy, and live-update configuration for the analytics microservice.
Provides real-time dashboards, custom reporting, funnel analysis, and
predictive analytics across all GRC Claw services.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "analytics"
IMAGE_NAME = "grc-claw/analytics"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8091
REMOTE_PORT = 8091

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
        sync("./dashboards", "/app/dashboards"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/analytics"))

k8s_resource(
    workload="analytics",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["analytics", "reporting", "dashboards"],
    resource_deps=["analytics-db", "redis-cache", "clickhouse"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="analytics-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=analytics postgres:15",
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
    name="clickhouse",
    cmd="docker run --rm -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server:latest",
    serve_cmd="curl -s http://localhost:8123/ping",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["olap", "clickhouse"],
)

local_resource(
    name="seed-dashboards",
    cmd="python scripts/seed_dashboards.py",
    deps=["./scripts/seed_dashboards.py", "./data/dashboards/"],
    labels=["seed", "dashboards"],
    resource_deps=["analytics-db"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./dashboards")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="analytics",
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

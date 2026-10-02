"""
Tiltfile for Sales Automator Service
=====================================
Build, deploy, and live-update configuration for the sales automation
microservice. Automates follow-ups, pipeline management, proposal generation,
and sales forecasting.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "sales-automator"
IMAGE_NAME = "grc-claw/sales-automator"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8089
REMOTE_PORT = 8089

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
        sync("./workflows", "/app/workflows"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/sales-automator"))

k8s_resource(
    workload="sales-automator",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["sales", "automation", "pipeline"],
    resource_deps=["sales-db", "redis-cache", "document-generator"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="sales-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=sales postgres:15",
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
    name="document-generator",
    cmd="docker run --rm -p 3000:3000 gotenberg/gotenberg:8",
    serve_cmd="curl -s http://localhost:3000/health",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["documents", "pdf"],
)

local_resource(
    name="seed-pipeline",
    cmd="python scripts/seed_pipeline.py",
    deps=["./scripts/seed_pipeline.py", "./data/pipeline_stages.yaml"],
    labels=["seed", "data"],
    resource_deps=["sales-db"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./workflows")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="sales-automator",
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

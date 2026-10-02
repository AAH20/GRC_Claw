"""
Tiltfile for SEO Optimizer Service
====================================
Build, deploy, and live-update configuration for the SEO optimization
microservice. Provides keyword research, on-page optimization, technical
SEO audits, and rank tracking.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "seo-optimizer"
IMAGE_NAME = "grc-claw/seo-optimizer"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8087
REMOTE_PORT = 8087

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
        sync("./rules", "/app/rules"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/seo-optimizer"))

k8s_resource(
    workload="seo-optimizer",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["seo", "optimization", "ranking"],
    resource_deps=["seo-db", "redis-cache", "crawler-queue"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="seo-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=seo postgres:15",
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
    name="crawler-queue",
    cmd="docker run --rm -p 5672:5672 -p 15672:15672 rabbitmq:3-management-alpine",
    serve_cmd="curl -s http://localhost:15672/api/overview",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["queue", "crawler"],
)

local_resource(
    name="seed-keywords",
    cmd="python scripts/seed_keywords.py",
    deps=["./scripts/seed_keywords.py", "./data/keywords.csv"],
    labels=["seed", "data"],
    resource_deps=["seo-db"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./rules")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="seo-optimizer",
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

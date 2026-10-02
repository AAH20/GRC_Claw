"""
Tiltfile for Email Marketing Service
=====================================
Build, deploy, and live-update configuration for the email marketing
microservice. Handles campaign creation, template management, delivery
tracking, and engagement analytics.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "email-marketing"
IMAGE_NAME = "grc-claw/email-marketing"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8085
REMOTE_PORT = 8085

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
        sync("./templates", "/app/templates"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/email-marketing"))

k8s_resource(
    workload="email-marketing",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["email", "marketing", "delivery"],
    resource_deps=["email-db", "redis-cache", "smtp-relay"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="email-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=email_marketing postgres:15",
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
    name="smtp-relay",
    cmd="docker run --rm -p 1025:1025 -p 8025:8025 mailhog/mailhog:latest",
    serve_cmd="curl -s http://localhost:8025/api/v2/messages",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["email", "smtp"],
)

local_resource(
    name="seed-templates",
    cmd="python scripts/seed_templates.py",
    deps=["./scripts/seed_templates.py", "./data/templates/"],
    labels=["seed", "data"],
    resource_deps=["email-db"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./templates")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="email-marketing",
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

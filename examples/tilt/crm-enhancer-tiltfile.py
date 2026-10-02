"""
Tiltfile for CRM Enhancer Service
==================================
Build, deploy, and live-update configuration for the CRM enhancement
microservice. Enriches CRM data with AI-driven insights, contact scoring,
and relationship mapping.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "crm-enhancer"
IMAGE_NAME = "grc-claw/crm-enhancer"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8088
REMOTE_PORT = 8088

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
        sync("./enrichment", "/app/enrichment"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/crm-enhancer"))

k8s_resource(
    workload="crm-enhancer",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["crm", "enrichment", "ai"],
    resource_deps=["crm-db", "redis-cache", "data-warehouse"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="crm-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=crm postgres:15",
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
    name="data-warehouse",
    cmd="docker run --rm -p 5433:5432 -e POSTGRES_DB=warehouse postgres:15",
    serve_cmd="pg_isready -h localhost -p 5432",
    readiness_probe=probe(period_secs=5, failure_threshold=12),
    labels=["warehouse", "analytics"],
)

local_resource(
    name="enrich-contacts",
    cmd="python scripts/enrich_contacts.py",
    deps=["./scripts/enrich_contacts.py"],
    labels=["enrichment", "contacts"],
    resource_deps=["crm-db", "data-warehouse"],
    trigger_mode=TRIGGER_MODE_AUTO,
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./enrichment")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="crm-enhancer",
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

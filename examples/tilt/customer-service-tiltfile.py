"""
Tiltfile for Customer Service Service
======================================
Build, deploy, and live-update configuration for the customer service
microservice. Powers AI-assisted ticketing, chatbots, knowledge base
management, and customer satisfaction tracking.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "customer-service"
IMAGE_NAME = "grc-claw/customer-service"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8090
REMOTE_PORT = 8090

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
        sync("./knowledge_base", "/app/knowledge_base"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/customer-service"))

k8s_resource(
    workload="customer-service",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["support", "service", "ai"],
    resource_deps=["cs-db", "redis-cache", "nlp-engine"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="cs-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=customer_service postgres:15",
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
    name="nlp-engine",
    cmd="docker run --rm -p 5000:5000 -e MODEL_NAME=distilbert-base-uncased huggingface/transformers-pytorch-cpu:latest",
    serve_cmd="curl -s http://localhost:5000/health",
    readiness_probe=probe(period_secs=15, failure_threshold=4),
    labels=["ai", "nlp"],
)

local_resource(
    name="seed-kb",
    cmd="python scripts/seed_knowledge_base.py",
    deps=["./scripts/seed_knowledge_base.py", "./data/kb_articles.json"],
    labels=["seed", "knowledge-base"],
    resource_deps=["cs-db"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./knowledge_base")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="customer-service",
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

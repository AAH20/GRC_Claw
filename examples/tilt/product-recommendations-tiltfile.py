"""
Tiltfile for Product Recommendations Service
=============================================
Build, deploy, and live-update configuration for the product recommendations
microservice. Provides AI-driven product suggestions, cross-sell/upsell
recommendations, and personalized product catalogs.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "product-recommendations"
IMAGE_NAME = "grc-claw/product-recommendations"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8093
REMOTE_PORT = 8093

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
        sync("./models", "/app/models"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/product-recommendations"))

k8s_resource(
    workload="product-recommendations",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["recommendations", "ai", "products"],
    resource_deps=["recs-db", "redis-cache", "vector-store"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="recs-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=recommendations postgres:15",
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
    name="vector-store",
    cmd="docker run --rm -p 6333:6333 qdrant/qdrant:latest",
    serve_cmd="curl -s http://localhost:6333/healthz",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["vector", "embeddings"],
)

local_resource(
    name="train-recs",
    cmd="python scripts/train_recommender.py --output-dir ./models",
    deps=["./scripts/train_recommender.py", "./data/products.parquet"],
    labels=["ml", "training"],
    resource_deps=["recs-db", "vector-store"],
    trigger_mode=TRIGGER_MODE_AUTO,
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./models")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="product-recommendations",
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

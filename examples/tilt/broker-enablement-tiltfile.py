"""
Tiltfile for Broker Enablement Service
=======================================
Build, deploy, and live-update configuration for the broker enablement
microservice. Provides training modules, compliance tracking, licensing
management, and performance analytics for insurance brokers.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "broker-enablement"
IMAGE_NAME = "grc-claw/broker-enablement"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8092
REMOTE_PORT = 8092

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
        sync("./training", "/app/training"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/broker-enablement"))

k8s_resource(
    workload="broker-enablement",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["broker", "training", "compliance"],
    resource_deps=["broker-db", "redis-cache", "document-store"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="broker-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=broker_enablement postgres:15",
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
    name="document-store",
    cmd="docker run --rm -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ':9001'",
    serve_cmd="curl -s http://localhost:9000/minio/health/live",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["storage", "minio"],
)

local_resource(
    name="seed-training",
    cmd="python scripts/seed_training_modules.py",
    deps=["./scripts/seed_training_modules.py", "./data/training_modules.yaml"],
    labels=["seed", "training"],
    resource_deps=["broker-db"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./training")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="broker-enablement",
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

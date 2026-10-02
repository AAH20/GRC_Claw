"""
Tiltfile for Journey Orchestrator Service
==========================================
Build, deploy, and live-update configuration for the customer journey
orchestration microservice. Manages multi-step customer journeys across
channels with real-time personalization.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "journey-orchestrator"
IMAGE_NAME = "grc-claw/journey-orchestrator"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8082
REMOTE_PORT = 8082

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
        sync("./journeys", "/app/journeys"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/journey-orchestrator"))

k8s_resource(
    workload="journey-orchestrator",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["orchestration", "journeys", "personalization"],
    resource_deps=["journey-db", "event-bus", "redis-cache"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="journey-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=journeys postgres:15",
    serve_cmd="pg_isready -h localhost -p 5432",
    readiness_probe=probe(period_secs=5, failure_threshold=12),
    labels=["database"],
)

local_resource(
    name="event-bus",
    cmd="docker run --rm -p 9092:9092 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 confluentinc/cp-kafka:latest",
    serve_cmd="kafka-broker-api-versions.sh --bootstrap-server localhost:9092",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["messaging", "kafka"],
)

local_resource(
    name="redis-cache",
    cmd="docker run --rm -p 6379:6379 redis:7-alpine",
    serve_cmd="redis-cli ping",
    readiness_probe=probe(period_secs=5, failure_threshold=12),
    labels=["cache"],
)

local_resource(
    name="seed-journeys",
    cmd="python scripts/seed_journeys.py",
    deps=["./scripts/seed_journeys.py", "./data/journeys.yaml"],
    labels=["seed", "data"],
    resource_deps=["journey-db"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./journeys")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="journey-orchestrator",
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

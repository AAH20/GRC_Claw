"""
Tiltfile for Lead Scorer Service
=================================
Build, deploy, and live-update configuration for the lead scoring
microservice. Uses ML models to score and rank sales leads in real-time.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "lead-scorer"
IMAGE_NAME = "grc-claw/lead-scorer"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8081
REMOTE_PORT = 8081
MODEL_DIR = "./models"

# ---------------------------------------------------------------------------
# Docker Build
# ---------------------------------------------------------------------------
docker_build(
    ref=IMAGE_NAME,
    context=".",
    dockerfile=DOCKERFILE,
    build_args={
        "PYTHON_VERSION": "3.11",
        "MLFLOW_VERSION": "2.8",
        "ENVIRONMENT": "production",
    },
    live_update=[
        sync("./src", "/app/src"),
        sync(MODEL_DIR, "/app/models"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/lead-scorer"))

k8s_resource(
    workload="lead-scorer",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["ml", "scoring", "leads"],
    resource_deps=["model-registry", "feature-store"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="model-registry",
    cmd="mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts",
    serve_cmd="curl -s http://localhost:5000/health",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["ml", "model-registry"],
)

local_resource(
    name="feature-store",
    cmd="docker run --rm -p 6566:6566 feast/feature-server:latest",
    serve_cmd="curl -s http://localhost:6566/health",
    readiness_probe=probe(period_secs=10, failure_threshold=6),
    labels=["ml", "feature-store"],
)

local_resource(
    name="train-model",
    cmd="python scripts/train_scoring_model.py --output-dir ./models",
    deps=["./scripts/train_scoring_model.py", "./data/leads.parquet"],
    labels=["ml", "training"],
    resource_deps=["model-registry", "feature-store"],
    trigger_mode=TRIGGER_MODE_AUTO,
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file(MODEL_DIR)

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="lead-scorer",
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

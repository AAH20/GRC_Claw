"""
Tiltfile for Content Generator Service
=======================================
Build, deploy, and live-update configuration for the AI-powered content
generation microservice. Generates marketing copy, blog posts, and social
media content using LLMs.
"""

load("ext://helm_remote", "helm_remote")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NAMESPACE = "content-generator"
IMAGE_NAME = "grc-claw/content-generator"
IMAGE_TAG = "latest"
DOCKERFILE = "./Dockerfile"
K8S_DIR = "./k8s"
LOCAL_PORT = 8083
REMOTE_PORT = 8083

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
        sync("./prompts", "/app/prompts"),
        sync("./templates", "/app/templates"),
        run("pip install -r requirements.txt", trigger="./requirements.txt"),
        restart_container(),
    ],
)

# ---------------------------------------------------------------------------
# Kubernetes Deploy
# ---------------------------------------------------------------------------
k8s_yaml(helm("./helm/content-generator"))

k8s_resource(
    workload="content-generator",
    port_forwards=[f"{LOCAL_PORT}:{REMOTE_PORT}"],
    labels=["ai", "content", "generation"],
    resource_deps=["llm-gateway", "content-db"],
)

# ---------------------------------------------------------------------------
# Local Development Resources
# ---------------------------------------------------------------------------
local_resource(
    name="llm-gateway",
    cmd="docker run --rm -p 8080:8080 -e OPENAI_API_KEY=$OPENAI_API_KEY vllm/vllm-openai:latest --model meta-llama/Llama-3.1-8B-Instruct",
    serve_cmd="curl -s http://localhost:8080/v1/models",
    readiness_probe=probe(period_secs=15, failure_threshold=4),
    labels=["ai", "llm"],
)

local_resource(
    name="content-db",
    cmd="docker run --rm -p 5432:5432 -e POSTGRES_DB=content postgres:15",
    serve_cmd="pg_isready -h localhost -p 5432",
    readiness_probe=probe(period_secs=5, failure_threshold=12),
    labels=["database"],
)

local_resource(
    name="warm-models",
    cmd="python scripts/warm_models.py",
    deps=["./scripts/warm_models.py"],
    labels=["ai", "warmup"],
    resource_deps=["llm-gateway"],
)

# ---------------------------------------------------------------------------
# Live Update Rules
# ---------------------------------------------------------------------------
watch_file("./src")
watch_file("./prompts")
watch_file("./templates")

# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------
k8s_resource(
    workload="content-generator",
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

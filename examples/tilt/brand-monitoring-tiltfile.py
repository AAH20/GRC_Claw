"""
Tiltfile: Brand Monitoring Service
Monitors brand mentions across social media, news, and review platforms.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/brand-monitoring:latest",
    context="./services/brand-monitoring",
    dockerfile="./services/brand-monitoring/Dockerfile",
    live_update=[
        sync("./services/brand-monitoring/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/brand-monitoring/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "brand-monitoring",
    chart="./deploy/charts/brand-monitoring",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/brand-monitoring/values.yaml",
)

# Port-forward for local access
local_resource(
    "brand-monitoring-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/brand-monitoring 8080:8080",
    resource_deps=["brand-monitoring"],
)

# Live update for rapid iteration
local_resource(
    "brand-monitoring-hot-reload",
    serve_cmd="cd ./services/brand-monitoring && python -m src.main --reload",
    resource_deps=["brand-monitoring"],
)

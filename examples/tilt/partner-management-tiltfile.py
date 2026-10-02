"""
Tiltfile: Partner Management Service
Partner onboarding, relationship tracking, and co-marketing campaign management.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/partner-management:latest",
    context="./services/partner-management",
    dockerfile="./services/partner-management/Dockerfile",
    live_update=[
        sync("./services/partner-management/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/partner-management/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "partner-management",
    chart="./deploy/charts/partner-management",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/partner-management/values.yaml",
)

# Port-forward for local access
local_resource(
    "partner-management-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/partner-management 8086:8080",
    resource_deps=["partner-management"],
)

# Live update for rapid iteration
local_resource(
    "partner-management-hot-reload",
    serve_cmd="cd ./services/partner-management && python -m src.main --reload",
    resource_deps=["partner-management"],
)

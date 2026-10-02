"""
Tiltfile: Cross-Project Orchestrator
Coordinates and orchestrates all GRC Claw marketing services.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/cross-project-orchestrator:latest",
    context="./services/cross-project-orchestrator",
    dockerfile="./services/cross-project-orchestrator/Dockerfile",
    live_update=[
        sync("./services/cross-project-orchestrator/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/cross-project-orchestrator/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "cross-project-orchestrator",
    chart="./deploy/charts/cross-project-orchestrator",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/cross-project-orchestrator/values.yaml",
)

# Port-forward for local access
local_resource(
    "cross-project-orchestrator-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/cross-project-orchestrator 8094:8080",
    resource_deps=["cross-project-orchestrator"],
)

# Live update for rapid iteration
local_resource(
    "cross-project-orchestrator-hot-reload",
    serve_cmd="cd ./services/cross-project-orchestrator && python -m src.main --reload",
    resource_deps=["cross-project-orchestrator"],
)

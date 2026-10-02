"""
Tiltfile: Agency Marketing Service
Multi-client campaign management, reporting, and white-label marketing tools.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/agency-marketing:latest",
    context="./services/agency-marketing",
    dockerfile="./services/agency-marketing/Dockerfile",
    live_update=[
        sync("./services/agency-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/agency-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "agency-marketing",
    chart="./deploy/charts/agency-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/agency-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "agency-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/agency-marketing 8088:8080",
    resource_deps=["agency-marketing"],
)

# Live update for rapid iteration
local_resource(
    "agency-marketing-hot-reload",
    serve_cmd="cd ./services/agency-marketing && python -m src.main --reload",
    resource_deps=["agency-marketing"],
)

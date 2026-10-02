"""
Tiltfile: Affiliate Marketing Service
Affiliate tracking, commission management, and partner link optimization.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/affiliate-marketing:latest",
    context="./services/affiliate-marketing",
    dockerfile="./services/affiliate-marketing/Dockerfile",
    live_update=[
        sync("./services/affiliate-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/affiliate-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "affiliate-marketing",
    chart="./deploy/charts/affiliate-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/affiliate-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "affiliate-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/affiliate-marketing 8085:8080",
    resource_deps=["affiliate-marketing"],
)

# Live update for rapid iteration
local_resource(
    "affiliate-marketing-hot-reload",
    serve_cmd="cd ./services/affiliate-marketing && python -m src.main --reload",
    resource_deps=["affiliate-marketing"],
)

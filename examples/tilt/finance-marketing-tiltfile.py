"""
Tiltfile: Finance Marketing Service
Financial product promotion, lead generation, and compliance-aware campaigns.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/finance-marketing:latest",
    context="./services/finance-marketing",
    dockerfile="./services/finance-marketing/Dockerfile",
    live_update=[
        sync("./services/finance-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/finance-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "finance-marketing",
    chart="./deploy/charts/finance-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/finance-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "finance-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/finance-marketing 8091:8080",
    resource_deps=["finance-marketing"],
)

# Live update for rapid iteration
local_resource(
    "finance-marketing-hot-reload",
    serve_cmd="cd ./services/finance-marketing && python -m src.main --reload",
    resource_deps=["finance-marketing"],
)

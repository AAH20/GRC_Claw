"""
Tiltfile: Real Estate Marketing Service
Property listing promotion, virtual tours, and lead nurturing for real estate.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/real-estate-marketing:latest",
    context="./services/real-estate-marketing",
    dockerfile="./services/real-estate-marketing/Dockerfile",
    live_update=[
        sync("./services/real-estate-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/real-estate-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "real-estate-marketing",
    chart="./deploy/charts/real-estate-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/real-estate-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "real-estate-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/real-estate-marketing 8092:8080",
    resource_deps=["real-estate-marketing"],
)

# Live update for rapid iteration
local_resource(
    "real-estate-marketing-hot-reload",
    serve_cmd="cd ./services/real-estate-marketing && python -m src.main --reload",
    resource_deps=["real-estate-marketing"],
)

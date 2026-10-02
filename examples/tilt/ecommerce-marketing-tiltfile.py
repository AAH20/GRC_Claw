"""
Tiltfile: E-commerce Marketing Service
Product promotion, cart recovery, and personalized shopping experiences.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/ecommerce-marketing:latest",
    context="./services/ecommerce-marketing",
    dockerfile="./services/ecommerce-marketing/Dockerfile",
    live_update=[
        sync("./services/ecommerce-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/ecommerce-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "ecommerce-marketing",
    chart="./deploy/charts/ecommerce-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/ecommerce-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "ecommerce-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/ecommerce-marketing 8089:8080",
    resource_deps=["ecommerce-marketing"],
)

# Live update for rapid iteration
local_resource(
    "ecommerce-marketing-hot-reload",
    serve_cmd="cd ./services/ecommerce-marketing && python -m src.main --reload",
    resource_deps=["ecommerce-marketing"],
)

"""
Tiltfile: Market Research Service
Aggregates and analyzes market data, competitor intelligence, and consumer trends.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/market-research:latest",
    context="./services/market-research",
    dockerfile="./services/market-research/Dockerfile",
    live_update=[
        sync("./services/market-research/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/market-research/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "market-research",
    chart="./deploy/charts/market-research",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/market-research/values.yaml",
)

# Port-forward for local access
local_resource(
    "market-research-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/market-research 8081:8080",
    resource_deps=["market-research"],
)

# Live update for rapid iteration
local_resource(
    "market-research-hot-reload",
    serve_cmd="cd ./services/market-research && python -m src.main --reload",
    resource_deps=["market-research"],
)

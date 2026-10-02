"""
Tiltfile: Website Optimization Service
A/B testing, performance monitoring, and SEO optimization for websites.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/website-optimization:latest",
    context="./services/website-optimization",
    dockerfile="./services/website-optimization/Dockerfile",
    live_update=[
        sync("./services/website-optimization/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/website-optimization/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "website-optimization",
    chart="./deploy/charts/website-optimization",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/website-optimization/values.yaml",
)

# Port-forward for local access
local_resource(
    "website-optimization-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/website-optimization 8082:8080",
    resource_deps=["website-optimization"],
)

# Live update for rapid iteration
local_resource(
    "website-optimization-hot-reload",
    serve_cmd="cd ./services/website-optimization && python -m src.main --reload",
    resource_deps=["website-optimization"],
)

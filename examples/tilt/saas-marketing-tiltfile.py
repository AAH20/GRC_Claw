"""
Tiltfile: SaaS Marketing Service
Product-led growth, onboarding optimization, and churn reduction campaigns.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/saas-marketing:latest",
    context="./services/saas-marketing",
    dockerfile="./services/saas-marketing/Dockerfile",
    live_update=[
        sync("./services/saas-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/saas-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "saas-marketing",
    chart="./deploy/charts/saas-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/saas-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "saas-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/saas-marketing 8093:8080",
    resource_deps=["saas-marketing"],
)

# Live update for rapid iteration
local_resource(
    "saas-marketing-hot-reload",
    serve_cmd="cd ./services/saas-marketing && python -m src.main --reload",
    resource_deps=["saas-marketing"],
)

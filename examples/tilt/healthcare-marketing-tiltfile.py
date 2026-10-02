"""
Tiltfile: Healthcare Marketing Service
HIPAA-compliant patient engagement, provider marketing, and health education.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/healthcare-marketing:latest",
    context="./services/healthcare-marketing",
    dockerfile="./services/healthcare-marketing/Dockerfile",
    live_update=[
        sync("./services/healthcare-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/healthcare-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "healthcare-marketing",
    chart="./deploy/charts/healthcare-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/healthcare-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "healthcare-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/healthcare-marketing 8090:8080",
    resource_deps=["healthcare-marketing"],
)

# Live update for rapid iteration
local_resource(
    "healthcare-marketing-hot-reload",
    serve_cmd="cd ./services/healthcare-marketing && python -m src.main --reload",
    resource_deps=["healthcare-marketing"],
)

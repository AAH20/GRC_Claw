"""
Tiltfile: Conversational Marketing Service
Chatbots, conversational AI, and messaging automation for customer engagement.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/conversational-marketing:latest",
    context="./services/conversational-marketing",
    dockerfile="./services/conversational-marketing/Dockerfile",
    live_update=[
        sync("./services/conversational-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/conversational-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "conversational-marketing",
    chart="./deploy/charts/conversational-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/conversational-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "conversational-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/conversational-marketing 8083:8080",
    resource_deps=["conversational-marketing"],
)

# Live update for rapid iteration
local_resource(
    "conversational-marketing-hot-reload",
    serve_cmd="cd ./services/conversational-marketing && python -m src.main --reload",
    resource_deps=["conversational-marketing"],
)

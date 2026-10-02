"""
Tiltfile: Video Marketing Service
Video creation, optimization, and distribution across platforms.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/video-marketing:latest",
    context="./services/video-marketing",
    dockerfile="./services/video-marketing/Dockerfile",
    live_update=[
        sync("./services/video-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/video-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "video-marketing",
    chart="./deploy/charts/video-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/video-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "video-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/video-marketing 8084:8080",
    resource_deps=["video-marketing"],
)

# Live update for rapid iteration
local_resource(
    "video-marketing-hot-reload",
    serve_cmd="cd ./services/video-marketing && python -m src.main --reload",
    resource_deps=["video-marketing"],
)

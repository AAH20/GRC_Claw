"""
Tiltfile: SMB Marketing Service
Marketing automation tailored for small and medium-sized businesses.
"""

load("ext://helm_remote", "helm_remote")

# Build
docker_build(
    "ghcr.io/grc-claw/smb-marketing:latest",
    context="./services/smb-marketing",
    dockerfile="./services/smb-marketing/Dockerfile",
    live_update=[
        sync("./services/smb-marketing/src", "/app/src"),
        run("pip install -r /app/requirements.txt", trigger="./services/smb-marketing/requirements.txt"),
        restart_container(),
    ],
)

# Deploy
helm_remote(
    "smb-marketing",
    chart="./deploy/charts/smb-marketing",
    namespace="grc-claw",
    create_namespace=True,
    values="./deploy/charts/smb-marketing/values.yaml",
)

# Port-forward for local access
local_resource(
    "smb-marketing-port-forward",
    serve_cmd="kubectl port-forward -n grc-claw svc/smb-marketing 8087:8080",
    resource_deps=["smb-marketing"],
)

# Live update for rapid iteration
local_resource(
    "smb-marketing-hot-reload",
    serve_cmd="cd ./services/smb-marketing && python -m src.main --reload",
    resource_deps=["smb-marketing"],
)

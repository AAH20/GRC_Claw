"""
Tiltfile for Workflow Automation Service
=========================================
Build, deploy, and live-update configuration for the workflow automation
engine. Manages business process automation, task orchestration, and triggers.
"""

# ── Build ────────────────────────────────────────────────────────────────────

docker_build(
    "ghcr.io/acme/workflow-automation",
    context=".",
    dockerfile="Dockerfile",
    live_update=[
        sync("./src", "/app/src"),
        sync("./config", "/app/config"),
        run("pip install -r requirements.txt", trigger="requirements.txt"),
        restart_container(),
    ],
    build_args={"ENV": "production"},
    only=["src", "config", "requirements.txt"],
)

# ── Deploy ───────────────────────────────────────────────────────────────────

k8s_yaml("k8s/workflow-automation-deployment.yaml")
k8s_yaml("k8s/workflow-automation-service.yaml")
k8s_yaml("k8s/workflow-automation-hpa.yaml")

k8s_resource(
    "workflow-automation",
    port_forwards=["8080:8080"],
    resource_deps=["postgres", "redis", "kafka"],
)

# ── Live Update ──────────────────────────────────────────────────────────────

local_resource(
    "workflow-config-reload",
    serve_cmd="python scripts/watch_config.py --dir config/",
    resource_deps=["workflow-automation"],
    auto_init=False,
)

# ── Dependencies ─────────────────────────────────────────────────────────────

k8s_yaml("k8s/postgres.yaml")
k8s_yaml("k8s/redis.yaml")
k8s_yaml("k8s/kafka.yaml")

# ── Health Checks ────────────────────────────────────────────────────────────

probes = {
    "readiness": k8s_probe(
        "workflow-automation",
        http_get_path="/health/ready",
        http_get_port=8080,
        initial_delay_seconds=10,
        period_seconds=15,
    ),
    "liveness": k8s_probe(
        "workflow-automation",
        http_get_path="/health/live",
        http_get_port=8080,
        initial_delay_seconds=30,
        period_seconds=20,
    ),
}

# ── Environment ──────────────────────────────────────────────────────────────

config.define_string_list("ENV_VARS")
cfg = config.parse()

k8s_yaml(
    yaml.replace_all(
        "k8s/workflow-automation-deployment.yaml",
        "__REPLICAS__",
        str(cfg.get("replicas", 3)),
    )
)

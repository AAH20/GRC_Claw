"""
Tiltfile for Onboarding & Training Service
===========================================
Build, deploy, and live-update configuration for the onboarding and training
platform. Manages user onboarding flows, training modules, and progress tracking.
"""

# ── Build ────────────────────────────────────────────────────────────────────

docker_build(
    "ghcr.io/acme/onboarding-training",
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

k8s_yaml("k8s/onboarding-training-deployment.yaml")
k8s_yaml("k8s/onboarding-training-service.yaml")
k8s_yaml("k8s/onboarding-training-hpa.yaml")

k8s_resource(
    "onboarding-training",
    port_forwards=["8080:8080"],
    resource_deps=["postgres", "redis"],
)

# ── Live Update ──────────────────────────────────────────────────────────────

local_resource(
    "onboarding-config-reload",
    serve_cmd="python scripts/watch_config.py --dir config/",
    resource_deps=["onboarding-training"],
    auto_init=False,
)

# ── Dependencies ─────────────────────────────────────────────────────────────

k8s_yaml("k8s/postgres.yaml")
k8s_yaml("k8s/redis.yaml")

# ── Health Checks ────────────────────────────────────────────────────────────

probes = {
    "readiness": k8s_probe(
        "onboarding-training",
        http_get_path="/health/ready",
        http_get_port=8080,
        initial_delay_seconds=10,
        period_seconds=15,
    ),
    "liveness": k8s_probe(
        "onboarding-training",
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
        "k8s/onboarding-training-deployment.yaml",
        "__REPLICAS__",
        str(cfg.get("replicas", 3)),
    )
)

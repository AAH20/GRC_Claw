"""
Tiltfile for Marketing Personalization Service
===============================================
Build, deploy, and live-update configuration for the personalization engine.
Manages real-time content personalization, recommendations, and A/B testing.
"""

# ── Build ────────────────────────────────────────────────────────────────────

docker_build(
    "ghcr.io/acme/marketing-personalization",
    context=".",
    dockerfile="Dockerfile",
    live_update=[
        sync("./src", "/app/src"),
        sync("./models", "/app/models"),
        sync("./config", "/app/config"),
        run("pip install -r requirements.txt", trigger="requirements.txt"),
        restart_container(),
    ],
    build_args={"ENV": "production"},
    only=["src", "models", "config", "requirements.txt"],
)

# ── Deploy ───────────────────────────────────────────────────────────────────

k8s_yaml("k8s/marketing-personalization-deployment.yaml")
k8s_yaml("k8s/marketing-personalization-service.yaml")
k8s_yaml("k8s/marketing-personalization-hpa.yaml")

k8s_resource(
    "marketing-personalization",
    port_forwards=["8080:8080"],
    resource_deps=["postgres", "redis", "kafka"],
)

# ── Live Update ──────────────────────────────────────────────────────────────

local_resource(
    "personalization-model-reload",
    serve_cmd="python scripts/watch_models.py --dir models/",
    resource_deps=["marketing-personalization"],
    auto_init=False,
)

local_resource(
    "personalization-config-reload",
    serve_cmd="python scripts/watch_config.py --dir config/",
    resource_deps=["marketing-personalization"],
    auto_init=False,
)

# ── Dependencies ─────────────────────────────────────────────────────────────

k8s_yaml("k8s/postgres.yaml")
k8s_yaml("k8s/redis.yaml")
k8s_yaml("k8s/kafka.yaml")

# ── Health Checks ────────────────────────────────────────────────────────────

probes = {
    "readiness": k8s_probe(
        "marketing-personalization",
        http_get_path="/health/ready",
        http_get_port=8080,
        initial_delay_seconds=10,
        period_seconds=15,
    ),
    "liveness": k8s_probe(
        "marketing-personalization",
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
        "k8s/marketing-personalization-deployment.yaml",
        "__REPLICAS__",
        str(cfg.get("replicas", 3)),
    )
)

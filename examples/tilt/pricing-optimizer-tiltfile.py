"""
Tiltfile for Pricing Optimizer Service
=======================================
Build, deploy, and live-update configuration for the dynamic pricing
optimization engine. Runs ML-based price recommendations and A/B testing.
"""

# ── Build ────────────────────────────────────────────────────────────────────

docker_build(
    "ghcr.io/acme/pricing-optimizer",
    context=".",
    dockerfile="Dockerfile",
    live_update=[
        sync("./src", "/app/src"),
        sync("./models", "/app/models"),
        sync("./config", "/app/config"),
        run("pip install -r requirements.txt", trigger="requirements.txt"),
        restart_container(),
    ],
    build_args={"ENV": "production", "MODEL_VERSION": "v2"},
    only=["src", "models", "config", "requirements.txt"],
)

# ── Deploy ───────────────────────────────────────────────────────────────────

k8s_yaml("k8s/pricing-optimizer-deployment.yaml")
k8s_yaml("k8s/pricing-optimizer-service.yaml")
k8s_yaml("k8s/pricing-optimizer-hpa.yaml")

k8s_resource(
    "pricing-optimizer",
    port_forwards=["8080:8080"],
    resource_deps=["postgres", "redis", "kafka"],
)

# ── Live Update ──────────────────────────────────────────────────────────────

local_resource(
    "pricing-model-hot-reload",
    serve_cmd="python scripts/watch_models.py --dir models/ --signal",
    resource_deps=["pricing-optimizer"],
    auto_init=False,
)

local_resource(
    "pricing-config-reload",
    serve_cmd="python scripts/watch_config.py --dir config/",
    resource_deps=["pricing-optimizer"],
    auto_init=False,
)

# ── Dependencies ─────────────────────────────────────────────────────────────

k8s_yaml("k8s/postgres.yaml")
k8s_yaml("k8s/redis.yaml")
k8s_yaml("k8s/kafka.yaml")

# ── Health Checks ────────────────────────────────────────────────────────────

probes = {
    "readiness": k8s_probe(
        "pricing-optimizer",
        http_get_path="/health/ready",
        http_get_port=8080,
        initial_delay_seconds=10,
        period_seconds=15,
    ),
    "liveness": k8s_probe(
        "pricing-optimizer",
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
        "k8s/pricing-optimizer-deployment.yaml",
        "__REPLICAS__",
        str(cfg.get("replicas", 3)),
    )
)

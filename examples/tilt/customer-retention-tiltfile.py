"""
Tiltfile for Customer Retention Service
========================================
Build, deploy, and live-update configuration for the customer retention
microservice. Handles churn prediction, retention campaigns, and customer
lifecycle management.
"""

# ── Build ────────────────────────────────────────────────────────────────────

docker_build(
    "ghcr.io/acme/customer-retention",
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

k8s_yaml("k8s/customer-retention-deployment.yaml")
k8s_yaml("k8s/customer-retention-service.yaml")
k8s_yaml("k8s/customer-retention-hpa.yaml")

k8s_resource(
    "customer-retention",
    port_forwards=["8080:8080"],
    resource_deps=["postgres", "redis"],
)

# ── Live Update ──────────────────────────────────────────────────────────────

local_resource(
    "retention-model-reload",
    serve_cmd="python scripts/reload_models.py --watch",
    resource_deps=["customer-retention"],
    auto_init=False,
)

# ── Dependencies ─────────────────────────────────────────────────────────────

k8s_yaml("k8s/postgres.yaml")
k8s_yaml("k8s/redis.yaml")

# ── Health Checks ────────────────────────────────────────────────────────────

probes = {
    "readiness": k8s_probe(
        "customer-retention",
        http_get_path="/health/ready",
        http_get_port=8080,
        initial_delay_seconds=10,
        period_seconds=15,
    ),
    "liveness": k8s_probe(
        "customer-retention",
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
        "k8s/customer-retention-deployment.yaml",
        "__REPLICAS__",
        str(cfg.get("replicas", 3)),
    )
)

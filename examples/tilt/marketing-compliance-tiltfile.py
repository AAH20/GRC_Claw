"""
Tiltfile for Marketing Compliance Service
==========================================
Build, deploy, and live-update configuration for the marketing compliance
engine. Manages consent, GDPR/CCPA compliance, and regulatory checks.
"""

# ── Build ────────────────────────────────────────────────────────────────────

docker_build(
    "ghcr.io/acme/marketing-compliance",
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

k8s_yaml("k8s/marketing-compliance-deployment.yaml")
k8s_yaml("k8s/marketing-compliance-service.yaml")
k8s_yaml("k8s/marketing-compliance-hpa.yaml")

k8s_resource(
    "marketing-compliance",
    port_forwards=["8080:8080"],
    resource_deps=["postgres", "redis"],
)

# ── Live Update ──────────────────────────────────────────────────────────────

local_resource(
    "compliance-rules-reload",
    serve_cmd="python scripts/watch_rules.py --dir config/rules/",
    resource_deps=["marketing-compliance"],
    auto_init=False,
)

# ── Dependencies ─────────────────────────────────────────────────────────────

k8s_yaml("k8s/postgres.yaml")
k8s_yaml("k8s/redis.yaml")

# ── Health Checks ────────────────────────────────────────────────────────────

probes = {
    "readiness": k8s_probe(
        "marketing-compliance",
        http_get_path="/health/ready",
        http_get_port=8080,
        initial_delay_seconds=10,
        period_seconds=15,
    ),
    "liveness": k8s_probe(
        "marketing-compliance",
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
        "k8s/marketing-compliance-deployment.yaml",
        "__REPLICAS__",
        str(cfg.get("replicas", 3)),
    )
)

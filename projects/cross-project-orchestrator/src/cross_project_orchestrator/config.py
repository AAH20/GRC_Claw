"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="ORCHESTRATOR_", env_file=".env")

    environment: str = "development"
    port: int = 8080
    log_level: str = "INFO"
    workers: int = 4


class KubernetesSettings(BaseSettings):
    """Kubernetes integration settings."""

    model_config = SettingsConfigDict(env_prefix="KUBERNETES_", env_file=".env")

    enabled: bool = True
    namespace: str = "default"
    in_cluster: bool = True
    kubeconfig_path: str | None = None


class TerraformSettings(BaseSettings):
    """Terraform integration settings."""

    model_config = SettingsConfigDict(env_prefix="TERRAFORM_", env_file=".env")

    enabled: bool = True
    state_path: str = "./tfstate"
    workspace: str = "default"
    auto_approve: bool = False


class PrometheusSettings(BaseSettings):
    """Prometheus integration settings."""

    model_config = SettingsConfigDict(env_prefix="PROMETHEUS_", env_file=".env")

    enabled: bool = True
    url: str = "http://localhost:9090"
    scrape_interval: int = 15
    timeout: int = 10


class Settings(BaseSettings):
    """Root settings aggregating all sub-configurations."""

    model_config = SettingsConfigDict(env_file=".env")

    orchestrator: OrchestratorSettings = OrchestratorSettings()
    kubernetes: KubernetesSettings = KubernetesSettings()
    terraform: TerraformSettings = TerraformSettings()
    prometheus: PrometheusSettings = PrometheusSettings()


def get_settings() -> Settings:
    """Get the application settings singleton.

    Returns:
        Application settings instance.
    """
    return Settings()

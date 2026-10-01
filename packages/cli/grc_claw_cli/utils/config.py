"""Configuration management for GRC_Claw CLI."""
import json
import os
from pathlib import Path
from typing import Any, Optional


DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.grc-claw.a2z-soc.com/v1",
    "gateway_host": "127.0.0.1",
    "gateway_port": 18791,
    "gateway_token": "",
    "timeout": 30,
    "output_format": "table",
    "framework": "iso27001",
    "org": "my-org",
    "evidence_dir": "./compliance-evidence",
    "retention_days": 365,
}


class Config:
    """Manages CLI configuration stored in ~/.grc_claw/config.json."""

    CONFIG_DIR = Path.home() / ".grc_claw"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    def __init__(self):
        self._data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self) -> None:
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    self._data.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass

    def save(self) -> None:
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    @property
    def api_key(self) -> str:
        return self._data.get("api_key") or os.environ.get("GRC_CLAW_API_KEY", "")

    @property
    def gateway_token(self) -> str:
        return self._data.get("gateway_token") or os.environ.get("GRC_CLAW_GATEWAY_TOKEN", "")

    @property
    def base_url(self) -> str:
        return self._data.get("base_url", DEFAULT_CONFIG["base_url"])

    def as_dict(self) -> dict:
        return dict(self._data)

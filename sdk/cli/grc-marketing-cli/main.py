"""GRC Marketing CLI — Command-line interface for the GRC Marketing API."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

import requests

from . import campaigns, journeys, leads, analytics


DEFAULT_BASE_URL = "https://api.grc.example.com"
CONFIG_DIR = os.path.expanduser("~/.config/grc-marketing")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_config() -> dict[str, Any]:
    """Load CLI configuration from disk.

    Returns:
        Configuration dictionary.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict[str, Any]) -> None:
    """Save CLI configuration to disk.

    Args:
        config: Configuration dictionary to save.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_base_url() -> str:
    """Get the API base URL from config or environment.

    Returns:
        The base URL.
    """
    return os.environ.get("GRC_BASE_URL") or load_config().get("base_url") or DEFAULT_BASE_URL


def get_api_key() -> Optional[str]:
    """Get the API key from config or environment.

    Returns:
        The API key, or None.
    """
    return os.environ.get("GRC_API_KEY", load_config().get("api_key"))


def make_client() -> requests.Session:
    """Create an authenticated requests session.

    Returns:
        Configured session.
    """
    session = requests.Session()
    api_key = get_api_key()
    if api_key:
        session.headers.update({"Authorization": f"Bearer {api_key}"})
    session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    return session


def print_json(data: Any) -> None:
    """Pretty-print JSON data.

    Args:
        data: Data to print.
    """
    print(json.dumps(data, indent=2, default=str))


def handle_error(error: requests.RequestException) -> None:
    """Handle and display request errors.

    Args:
        error: The request exception.
    """
    if error.response is not None:
        try:
            body = error.response.json()
            print(f"Error [{error.response.status_code}]: {body.get('message', body)}", file=sys.stderr)
        except (ValueError, AttributeError):
            print(f"Error [{error.response.status_code}]: {error.response.text}", file=sys.stderr)
    else:
        print(f"Error: {error}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: grc-marketing <command> [options]")
        print("")
        print("Commands:")
        print("  auth      Manage authentication")
        print("  campaigns Manage campaigns")
        print("  leads     Manage leads")
        print("  journeys  Manage journeys")
        print("  analytics View analytics")
        print("")
        print("Run 'grc-marketing <command> --help' for more information.")
        sys.exit(1)

    command = sys.argv[1]
    remaining_args = sys.argv[2:]

    commands = {
        "auth": _cmd_auth,
        "campaigns": campaigns.main,
        "leads": leads.main,
        "journeys": journeys.main,
        "analytics": analytics.main,
    }

    handler = commands.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(f"Available commands: {', '.join(commands.keys())}", file=sys.stderr)
        sys.exit(1)

    handler(remaining_args)


def _cmd_auth(args: list[str]) -> None:
    """Handle auth subcommands.

    Args:
        args: Command-line arguments.
    """
    if not args or args[0] == "--help":
        print("Usage: grc-marketing auth <subcommand>")
        print("")
        print("Subcommands:")
        print("  login     Authenticate and save credentials")
        print("  logout    Clear saved credentials")
        print("  status    Show authentication status")
        return

    subcmd = args[0]

    if subcmd == "login":
        api_key = input("API Key: ").strip()
        if not api_key:
            print("Error: API key is required", file=sys.stderr)
            sys.exit(1)
        base_url = input(f"Base URL [{DEFAULT_BASE_URL}]: ").strip() or DEFAULT_BASE_URL
        config = load_config()
        config["api_key"] = api_key
        config["base_url"] = base_url
        save_config(config)
        print("Credentials saved.")
    elif subcmd == "logout":
        config = load_config()
        config.pop("api_key", None)
        save_config(config)
        print("Credentials cleared.")
    elif subcmd == "status":
        config = load_config()
        if config.get("api_key"):
            print(f"Authenticated (base URL: {config.get('base_url', DEFAULT_BASE_URL)})")
        else:
            print("Not authenticated. Run 'grc-marketing auth login' to authenticate.")
    else:
        print(f"Unknown auth subcommand: {subcmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

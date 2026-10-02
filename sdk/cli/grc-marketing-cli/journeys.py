"""Journey commands for the GRC Marketing CLI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests

from .main import get_base_url, get_api_key, make_client, print_json, handle_error


def main(args: list[str]) -> None:
    """Handle journey subcommands.

    Args:
        args: Command-line arguments.
    """
    parser = argparse.ArgumentParser(prog="grc-marketing journeys", description="Manage journeys")
    subparsers = parser.add_subparsers(dest="action")

    # list
    list_parser = subparsers.add_parser("list", help="List journeys")
    list_parser.add_argument("--page", type=int, default=1)
    list_parser.add_argument("--per-page", type=int, default=20)
    list_parser.add_argument("--status", choices=["draft", "active", "paused", "completed"])

    # get
    get_parser = subparsers.add_parser("get", help="Get a journey")
    get_parser.add_argument("id", help="Journey ID")

    # create
    create_parser = subparsers.add_parser("create", help="Create a journey")
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument("--description", default="")
    create_parser.add_argument("--status", default="draft")
    create_parser.add_argument("--steps", help="JSON array of steps")
    create_parser.add_argument("--tags", nargs="*", default=[])

    # update
    update_parser = subparsers.add_parser("update", help="Update a journey")
    update_parser.add_argument("id", help="Journey ID")
    update_parser.add_argument("--name")
    update_parser.add_argument("--description")
    update_parser.add_argument("--status")
    update_parser.add_argument("--steps", help="JSON array of steps")
    update_parser.add_argument("--tags", nargs="*")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a journey")
    delete_parser.add_argument("id", help="Journey ID")

    # activate
    activate_parser = subparsers.add_parser("activate", help="Activate a journey")
    activate_parser.add_argument("id", help="Journey ID")

    # pause
    pause_parser = subparsers.add_parser("pause", help="Pause a journey")
    pause_parser.add_argument("id", help="Journey ID")

    # complete
    complete_parser = subparsers.add_parser("complete", help="Complete a journey")
    complete_parser.add_argument("id", help="Journey ID")

    parsed = parser.parse_args(args)

    if not parsed.action:
        parser.print_help()
        return

    try:
        if parsed.action == "list":
            _list_journeys(parsed)
        elif parsed.action == "get":
            _get_journey(parsed)
        elif parsed.action == "create":
            _create_journey(parsed)
        elif parsed.action == "update":
            _update_journey(parsed)
        elif parsed.action == "delete":
            _delete_journey(parsed)
        elif parsed.action == "activate":
            _update_status(parsed.id, "active")
        elif parsed.action == "pause":
            _update_status(parsed.id, "paused")
        elif parsed.action == "complete":
            _update_status(parsed.id, "completed")
    except requests.RequestException as e:
        handle_error(e)


def _list_journeys(args: argparse.Namespace) -> None:
    """List journeys.

    Args:
        args: Parsed arguments.
    """
    params: dict[str, Any] = {"page": args.page, "per_page": args.per_page}
    if args.status:
        params["status"] = args.status

    client = make_client()
    resp = client.get(f"{get_base_url()}/journeys", params=params)
    resp.raise_for_status()
    print_json(resp.json())


def _get_journey(args: argparse.Namespace) -> None:
    """Get a journey.

    Args:
        args: Parsed arguments.
    """
    client = make_client()
    resp = client.get(f"{get_base_url()}/journeys/{args.id}")
    resp.raise_for_status()
    print_json(resp.json())


def _create_journey(args: argparse.Namespace) -> None:
    """Create a journey.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {
        "name": args.name,
        "description": args.description,
        "status": args.status,
        "tags": args.tags,
    }
    if args.steps:
        try:
            payload["steps"] = json.loads(args.steps)
        except json.JSONDecodeError:
            print("Error: --steps must be valid JSON", file=sys.stderr)
            sys.exit(1)

    client = make_client()
    resp = client.post(f"{get_base_url()}/journeys", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _update_journey(args: argparse.Namespace) -> None:
    """Update a journey.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {}
    if args.name:
        payload["name"] = args.name
    if args.description:
        payload["description"] = args.description
    if args.status:
        payload["status"] = args.status
    if args.steps:
        try:
            payload["steps"] = json.loads(args.steps)
        except json.JSONDecodeError:
            print("Error: --steps must be valid JSON", file=sys.stderr)
            sys.exit(1)
    if args.tags:
        payload["tags"] = args.tags

    client = make_client()
    resp = client.patch(f"{get_base_url()}/journeys/{args.id}", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _delete_journey(args: argparse.Namespace) -> None:
    """Delete a journey.

    Args:
        args: Parsed arguments.
    """
    client = make_client()
    resp = client.delete(f"{get_base_url()}/journeys/{args.id}")
    resp.raise_for_status()
    print(f"Journey {args.id} deleted.")


def _update_status(journey_id: str, status: str) -> None:
    """Update journey status.

    Args:
        journey_id: The journey ID.
        status: The new status.
    """
    client = make_client()
    resp = client.patch(f"{get_base_url()}/journeys/{journey_id}", json={"status": status})
    resp.raise_for_status()
    print_json(resp.json())

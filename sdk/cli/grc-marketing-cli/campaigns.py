"""Campaign commands for the GRC Marketing CLI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests

from .main import get_base_url, get_api_key, make_client, print_json, handle_error


def main(args: list[str]) -> None:
    """Handle campaign subcommands.

    Args:
        args: Command-line arguments.
    """
    parser = argparse.ArgumentParser(prog="grc-marketing campaigns", description="Manage campaigns")
    subparsers = parser.add_subparsers(dest="action")

    # list
    list_parser = subparsers.add_parser("list", help="List campaigns")
    list_parser.add_argument("--page", type=int, default=1)
    list_parser.add_argument("--per-page", type=int, default=20)
    list_parser.add_argument("--status", choices=["draft", "active", "paused", "completed", "archived"])
    list_parser.add_argument("--channel", choices=["email", "sms", "push", "social", "web"])

    # get
    get_parser = subparsers.add_parser("get", help="Get a campaign")
    get_parser.add_argument("id", help="Campaign ID")

    # create
    create_parser = subparsers.add_parser("create", help="Create a campaign")
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument("--description", default="")
    create_parser.add_argument("--channel", default="email")
    create_parser.add_argument("--status", default="draft")
    create_parser.add_argument("--start-date")
    create_parser.add_argument("--end-date")
    create_parser.add_argument("--budget", type=float, default=0.0)
    create_parser.add_argument("--tags", nargs="*", default=[])

    # update
    update_parser = subparsers.add_parser("update", help="Update a campaign")
    update_parser.add_argument("id", help="Campaign ID")
    update_parser.add_argument("--name")
    update_parser.add_argument("--description")
    update_parser.add_argument("--status")
    update_parser.add_argument("--start-date")
    update_parser.add_argument("--end-date")
    update_parser.add_argument("--budget", type=float)
    update_parser.add_argument("--tags", nargs="*")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a campaign")
    delete_parser.add_argument("id", help="Campaign ID")

    # activate
    activate_parser = subparsers.add_parser("activate", help="Activate a campaign")
    activate_parser.add_argument("id", help="Campaign ID")

    # pause
    pause_parser = subparsers.add_parser("pause", help="Pause a campaign")
    pause_parser.add_argument("id", help="Campaign ID")

    # complete
    complete_parser = subparsers.add_parser("complete", help="Complete a campaign")
    complete_parser.add_argument("id", help="Campaign ID")

    # archive
    archive_parser = subparsers.add_parser("archive", help="Archive a campaign")
    archive_parser.add_argument("id", help="Campaign ID")

    parsed = parser.parse_args(args)

    if not parsed.action:
        parser.print_help()
        return

    try:
        if parsed.action == "list":
            _list_campaigns(parsed)
        elif parsed.action == "get":
            _get_campaign(parsed)
        elif parsed.action == "create":
            _create_campaign(parsed)
        elif parsed.action == "update":
            _update_campaign(parsed)
        elif parsed.action == "delete":
            _delete_campaign(parsed)
        elif parsed.action == "activate":
            _update_status(parsed.id, "active")
        elif parsed.action == "pause":
            _update_status(parsed.id, "paused")
        elif parsed.action == "complete":
            _update_status(parsed.id, "completed")
        elif parsed.action == "archive":
            _update_status(parsed.id, "archived")
    except requests.RequestException as e:
        handle_error(e)


def _list_campaigns(args: argparse.Namespace) -> None:
    """List campaigns.

    Args:
        args: Parsed arguments.
    """
    params: dict[str, Any] = {"page": args.page, "per_page": args.per_page}
    if args.status:
        params["status"] = args.status
    if args.channel:
        params["channel"] = args.channel

    client = make_client()
    resp = client.get(f"{get_base_url()}/campaigns", params=params)
    resp.raise_for_status()
    print_json(resp.json())


def _get_campaign(args: argparse.Namespace) -> None:
    """Get a campaign.

    Args:
        args: Parsed arguments.
    """
    client = make_client()
    resp = client.get(f"{get_base_url()}/campaigns/{args.id}")
    resp.raise_for_status()
    print_json(resp.json())


def _create_campaign(args: argparse.Namespace) -> None:
    """Create a campaign.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {
        "name": args.name,
        "description": args.description,
        "channel": args.channel,
        "status": args.status,
        "budget": args.budget,
        "tags": args.tags,
    }
    if args.start_date:
        payload["start_date"] = args.start_date
    if args.end_date:
        payload["end_date"] = args.end_date

    client = make_client()
    resp = client.post(f"{get_base_url()}/campaigns", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _update_campaign(args: argparse.Namespace) -> None:
    """Update a campaign.

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
    if args.start_date:
        payload["start_date"] = args.start_date
    if args.end_date:
        payload["end_date"] = args.end_date
    if args.budget is not None:
        payload["budget"] = args.budget
    if args.tags:
        payload["tags"] = args.tags

    client = make_client()
    resp = client.patch(f"{get_base_url()}/campaigns/{args.id}", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _delete_campaign(args: argparse.Namespace) -> None:
    """Delete a campaign.

    Args:
        args: Parsed arguments.
    """
    client = make_client()
    resp = client.delete(f"{get_base_url()}/campaigns/{args.id}")
    resp.raise_for_status()
    print(f"Campaign {args.id} deleted.")


def _update_status(campaign_id: str, status: str) -> None:
    """Update campaign status.

    Args:
        campaign_id: The campaign ID.
        status: The new status.
    """
    client = make_client()
    resp = client.patch(f"{get_base_url()}/campaigns/{campaign_id}", json={"status": status})
    resp.raise_for_status()
    print_json(resp.json())

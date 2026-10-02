"""Lead commands for the GRC Marketing CLI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests

from .main import get_base_url, get_api_key, make_client, print_json, handle_error


def main(args: list[str]) -> None:
    """Handle lead subcommands.

    Args:
        args: Command-line arguments.
    """
    parser = argparse.ArgumentParser(prog="grc-marketing leads", description="Manage leads")
    subparsers = parser.add_subparsers(dest="action")

    # list
    list_parser = subparsers.add_parser("list", help="List leads")
    list_parser.add_argument("--page", type=int, default=1)
    list_parser.add_argument("--per-page", type=int, default=20)
    list_parser.add_argument("--status", choices=["new", "contacted", "qualified", "converted", "lost"])
    list_parser.add_argument("--source")

    # get
    get_parser = subparsers.add_parser("get", help="Get a lead")
    get_parser.add_argument("id", help="Lead ID")

    # create
    create_parser = subparsers.add_parser("create", help="Create a lead")
    create_parser.add_argument("--email", required=True)
    create_parser.add_argument("--first-name", default="")
    create_parser.add_argument("--last-name", default="")
    create_parser.add_argument("--phone", default="")
    create_parser.add_argument("--company", default="")
    create_parser.add_argument("--source", default="")
    create_parser.add_argument("--status", default="new")
    create_parser.add_argument("--tags", nargs="*", default=[])

    # update
    update_parser = subparsers.add_parser("update", help="Update a lead")
    update_parser.add_argument("id", help="Lead ID")
    update_parser.add_argument("--email")
    update_parser.add_argument("--first-name")
    update_parser.add_argument("--last-name")
    update_parser.add_argument("--phone")
    update_parser.add_argument("--company")
    update_parser.add_argument("--source")
    update_parser.add_argument("--status")
    update_parser.add_argument("--tags", nargs="*")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a lead")
    delete_parser.add_argument("id", help="Lead ID")

    # qualify
    qualify_parser = subparsers.add_parser("qualify", help="Qualify a lead")
    qualify_parser.add_argument("id", help="Lead ID")

    # convert
    convert_parser = subparsers.add_parser("convert", help="Convert a lead")
    convert_parser.add_argument("id", help="Lead ID")

    # mark-lost
    lost_parser = subparsers.add_parser("mark-lost", help="Mark a lead as lost")
    lost_parser.add_argument("id", help="Lead ID")

    parsed = parser.parse_args(args)

    if not parsed.action:
        parser.print_help()
        return

    try:
        if parsed.action == "list":
            _list_leads(parsed)
        elif parsed.action == "get":
            _get_lead(parsed)
        elif parsed.action == "create":
            _create_lead(parsed)
        elif parsed.action == "update":
            _update_lead(parsed)
        elif parsed.action == "delete":
            _delete_lead(parsed)
        elif parsed.action == "qualify":
            _update_status(parsed.id, "qualified")
        elif parsed.action == "convert":
            _update_status(parsed.id, "converted")
        elif parsed.action == "mark-lost":
            _update_status(parsed.id, "lost")
    except requests.RequestException as e:
        handle_error(e)


def _list_leads(args: argparse.Namespace) -> None:
    """List leads.

    Args:
        args: Parsed arguments.
    """
    params: dict[str, Any] = {"page": args.page, "per_page": args.per_page}
    if args.status:
        params["status"] = args.status
    if args.source:
        params["source"] = args.source

    client = make_client()
    resp = client.get(f"{get_base_url()}/leads", params=params)
    resp.raise_for_status()
    print_json(resp.json())


def _get_lead(args: argparse.Namespace) -> None:
    """Get a lead.

    Args:
        args: Parsed arguments.
    """
    client = make_client()
    resp = client.get(f"{get_base_url()}/leads/{args.id}")
    resp.raise_for_status()
    print_json(resp.json())


def _create_lead(args: argparse.Namespace) -> None:
    """Create a lead.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {
        "email": args.email,
        "first_name": args.first_name,
        "last_name": args.last_name,
        "phone": args.phone,
        "company": args.company,
        "source": args.source,
        "status": args.status,
        "tags": args.tags,
    }

    client = make_client()
    resp = client.post(f"{get_base_url()}/leads", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _update_lead(args: argparse.Namespace) -> None:
    """Update a lead.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {}
    if args.email:
        payload["email"] = args.email
    if args.first_name:
        payload["first_name"] = args.first_name
    if args.last_name:
        payload["last_name"] = args.last_name
    if args.phone:
        payload["phone"] = args.phone
    if args.company:
        payload["company"] = args.company
    if args.source:
        payload["source"] = args.source
    if args.status:
        payload["status"] = args.status
    if args.tags:
        payload["tags"] = args.tags

    client = make_client()
    resp = client.patch(f"{get_base_url()}/leads/{args.id}", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _delete_lead(args: argparse.Namespace) -> None:
    """Delete a lead.

    Args:
        args: Parsed arguments.
    """
    client = make_client()
    resp = client.delete(f"{get_base_url()}/leads/{args.id}")
    resp.raise_for_status()
    print(f"Lead {args.id} deleted.")


def _update_status(lead_id: str, status: str) -> None:
    """Update lead status.

    Args:
        lead_id: The lead ID.
        status: The new status.
    """
    client = make_client()
    resp = client.patch(f"{get_base_url()}/leads/{lead_id}", json={"status": status})
    resp.raise_for_status()
    print_json(resp.json())

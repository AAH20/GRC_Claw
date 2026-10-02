"""Analytics commands for the GRC Marketing CLI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests

from .main import get_base_url, get_api_key, make_client, print_json, handle_error


def main(args: list[str]) -> None:
    """Handle analytics subcommands.

    Args:
        args: Command-line arguments.
    """
    parser = argparse.ArgumentParser(prog="grc-marketing analytics", description="View analytics")
    subparsers = parser.add_subparsers(dest="action")

    # report
    report_parser = subparsers.add_parser("report", help="Get analytics report")
    report_parser.add_argument("--start-date")
    report_parser.add_argument("--end-date")
    report_parser.add_argument("--metrics", nargs="*")
    report_parser.add_argument("--dimensions", nargs="*")

    # campaign-performance
    campaign_parser = subparsers.add_parser("campaign-performance", help="Get campaign performance")
    campaign_parser.add_argument("--start-date")
    campaign_parser.add_argument("--end-date")
    campaign_parser.add_argument("--campaign-ids", nargs="*")

    # lead-funnel
    funnel_parser = subparsers.add_parser("lead-funnel", help="Get lead funnel analytics")
    funnel_parser.add_argument("--start-date")
    funnel_parser.add_argument("--end-date")

    # channel-performance
    channel_parser = subparsers.add_parser("channel-performance", help="Get channel performance")
    channel_parser.add_argument("--start-date")
    channel_parser.add_argument("--end-date")

    # journey-analytics
    journey_parser = subparsers.add_parser("journey-analytics", help="Get journey analytics")
    journey_parser.add_argument("journey_id", help="Journey ID")
    journey_parser.add_argument("--start-date")
    journey_parser.add_argument("--end-date")

    parsed = parser.parse_args(args)

    if not parsed.action:
        parser.print_help()
        return

    try:
        if parsed.action == "report":
            _get_report(parsed)
        elif parsed.action == "campaign-performance":
            _get_campaign_performance(parsed)
        elif parsed.action == "lead-funnel":
            _get_lead_funnel(parsed)
        elif parsed.action == "channel-performance":
            _get_channel_performance(parsed)
        elif parsed.action == "journey-analytics":
            _get_journey_analytics(parsed)
    except requests.RequestException as e:
        handle_error(e)


def _get_report(args: argparse.Namespace) -> None:
    """Get analytics report.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {}
    if args.start_date:
        payload["start_date"] = args.start_date
    if args.end_date:
        payload["end_date"] = args.end_date
    if args.metrics:
        payload["metrics"] = args.metrics
    if args.dimensions:
        payload["dimensions"] = args.dimensions

    client = make_client()
    resp = client.post(f"{get_base_url()}/analytics/report", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _get_campaign_performance(args: argparse.Namespace) -> None:
    """Get campaign performance.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {
        "metrics": ["impressions", "clicks", "conversions", "spend", "revenue"],
        "dimensions": ["campaign_id", "campaign_name"],
    }
    if args.start_date:
        payload["start_date"] = args.start_date
    if args.end_date:
        payload["end_date"] = args.end_date
    if args.campaign_ids:
        payload["filters"] = {"campaign_id": args.campaign_ids}

    client = make_client()
    resp = client.post(f"{get_base_url()}/analytics/campaigns", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _get_lead_funnel(args: argparse.Namespace) -> None:
    """Get lead funnel analytics.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {
        "metrics": ["total_leads", "qualified_leads", "converted_leads", "conversion_rate"],
        "dimensions": ["stage"],
    }
    if args.start_date:
        payload["start_date"] = args.start_date
    if args.end_date:
        payload["end_date"] = args.end_date

    client = make_client()
    resp = client.post(f"{get_base_url()}/analytics/lead-funnel", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _get_channel_performance(args: argparse.Namespace) -> None:
    """Get channel performance.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {
        "metrics": ["impressions", "clicks", "conversions", "spend", "revenue", "roas"],
        "dimensions": ["channel"],
    }
    if args.start_date:
        payload["start_date"] = args.start_date
    if args.end_date:
        payload["end_date"] = args.end_date

    client = make_client()
    resp = client.post(f"{get_base_url()}/analytics/channels", json=payload)
    resp.raise_for_status()
    print_json(resp.json())


def _get_journey_analytics(args: argparse.Namespace) -> None:
    """Get journey analytics.

    Args:
        args: Parsed arguments.
    """
    payload: dict[str, Any] = {
        "metrics": ["enrollments", "completions", "drop_offs", "conversion_rate"],
        "dimensions": ["step"],
        "filters": {"journey_id": args.journey_id},
    }
    if args.start_date:
        payload["start_date"] = args.start_date
    if args.end_date:
        payload["end_date"] = args.end_date

    client = make_client()
    resp = client.post(f"{get_base_url()}/analytics/journeys", json=payload)
    resp.raise_for_status()
    print_json(resp.json())

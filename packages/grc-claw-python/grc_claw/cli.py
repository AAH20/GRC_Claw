"""CLI interface for GRC_Claw SDK."""

import argparse
import json
import sys
import os

from grc_claw.client import GRCClient
from grc_claw.exceptions import GRCError
from grc_claw import __version__


def _get_client(args) -> GRCClient:
    """Create a GRCClient from CLI args."""
    api_key = args.api_key or os.environ.get("GRC_CLAW_API_KEY")
    if not api_key:
        print("Error: API key required. Set GRC_CLAW_API_KEY or use --api-key", file=sys.stderr)
        sys.exit(1)

    return GRCClient(
        api_key=api_key,
        base_url=args.base_url,
        timeout=args.timeout,
    )


def _print_json(data, pretty=True):
    """Print JSON output."""
    if pretty:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(json.dumps(data, default=str))


def cmd_scan(args):
    """Handle the 'scan' command."""
    client = _get_client(args)
    try:
        result = client.scan(
            path=args.path,
            frameworks=args.frameworks,
            severity_threshold=args.severity,
        )
        _print_json(result)

        total = result.get("total_findings", 0)
        if total > 0:
            print(f"\nFound {total} compliance issues", file=sys.stderr)
            sys.exit(1)
        else:
            print("\nNo compliance issues found", file=sys.stderr)
    except GRCError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()


def cmd_cmmc(args):
    """Handle the 'cmmc' command."""
    client = _get_client(args)
    try:
        result = client.cmmc_assess(
            path=args.path,
            level=args.level,
            practice_domain=args.domain,
        )
        _print_json(result)

        score = result.get("overall_score", 0)
        print(f"\nCMMC Level {args.level} Score: {score}%", file=sys.stderr)
    except GRCError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()


def cmd_trust(args):
    """Handle the 'trust' command."""
    client = _get_client(args)
    try:
        result = client.trust_score(
            entity_id=args.entity_id,
            entity_type=args.entity_type,
        )
        _print_json(result)

        score = result.get("score", "N/A")
        print(f"\nTrust Score: {score}/100", file=sys.stderr)
    except GRCError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()


def cmd_frameworks(args):
    """Handle the 'frameworks' command."""
    client = _get_client(args)
    try:
        frameworks = client.list_frameworks()
        _print_json(frameworks)

        print(f"\nTotal frameworks: {len(frameworks)}", file=sys.stderr)
    except GRCError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()


def cmd_controls(args):
    """Handle the 'controls' command."""
    client = _get_client(args)
    try:
        controls = client.list_controls(framework=args.framework)
        _print_json(controls)

        print(f"\nTotal controls: {len(controls)}", file=sys.stderr)
    except GRCError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="grc",
        description="GRC_Claw CLI - Compliance automation tools",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--api-key", help="API key (or set GRC_CLAW_API_KEY)")
    parser.add_argument("--base-url", help="API base URL", default=None)
    parser.add_argument("--timeout", type=int, help="Request timeout in seconds", default=30)

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan directory for compliance issues")
    scan_parser.add_argument("path", help="Directory path to scan")
    scan_parser.add_argument("--frameworks", nargs="+", help="Frameworks to check")
    scan_parser.add_argument(
        "--severity",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Minimum severity threshold",
    )
    scan_parser.set_defaults(func=cmd_scan)

    # cmmc command
    cmmc_parser = subparsers.add_parser("cmmc", help="Run CMMC assessment")
    cmmc_parser.add_argument("path", help="Directory path to assess")
    cmmc_parser.add_argument("--level", type=int, choices=[1, 2, 3], default=1, help="CMMC level")
    cmmc_parser.add_argument("--domain", help="Practice domain to focus on")
    cmmc_parser.set_defaults(func=cmd_cmmc)

    # trust command
    trust_parser = subparsers.add_parser("trust", help="Get trust score")
    trust_parser.add_argument("entity_id", help="Entity ID")
    trust_parser.add_argument(
        "--entity-type",
        choices=["organization", "agent", "service"],
        default="organization",
        help="Entity type",
    )
    trust_parser.set_defaults(func=cmd_trust)

    # frameworks command
    frameworks_parser = subparsers.add_parser("frameworks", help="List supported frameworks")
    frameworks_parser.set_defaults(func=cmd_frameworks)

    # controls command
    controls_parser = subparsers.add_parser("controls", help="List controls for a framework")
    controls_parser.add_argument(
        "--framework", default="CMMC", help="Framework name"
    )
    controls_parser.set_defaults(func=cmd_controls)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

"""
GRC_Claw Unified CLI — Main entry point.

Usage:
    grc <command> [subcommand] [options]

Commands:
    policy       Policy management
    evidence     Evidence management
    compliance   Compliance scanning and reporting
    risk         Risk management and quantification
    agent        Agent governance
    report       Report generation
    quote        Quote generation
    config       Configuration management
    doctor       Environment health check
    version      Show version information
"""

import argparse
import json
import os
import sys
from pathlib import Path

from grc_claw_cli import __version__
from grc_claw_cli.utils.config import Config
from grc_claw_cli.utils.output import print_json, print_success, print_error, print_warning, print_info
from grc_claw_cli.commands import policy, evidence, compliance, risk, agent_governance, reporting, quote


def cmd_config(args, config: Config):
    """Handle config command."""
    if args.config_command == "set":
        config.set(args.key, args.value)
        config.save()
        print_success(f"Config set: {args.key} = {args.value}")
        return 0
    elif args.config_command == "get":
        value = config.get(args.key)
        if value is None:
            print_error(f"Config key not found: {args.key}")
            return 1
        print_json({args.key: value})
        return 0
    elif args.config_command == "list":
        print_json(config.as_dict())
        return 0
    else:
        print_error("Usage: grc config <set|get|list>")
        return 1


def cmd_doctor(args, config: Config):
    """Run environment health checks."""
    print_info("GRC_Claw Doctor — Environment Health Check")
    print()

    checks = []

    # Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(("Python version", True, f"Python {py_version}"))

    # Config file
    config_exists = config.CONFIG_FILE.exists()
    checks.append(("Config file", config_exists, str(config.CONFIG_FILE) if config_exists else "Not found — run: grc config set api_key <key>"))

    # API key
    api_key = config.api_key
    checks.append(("API key", bool(api_key), "Set" if api_key else "Not set — run: grc config set api_key <key>"))

    # Gateway token
    gw_token = config.gateway_token
    checks.append(("Gateway token", bool(gw_token), "Set" if gw_token else "Not set (optional)"))

    # Evidence directory
    ev_dir = Path(config.get("evidence_dir", "./compliance-evidence"))
    checks.append(("Evidence directory", ev_dir.exists(), str(ev_dir) if ev_dir.exists() else "Not created (will be created on first use)"))

    # Policies file
    pol_file = config.CONFIG_DIR / "policies.json"
    checks.append(("Policy store", pol_file.exists(), str(pol_file) if pol_file.exists() else "Not created (will be created on first use)"))

    # Risks file
    risk_file = config.CONFIG_DIR / "risks.json"
    checks.append(("Risk register", risk_file.exists(), str(risk_file) if risk_file.exists() else "Not created (will be created on first use)"))

    # Reports file
    rep_file = config.CONFIG_DIR / "reports.json"
    checks.append(("Report store", rep_file.exists(), str(rep_file) if rep_file.exists() else "Not created (will be created on first use)"))

    failures = 0
    for name, passed, detail in checks:
        status = "✓" if passed else "✗"
        color = "\033[32m" if passed else "\033[31m"
        print(f"  {color}{status}\033[0m {name:<24} {detail}")
        if not passed:
            failures += 1

    print()
    if failures == 0:
        print_success("All checks passed!")
    else:
        print_warning(f"{failures} check(s) need attention")
    return 0 if failures == 0 else 1


def build_parser():
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="grc",
        description="GRC_Claw Unified CLI — Governance, Risk, and Compliance automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  grc policy create --title "Access Control" --category security --owner alice --approver bob --content "All access must be authenticated"
  grc policy list --category security
  grc evidence attach --control-id CC6.1 --file ./logs/access.log
  grc compliance scan . --json
  grc compliance report --framework iso27001 --output report.json
  grc risk add --title "Data Breach" --category cybersecurity --likelihood 4 --impact 5 --owner security-team
  grc risk heatmap
  grc agent system-register --name "Chatbot" --owner ai-team --department engineering --use-case "customer-service" --risk-class limited
  grc agent firewall --actor-id agent-1 --actor-type agent --tool "db.write" --tier write --data-boundary tenant-confidential
  grc report generate --type board_summary --period Q4-2024
  grc quote generate --org-name "Acme Corp" --industry fintech --agents 10 --models 3 --policies 50 --evidence-gb 100 --frameworks iso27001 soc2
  grc config set api_key <your-key>
  grc doctor
        """,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--json", action="store_true", help="Output as JSON (global flag)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register all command modules
    policy.register(subparsers)
    evidence.register(subparsers)
    compliance.register(subparsers)
    risk.register(subparsers)
    agent_governance.register(subparsers)
    reporting.register(subparsers)
    quote.register(subparsers)

    # config command
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_sub = config_parser.add_subparsers(dest="config_command", help="Config operations")
    set_p = config_sub.add_parser("set", help="Set a config value")
    set_p.add_argument("key", help="Config key")
    set_p.add_argument("value", help="Config value")
    get_p = config_sub.add_parser("get", help="Get a config value")
    get_p.add_argument("key", help="Config key")
    config_sub.add_parser("list", help="List all config values")

    # doctor command
    subparsers.add_parser("doctor", help="Environment health check")

    # version command
    subparsers.add_parser("version", help="Show version information")

    return parser


def main():
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    config = Config()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "version":
        print(f"grc {__version__}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Platform: {sys.platform}")
        sys.exit(0)

    if args.command == "doctor":
        sys.exit(cmd_doctor(args, config))

    if args.command == "config":
        sys.exit(cmd_config(args, config))

    # Dispatch to command modules
    command_map = {
        "policy": policy.handle,
        "evidence": evidence.handle,
        "compliance": compliance.handle,
        "risk": risk.handle,
        "agent": agent_governance.handle,
        "report": reporting.handle,
        "quote": quote.handle,
    }

    handler = command_map.get(args.command)
    if handler:
        try:
            result = handler(args, config)
            sys.exit(result or 0)
        except KeyboardInterrupt:
            print_error("Interrupted")
            sys.exit(130)
        except Exception as e:
            print_error(f"Error: {e}")
            if os.environ.get("GRC_DEBUG"):
                import traceback
                traceback.print_exc()
            sys.exit(1)
    else:
        print_error(f"Unknown command: {args.command}")
        print_info("Run 'grc --help' for usage")
        sys.exit(1)


if __name__ == "__main__":
    main()

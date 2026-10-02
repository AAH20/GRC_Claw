"""CLI entry point for lead-scorer."""

from __future__ import annotations

import argparse
import asyncio
import uvicorn

from core.config import get_settings
from core.logging import configure_logging, get_logger

logger = get_logger(__name__)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="lead-scorer",
        description="AI-Powered Lead Scoring & Qualification",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default=None, help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    serve_parser.add_argument(
        "--workers", type=int, default=None, help="Number of worker processes"
    )
    serve_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload (dev mode)"
    )

    # Version command
    subparsers.add_parser("version", help="Show version info")

    args = parser.parse_args()

    if args.command == "serve":
        configure_logging()
        settings = get_settings()

        host = args.host or settings.api_host
        port = args.port or settings.api_port
        workers = args.workers or settings.api_workers

        logger.info(
            "starting_server",
            host=host,
            port=port,
            workers=workers,
            environment=settings.environment,
        )

        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            workers=workers if not args.reload else 1,
            reload=args.reload,
            log_level=settings.log_level.lower(),
        )

    elif args.command == "version":
        settings = get_settings()
        print(f"lead-scorer v{settings.app_version}")
        print(f"Environment: {settings.environment}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

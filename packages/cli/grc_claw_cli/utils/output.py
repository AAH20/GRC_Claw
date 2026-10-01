"""Output formatting utilities."""
import json
import sys
from typing import Any


class OutputFormatter:
    """Handles colored, structured output for the CLI."""

    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bg_red": "\033[41m",
        "bg_green": "\033[42m",
    }

    def __init__(self, use_color: bool = True, json_mode: bool = False):
        self.use_color = use_color and not json_mode
        self.json_mode = json_mode

    def color(self, name: str, text: str) -> str:
        if not self.use_color:
            return text
        return f"{self.COLORS.get(name, '')}{text}{self.COLORS['reset']}"

    def bold(self, text: str) -> str:
        return self.color("bold", text)

    def dim(self, text: str) -> str:
        return self.color("dim", text)

    def red(self, text: str) -> str:
        return self.color("red", text)

    def green(self, text: str) -> str:
        return self.color("green", text)

    def yellow(self, text: str) -> str:
        return self.color("yellow", text)

    def cyan(self, text: str) -> str:
        return self.color("cyan", text)


def print_json(data: Any, pretty: bool = True) -> None:
    """Print data as JSON."""
    if pretty:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(json.dumps(data, default=str))


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a formatted table."""
    if not rows:
        print("(no data)")
        return
    widths = [max(len(h), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    sep = "┼".join("─" * (w + 2) for w in widths)
    hdr = "│".join(f" {h.ljust(widths[i])} " for i, h in enumerate(headers))
    print(hdr)
    print(sep)
    for row in rows:
        line = "│".join(f" {str(cell).ljust(widths[i])} " for i, cell in enumerate(row))
        print(line)


def print_success(msg: str) -> None:
    print(f"\033[32m✓\033[0m {msg}")


def print_error(msg: str) -> None:
    print(f"\033[31m✗\033[0m {msg}", file=sys.stderr)


def print_warning(msg: str) -> None:
    print(f"\033[33m⚠\033[0m {msg}")


def print_info(msg: str) -> None:
    print(f"\033[36mℹ\033[0m {msg}")

#!/usr/bin/env python3
"""
Unified documentation framework orchestrator for GRC_Claw.
Runs all documentation tools and generates a consolidated report.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent

TOOLS = [
    {
        "name": "search",
        "script": "doc-search.py",
        "description": "Unified documentation search",
        "args": ["--stats"],
    },
    {
        "name": "xref",
        "script": "doc-xref-validator.py",
        "description": "Cross-reference validator",
        "args": ["--json"],
    },
    {
        "name": "generator",
        "script": "doc-generator.py",
        "description": "Documentation generator",
        "args": ["--format", "all"],
    },
    {
        "name": "linkcheck",
        "script": "doc-link-checker.py",
        "description": "Link checker",
        "args": ["--json"],
    },
    {
        "name": "stale",
        "script": "doc-stale-detector.py",
        "description": "Stale content detector",
        "args": ["--json"],
    },
]


def run_tool(tool: Dict, root: Path) -> Dict:
    """Run a single documentation tool and capture output."""
    script_path = SCRIPTS_DIR / tool["script"]
    cmd = [sys.executable, str(script_path), "--root", str(root)] + tool["args"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(root),
        )
        return {
            "name": tool["name"],
            "description": tool["description"],
            "script": tool["script"],
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode in (0, 1),  # 1 is expected for validators with issues
        }
    except subprocess.TimeoutExpired:
        return {
            "name": tool["name"],
            "description": tool["description"],
            "script": tool["script"],
            "exit_code": -1,
            "stdout": "",
            "stderr": "Timeout after 120s",
            "success": False,
        }
    except Exception as e:
        return {
            "name": tool["name"],
            "description": tool["description"],
            "script": tool["script"],
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
        }


def generate_consolidated_report(results: List[Dict], root: Path) -> str:
    """Generate a consolidated markdown report from all tool results."""
    lines = [
        "# GRC_Claw Documentation Framework Report",
        "",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Repository: {root}",
        "",
        "## Summary",
        "",
        "| Tool | Description | Status |",
        "|------|-------------|--------|",
    ]

    for r in results:
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        lines.append(f"| {r['name']} | {r['description']} | {status} |")

    lines.extend(["", "## Detailed Results", ""])

    for r in results:
        lines.append(f"### {r['name']} — {r['description']}")
        lines.append(f"")
        lines.append(f"**Script:** `{r['script']}`")
        lines.append(f"**Exit code:** {r['exit_code']}")
        lines.append(f"")

        if r["stdout"]:
            lines.append("```")
            lines.append(r["stdout"][:3000])  # Truncate long output
            if len(r["stdout"]) > 3000:
                lines.append("... (truncated)")
            lines.append("```")
        else:
            lines.append("*(no output)*")

        if r["stderr"]:
            lines.append("")
            lines.append("**Stderr:**")
            lines.append("```")
            lines.append(r["stderr"][:1000])
            lines.append("```")

        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Unified documentation framework for GRC_Claw"
    )
    parser.add_argument(
        "--root", type=Path, default=None, help="Repository root"
    )
    parser.add_argument(
        "--tools", nargs="*", default=None,
        help="Specific tools to run (default: all)"
    )
    parser.add_argument(
        "--report", type=Path, default=None,
        help="Write consolidated report to file"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    args = parser.parse_args()
    root = args.root or REPO_ROOT

    tools_to_run = TOOLS
    if args.tools:
        tools_to_run = [t for t in TOOLS if t["name"] in args.tools]

    print(f"GRC_Claw Documentation Framework")
    print(f"{'=' * 50}")
    print(f"Repository: {root}")
    print(f"Tools: {len(tools_to_run)}")
    print()

    results = []
    for tool in tools_to_run:
        print(f"Running {tool['name']} ({tool['description']})...", end=" ", flush=True)
        result = run_tool(tool, root)
        results.append(result)
        status = "done" if result["success"] else "FAILED"
        print(f"{status} (exit: {result['exit_code']})")

    print()

    if args.json:
        output = {
            "generated": datetime.utcnow().isoformat() + "Z",
            "repository": str(root),
            "tools_run": len(results),
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        report = generate_consolidated_report(results, root)
        print(report)

    if args.report:
        report = generate_consolidated_report(results, root)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
        print(f"\nReport written to: {args.report}")

    # Exit 1 if any tool failed
    failed = sum(1 for r in results if not r["success"])
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()

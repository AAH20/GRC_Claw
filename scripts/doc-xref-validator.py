#!/usr/bin/env python3
"""
Cross-reference validator for GRC_Claw documentation.
Validates internal references between documents, checks for broken links,
orphaned documents, and missing backlinks.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_EXTENSIONS = {".md", ".mdx"}
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

# Regex patterns for cross-reference detection
LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
REF_PATTERN = re.compile(r"(?:see|refer to|described in|defined in|documented in)\s+\[([^\]]*)\]\(([^)]+)\)", re.IGNORECASE)
ANCHOR_PATTERN = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def find_doc_files(root: Path) -> List[Path]:
    """Recursively find all documentation files."""
    docs = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in DOC_EXTENSIONS:
            if not any(part in EXCLUDE_DIRS for part in path.parts):
                docs.append(path)
    return sorted(docs)


def extract_links(content: str) -> List[Tuple[str, str]]:
    """Extract all markdown links from content."""
    links = []
    for match in LINK_PATTERN.finditer(content):
        text, url = match.group(1), match.group(2)
        links.append((text, url))
    return links


def extract_anchors(content: str) -> Set[str]:
    """Extract all heading anchors from content."""
    anchors = set()
    for match in ANCHOR_PATTERN.finditer(content):
        heading = match.group(1).strip()
        # GitHub-style anchor: lowercase, remove special chars, spaces to hyphens
        anchor = re.sub(r"[^\w\s-]", "", heading.lower())
        anchor = re.sub(r"\s+", "-", anchor)
        anchors.add(anchor)
    return anchors


def resolve_link(source_file: Path, link: str, root: Path) -> Optional[Path]:
    """Resolve a relative link to an absolute file path."""
    if link.startswith(("http://", "https://", "mailto:", "#")):
        return None

    # Remove anchor
    path_part = link.split("#")[0]
    if not path_part:
        return None

    # Resolve relative to source file's directory
    resolved = (source_file.parent / path_part).resolve()
    return resolved


def validate_file(
    filepath: Path,
    root: Path,
    all_files: Set[Path],
    all_anchors: Dict[Path, Set[str]],
) -> List[Dict]:
    """Validate cross-references in a single file."""
    issues = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [{"file": str(filepath.relative_to(root)), "type": "read_error", "detail": str(e)}]

    links = extract_links(content)
    rel_path = str(filepath.relative_to(root))

    for text, link in links:
        # Skip external links
        if link.startswith(("http://", "https://", "mailto:")):
            continue

        # Handle anchor-only links
        if link.startswith("#"):
            anchor = link[1:]
            file_anchors = extract_anchors(content)
            if anchor and anchor not in file_anchors:
                issues.append({
                    "file": rel_path,
                    "type": "broken_anchor",
                    "detail": f"Anchor '#{anchor}' not found in document",
                    "link_text": text,
                    "link_target": link,
                })
            continue

        # Resolve the link target
        resolved = resolve_link(filepath, link, root)
        if resolved is None:
            continue

        # Check if target exists
        if not resolved.exists():
            # Try with .md extension
            if resolved.suffix == "" and resolved.with_suffix(".md").exists():
                continue
            issues.append({
                "file": rel_path,
                "type": "broken_link",
                "detail": f"Target file does not exist: {link}",
                "link_text": text,
                "link_target": link,
            })
            continue

        # Check anchor in target file
        if "#" in link:
            anchor = link.split("#", 1)[1]
            if anchor and resolved in all_anchors:
                if anchor not in all_anchors[resolved]:
                    issues.append({
                        "file": rel_path,
                        "type": "broken_anchor",
                        "detail": f"Anchor '#{anchor}' not found in {resolved.relative_to(root)}",
                        "link_text": text,
                        "link_target": link,
                    })

    return issues


def find_orphaned_docs(
    root: Path,
    all_files: List[Path],
    link_graph: Dict[Path, Set[Path]],
) -> List[Dict]:
    """Find documents that are not linked from any other document."""
    orphaned = []
    incoming: Dict[Path, int] = defaultdict(int)

    for source, targets in link_graph.items():
        for target in targets:
            incoming[target] += 1

    for doc in all_files:
        rel = str(doc.relative_to(root))
        # Skip index/README files at root level
        if doc.parent == root and doc.stem.lower() in ("readme", "index", "intro"):
            continue
        if incoming[doc] == 0:
            orphaned.append({
                "file": rel,
                "type": "orphaned",
                "detail": "Document is not linked from any other document",
            })

    return orphaned


def build_link_graph(root: Path, all_files: List[Path]) -> Dict[Path, Set[Path]]:
    """Build a graph of document links."""
    graph = defaultdict(set)
    all_file_set = {f.resolve() for f in all_files}

    for doc in all_files:
        try:
            content = doc.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        links = extract_links(content)
        for _, link in links:
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            resolved = resolve_link(doc, link, root)
            if resolved and resolved.resolve() in all_file_set:
                graph[doc].add(resolved.resolve())

    return graph


def validate_all(
    root: Optional[Path] = None,
    check_orphans: bool = True,
    check_links: bool = True,
) -> Dict:
    """Run full cross-reference validation."""
    root = root or REPO_ROOT
    all_files = find_doc_files(root)
    all_file_set = {f.resolve() for f in all_files}

    # Pre-compute anchors for all files
    all_anchors: Dict[Path, Set[str]] = {}
    for doc in all_files:
        try:
            content = doc.read_text(encoding="utf-8", errors="replace")
            all_anchors[doc.resolve()] = extract_anchors(content)
        except Exception:
            pass

    result = {
        "summary": {
            "total_files": len(all_files),
            "total_issues": 0,
            "broken_links": 0,
            "broken_anchors": 0,
            "orphaned_docs": 0,
        },
        "issues": [],
    }

    if check_links:
        for doc in all_files:
            issues = validate_file(doc, root, all_file_set, all_anchors)
            result["issues"].extend(issues)

    if check_orphans:
        link_graph = build_link_graph(root, all_files)
        orphaned = find_orphaned_docs(root, all_files, link_graph)
        result["issues"].extend(orphaned)

    # Update summary
    for issue in result["issues"]:
        if issue["type"] == "broken_link":
            result["summary"]["broken_links"] += 1
        elif issue["type"] == "broken_anchor":
            result["summary"]["broken_anchors"] += 1
        elif issue["type"] == "orphaned":
            result["summary"]["orphaned_docs"] += 1

    result["summary"]["total_issues"] = len(result["issues"])
    return result


def main():
    parser = argparse.ArgumentParser(description="Cross-reference validator for GRC_Claw docs")
    parser.add_argument("--root", type=Path, default=None, help="Repository root")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--no-orphans", action="store_true", help="Skip orphan detection")
    parser.add_argument("--no-links", action="store_true", help="Skip link validation")
    parser.add_argument("--severity", choices=["all", "errors", "warnings"], default="all")

    args = parser.parse_args()

    result = validate_all(
        root=args.root,
        check_orphans=not args.no_orphans,
        check_links=not args.no_links,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        s = result["summary"]
        print(f"Cross-Reference Validation Report")
        print(f"{'='*50}")
        print(f"Files scanned: {s['total_files']}")
        print(f"Total issues:  {s['total_issues']}")
        print(f"  Broken links:   {s['broken_links']}")
        print(f"  Broken anchors: {s['broken_anchors']}")
        print(f"  Orphaned docs:  {s['orphaned_docs']}")

        if result["issues"]:
            print(f"\nIssues:")
            print(f"{'-'*50}")
            for issue in result["issues"]:
                severity_icon = "❌" if issue["type"] in ("broken_link", "broken_anchor") else "⚠️"
                print(f"  {severity_icon} [{issue['type']}] {issue['file']}")
                print(f"     {issue['detail']}")

    sys.exit(1 if result["summary"]["broken_links"] > 0 or result["summary"]["broken_anchors"] > 0 else 0)


if __name__ == "__main__":
    main()

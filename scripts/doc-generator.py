#!/usr/bin/env python3
"""
Documentation generator for GRC_Claw.
Generates an index, table of contents, and searchable JSON corpus
from all markdown documentation files.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_EXTENSIONS = {".md", ".mdx"}
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def find_doc_files(root: Path) -> List[Path]:
    """Recursively find all documentation files."""
    docs = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in DOC_EXTENSIONS:
            if not any(part in EXCLUDE_DIRS for part in path.parts):
                docs.append(path)
    return sorted(docs)


def extract_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
    """Extract YAML frontmatter if present."""
    metadata = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    metadata[key.strip()] = value.strip()
            body = parts[2]
    return metadata, body


def extract_title(content: str, fallback: str) -> str:
    """Extract the first H1 title from content."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def extract_description(content: str, metadata: Dict[str, str]) -> str:
    """Extract a short description from metadata or first paragraph."""
    if "description" in metadata:
        return metadata["description"]
    if "summary" in metadata:
        return metadata["summary"]

    # Try first non-heading paragraph
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            return stripped[:200]
    return ""


def extract_headings(content: str) -> List[Dict[str, str]]:
    """Extract all headings with their levels."""
    headings = []
    for match in re.finditer(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()
        anchor = re.sub(r"[^\w\s-]", "", text.lower())
        anchor = re.sub(r"\s+", "-", anchor)
        headings.append({"level": level, "text": text, "anchor": anchor})
    return headings


def categorize_file(filepath: Path, root: Path) -> str:
    """Categorize a document based on its path."""
    rel = filepath.relative_to(root)
    parts = rel.parts

    if len(parts) == 1:
        return "root"

    top_dir = parts[0].lower()
    category_map = {
        "specs": "specifications",
        "docs": "documentation",
        "guides": "guides",
        "tutorials": "tutorials",
        "examples": "examples",
        "architecture": "architecture",
        "design": "design",
        "api": "api-reference",
        "reference": "reference",
        "deploy": "deployment",
        "deployment": "deployment",
        "integrations": "integrations",
        "strategy": "strategy",
        "gap-blueprints": "gap-blueprints",
        "implementations": "implementations",
        "schemas": "schemas",
        "skills": "skills",
        "speculative": "speculative",
    }

    return category_map.get(top_dir, top_dir)


def generate_index_entry(filepath: Path, root: Path, content: str) -> Dict:
    """Generate an index entry for a single document."""
    metadata, _ = extract_frontmatter(content)
    title = extract_title(content, filepath.stem)
    description = extract_description(content, metadata)
    category = categorize_file(filepath, root)
    headings = extract_headings(content)

    return {
        "file": str(filepath.relative_to(root)),
        "title": title,
        "description": description,
        "category": category,
        "headings": headings,
        "metadata": metadata,
        "line_count": len(content.splitlines()),
        "word_count": len(content.split()),
    }


def generate_markdown_index(entries: List[Dict], root: Path) -> str:
    """Generate a markdown index document."""
    lines = [
        "# GRC_Claw Documentation Index",
        "",
        f"Auto-generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        f"**Total documents:** {len(entries)}",
        "",
        "## Table of Contents",
        "",
    ]

    # Group by category
    by_category = defaultdict(list)
    for entry in entries:
        by_category[entry["category"]].append(entry)

    for category in sorted(by_category.keys()):
        lines.append(f"### {category.replace('-', ' ').title()}")
        lines.append("")
        for entry in sorted(by_category[category], key=lambda x: x["title"]):
            rel_path = entry["file"]
            lines.append(f"- [{entry['title']}]({rel_path})")
            if entry["description"]:
                lines.append(f"  - {entry['description'][:100]}")
        lines.append("")

    return "\n".join(lines)


def generate_toc(content: str, max_depth: int = 3) -> str:
    """Generate a table of contents from markdown content."""
    headings = extract_headings(content)
    lines = ["## Table of Contents", ""]

    for h in headings:
        if h["level"] > max_depth:
            continue
        indent = "  " * (h["level"] - 1)
        lines.append(f"{indent}- [{h['text']}](#{h['anchor']})")

    return "\n".join(lines)


def generate_search_index(entries: List[Dict]) -> Dict:
    """Generate a searchable JSON index."""
    search_docs = []
    for entry in entries:
        search_docs.append({
            "file": entry["file"],
            "title": entry["title"],
            "description": entry["description"],
            "category": entry["category"],
            "headings": [h["text"] for h in entry["headings"]],
        })

    return {
        "generated": datetime.utcnow().isoformat() + "Z",
        "total_documents": len(entries),
        "documents": search_docs,
    }


def generate_readme_overview(entries: List[Dict], root: Path) -> str:
    """Generate a README overview section."""
    by_category = defaultdict(list)
    for entry in entries:
        by_category[entry["category"]].append(entry)

    lines = [
        "## Documentation Overview",
        "",
        f"The GRC_Claw documentation contains **{len(entries)} documents** across {len(by_category)} categories.",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ]

    for category in sorted(by_category.keys()):
        count = len(by_category[category])
        lines.append(f"| {category.replace('-', ' ').title()} | {count} |")

    lines.append("")
    lines.append("### Quick Links")
    lines.append("")

    # Find key documents
    key_docs = ["README.md", "ARCHITECTURE.md", "CONTRIBUTING.md", "CHANGELOG.md"]
    for doc_name in key_docs:
        for entry in entries:
            if entry["file"].endswith(doc_name):
                lines.append(f"- [{entry['title']}]({entry['file']})")
                break

    lines.append("")
    lines.append("### Recently Added")
    lines.append("")

    # Sort by file path as proxy for recency
    for entry in sorted(entries, key=lambda x: x["file"], reverse=True)[:5]:
        lines.append(f"- [{entry['title']}]({entry['file']})")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Documentation generator for GRC_Claw")
    parser.add_argument("--root", type=Path, default=None, help="Repository root")
    parser.add_argument("--output", type=Path, default=None, help="Output directory")
    parser.add_argument("--format", choices=["markdown", "json", "all"], default="all")
    parser.add_argument("--toc", action="store_true", help="Generate per-file TOCs")
    parser.add_argument("--readme", action="store_true", help="Generate README overview")

    args = parser.parse_args()

    root = args.root or REPO_ROOT
    output = args.output or root / "docs" / "generated"
    output.mkdir(parents=True, exist_ok=True)

    all_files = find_doc_files(root)
    entries = []

    for doc in all_files:
        try:
            content = doc.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        entry = generate_index_entry(doc, root, content)
        entries.append(entry)

    generated_files = []

    # Generate markdown index
    if args.format in ("markdown", "all"):
        index_md = generate_markdown_index(entries, root)
        index_path = output / "INDEX.md"
        index_path.write_text(index_md, encoding="utf-8")
        generated_files.append(str(index_path.relative_to(root)))

    # Generate JSON search index
    if args.format in ("json", "all"):
        search_index = generate_search_index(entries)
        json_path = output / "search-index.json"
        json_path.write_text(json.dumps(search_index, indent=2), encoding="utf-8")
        generated_files.append(str(json_path.relative_to(root)))

    # Generate per-file TOCs
    if args.toc:
        toc_dir = output / "tocs"
        toc_dir.mkdir(exist_ok=True)
        for doc in all_files:
            try:
                content = doc.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            toc = generate_toc(content)
            rel = doc.relative_to(root)
            toc_path = toc_dir / rel.with_suffix(".toc.md")
            toc_path.parent.mkdir(parents=True, exist_ok=True)
            toc_path.write_text(toc, encoding="utf-8")
            generated_files.append(str(toc_path.relative_to(root)))

    # Generate README overview
    if args.readme:
        overview = generate_readme_overview(entries, root)
        overview_path = output / "OVERVIEW.md"
        overview_path.write_text(overview, encoding="utf-8")
        generated_files.append(str(overview_path.relative_to(root)))

    # Print summary
    print(f"Documentation Generation Complete")
    print(f"{'='*40}")
    print(f"Documents processed: {len(entries)}")
    print(f"Output directory: {output}")
    print(f"Generated files: {len(generated_files)}")
    for f in generated_files:
        print(f"  - {f}")

    # Output JSON summary for programmatic use
    summary = {
        "total_documents": len(entries),
        "generated_files": generated_files,
        "output_directory": str(output.relative_to(root)),
    }
    print(f"\n{json.dumps(summary)}")


if __name__ == "__main__":
    main()

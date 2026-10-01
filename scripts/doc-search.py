#!/usr/bin/env python3
"""
Unified documentation search for GRC_Claw.
Searches across all markdown files with relevance scoring and filtering.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
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


def score_document(content: str, query: str, filepath: Path) -> float:
    """Score a document based on query relevance."""
    query_lower = query.lower()
    content_lower = content.lower()
    score = 0.0

    # Title match (highest weight)
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_match and query_lower in title_match.group(1).lower():
        score += 10.0

    # Heading matches
    for heading in re.findall(r"^#{1,6}\s+(.+)$", content, re.MULTILINE):
        if query_lower in heading.lower():
            score += 5.0

    # Content frequency
    count = content_lower.count(query_lower)
    score += min(count * 0.5, 10.0)

    # Frontmatter tags/keywords
    metadata, _ = extract_frontmatter(content)
    for key in ("tags", "keywords", "categories"):
        if key in metadata and query_lower in metadata[key].lower():
            score += 3.0

    # Path relevance
    if query_lower in str(filepath).lower():
        score += 2.0

    return score


def search_docs(
    query: str,
    root: Optional[Path] = None,
    limit: int = 20,
    min_score: float = 0.5,
    file_pattern: Optional[str] = None,
) -> List[Dict]:
    """Search all documentation files for the given query."""
    root = root or REPO_ROOT
    docs = find_doc_files(root)

    if file_pattern:
        regex = re.compile(file_pattern)
        docs = [d for d in docs if regex.search(str(d))]

    results = []
    for doc in docs:
        try:
            content = doc.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        score = score_document(content, query, doc)
        if score < min_score:
            continue

        metadata, body = extract_frontmatter(content)
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else doc.stem

        # Extract snippet around first match
        snippet = ""
        content_lower = content.lower()
        idx = content_lower.find(query.lower())
        if idx >= 0:
            start = max(0, idx - 80)
            end = min(len(content), idx + 120)
            snippet = content[start:end].replace("\n", " ").strip()

        results.append({
            "file": str(doc.relative_to(root)),
            "title": title,
            "score": round(score, 2),
            "snippet": snippet,
            "metadata": metadata,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def main():
    parser = argparse.ArgumentParser(description="Unified documentation search for GRC_Claw")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--root", type=Path, default=None, help="Repository root (default: auto-detect)")
    parser.add_argument("--limit", type=int, default=20, help="Maximum results")
    parser.add_argument("--min-score", type=float, default=0.5, help="Minimum relevance score")
    parser.add_argument("--pattern", type=str, default=None, help="File path regex filter")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--stats", action="store_true", help="Show corpus statistics")

    args = parser.parse_args()

    if args.stats:
        root = args.root or REPO_ROOT
        docs = find_doc_files(root)
        total_lines = sum(len(d.read_text(errors="replace").splitlines()) for d in docs)
        by_dir = defaultdict(int)
        for d in docs:
            rel = d.relative_to(root)
            top = rel.parts[0] if len(rel.parts) > 1 else "."
            by_dir[top] += 1
        stats = {
            "total_files": len(docs),
            "total_lines": total_lines,
            "by_directory": dict(sorted(by_dir.items(), key=lambda x: -x[1])),
        }
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"Documentation Corpus Statistics")
            print(f"{'='*40}")
            print(f"Total files: {stats['total_files']}")
            print(f"Total lines: {stats['total_lines']}")
            print(f"\nFiles by directory:")
            for dir_name, count in stats["by_directory"].items():
                print(f"  {dir_name}: {count}")
        return

    results = search_docs(
        query=args.query,
        root=args.root,
        limit=args.limit,
        min_score=args.min_score,
        file_pattern=args.pattern,
    )

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if not results:
            print(f"No results found for '{args.query}'")
            return
        print(f"Found {len(results)} result(s) for '{args.query}':")
        print(f"{'='*60}")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. [{r['score']}] {r['title']}")
            print(f"   File: {r['file']}")
            if r["snippet"]:
                print(f"   ...{r['snippet']}...")


if __name__ == "__main__":
    main()

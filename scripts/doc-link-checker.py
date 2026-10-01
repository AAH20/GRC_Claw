#!/usr/bin/env python3
"""
Link checker for GRC_Claw documentation.
Validates all internal and external links in markdown files.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_EXTENSIONS = {".md", ".mdx"}
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTML_LINK_PATTERN = re.compile(r'<a\s+[^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)
HTML_IMG_PATTERN = re.compile(r'<img\s+[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)


def find_doc_files(root: Path) -> List[Path]:
    """Recursively find all documentation files."""
    docs = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in DOC_EXTENSIONS:
            if not any(part in EXCLUDE_DIRS for part in path.parts):
                docs.append(path)
    return sorted(docs)


def extract_all_links(content: str) -> List[Tuple[str, str, str]]:
    """Extract all links from content. Returns (type, text, url) tuples."""
    links = []

    for match in LINK_PATTERN.finditer(content):
        links.append(("markdown", match.group(1), match.group(2)))

    for match in IMAGE_PATTERN.finditer(content):
        links.append(("image", match.group(1), match.group(2)))

    for match in HTML_LINK_PATTERN.finditer(content):
        links.append(("html_link", "", match.group(1)))

    for match in HTML_IMG_PATTERN.finditer(content):
        links.append(("html_image", "", match.group(1)))

    return links


def is_external(url: str) -> bool:
    """Check if a URL is external."""
    return url.startswith(("http://", "https://", "mailto:", "ftp://"))


def is_anchor(url: str) -> bool:
    """Check if a URL is an anchor-only link."""
    return url.startswith("#")


def check_external_link(url: str, timeout: int = 10) -> Dict:
    """Check if an external link is reachable."""
    if url.startswith("mailto:"):
        return {"url": url, "status": "ok", "status_code": None}

    try:
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "GRC_Claw-DocChecker/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"url": url, "status": "ok", "status_code": resp.status}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": "error", "status_code": e.code, "error": str(e)}
    except urllib.error.URLError as e:
        return {"url": url, "status": "error", "status_code": None, "error": str(e.reason)}
    except Exception as e:
        return {"url": url, "status": "error", "status_code": None, "error": str(e)}


def check_internal_link(source_file: Path, url: str, root: Path) -> Dict:
    """Check if an internal link resolves to an existing file."""
    if is_anchor(url):
        return {"url": url, "status": "anchor", "status_code": None}

    path_part = url.split("#")[0]
    if not path_part:
        return {"url": url, "status": "anchor", "status_code": None}

    resolved = (source_file.parent / path_part).resolve()

    if resolved.exists():
        return {"url": url, "status": "ok", "status_code": 200}

    # Try with .md extension
    if resolved.suffix == "" and resolved.with_suffix(".md").exists():
        return {"url": url, "status": "ok", "status_code": 200}

    return {"url": url, "status": "broken", "status_code": 404, "error": "File not found"}


def check_file_links(
    filepath: Path,
    root: Path,
    check_external: bool = True,
    external_timeout: int = 10,
) -> List[Dict]:
    """Check all links in a single file."""
    results = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [{"file": str(filepath.relative_to(root)), "url": "", "status": "read_error", "error": str(e)}]

    links = extract_all_links(content)
    rel_path = str(filepath.relative_to(root))

    for link_type, text, url in links:
        if is_external(url):
            if check_external:
                result = check_external_link(url, external_timeout)
                result["file"] = rel_path
                result["link_type"] = link_type
                result["link_text"] = text
                results.append(result)
        elif is_anchor(url):
            # Check anchor exists in same file
            anchor = url[1:]
            headings = re.findall(r"^#{1,6}\s+(.+)$", content, re.MULTILINE)
            anchors = set()
            for h in headings:
                a = re.sub(r"[^\w\s-]", "", h.lower())
                a = re.sub(r"\s+", "-", a)
                anchors.add(a)
            status = "ok" if anchor in anchors else "broken"
            results.append({
                "file": rel_path,
                "url": url,
                "status": status,
                "status_code": 200 if status == "ok" else 404,
                "link_type": link_type,
                "link_text": text,
            })
        else:
            result = check_internal_link(filepath, url, root)
            result["file"] = rel_path
            result["link_type"] = link_type
            result["link_text"] = text
            results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(description="Link checker for GRC_Claw documentation")
    parser.add_argument("--root", type=Path, default=None, help="Repository root")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--external", action="store_true", help="Check external links (slower)")
    parser.add_argument("--timeout", type=int, default=10, help="External link timeout in seconds")
    parser.add_argument("--workers", type=int, default=10, help="Parallel workers for external checks")
    parser.add_argument("--pattern", type=str, default=None, help="File path regex filter")

    args = parser.parse_args()

    root = args.root or REPO_ROOT
    all_files = find_doc_files(root)

    if args.pattern:
        regex = re.compile(args.pattern)
        all_files = [f for f in all_files if regex.search(str(f))]

    all_results = []

    # Check internal links for all files
    for doc in all_files:
        results = check_file_links(doc, root, check_external=False)
        all_results.extend(results)

    # Check external links in parallel
    if args.external:
        external_urls = set()
        for r in all_results:
            if r["url"].startswith(("http://", "https://")):
                external_urls.add(r["url"])

        external_results = {}
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(check_external_link, url, args.timeout): url
                for url in external_urls
            }
            for future in as_completed(futures):
                url = futures[future]
                try:
                    external_results[url] = future.result()
                except Exception as e:
                    external_results[url] = {"url": url, "status": "error", "error": str(e)}

        # Update results with external check results
        for r in all_results:
            if r["url"] in external_results:
                r.update(external_results[r["url"]])

    # Summarize
    total = len(all_results)
    ok = sum(1 for r in all_results if r["status"] == "ok")
    broken = sum(1 for r in all_results if r["status"] == "broken")
    errors = sum(1 for r in all_results if r["status"] == "error")
    anchors = sum(1 for r in all_results if r["status"] == "anchor")

    summary = {
        "total_links": total,
        "ok": ok,
        "broken": broken,
        "errors": errors,
        "anchors": anchors,
        "files_checked": len(all_files),
    }

    if args.json:
        output = {"summary": summary, "results": all_results}
        print(json.dumps(output, indent=2))
    else:
        print(f"Link Checker Report")
        print(f"{'='*50}")
        print(f"Files checked: {summary['files_checked']}")
        print(f"Total links:   {summary['total_links']}")
        print(f"  OK:      {summary['ok']}")
        print(f"  Anchors: {summary['anchors']}")
        print(f"  Broken:  {summary['broken']}")
        print(f"  Errors:  {summary['errors']}")

        if broken > 0 or errors > 0:
            print(f"\nProblematic Links:")
            print(f"{'-'*50}")
            for r in all_results:
                if r["status"] in ("broken", "error"):
                    icon = "❌" if r["status"] == "broken" else "⚠️"
                    print(f"  {icon} [{r['status']}] {r['file']}")
                    print(f"     URL: {r['url']}")
                    if "error" in r:
                        print(f"     Error: {r['error']}")

    sys.exit(1 if broken > 0 else 0)


if __name__ == "__main__":
    main()

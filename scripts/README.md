# GRC_Claw Documentation Framework

Unified documentation tooling for the GRC_Claw repository. Provides search, validation, generation, link checking, and stale content detection across 240+ markdown documents.

## Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `doc-search.py` | Unified search with relevance scoring | `python3 doc-search.py "query" [--limit N] [--json]` |
| `doc-xref-validator.py` | Cross-reference & orphan detection | `python3 doc-xref-validator.py [--json] [--no-orphans]` |
| `doc-generator.py` | Index, TOC & search index generation | `python3 doc-generator.py [--format markdown\|json\|all]` |
| `doc-link-checker.py` | Internal & external link validation | `python3 doc-link-checker.py [--external] [--json]` |
| `doc-stale-detector.py` | Stale content identification | `python3 doc-stale-detector.py [--age-threshold N] [--json]` |
| `doc-framework.py` | Orchestrator — runs all tools | `python3 doc-framework.py [--tools search xref] [--report FILE]` |

## Quick Start

```bash
# Run all tools and generate a consolidated report
python3 scripts/doc-framework.py --report docs/generated/FRAMEWORK_REPORT.md

# Search documentation
python3 scripts/doc-search.py "deployment architecture" --limit 10

# Validate cross-references
python3 scripts/doc-xref-validator.py

# Generate documentation index
python3 scripts/doc-generator.py --format all --toc --readme

# Check all links (including external)
python3 scripts/doc-link-checker.py --external

# Find stale documents
python3 scripts/doc-stale-detector.py --age-threshold 180 --severity high
```

## Output

- **Search**: Ranked results with scores, snippets, and metadata
- **Xref validation**: Broken links, broken anchors, orphaned documents
- **Generator**: `docs/generated/INDEX.md`, `search-index.json`, per-file TOCs
- **Link checker**: Internal file validation + optional external URL checks
- **Stale detector**: Age-based and content-based freshness analysis

## Exit Codes

- `0`: Success (no critical issues)
- `1`: Issues found (broken links, stale content, etc.)

## Corpus Statistics

The GRC_Claw documentation corpus contains approximately 247 markdown files across multiple directories including `docs/`, `specs/`, `deployment/`, `integrations/`, `strategy/`, and more.

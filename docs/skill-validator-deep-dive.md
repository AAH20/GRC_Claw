# Deep-Dive Analysis: agent-ecosystem/skill-validator

> **For:** Ahmed Hassan — 529-repo agent skill validation & scoring
> **Tool:** `skill-validator` v1.6.1 (Go CLI + importable library)
> **Repo:** https://github.com/agent-ecosystem/skill-validator
> **License:** MIT

---

## 1. Architecture Overview

`skill-validator` is a **Go-based CLI tool** that validates and scores [Agent Skill](https://agentskills.io) packages. It operates as both a standalone command-line binary and a set of importable Go library packages for custom tooling and CI pipelines.

### Core Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CLI Layer                          │
│  cmd/skill-validator/                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │ validate │ │ analyze  │ │ score / check    │    │
│  │ structure│ │ content  │ │                  │    │
│  └────┬─────┘ └────┬─────┘ └────────┬─────────┘    │
│       │              │              │               │
│  ┌────┴──────────────┴──────────────┴─────────┐     │
│  │          orchestrate package               │     │
│  │  Coordinates all validation checks         │     │
│  │  Returns unified types.Report              │     │
│  └────┬──────────────┬──────────────┬─────────┘     │
│       │              │              │               │
│  ┌────┴────┐   ┌─────┴────┐   ┌────┴─────┐         │
│  │structure│   │ content  │   │contamina-│         │
│  │  links  │   │ analysis │   │  tion    │         │
│  └─────────┘   └──────────┘   └──────────┘         │
│                                                     │
│  ┌──────────────────────────────────────────┐      │
│  │         evaluate + judge packages         │      │
│  │  LLM-as-judge scoring with caching         │      │
│  │  Built-in: Anthropic, OpenAI-compatible   │      │
│  └──────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

### Package Hierarchy

| Package | Purpose |
|---------|---------|
| `orchestrate` | Coordinates all validation checks, returns unified `types.Report` |
| `structure` | Directory layout, frontmatter, tokens, internal links |
| `content` | Content quality metrics (density, specificity, imperative ratio) |
| `contamination` | Cross-language contamination detection |
| `links` | External HTTP/HTTPS link validation |
| `skill` | SKILL.md parsing (frontmatter + body) |
| `skillcheck` | Skill detection and reference file analysis |
| `report` | Output formatting (text, JSON, markdown, GitHub annotations) |
| `types` | Shared data types (Report, Result, Level, etc.) |
| `judge` | LLM API calls for scoring (Anthropic, OpenAI-compatible) |
| `evaluate` | Scoring orchestration with caching and progress reporting |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Clean pass (no errors, no warnings) |
| 1 | Validation errors present |
| 2 | Warnings present, no errors |
| 3 | CLI/usage error (bad flags, missing args) |

### Installation Methods

```bash
# Homebrew (macOS)
brew tap agent-ecosystem/tap
brew install skill-validator

# Using Go
go install github.com/agent-ecosystem/skill-validator/cmd/skill-validator@latest

# Build from source
git clone https://github.com/agent-ecosystem/skill-validator.git
cd skill-validator
go build -o skill-validator ./cmd/skill-validator
```

---

## 2. Key Features for Ahmed's Stack

### 2.1 Structure Validation (`validate structure`)

Validates conformance with the [Agent Skills specification](https://agentskills.io/specification):

- **Directory structure**: `SKILL.md` exists; only recognized directories (`scripts/`, `references/`, `assets/`); no deep nesting; no orphan files
- **Frontmatter validation**: Required fields (`name`, `description`) present and valid; name is lowercase alphanumeric with hyphens (1-64 chars) and matches directory name; optional fields (`license`, `compatibility`, `metadata`, `allowed-tools`) conform to expected types
- **Extraneous file detection**: Flags `README.md`, `CHANGELOG.md`, `LICENSE` at skill root (human-facing, not agent-facing)
- **AGENTS.md warning**: Repo-level agent config should live outside skill directory
- **Keyword stuffing detection**: Descriptions with 8+ comma-separated short segments flagged as keyword lists
- **Token counting and limits**: Reports per-file and total token counts; warns when SKILL.md body exceeds 5,000 tokens
- **Holistic structure check**: Errors if non-standard content exceeds 10x standard structure content (and is over 25,000 tokens)
- **Markdown validation**: Checks for unclosed code fences (reported as errors — they break agent usability)
- **Internal link validation**: Verifies relative links within the skill resolve to actual files
- **Orphan detection**: Files in `scripts/`, `references/`, `assets/` that are never referenced from SKILL.md

### 2.2 Link Validation (`validate links`)

- Validates external HTTP/HTTPS links in SKILL.md
- Internal (relative) links are checked by `validate structure`
- Reports broken links with HTTP status codes

### 2.3 Content Analysis (`analyze content`)

Computes content quality metrics for SKILL.md and reference markdown files:

- **Density**: Information density per token
- **Specificity**: How specific vs. generic the instructions are
- **Imperative ratio**: Ratio of imperative (action-oriented) sentences
- Supports `--per-file` for granular analysis

### 2.4 Contamination Analysis (`analyze contamination`)

- Detects cross-language contamination (e.g., Python code in a JavaScript skill)
- Prevents skill quality degradation from mixed-language content

### 2.5 LLM-as-Judge Scoring (`score evaluate`)

Based on [agent-skill-analysis](https://github.com/agent-ecosystem/agent-skill-analysis) research — novelty is a key predictor of skill value:

- **Dimensions scored**: Clarity, Instructional Value, Token Efficiency, Actionability, Novelty
- **Providers supported**: Anthropic (default), OpenAI-compatible (Ollama, Together, Groq, Azure, etc.), Claude CLI
- **Modes**: `--skill-only`, `--refs-only`, `--display files`
- **Caching**: Results cached to avoid redundant API calls

```bash
export ANTHROPIC_API_KEY=your-key-here
skill-validator score evaluate <path>
skill-validator score evaluate --skill-only <path>
skill-validator score evaluate --refs-only <path>
skill-validator score evaluate --provider claude-cli <path>
```

### 2.6 Pre-Publish Check (`check`)

Runs everything (except LLM scoring) — the main CI command:

```bash
skill-validator check <path>
skill-validator check --only structure,links <path>
skill-validator check --skip contamination <path>
skill-validator check --per-file <path>
skill-validator check --strict <path>
```

Valid check groups: `structure`, `links`, `content`, `contamination`.

---

## 3. Integration Guide — Validating Hermes Agent Skills

### 3.1 Hermes Skill Layout

Hermes Agent uses the standard Agent Skills layout at `~/.hermes/skills/<name>/SKILL.md`:

```
~/.hermes/skills/
├── my-skill/
│   ├── SKILL.md              # Main skill file with YAML frontmatter
│   ├── scripts/              # Executable scripts
│   ├── references/           # Reference documentation
│   └── assets/               # Static assets
├── another-skill/
│   ├── SKILL.md
│   └── ...
```

### 3.2 Quick Start for Hermes Skills

```bash
# Install skill-validator
brew tap agent-ecosystem/tap
brew install skill-validator

# Validate all Hermes skills
skill-validator check --strict ~/.hermes/skills/

# Validate a single skill
skill-validator check ~/.hermes/skills/my-skill/

# Full validation with LLM scoring
export ANTHROPIC_API_KEY=your-key-here
skill-validator check --strict ~/.hermes/skills/
skill-validator score evaluate ~/.hermes/skills/my-skill/
```

### 3.3 Pre-Commit Hook for Hermes Skills

Add to `.pre-commit-config.yaml` in your skills repo:

```yaml
repos:
  - repo: https://github.com/agent-ecosystem/skill-validator
    rev: v1.6.1
    hooks:
      - id: skill-validator
        args: ["check", "--strict", "skills/"]
```

Platform-specific hooks available: `skill-validator-amp`, `skill-validator-cline`, `skill-validator-claude`, `skill-validator-codex`, `skill-validator-copilot`, `skill-validator-cursor`, `skill-validator-gemini`, `skill-validator-goose`, `skill-validator-kiro`, `skill-validator-mistral-vibe`, `skill-validator-roo-code`, `skill-validator-trae`, `skill-validator-windsurf`.

### 3.4 As a Go Library

For custom tooling or enterprise integration:

```go
import (
    "github.com/agent-ecosystem/skill-validator/orchestrate"
    "github.com/agent-ecosystem/skill-validator/judge"
    "github.com/agent-ecosystem/skill-validator/evaluate"
)

// Run all validation checks
report, err := orchestrate.Validate(ctx, "./my-skill", orchestrate.AllGroups)

// Run specific checks
report, err := orchestrate.RunContentAnalysis(ctx, "./my-skill")
report, err := orchestrate.RunContaminationAnalysis(ctx, "./my-skill")
report, err := orchestrate.RunLinkChecks(ctx, "./my-skill")

// LLM scoring with custom provider
client, err := judge.NewClient(judge.ClientOptions{
    Provider: "openai",
    APIKey:   os.Getenv("OPENAI_API_KEY"),
    Model:    "gpt-4o",
})
result, err := evaluate.EvaluateSkill(ctx, "./my-skill", client, evaluate.Options{
    MaxLen: judge.DefaultMaxContentLen,
})
```

### 3.5 Custom LLM Providers

For providers not built-in (AWS Bedrock, Azure OpenAI, local models):

```go
type LLMClient interface {
    Complete(ctx context.Context, systemPrompt, userContent string) (string, error)
    Provider() string
    ModelName() string
}
```

The `Complete` method receives the scoring rubric as system prompt and skill/reference content as user content. Return raw LLM response text; the judge package handles JSON parsing.

For OpenAI-compatible providers with custom base URL:

```go
client, err := judge.NewClient(judge.ClientOptions{
    Provider: "openai",
    APIKey:   os.Getenv("AZURE_OPENAI_API_KEY"),
    BaseURL:  "https://your-resource.openai.azure.com/openai/deployments/your-deployment",
    Model:    "gpt-4o",
})
```

---

## 4. Configuration Examples

### 4.1 Validation Rules — Flag Reference

| Flag | Effect |
|------|--------|
| `--strict` | Treat warnings as errors (exit 1 instead of 2) |
| `--skip-orphans` | Suppress warnings about unreferenced files in `scripts/`, `references/`, `assets/` |
| `--allow-extra-frontmatter` | Suppress warnings for non-spec frontmatter fields (e.g., `user-invokable`) |
| `--allow-flat-layouts` | Allow files at skill root without warnings |
| `--allow-dirs=evals,testing` | Accept specific non-standard directories without warnings |
| `--allow-nested-paths=assets/components` | Allow deep nesting only within specific skill-relative paths |
| `--exclude-token-paths=site` | Exclude specific subtrees from non-standard token accounting |
| `--only structure,links` | Run only specified check groups |
| `--skip contamination` | Skip specified check groups |
| `--per-file` | Per-file analysis in content analysis |
| `--emit-annotations` | GitHub Actions annotations output |
| `-o compact\|json\|markdown` | Output format selection |

### 4.2 Example: Permissive Configuration for Internal Skills

For skills not distributed cross-platform:

```bash
skill-validator check \
  --allow-flat-layouts \
  --allow-dirs=evals,testing,site \
  --exclude-token-paths=site,dist \
  --allow-extra-frontmatter \
  --skip-orphans \
  --strict \
  ~/.hermes/skills/
```

### 4.3 Example: Strict Cross-Platform Configuration

For skills intended for distribution:

```bash
skill-validator check \
  --strict \
  --emit-annotations \
  -o markdown \
  skills/
```

### 4.4 Example: Selective Check Groups

```bash
# Only structure and links (fast, no content analysis)
skill-validator check --only structure,links --strict skills/

# Skip contamination (useful for multi-language skills)
skill-validator check --skip contamination skills/

# Per-file content analysis
skill-validator analyze content --per-file skills/my-skill/
```

### 4.5 Example: LLM Scoring Configuration

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY=your-key-here
skill-validator score evaluate --provider anthropic skills/my-skill/

# OpenAI
export OPENAI_API_KEY=your-key-here
skill-validator score evaluate --provider openai skills/my-skill/

# Claude CLI (no API key needed if already authenticated)
skill-validator score evaluate --provider claude-cli skills/my-skill/

# Score only SKILL.md (skip references)
skill-validator score evaluate --skill-only skills/my-skill/

# Score only reference files
skill-validator score evaluate --refs-only skills/my-skill/

# Display files being scored
skill-validator score evaluate --display files skills/my-skill/
```

### 4.6 Example: Score Report (Multi-Model Comparison)

```bash
# Compare scores across different LLM providers/models
skill-validator score report \
  --providers anthropic,openai \
  --models claude-sonnet-4-5,gpt-4o \
  skills/my-skill/
```

---

## 5. CI/CD Integration

### 5.1 GitHub Actions Workflow

```yaml
name: Validate Skills

on:
  pull_request:
    paths:
      - "skills/**"
      - "**/SKILL.md"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install skill-validator
        run: |
          brew install agent-ecosystem/tap/skill-validator

      - name: Validate skills
        run: |
          skill-validator check --strict --emit-annotations skills/
          skill-validator check --strict -o markdown skills/ >> "$GITHUB_STEP_SUMMARY"

      - name: Upload JSON report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: skill-validation-report
          path: skills/validation-report.json
```

### 5.2 Multi-Skill Directory Validation

```bash
# Each skill is validated independently
skill-validator check skills/

# JSON output wraps individual skill reports in a skills array
# {
#   "passed": false,
#   "errors": 3,
#   "warnings": 1,
#   "skills": [
#     { "skill_dir": "...", "passed": true, "errors": 0, "warnings": 0, "results": [...] },
#     { "skill_dir": "...", "passed": false, "errors": 3, "warnings": 1, "results": [...] }
#   ]
# }
```

### 5.3 Pre-Commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/agent-ecosystem/skill-validator
    rev: v1.6.1
    hooks:
      - id: skill-validator
        args: ["check", "--strict", "skills/"]
```

### 5.4 CI Script for Changed Skills Only

```bash
#!/bin/bash
# .github/scripts/validate-skills.sh
set -euo pipefail

# Get changed skill directories
CHANGED_SKILLS=$(git diff --name-only --diff-filter=ACMRT origin/${GITHUB_BASE_REF}...HEAD | \
  grep -E '(^|/)SKILL\.md$' | \
  xargs -I{} dirname {} | \
  sort -u)

if [ -z "$CHANGED_SKILLS" ]; then
  echo "No skills changed, skipping validation"
  exit 0
fi

echo "Validating changed skills:"
echo "$CHANGED_SKILLS"

for skill_dir in $CHANGED_SKILLS; do
  echo "--- Validating $skill_dir ---"
  skill-validator check --strict --emit-annotations "$skill_dir"
done
```

### 5.5 Library Integration in Custom CI

```go
// main.go — custom CI validator
package main

import (
    "context"
    "fmt"
    "os"

    "github.com/agent-ecosystem/skill-validator/orchestrate"
)

func main() {
    ctx := context.Background()
    skillPath := os.Args[1]

    report, err := orchestrate.Validate(ctx, skillPath, orchestrate.AllGroups)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Validation error: %v\n", err)
        os.Exit(1)
    }

    if !report.Passed {
        for _, result := range report.Results {
            if result.Level == types.LevelError || result.Level == types.LevelWarning {
                fmt.Printf("[%s] %s: %s\n", result.Level, result.Category, result.Message)
            }
        }
        os.Exit(1)
    }

    fmt.Printf("Skill passed: %d checks\n", len(report.Results))
}
```

---

## 6. Pitfalls and Best Practices

### 6.1 Pitfalls

| Pitfall | Impact | Mitigation |
|---------|--------|------------|
| **Unclosed code fences** | Agents misinterpret everything after the fence as code — reported as errors | Always close ` ``` ` and `~~~` fences; run `validate structure` before committing |
| **Orphan files** | Files never referenced from SKILL.md are dead weight in the context window | Use `--skip-orphans` only when intentional; otherwise add references or remove files |
| **Keyword stuffing in descriptions** | Descriptions with 8+ comma-separated segments flagged as keyword lists | Write concise, natural descriptions |
| **Token bloat** | SKILL.md body > 5,000 tokens triggers warnings; 60k-token reference files pass spec but perform poorly | Use progressive disclosure — move large content to `references/` |
| **Cross-language contamination** | Mixed-language content degrades skill quality | Use `analyze contamination` to detect; keep skills single-language |
| **Non-standard directories** | Unknown directories at skill root produce warnings | Use `--allow-dirs` for known-good dirs; move content to `references/` or `assets/` |
| **Flat layout token accounting** | Files at skill root counted as non-standard content for token limits | Use `--allow-flat-layouts` or move files to standard directories |
| **LLM scoring API costs** | Scoring with large skills can be expensive | Use `--skill-only` or `--refs-only` to limit scope; results are cached |
| **OpenAI-compatible provider compatibility** | Some providers don't support `max_tokens` parameter | Check provider docs; use `--provider` to switch backends |
| **False sense of security** | Spec compliance ≠ practical quality | A spec-compliant skill with broken links or huge token count passes spec but performs poorly — always run full `check` |

### 6.2 Best Practices

1. **Run `check --strict` in CI** — Binary pass/fail for pull requests
2. **Use `--emit-annotations`** — Surfaces errors inline in GitHub PR diff
3. **Validate before publishing** — Run `score evaluate` with LLM scoring for quality assessment
4. **Keep descriptions concise** — Under 60 chars for Hermes in-repo standard; natural language, not keyword lists
5. **Use progressive disclosure** — SKILL.md for core instructions; `references/` for detailed docs; `scripts/` for executables
6. **Respect token budgets** — Keep SKILL.md body under 5,000 tokens; move large content to references
7. **Single-language skills** — Avoid cross-language contamination for better agent comprehension
8. **Standard directory structure** — `scripts/`, `references/`, `assets/` for maximum portability
9. **Pre-commit hooks** — Catch issues before they reach CI
10. **Cache LLM scoring results** — The `evaluate` package caches to avoid redundant API calls
11. **Use `--exclude-token-paths` for generated content** — Committed generated output that agents don't load as instructions
12. **Validate multi-skill directories** — Each skill is validated independently; one broken skill doesn't hide

### 6.3 Recommended Validation Pipeline for Ahmed's 529 Repos

```bash
#!/bin/bash
# validate-all-skills.sh — Run across all repos with skills

SKILLS_BASE="$HOME/.hermes/skills"
REPORT_DIR="./validation-reports"
mkdir -p "$REPORT_DIR"

# 1. Structure validation (fast, no API calls)
echo "=== Phase 1: Structure Validation ==="
skill-validator check --strict --only structure "$SKILLS_BASE/" \
  -o json > "$REPORT_DIR/structure-report.json"

# 2. Link validation (network calls, no API key needed)
echo "=== Phase 2: Link Validation ==="
skill-validator check --strict --only links "$SKILLS_BASE/" \
  -o json > "$REPORT_DIR/links-report.json"

# 3. Content analysis (local computation)
echo "=== Phase 3: Content Analysis ==="
skill-validator check --strict --only content "$SKILLS_BASE/" \
  -o json > "$REPORT_DIR/content-report.json"

# 4. Contamination analysis (local computation)
echo "=== Phase 4: Contamination Analysis ==="
skill-validator check --strict --only contamination "$SKILLS_BASE/" \
  -o json > "$REPORT_DIR/contamination-report.json"

# 5. LLM scoring (requires API key, cached)
echo "=== Phase 5: LLM Scoring ==="
if [ -n "$ANTHROPIC_API_KEY" ]; then
  for skill_dir in "$SKILLS_BASE"/*/; do
    skill_name=$(basename "$skill_dir")
    echo "Scoring: $skill_name"
    skill-provider score evaluate "$skill_dir" \
      -o json > "$REPORT_DIR/scores/${skill_name}.json" 2>/dev/null || \
    echo "  Warning: Scoring failed for $skill_name"
  done
else
  echo "Skipping LLM scoring (no ANTHROPIC_API_KEY)"
fi

echo "=== Validation Complete ==="
echo "Reports saved to: $REPORT_DIR"
```

---

## Summary

`skill-validator` is a comprehensive, production-ready tool for Agent Skill validation that goes well beyond spec compliance. For Ahmed's 529-repo ecosystem:

- **Structure validation** catches spec violations, orphan files, token bloat, and markdown issues
- **Link validation** ensures external references resolve
- **Content analysis** measures instruction quality
- **Contamination analysis** prevents cross-language mixing
- **LLM scoring** provides quality assessment across clarity, actionability, and novelty dimensions
- **CI/CD integration** via GitHub Actions, pre-commit hooks, or Go library import
- **Flexible configuration** via flags for permissive internal use or strict cross-platform distribution

The tool's exit codes (0/1/2/3) and `--strict` mode make it ideal for binary pass/fail CI pipelines, while its JSON and GitHub Actions annotation output formats integrate seamlessly with existing infrastructure.

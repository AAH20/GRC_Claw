# Agent Output Contract — Deep-Dive Analysis & Integration Guide

**Target:** Ahmed Hassan — validating Hermes Agent deliverables against local file contracts  
**Source:** [thecatnamedkuro/agent-output-contract](https://github.com/thecatnamedkuro/agent-output-contract) (v0.1.0, MIT)

---

## 1. Architecture Overview

### What It Is

A **local-first, zero-dependency Python CLI** that validates AI coding-agent deliverables against declarative file contracts. It reads a YAML or JSON contract file, walks a target directory tree, and asserts that:

- Required files exist
- Forbidden files are absent
- Files contain (or don't contain) specific text
- Regex patterns match (or don't match)
- JSON files parse
- Markdown headings are present
- File sizes are within bounds

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **CLI entry point** | `src/agent_output_contract/cli.py` | Argument parsing, contract loading, validation orchestration, exit codes |
| **Contract loader** | `load_contract()` in `cli.py` | Parses JSON (stdlib) or YAML (PyYAML optional) |
| **File matcher** | `match_paths()` in `cli.py` | Glob/fnmatch-based path resolution with dedup |
| **Validator** | `validate()` in `cli.py` | Runs all check types, collects `Failure` dataclasses |
| **Markdown parser** | `markdown_heading_titles()` in `cli.py` | Regex-based heading extraction (levels 1–6) |
| **Output formatter** | `format_failures()` in `cli.py` | Human-readable stderr output |
| **JSON reporter** | `--json` flag | Machine-readable `{"ok": bool, "failures": [...]}` |

### Data Flow

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Contract File  │────▶│ load_contract│────▶│  dict[str, Any] │
│  (YAML or JSON) │     │              │     │                 │
└─────────────────┘     └──────────────┘     └────────┬────────┘
                                                       │
┌─────────────────┐     ┌──────────────┐              ▼
│  Target Root    │────▶│  match_paths │────▶  ┌──────────────┐
│  (directory)    │     │  (fnmatch)   │      │   validate() │
└─────────────────┘     └──────────────┘      │              │
                                              │  • required  │
                                              │  • forbidden │
                                              │  • contains  │
                                              │  • regex     │
                                              │  • json      │
                                              │  • headings  │
                                              │  • max_bytes │
                                              └──────┬───────┘
                                                     │
                                              ┌──────▼───────┐
                                              │  Failures[]  │
                                              │  (dataclass) │
                                              └──────┬───────┘
                                                     │
                                       ┌─────────────┼─────────────┐
                                       ▼             ▼             ▼
                                  Exit 0       Exit 1        Exit 2
                                 (pass)      (fail)       (error)
```

### Key Design Decisions

1. **No network calls** — purely local file system operations
2. **No LLM invocation** — deterministic checks only
3. **Python 3.9+ compatible** — uses `from __future__ import annotations` for modern type hints
4. **Optional YAML** — JSON works out of the box; YAML requires `PyYAML>=6`
5. **Glob support** — `fnmatch` patterns for flexible file matching
6. **Multiline regex** — all regex checks use `re.MULTILINE` flag
7. **Stable dedup** — file matches are sorted and deduplicated

---

## 2. Key Features for Ahmed's Stack

### 2.1 Assert Required Files Exist

```yaml
required_files:
  - README.md
  - pyproject.toml
  - src/**/*.py
  - tests/test_*.py
```

- Each entry is a glob pattern
- At least one file must match each pattern
- Fails with `"no files matched 'pattern'"` if none found

### 2.2 Assert Forbidden Files Are Absent

```yaml
forbidden_paths:
  - .env
  - secrets/**
  - "*.key"
  - "node_modules/**"
```

- Fails if **any** file matches the pattern
- Reports up to 5 matching files in the error message

### 2.3 Assert Expected Text Appears

```yaml
files:
  README.md:
    contains:
      - "## Install"
      - "## Usage"
      - "MIT License"
```

- Simple substring search (case-sensitive)
- Fails with `"does not contain 'needle'"` 

### 2.4 Assert Forbidden Text Is Absent

```yaml
files:
  src/main.py:
    not_contains:
      - "TODO: fix this"
      - "HACK:"
      - "console.log"
```

- Fails if the text is found anywhere in the file

### 2.5 Regex Validation (Required)

```yaml
files:
  pyproject.toml:
    regex_contains:
      - '^version = "[0-9]+\.[0-9]+\.[0-9]+"'
      - '^name = "[a-z][a-z0-9_-]*"'
```

- Python `re` module with `MULTILINE` flag
- Anchors `^` and `$` work per-line
- Invalid regex patterns are caught and reported as failures

### 2.6 Regex Validation (Forbidden)

```yaml
files:
  src/**/*.py:
    not_regex_contains:
      - '^\s*print\('          # no print statements
      - 'import pdb'           # no debugger imports
      - '^\s*breakpoint\(\)'   # no breakpoints
```

### 2.7 JSON Parse Validation

```yaml
json_files:
  - package.json
  - tsconfig.json
  - "*.schema.json"
```

- Each matched file must be valid JSON
- Fails with parse error details if invalid

### 2.8 Markdown Heading Validation

```yaml
files:
  README.md:
    markdown_headings:
      - "Install"
      - "Usage"
      - "API Reference"
      - "Contributing"
```

- Case-sensitive heading title matching
- Heading level ignored (`#` through `######` all match)
- Trailing `#` characters are stripped

### 2.9 File Size Limits

```yaml
files:
  README.md:
    max_bytes: 20000
  docs/**/*.md:
    max_bytes: 50000
```

- Prevents bloated agent outputs
- Checks `path.stat().st_size`

### 2.10 Machine-Readable Output

```bash
agent-output-contract check --contract contract.yml --root . --json
```

Output:
```json
{
  "ok": false,
  "failures": [
    {
      "check": "required_files",
      "message": "no files matched 'CHANGELOG.md'"
    },
    {
      "check": "contains",
      "message": "README.md does not contain '## API Reference'"
    }
  ]
}
```

---

## 3. Integration Guide — Validating Hermes Agent Outputs

### 3.1 Installation

```bash
# From PyPI (when published)
pip install agent-output-contract

# From source
git clone https://github.com/thecatnamedkuro/agent-output-contract.git
cd agent-output-contract
pip install -e .

# With YAML support
pip install -e '.[yaml]'

# With all dev dependencies
pip install -e '.[test,yaml]'
```

### 3.2 Basic Usage

```bash
# Check with default contract path (agent-output-contract.yml)
agent-output-contract check --root .

# Specify contract and root explicitly
agent-output-contract check --contract contracts/hermes-output.yml --root ./output

# JSON output for programmatic consumption
agent-output-contract check --contract contract.yml --root . --json
```

### 3.3 Hermes Agent Integration Patterns

#### Pattern A: Post-Task Hook Validation

Add to `.hermes/hooks.json` or equivalent:

```json
{
  "hooks": {
    "post_task": [
      {
        "command": "agent-output-contract check --contract .hermes/contracts/task-output.yml --root .",
        "on_failure": "block"
      }
    ]
  }
}
```

#### Pattern B: Wrapper Script

```bash
#!/usr/bin/env bash
# hermes-validate.sh — run after Hermes agent completes a task

set -euo pipefail

CONTRACT_PATH="${1:-.hermes/contracts/default.yml}"
ROOT_PATH="${2:-.}"

echo "🔍 Validating agent output against contract..."
if agent-output-contract check --contract "$CONTRACT_PATH" --root "$ROOT_PATH" --json; then
    echo "✅ All contract checks passed"
    exit 0
else
    echo "❌ Contract validation failed"
    exit 1
fi
```

#### Pattern C: Python Integration

```python
import json
import subprocess
import sys
from pathlib import Path

def validate_agent_output(
    contract_path: Path,
    root_path: Path,
    raise_on_failure: bool = True
) -> dict:
    """
    Validate agent deliverables against a contract.
    
    Returns the JSON result dict.
    Raises RuntimeError on contract failure if raise_on_failure=True.
    """
    result = subprocess.run(
        [
            "agent-output-contract", "check",
            "--contract", str(contract_path),
            "--root", str(root_path),
            "--json"
        ],
        capture_output=True,
        text=True
    )
    
    payload = json.loads(result.stdout)
    
    if not payload["ok"] and raise_on_failure:
        failures = "\n".join(
            f"  [{f['check']}] {f['message']}"
            for f in payload["failures"]
        )
        raise RuntimeError(f"Contract validation failed:\n{failures}")
    
    return payload

# Usage in a Hermes skill or hook
try:
    result = validate_agent_output(
        contract_path=Path(".hermes/contracts/api-endpoint.yml"),
        root_path=Path(".")
    )
    print("Agent output validated successfully")
except RuntimeError as e:
    print(f"Validation error: {e}", file=sys.stderr)
    sys.exit(1)
```

#### Pattern D: Makefile Integration

```makefile
.PHONY: validate-agent-output

CONTRACT ?= .hermes/contracts/default.yml
ROOT ?= .

validate-agent-output:
	agent-output-contract check --contract $(CONTRACT) --root $(ROOT)

# Run after agent task
post-agent-task: validate-agent-output
	@echo "Agent task complete and validated"
```

### 3.4 Exit Code Handling

| Exit Code | Meaning | CI Action |
|-----------|---------|-----------|
| `0` | All checks passed | Continue pipeline |
| `1` | One or more checks failed | Fail the step, report failures |
| `2` | Contract or invocation error | Fail the step, check contract syntax |

```bash
# In CI scripts
agent-output-contract check --contract contract.yml --root .
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Contract validation passed"
elif [ $EXIT_CODE -eq 1 ]; then
    echo "❌ Contract validation failed"
    # Fail the build
    exit 1
else
    echo "⚠️ Contract error (check syntax)"
    exit 2
fi
```

---

## 4. Configuration Examples

### 4.1 Basic Python Project Contract

```yaml
# .hermes/contracts/python-project.yml
required_files:
  - README.md
  - pyproject.toml
  - src/**/__init__.py
  - tests/test_*.py

forbidden_paths:
  - .env
  - secrets/**
  - "*.key"
  - __pycache__/**
  - "*.pyc"

json_files:
  - pyproject.toml

files:
  README.md:
    contains:
      - "## Install"
      - "## Usage"
    markdown_headings:
      - "Install"
      - "Usage"
    max_bytes: 20000

  pyproject.toml:
    contains:
      - "[project]"
      - "[build-system]"
    regex_contains:
      - '^version = "[0-9]+\.[0-9]+\.[0-9]+"'
      - '^name = "[a-z][a-z0-9_-]*"'
    not_regex_contains:
      - '^DRAFT ONLY$'

  src/**/__init__.py:
    not_contains:
      - "TODO: implement"
      - "pass  # stub"

  tests/test_*.py:
    contains:
      - "def test_"
    not_contains:
      - "skip"
      - "xfail"
```

### 4.2 Web API Project Contract

```yaml
# .hermes/contracts/web-api.yml
required_files:
  - README.md
  - package.json
  - tsconfig.json
  - src/index.ts
  - src/routes/**/*.ts
  - tests/**/*.test.ts

forbidden_paths:
  - node_modules/**
  - .env
  - "*.log"
  - dist/**

json_files:
  - package.json
  - tsconfig.json

files:
  README.md:
    markdown_headings:
      - "Installation"
      - "API Endpoints"
      - "Configuration"
    contains:
      - "## API Endpoints"

  package.json:
    regex_contains:
      - '"scripts"'
      - '"test"'
      - '"build"'

  src/routes/**/*.ts:
    contains:
      - "Router"
      - "export"
    not_contains:
      - "any"
      - "@ts-ignore"
      - "console.log"

  tests/**/*.test.ts:
    contains:
      - "describe("
      - "it("
      - "expect("
```

### 4.3 Documentation-Heavy Contract

```yaml
# .hermes/contracts/docs.yml
required_files:
  - README.md
  - CHANGELOG.md
  - CONTRIBUTING.md
  - docs/**/*.md

forbidden_paths:
  - drafts/**
  - "*.draft.md"
  - "*.wip.md"

files:
  README.md:
    markdown_headings:
      - "Overview"
      - "Installation"
      - "Usage"
      - "API"
      - "Contributing"
      - "License"
    contains:
      - "MIT"
      - "Apache"
      - "BSD"
    max_bytes: 30000

  CHANGELOG.md:
    regex_contains:
      - '^## \[?[0-9]+\.[0-9]+\.[0-9]+\]?'
    markdown_headings:
      - "Changelog"

  CONTRIBUTING.md:
    markdown_headings:
      - "Development Setup"
      - "Pull Request Process"
      - "Code Style"

  docs/**/*.md:
    max_bytes: 50000
    not_contains:
      - "TODO: write this section"
      - "Lorem ipsum"
```

### 4.4 Minimal JSON Contract (No YAML Dependency)

```json
{
  "required_files": ["README.md", "src/main.py"],
  "forbidden_paths": [".env", "secrets/**"],
  "json_files": [],
  "files": {
    "README.md": {
      "contains": ["## Usage"],
      "markdown_headings": ["Usage"],
      "max_bytes": 10000
    },
    "src/main.py": {
      "not_contains": ["print(", "import pdb"],
      "regex_contains": ["^def main\\("]
    }
  }
}
```

### 4.5 Hermes Agent Task-Specific Contract

```yaml
# .hermes/contracts/hermes-task.yml
# Use this to validate outputs from Hermes Agent coding tasks

required_files:
  - README.md
  - pyproject.toml
  - src/**
  - tests/**

forbidden_paths:
  - .env
  - secrets/**
  - "*.key"
  - node_modules/**
  - __pycache__/**
  - ".pytest_cache/**"
  - "*.egg-info/**"

json_files:
  - pyproject.toml

files:
  README.md:
    contains:
      - "## Install"
      - "## Usage"
    markdown_headings:
      - "Install"
      - "Usage"
    max_bytes: 20000

  pyproject.toml:
    contains:
      - "[project]"
      - "[build-system]"
    regex_contains:
      - '^version = "[0-9]+\.[0-9]+\.[0-9]+"'
    not_regex_contains:
      - '^DRAFT ONLY$'

  src/**/*.py:
    not_contains:
      - "TODO: implement"
      - "pass  # stub"
      - "raise NotImplementedError"
    not_regex_contains:
      - '^\s*print\('
      - 'import pdb'
      - 'breakpoint\(\)'

  tests/**/*.py:
    contains:
      - "def test_"
    not_contains:
      - "@pytest.mark.skip"
      - "@pytest.mark.xfail"
```

---

## 5. CI/CD Integration

### 5.1 GitHub Actions

```yaml
# .github/workflows/agent-output-contract.yml
name: Agent Output Contract

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.9", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install agent-output-contract
        run: |
          python -m pip install --upgrade pip
          python -m pip install git+https://github.com/thecatnamedkuro/agent-output-contract.git
      
      - name: Validate agent output contract
        run: |
          agent-output-contract check \
            --contract .hermes/contracts/default.yml \
            --root .
      
      - name: Validate with JSON output (for annotations)
        if: failure()
        run: |
          agent-output-contract check \
            --contract .hermes/contracts/default.yml \
            --root . \
            --json > contract-result.json
          
          # Parse and annotate failures
          python -c "
          import json
          import sys
          
          with open('contract-result.json') as f:
              data = json.load(f)
          
          for failure in data.get('failures', []):
              print(f\"::error::{failure['message']}\")
          "
```

### 5.2 GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - validate

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

validate-agent-output:
  stage: validate
  image: python:3.11-slim
  before_script:
    - pip install --upgrade pip
    - pip install git+https://github.com/thecatnamedkuro/agent-output-contract.git
  script:
    - agent-output-contract check --contract .hermes/contracts/default.yml --root .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

### 5.3 Pre-commit Hook

```yaml
# .pre-commit-hooks.yaml (for the agent-output-contract repo itself)
- id: agent-output-contract
  name: Agent Output Contract
  description: Validate agent deliverables against file contracts
  entry: agent-output-contract check
  language: python
  pass_filenames: false
  args: ["--contract", ".hermes/contracts/default.yml", "--root", "."]
```

```yaml
# .pre-commit-config.yaml (for consumer repos)
repos:
  - repo: https://github.com/thecatnamedkuro/agent-output-contract
    rev: v0.1.0
    hooks:
      - id: agent-output-contract
        args: ["--contract", ".hermes/contracts/default.yml", "--root", "."]
```

### 5.4 Docker Integration

```dockerfile
# Dockerfile.validation
FROM python:3.11-slim

RUN pip install --no-cache-dir \
    git+https://github.com/thecatnamedkuro/agent-output-contract.git

WORKDIR /workspace
COPY . .

ENTRYPOINT ["agent-output-contract", "check"]
CMD ["--contract", ".hermes/contracts/default.yml", "--root", "."]
```

```bash
# Build and run
docker build -f Dockerfile.validation -t agent-contract-validator .
docker run --rm -v $(pwd):/workspace agent-contract-validator
```

### 5.5 CircleCI

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  validate-agent-output:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run:
          name: Install agent-output-contract
          command: |
            pip install git+https://github.com/thecatnamedkuro/agent-output-contract.git
      - run:
          name: Validate contract
          command: |
            agent-output-contract check \
              --contract .hermes/contracts/default.yml \
              --root .

workflows:
  validate:
    jobs:
      - validate-agent-output
```

---

## 6. Pitfalls and Best Practices

### 6.1 Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **YAML not installed** | `ValueError: YAML contracts require PyYAML` | Use JSON contracts or `pip install PyYAML` |
| **Glob patterns too broad** | `src/**/*.py` matches test files too | Use specific patterns like `src/main/**/*.py` |
| **Case-sensitive headings** | `markdown_headings: ["install"]` won't match `## Install` | Match exact case from the file |
| **Regex special characters** | Unescaped `.` or `(` in patterns | Always escape: `\.` `\(` |
| **Binary files** | `UnicodeDecodeError` on binary files | Tool falls back to `errors="ignore"` but may give false positives |
| **Large directories** | Slow performance on huge repos | Use specific `--root` paths, not `.` |
| **`.git` not excluded** | Tool already excludes `.git` | No action needed, but be aware |
| **Symlinks** | `rglob` may follow symlinks | Test behavior in your environment |
| **Empty contract** | No checks run, exits 0 | Always have at least one check |
| **Contract path relative** | `--contract` is resolved relative to CWD | Use absolute paths in CI |

### 6.2 Best Practices

#### 1. Keep Contracts Small and Focused

```yaml
# ✅ Good — focused contract
required_files:
  - README.md
  - src/main.py

# ❌ Bad — tries to check everything
required_files:
  - "**/*"
```

#### 2. Use Specific Glob Patterns

```yaml
# ✅ Good
files:
  src/routes/**/*.ts:
    contains: ["Router"]

# ❌ Bad — too broad
files:
  "**/*.ts":
    contains: ["Router"]
```

#### 3. Combine Multiple Check Types

```yaml
files:
  README.md:
    contains: ["## Install"]           # substring
    regex_contains: ["^## Install$"]    # precise line match
    markdown_headings: ["Install"]      # heading structure
    max_bytes: 20000                    # size limit
    not_contains: ["TODO"]              # forbidden text
```

#### 4. Version Your Contracts

```
.hermes/contracts/
├── v1/
│   └── api-endpoint.yml
├── v2/
│   └── api-endpoint.yml
└── default.yml -> v2/api-endpoint.yml
```

#### 5. Use JSON for Simple Contracts

JSON works without PyYAML and is sufficient for most use cases:

```json
{
  "required_files": ["README.md"],
  "files": {
    "README.md": {
      "contains": ["## Usage"]
    }
  }
}
```

#### 6. Test Contracts Locally Before CI

```bash
# Dry run
agent-output-contract check --contract .hermes/contracts/default.yml --root . --json

# Verbose debugging
python -c "
from agent_output_contract.cli import load_contract, validate
from pathlib import Path
import json

contract = load_contract(Path('.hermes/contracts/default.yml'))
failures = validate(contract, Path('.'))
for f in failures:
    print(f'[{f.check}] {f.message}')
"
```

#### 7. Fail Fast in CI

```yaml
# In CI, fail immediately on contract violation
- name: Validate contract
  run: |
    agent-output-contract check \
      --contract .hermes/contracts/default.yml \
      --root . \
      --json | python -c "
    import json, sys
    data = json.load(sys.stdin)
    if not data['ok']:
        for f in data['failures']:
            print(f'::error file=::{f[\"message\"]}')
        sys.exit(1)
    "
```

#### 8. Document Contract Requirements

Add a comment block at the top of each contract:

```yaml
# Contract: Python API Endpoint
# Created: 2026-10-01
# Owner: Ahmed Hassan
# Description: Validates that a Python API endpoint task produces
#              proper project structure, tests, and documentation.
#
# Usage:
#   agent-output-contract check --contract .hermes/contracts/python-api.yml --root .

required_files:
  - README.md
  # ... rest of contract
```

#### 9. Use `--json` for Programmatic Pipelines

```bash
# In a shell script
RESULT=$(agent-output-contract check --contract contract.yml --root . --json)
OK=$(echo "$RESULT" | python -c "import json,sys; print(json.load(sys.stdin)['ok'])")

if [ "$OK" = "True" ]; then
    echo "✅ Proceeding with deployment"
else
    echo "❌ Halting pipeline"
    echo "$RESULT" | python -c "
import json, sys
data = json.load(sys.stdin)
for f in data['failures']:
    print(f'  - [{f[\"check\"]}] {f[\"message\"]}')
"
    exit 1
fi
```

#### 10. Incremental Validation

For large repos, validate only changed files:

```bash
# Get changed files in PR
CHANGED_FILES=$(git diff --name-only origin/main...HEAD)

# Create a temporary contract with only changed files
python -c "
import json
import sys

changed = '''$CHANGED_FILES'''.strip().split('\n')
contract = {
    'required_files': changed,
    'files': {f: {} for f in changed}
}
print(json.dumps(contract))
" > /tmp/incremental-contract.json

agent-output-contract check --contract /tmp/incremental-contract.json --root .
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                  agent-output-contract                      │
├─────────────────────────────────────────────────────────────┤
│ Install:  pip install agent-output-contract                 │
│           pip install -e '.[yaml]'  (for YAML support)      │
│                                                             │
│ Run:      agent-output-contract check \                     │
│             --contract <path> \                             │
│             --root <dir> \                                  │
│             [--json]                                        │
│                                                             │
│ Exit 0:   All checks passed                                 │
│ Exit 1:   One or more checks failed                         │
│ Exit 2:   Contract or invocation error                      │
│                                                             │
│ Contract fields:                                            │
│   required_files:    [glob patterns]                       │
│   forbidden_paths:   [glob patterns]                       │
│   json_files:        [glob patterns]                       │
│   files:             { pattern: { checks } }               │
│     contains:        [strings]                             │
│     not_contains:    [strings]                             │
│     regex_contains:  [regex patterns]                      │
│     not_regex_contains: [regex patterns]                  │
│     markdown_headings: [titles]                            │
│     max_bytes:       integer                               │
│                                                             │
│ No network. No LLM. Local-only. Python 3.9+.                │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary for Ahmed Hassan

| Aspect | Recommendation |
|--------|---------------|
| **Install** | `pip install -e '.[yaml]'` for YAML support |
| **Contract location** | `.hermes/contracts/` directory |
| **Default contract** | `.hermes/contracts/default.yml` |
| **CI integration** | GitHub Actions workflow with JSON output |
| **Local validation** | Pre-commit hook or Makefile target |
| **Hermes integration** | Post-task hook or wrapper script |
| **Output format** | `--json` for programmatic use |
| **Python version** | 3.9+ (tested on 3.9 and 3.12) |
| **Dependencies** | Zero (stdlib only); PyYAML optional |

---

*Generated: 2026-10-01*  
*Source: [github.com/thecatnamedkuro/agent-output-contract](https://github.com/thecatnamedkuro/agent-output-contract)*

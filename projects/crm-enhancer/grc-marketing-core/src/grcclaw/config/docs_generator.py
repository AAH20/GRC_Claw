"""Configuration documentation generator for GRC_Claw.

Generates human-readable Markdown documentation from the configuration
schema and type definitions. Produces a complete reference document
covering every configuration section, field, type, default value,
and description.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .schema import CONFIG_SCHEMA, get_schema
from .types import Config


# ─── Documentation Generator ───────────────────────────────────────────────


class ConfigDocsGenerator:
    """Generates Markdown documentation for GRC_Claw configuration."""

    def __init__(self, schema: Optional[dict[str, Any]] = None):
        """Initialize the generator.

        Args:
            schema: JSON Schema dictionary. Uses built-in schema if None.
        """
        self.schema = schema or get_schema()

    def generate(self) -> str:
        """Generate complete Markdown documentation.

        Returns:
            Markdown string with full configuration reference.
        """
        sections: list[str] = []

        # Header
        sections.append(self._generate_header())

        # Table of contents
        sections.append(self._generate_toc())

        # Each configuration section
        for section_name, section_schema in self.schema.get("properties", {}).items():
            sections.append(self._generate_section(section_name, section_schema))

        # Environment variable reference
        sections.append(self._generate_env_var_reference())

        # Secret reference documentation
        sections.append(self._generate_secret_reference())

        return "\n\n".join(sections)

    def generate_to_file(self, path: str | Path) -> None:
        """Generate documentation and write to a file.

        Args:
            path: Destination file path.
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.generate(), encoding="utf-8")

    def _generate_header(self) -> str:
        """Generate the document header."""
        title = self.schema.get("title", "GRC_Claw Configuration")
        description = self.schema.get("description", "")
        return f"""# {title}

{description}

This document is auto-generated from the configuration schema.
Do not edit manually.

## Overview

GRC_Claw uses a layered configuration system with the following
precedence (highest to lowest):

1. **Environment variables** (`GRCCLAW_*`)
2. **Environment-specific config file** (`config.production.json`)
3. **Local config file** (`config.local.json`)
4. **Base config file** (`config.json`)
5. **Default values**

Configuration files can be JSON or YAML format.
"""

    def _generate_toc(self) -> str:
        """Generate table of contents."""
        lines = ["## Table of Contents", ""]
        for section_name in self.schema.get("properties", {}).keys():
            anchor = section_name.lower().replace("_", "-")
            lines.append(f"- [{section_name.title()}](#{anchor})")
        lines.append("- [Environment Variables](#environment-variables)")
        lines.append("- [Secret References](#secret-references)")
        return "\n".join(lines)

    def _generate_section(self, name: str, section_schema: dict[str, Any]) -> str:
        """Generate documentation for a single configuration section."""
        description = section_schema.get("description", "")
        properties = section_schema.get("properties", {})

        lines = [
            f"## {name.title()}",
            "",
            description,
            "",
            "| Field | Type | Default | Description |",
            "|-------|------|---------|-------------|",
        ]

        for field_name, field_schema in properties.items():
            field_type = self._format_type(field_schema)
            default = self._format_default(field_schema)
            desc = field_schema.get("description", "")
            # Add constraints to description
            constraints = self._format_constraints(field_schema)
            if constraints:
                desc = f"{desc} {constraints}" if desc else constraints
            lines.append(f"| `{field_name}` | {field_type} | {default} | {desc} |")

        return "\n".join(lines)

    def _generate_env_var_reference(self) -> str:
        """Generate environment variable reference section."""
        lines = [
            "## Environment Variables",
            "",
            "All configuration values can be overridden using environment",
            "variables with the `GRCCLAW_` prefix. Use double underscores",
            "for nested keys.",
            "",
            "```bash",
            "# Example: Override database pool size",
            "export GRCCLAW_DATABASE__POOL_SIZE=20",
            "",
            "# Example: Override nested config",
            "export GRCCLAW_SECURITY__SECRET_KEY=my-secret-key",
            "",
            "# Example: Boolean values",
            "export GRCCLAW_APPLICATION__DEBUG=true",
            "",
            "# Example: List values (comma-separated)",
            "export GRCCLAW_API__CORS_ORIGINS=https://a.com,https://b.com",
            "```",
            "",
            "### Naming Convention",
            "",
            "| Config Path | Environment Variable |",
            "|-------------|---------------------|",
        ]

        for section_name, section_schema in self.schema.get("properties", {}).items():
            for field_name in section_schema.get("properties", {}).keys():
                env_var = f"GRCCLAW_{section_name.upper()}__{field_name.upper()}"
                lines.append(f"| `{section_name}.{field_name}` | `{env_var}` |")

        return "\n".join(lines)

    def _generate_secret_reference(self) -> str:
        """Generate secret reference documentation."""
        return """## Secret References

Sensitive values can be referenced using secret references instead
of being stored in plaintext in configuration files.

### Format

```
${secret:backend://path#key}
```

### Supported Backends

| Backend | Format | Example |
|---------|--------|---------|
| Environment Variable | `${secret:env://VAR_NAME}` | `${secret:env://DATABASE_PASSWORD}` |
| File | `${secret:file:///path/to/file}` | `${secret:file:///run/secrets/db_pass}` |
| AWS Secrets Manager | `${secret:aws://secret-name#key}` | `${secret:aws://prod/grc-claw/db#password}` |
| HashiCorp Vault | `${secret:vault://path#key}` | `${secret:vault://secret/data/grc-claw#api_key}` |
| Azure Key Vault | `${secret:azure://vault/secret}` | `${secret:azure://my-vault/api-key}` |

### Usage in Configuration

```json
{
  "database": {
    "url": "postgresql+asyncpg://user:${secret:env://DB_PASSWORD}@localhost/grc_claw"
  },
  "security": {
    "secret_key": "${secret:aws://prod/grc-claw/app#secret_key}"
  }
}
```

### Resolution Order

Secrets are resolved in the following order:

1. Environment variables
2. File-based secrets
3. AWS Secrets Manager
4. HashiCorp Vault
5. Azure Key Vault

The first backend that can resolve the reference wins.
"""

    def _format_type(self, field_schema: dict[str, Any]) -> str:
        """Format the type of a field for display."""
        json_type = field_schema.get("type", "any")

        if json_type == "array":
            items = field_schema.get("items", {})
            item_type = items.get("type", "any")
            if "enum" in items:
                item_type = " | ".join(f"`{v}`" for v in items["enum"])
            return f"array<{item_type}>"
        elif json_type == "object":
            return "object"
        elif "enum" in field_schema:
            return " | ".join(f"`{v}`" for v in field_schema["enum"])
        else:
            return f"`{json_type}`"

    def _format_default(self, field_schema: dict[str, Any]) -> str:
        """Format the default value for display."""
        if "default" not in field_schema:
            return "—"

        default = field_schema["default"]
        if isinstance(default, str):
            return f'`"{default}"`'
        elif isinstance(default, bool):
            return f"`{str(default).lower()}`"
        elif isinstance(default, list):
            if not default:
                return "`[]`"
            return f"`{json.dumps(default)}`"
        elif isinstance(default, dict):
            return f"`{json.dumps(default)}`"
        else:
            return f"`{default}`"

    def _format_constraints(self, field_schema: dict[str, Any]) -> str:
        """Format validation constraints for display."""
        constraints: list[str] = []

        if "minimum" in field_schema:
            constraints.append(f"min: {field_schema['minimum']}")
        if "maximum" in field_schema:
            constraints.append(f"max: {field_schema['maximum']}")
        if "minLength" in field_schema:
            constraints.append(f"minLength: {field_schema['minLength']}")
        if "maxLength" in field_schema:
            constraints.append(f"maxLength: {field_schema['maxLength']}")
        if "pattern" in field_schema:
            constraints.append(f"pattern: `{field_schema['pattern']}`")
        if "format" in field_schema:
            constraints.append(f"format: {field_schema['format']}")
        if "exclusiveMinimum" in field_schema:
            constraints.append(f"exclusiveMin: {field_schema['exclusiveMinimum']}")

        if constraints:
            return f"({', '.join(constraints)})"
        return ""


# ─── Quick Access ──────────────────────────────────────────────────────────


def generate_config_docs(output_path: Optional[str | Path] = None) -> str:
    """Generate configuration documentation.

    Args:
        output_path: If provided, write documentation to this file.

    Returns:
        The generated Markdown documentation.
    """
    generator = ConfigDocsGenerator()
    docs = generator.generate()

    if output_path:
        generator.generate_to_file(output_path)

    return docs

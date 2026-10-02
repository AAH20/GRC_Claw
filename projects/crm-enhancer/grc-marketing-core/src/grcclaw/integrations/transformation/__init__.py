"""
Data Transformation — Schema mapping, field transformation, and data normalization.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class TransformationResult:
    """Result of a data transformation operation."""

    success: bool
    data: Any = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class FieldTransformer(ABC):
    """Abstract base class for field-level transformations."""

    @abstractmethod
    def transform(self, value: Any, context: dict[str, Any] | None = None) -> Any:
        """Transform a single field value."""
        ...

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate the input value before transformation."""
        ...


class DataNormalizer:
    """Normalizes data formats (dates, strings, numbers, booleans)."""

    @staticmethod
    def normalize_date(value: Any, input_format: str = "", output_format: str = "iso") -> str:
        """Normalize date strings to a standard format."""
        if value is None:
            return ""

        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str):
            if input_format:
                dt = datetime.strptime(value, input_format)
            else:
                # Try common formats
                for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
                           "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"):
                    try:
                        dt = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return value  # Return as-is if no format matches
        else:
            return str(value)

        if output_format == "iso":
            return dt.isoformat()
        elif output_format == "timestamp":
            return str(int(dt.timestamp()))
        else:
            return dt.strftime(output_format)

    @staticmethod
    def normalize_string(value: Any, case: str = "lower", strip: bool = True) -> str:
        """Normalize string values."""
        if value is None:
            return ""
        result = str(value)
        if strip:
            result = result.strip()
        if case == "lower":
            result = result.lower()
        elif case == "upper":
            result = result.upper()
        elif case == "title":
            result = result.title()
        return result

    @staticmethod
    def normalize_number(value: Any, decimal_places: int = 2) -> float:
        """Normalize numeric values."""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return round(float(value), decimal_places)
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r"[^\d.\-]", "", str(value))
            return round(float(cleaned), decimal_places)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def normalize_boolean(value: Any) -> bool:
        """Normalize boolean values."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "y", "on")
        if isinstance(value, (int, float)):
            return value != 0
        return bool(value)

    @staticmethod
    def normalize_email(value: Any) -> str:
        """Normalize email addresses."""
        if value is None:
            return ""
        return str(value).strip().lower()

    @staticmethod
    def normalize_phone(value: Any, country_code: str = "") -> str:
        """Normalize phone numbers."""
        if value is None:
            return ""
        digits = re.sub(r"\D", "", str(value))
        if country_code and not digits.startswith(country_code):
            digits = country_code + digits
        return digits


class DataValidator:
    """Validates data against rules and schemas."""

    def __init__(self):
        self._rules: list[Callable] = []

    def add_rule(self, rule: Callable) -> None:
        """Add a validation rule."""
        self._rules.append(rule)

    def validate(self, data: Any, schema: dict[str, Any] | None = None) -> TransformationResult:
        """Validate data against rules and optional schema."""
        errors = []
        warnings = []

        # Schema validation
        if schema:
            schema_errors = self._validate_schema(data, schema)
            errors.extend(schema_errors)

        # Custom rules
        for rule in self._rules:
            try:
                result = rule(data)
                if isinstance(result, str):
                    errors.append(result)
                elif isinstance(result, tuple):
                    msg, is_error = result
                    if is_error:
                        errors.append(msg)
                    else:
                        warnings.append(msg)
            except Exception as e:
                errors.append(f"Validation rule error: {e}")

        return TransformationResult(
            success=len(errors) == 0,
            data=data,
            errors=errors,
            warnings=warnings,
        )

    def _validate_schema(self, data: Any, schema: dict[str, Any]) -> list[str]:
        """Validate data against a simple schema definition."""
        errors = []

        if not isinstance(data, dict):
            return [f"Expected dict, got {type(data).__name__}"]

        for field_name, field_spec in schema.items():
            if isinstance(field_spec, dict):
                required = field_spec.get("required", False)
                field_type = field_spec.get("type")
                field_value = data.get(field_name)

                if required and field_value is None:
                    errors.append(f"Required field '{field_name}' is missing")
                    continue

                if field_value is not None and field_type:
                    type_valid = self._check_type(field_value, field_type)
                    if not type_valid:
                        errors.append(
                            f"Field '{field_name}' expected type '{field_type}', "
                            f"got '{type(field_value).__name__}'"
                        )

                # Nested validation
                if "properties" in field_spec and isinstance(field_value, dict):
                    nested_errors = self._validate_schema(field_value, field_spec["properties"])
                    errors.extend(f"{field_name}.{e}" for e in nested_errors)

                # Array item validation
                if "items" in field_spec and isinstance(field_value, list):
                    for i, item in enumerate(field_value):
                        if isinstance(field_spec["items"], dict):
                            item_errors = self._validate_schema(item, field_spec["items"])
                            errors.extend(f"{field_name}[{i}].{e}" for e in item_errors)

        return errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches an expected type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        if isinstance(expected, tuple):
            return isinstance(value, expected)
        return isinstance(value, expected)


@dataclass
class TransformationRule:
    """A single transformation rule."""

    source_path: str
    target_path: str
    transform: Optional[Callable] = None
    condition: Optional[Callable] = None
    default_value: Any = None
    required: bool = False


class SchemaMapper:
    """
    Maps data from one schema to another using transformation rules.

    Supports:
    - Field renaming and restructuring
    - Nested field mapping
    - Conditional transformations
    - Default values
    - Type conversions
    """

    def __init__(self, rules: list[TransformationRule] | str = ""):
        if isinstance(rules, str):
            # Parse rules from a JSON string or mapping definition
            self.rules = self._parse_rules(rules)
        else:
            self.rules = rules

    def _parse_rules(self, definition: str) -> list[TransformationRule]:
        """Parse transformation rules from a JSON string."""
        try:
            parsed = json.loads(definition)
            rules = []
            for source, target in parsed.items():
                if isinstance(target, str):
                    rules.append(TransformationRule(source_path=source, target_path=target))
                elif isinstance(target, dict):
                    rules.append(TransformationRule(
                        source_path=source,
                        target_path=target.get("target", source),
                        transform=target.get("transform"),
                        condition=target.get("condition"),
                        default_value=target.get("default"),
                        required=target.get("required", False),
                    ))
            return rules
        except json.JSONDecodeError:
            return []

    def transform(self, data: Any) -> TransformationResult:
        """Transform input data according to the mapping rules."""
        errors = []
        warnings = []

        if not isinstance(data, dict):
            return TransformationResult(
                success=False,
                errors=[f"Expected dict input, got {type(data).__name__}"],
            )

        result = {}

        for rule in self.rules:
            try:
                # Check condition
                if rule.condition and not rule.condition(data):
                    continue

                # Extract source value
                source_value = self._get_nested_value(data, rule.source_path)

                if source_value is None:
                    if rule.required:
                        errors.append(f"Required field '{rule.source_path}' is missing")
                    elif rule.default_value is not None:
                        self._set_nested_value(result, rule.target_path, rule.default_value)
                    continue

                # Apply transformation
                if rule.transform:
                    try:
                        transformed = rule.transform(source_value, data)
                    except Exception as e:
                        errors.append(f"Transform error for '{rule.source_path}': {e}")
                        continue
                else:
                    transformed = source_value

                self._set_nested_value(result, rule.target_path, transformed)

            except Exception as e:
                errors.append(f"Rule error for '{rule.source_path}': {e}")

        # Include unmapped fields if no rules specified
        if not self.rules:
            result = data

        return TransformationResult(
            success=len(errors) == 0,
            data=result,
            errors=errors,
            warnings=warnings,
            metadata={"rules_applied": len(self.rules)},
        )

    def _get_nested_value(self, data: dict, path: str) -> Any:
        """Get a value from a nested dict using dot notation."""
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                idx = int(key)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None
        return current

    def _set_nested_value(self, data: dict, path: str, value: Any) -> None:
        """Set a value in a nested dict using dot notation."""
        keys = path.split(".")
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value


class FieldTransformerRegistry:
    """Registry of reusable field transformers."""

    def __init__(self):
        self._transformers: dict[str, Callable] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default transformers."""
        self.register("uppercase", lambda v: str(v).upper() if v else v)
        self.register("lowercase", lambda v: str(v).lower() if v else v)
        self.register("strip", lambda v: str(v).strip() if v else v)
        self.register("title_case", lambda v: str(v).title() if v else v)
        self.register("snake_case", lambda v: re.sub(r"(?<!^)(?=[A-Z])", "_", str(v)).lower() if v else v)
        self.register("camel_case", lambda v: re.sub(r"_([a-z])", lambda m: m.group(1).upper(), str(v)) if v else v)
        self.register("kebab_case", lambda v: re.sub(r"_", "-", str(v)).lower() if v else v)
        self.register("to_int", lambda v: int(v) if v is not None else 0)
        self.register("to_float", lambda v: float(v) if v is not None else 0.0)
        self.register("to_str", lambda v: str(v) if v is not None else "")
        self.register("to_bool", lambda v: str(v).lower() in ("true", "1", "yes", "y", "on") if v else False)
        self.register("to_list", lambda v: [v] if not isinstance(v, list) else v)
        self.register("first", lambda v: v[0] if isinstance(v, list) and v else None)
        self.register("last", lambda v: v[-1] if isinstance(v, list) and v else None)
        self.register("length", lambda v: len(v) if v is not None else 0)
        self.register("join", lambda v, sep=",": sep.join(str(i) for i in v) if isinstance(v, list) else str(v))
        self.register("split", lambda v, sep=",": str(v).split(sep) if v else [])
        self.register("date_iso", lambda v: DataNormalizer.normalize_date(v))
        self.register("date_ts", lambda v: DataNormalizer.normalize_date(v, output_format="timestamp"))
        self.register("email_normalize", lambda v: DataNormalizer.normalize_email(v))
        self.register("phone_normalize", lambda v: DataNormalizer.normalize_phone(v))
        self.register("number_normalize", lambda v: DataNormalizer.normalize_number(v))
        self.register("remove_nulls", lambda v: {k: val for k, val in v.items() if val is not None} if isinstance(v, dict) else v)
        self.register("flatten", lambda v: self._flatten(v))

    @staticmethod
    def _flatten(d: dict, parent_key: str = "", sep: str = ".") -> dict:
        """Flatten a nested dict."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(SchemaMapper._flatten(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def register(self, name: str, transformer: Callable) -> None:
        """Register a transformer."""
        self._transformers[name] = transformer

    def get(self, name: str) -> Optional[Callable]:
        """Get a transformer by name."""
        return self._transformers.get(name)

    def list_transformers(self) -> list[str]:
        """List all registered transformer names."""
        return list(self._transformers.keys())

    def apply(self, name: str, value: Any, *args, **kwargs) -> Any:
        """Apply a named transformer to a value."""
        transformer = self._transformers.get(name)
        if not transformer:
            raise ValueError(f"Unknown transformer: {name}")
        return transformer(value, *args, **kwargs)

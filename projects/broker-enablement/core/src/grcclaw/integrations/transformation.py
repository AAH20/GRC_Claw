"""
Data Transformation — schema mapping, field transformation, normalization, and validation.

Provides:
- SchemaMapper: maps fields between source and target schemas
- FieldTransformer: applies transformations to individual fields
- DataNormalizer: normalizes data formats (dates, strings, numbers)
- DataValidator: validates data against JSON Schema or custom rules
- TransformationRule: declarative transformation rules
- TransformationResult: result of a transformation operation
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TransformationType(str, Enum):
    """Types of field transformations."""

    MAP = "map"
    RENAME = "rename"
    CONVERT = "convert"
    FORMAT = "format"
    FILTER = "filter"
    DEFAULT = "default"
    COMPUTE = "compute"
    SPLIT = "split"
    JOIN = "join"
    TRIM = "trim"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    REPLACE = "replace"
    EXTRACT = "extract"
    CUSTOM = "custom"


@dataclass
class TransformationRule:
    """A declarative transformation rule."""

    source_field: str
    target_field: str
    transform_type: TransformationType = TransformationType.MAP
    params: dict[str, Any] = field(default_factory=dict)
    condition: Callable[[Any], bool] | None = None
    required: bool = False
    default_value: Any = None

    def should_apply(self, data: dict[str, Any]) -> bool:
        """Check if this rule should apply to the given data."""
        if self.condition:
            return self.condition(data)
        return True


@dataclass
class TransformationResult:
    """Result of a transformation operation."""

    success: bool
    data: Any = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fields_transformed: int = 0
    fields_skipped: int = 0
    duration_ms: float = 0.0

    @property
    def failed(self) -> bool:
        return not self.success

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


class FieldTransformer:
    """
    Transforms individual field values.

    Supports built-in transformations and custom transform functions.
    """

    def __init__(self):
        self._custom_transforms: dict[str, Callable[[Any, dict[str, Any]], Any]] = {}

    def register_transform(
        self,
        name: str,
        func: Callable[[Any, dict[str, Any]], Any],
    ) -> None:
        """Register a custom transform function."""
        self._custom_transforms[name] = func

    def transform(
        self,
        value: Any,
        transform_type: TransformationType | str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Transform a single value.

        Args:
            value: The value to transform.
            transform_type: Type of transformation to apply.
            params: Additional parameters for the transformation.

        Returns:
            The transformed value.
        """
        params = params or {}
        ttype = TransformationType(transform_type) if isinstance(transform_type, str) else transform_type

        if ttype == TransformationType.MAP:
            mapping = params.get("mapping", {})
            return mapping.get(value, mapping.get("__default__", value))

        elif ttype == TransformationType.RENAME:
            # Rename is handled at the schema level, not field level
            return value

        elif ttype == TransformationType.CONVERT:
            target_type = params.get("target_type", "string")
            return self._convert_type(value, target_type)

        elif ttype == TransformationType.FORMAT:
            fmt = params.get("format", "{}")
            if isinstance(value, (int, float)):
                return fmt.format(value)
            return str(value)

        elif ttype == TransformationType.FILTER:
            # Filter is handled at the collection level
            return value

        elif ttype == TransformationType.DEFAULT:
            if value is None or value == "":
                return params.get("default_value")
            return value

        elif ttype == TransformationType.COMPUTE:
            expression = params.get("expression")
            if expression:
                return self._safe_eval(expression, {"value": value, "data": params.get("context", {})})
            return value

        elif ttype == TransformationType.SPLIT:
            separator = params.get("separator", ",")
            if isinstance(value, str):
                return [v.strip() for v in value.split(separator)]
            return value

        elif ttype == TransformationType.JOIN:
            separator = params.get("separator", ", ")
            if isinstance(value, list):
                return separator.join(str(v) for v in value)
            return value

        elif ttype == TransformationType.TRIM:
            if isinstance(value, str):
                return value.strip()
            return value

        elif ttype == TransformationType.UPPERCASE:
            if isinstance(value, str):
                return value.upper()
            return value

        elif ttype == TransformationType.LOWERCASE:
            if isinstance(value, str):
                return value.lower()
            return value

        elif ttype == TransformationType.REPLACE:
            pattern = params.get("pattern", "")
            replacement = params.get("replacement", "")
            if isinstance(value, str):
                return re.sub(pattern, replacement, value)
            return value

        elif ttype == TransformationType.EXTRACT:
            pattern = params.get("pattern", "")
            group = params.get("group", 0)
            if isinstance(value, str):
                match = re.search(pattern, value)
                if match:
                    return match.group(group)
            return None

        elif ttype == TransformationType.CUSTOM:
            func_name = params.get("function")
            if func_name and func_name in self._custom_transforms:
                return self._custom_transforms[func_name](value, params)
            return value

        return value

    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert a value to a target type."""
        if value is None:
            return None

        try:
            if target_type == "string":
                return str(value)
            elif target_type == "integer":
                return int(value)
            elif target_type == "float":
                return float(value)
            elif target_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)
            elif target_type == "datetime":
                if isinstance(value, str):
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                return value
            elif target_type == "list":
                if isinstance(value, list):
                    return value
                return [value]
            elif target_type == "dict":
                if isinstance(value, dict):
                    return value
                return {"value": value}
            else:
                return value
        except (ValueError, TypeError) as e:
            logger.warning("Type conversion failed for %r -> %s: %s", value, target_type, e)
            return value

    def _safe_eval(self, expression: str, context: dict[str, Any]) -> Any:
        """Safely evaluate a simple expression."""
        try:
            # Only allow simple attribute access and basic operations
            allowed_names = {"value": context.get("value"), "data": context.get("data", {})}
            return eval(expression, {"__builtins__": {}}, allowed_names)
        except Exception as e:
            logger.warning("Expression evaluation failed: %s: %s", expression, e)
            return None


class DataNormalizer:
    """
    Normalizes data formats.

    Handles:
    - Date/time normalization
    - String normalization (whitespace, encoding)
    - Number normalization
    - Boolean normalization
    - Null/empty normalization
    """

    def __init__(self):
        self._date_formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]

    def normalize(self, data: dict[str, Any], rules: dict[str, str] | None = None) -> dict[str, Any]:
        """
        Normalize all fields in a data record.

        Args:
            data: The data record to normalize.
            rules: Optional field-specific normalization rules.

        Returns:
            Normalized data record.
        """
        result = {}
        rules = rules or {}

        for key, value in data.items():
            rule = rules.get(key)
            result[key] = self.normalize_field(value, rule)

        return result

    def normalize_field(self, value: Any, rule: str | None = None) -> Any:
        """Normalize a single field value."""
        if value is None:
            return None

        if rule:
            if rule == "datetime":
                return self.normalize_datetime(value)
            elif rule == "string":
                return self.normalize_string(value)
            elif rule == "number":
                return self.normalize_number(value)
            elif rule == "boolean":
                return self.normalize_boolean(value)
            elif rule == "trim":
                return str(value).strip() if value else value
            elif rule == "lowercase":
                return str(value).lower() if value else value
            elif rule == "uppercase":
                return str(value).upper() if value else value

        # Auto-detect type
        if isinstance(value, str):
            return self.normalize_string(value)
        elif isinstance(value, (int, float)):
            return self.normalize_number(value)
        elif isinstance(value, bool):
            return value
        elif isinstance(value, list):
            return [self.normalize_field(v) for v in value]
        elif isinstance(value, dict):
            return {k: self.normalize_field(v) for k, v in value.items()}

        return value

    def normalize_datetime(self, value: str) -> datetime | None:
        """Normalize a datetime string to a datetime object."""
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            return None

        for fmt in self._date_formats:
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except ValueError:
                continue

        # Try ISO format as fallback
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

        return None

    def normalize_string(self, value: Any) -> str:
        """Normalize a string value."""
        if value is None:
            return ""
        s = str(value)
        # Normalize whitespace
        s = re.sub(r"\s+", " ", s)
        # Remove control characters
        s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
        return s.strip()

    def normalize_number(self, value: Any) -> int | float | None:
        """Normalize a numeric value."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return value
        try:
            s = str(value).strip().replace(",", "")
            if "." in s:
                return float(s)
            return int(s)
        except (ValueError, TypeError):
            return None

    def normalize_boolean(self, value: Any) -> bool:
        """Normalize a boolean value."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on", "y")
        if isinstance(value, (int, float)):
            return value != 0
        return bool(value)

    def normalize_null(self, value: Any, null_values: set[str] | None = None) -> Any:
        """Normalize null-like values to None."""
        if value is None:
            return None
        null_values = null_values or {"", "null", "NULL", "None", "none", "N/A", "n/a", "-"}
        if isinstance(value, str) and value.strip() in null_values:
            return None
        return value


class DataValidator:
    """
    Validates data against JSON Schema or custom validation rules.
    """

    def __init__(self):
        self._custom_validators: dict[str, Callable[[Any], bool]] = {}

    def register_validator(self, name: str, func: Callable[[Any], bool]) -> None:
        """Register a custom field validator."""
        self._custom_validators[name] = func

    def validate(
        self,
        data: dict[str, Any],
        schema: dict[str, Any] | None = None,
        rules: list[dict[str, Any]] | None = None,
    ) -> TransformationResult:
        """
        Validate data against a schema and/or custom rules.

        Args:
            data: The data to validate.
            schema: Optional JSON Schema dict.
            rules: Optional list of custom validation rules.

        Returns:
            TransformationResult with validation outcome.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if schema:
            schema_errors = self._validate_schema(data, schema)
            errors.extend(schema_errors)

        if rules:
            for rule in rules:
                rule_errors = self._validate_rule(data, rule)
                errors.extend(rule_errors)

        success = len(errors) == 0
        return TransformationResult(
            success=success,
            data=data if success else None,
            errors=errors,
            warnings=warnings,
        )

    def _validate_schema(self, data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
        """Validate data against a JSON Schema (subset)."""
        errors: list[str] = []

        schema_type = schema.get("type")
        if schema_type == "object":
            if not isinstance(data, dict):
                return [f"Expected object, got {type(data).__name__}"]

            required = schema.get("required", [])
            for field_name in required:
                if field_name not in data or data[field_name] is None:
                    errors.append(f"Required field '{field_name}' is missing or null")

            properties = schema.get("properties", {})
            for field_name, field_schema in properties.items():
                if field_name in data and data[field_name] is not None:
                    field_errors = self._validate_field(data[field_name], field_schema, field_name)
                    errors.extend(field_errors)

        elif schema_type == "array":
            if not isinstance(data, list):
                return [f"Expected array, got {type(data).__name__}"]
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(data):
                    item_errors = self._validate_field(item, items_schema, f"[{i}]")
                    errors.extend(item_errors)

        else:
            type_errors = self._validate_field(data, schema, "root")
            errors.extend(type_errors)

        return errors

    def _validate_field(self, value: Any, schema: dict[str, Any], path: str) -> list[str]:
        """Validate a single field against its schema."""
        errors: list[str] = []
        schema_type = schema.get("type")

        if schema_type == "string":
            if not isinstance(value, str):
                errors.append(f"{path}: expected string, got {type(value).__name__}")
            else:
                if "minLength" in schema and len(value) < schema["minLength"]:
                    errors.append(f"{path}: string too short (min {schema['minLength']})")
                if "maxLength" in schema and len(value) > schema["maxLength"]:
                    errors.append(f"{path}: string too long (max {schema['maxLength']})")
                if "pattern" in schema and not re.match(schema["pattern"], value):
                    errors.append(f"{path}: does not match pattern {schema['pattern']}")
                if "enum" in schema and value not in schema["enum"]:
                    errors.append(f"{path}: must be one of {schema['enum']}")

        elif schema_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"{path}: expected integer, got {type(value).__name__}")
            else:
                if "minimum" in schema and value < schema["minimum"]:
                    errors.append(f"{path}: below minimum ({schema['minimum']})")
                if "maximum" in schema and value > schema["maximum"]:
                    errors.append(f"{path}: above maximum ({schema['maximum']})")

        elif schema_type == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{path}: expected number, got {type(value).__name__}")

        elif schema_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"{path}: expected boolean, got {type(value).__name__}")

        elif schema_type == "array":
            if not isinstance(value, list):
                errors.append(f"{path}: expected array, got {type(value).__name__}")

        elif schema_type == "object":
            if not isinstance(value, dict):
                errors.append(f"{path}: expected object, got {type(value).__name__}")

        return errors

    def _validate_rule(self, data: dict[str, Any], rule: dict[str, Any]) -> list[str]:
        """Validate data against a custom rule."""
        errors: list[str] = []
        field = rule.get("field", "")
        validator = rule.get("validator", "")

        value = data.get(field)

        if validator in self._custom_validators:
            if not self._custom_validators[validator](value):
                errors.append(f"{field}: custom validation '{validator}' failed")
        elif validator == "required":
            if value is None or value == "":
                errors.append(f"{field}: is required")
        elif validator == "email":
            if value and not re.match(r"^[^@]+@[^@]+\.[^@]+$", str(value)):
                errors.append(f"{field}: invalid email format")
        elif validator == "url":
            if value and not re.match(r"^https?://", str(value)):
                errors.append(f"{field}: invalid URL format")
        elif validator == "regex":
            pattern = rule.get("pattern", "")
            if value and not re.match(pattern, str(value)):
                errors.append(f"{field}: does not match pattern '{pattern}'")
        elif validator == "range":
            min_val = rule.get("min")
            max_val = rule.get("max")
            if value is not None:
                try:
                    num = float(value)
                    if min_val is not None and num < min_val:
                        errors.append(f"{field}: below minimum ({min_val})")
                    if max_val is not None and num > max_val:
                        errors.append(f"{path}: above maximum ({max_val})")
                except (ValueError, TypeError):
                    errors.append(f"{field}: not a valid number for range check")

        return errors


class SchemaMapper:
    """
    Maps data between different schemas using declarative rules.

    Supports:
    - Field mapping and renaming
    - Nested field mapping
    - Array mapping
    - Conditional mapping
    - Default values
    - Type conversion
    """

    def __init__(self):
        self._rules: list[TransformationRule] = []
        self._field_transformer = FieldTransformer()
        self._normalizer = DataNormalizer()
        self._validator = DataValidator()

    @property
    def rules(self) -> list[TransformationRule]:
        return list(self._rules)

    def add_rule(self, rule: TransformationRule) -> None:
        """Add a transformation rule."""
        self._rules.append(rule)

    def add_rules(self, rules: list[TransformationRule]) -> None:
        """Add multiple transformation rules."""
        self._rules.extend(rules)

    def clear_rules(self) -> None:
        """Clear all rules."""
        self._rules.clear()

    def map(
        self,
        data: dict[str, Any] | list[dict[str, Any]],
        *,
        normalize: bool = True,
        validate: bool = False,
        schema: dict[str, Any] | None = None,
    ) -> TransformationResult:
        """
        Map data from source schema to target schema.

        Args:
            data: Source data (single record or list of records).
            normalize: Whether to normalize values during mapping.
            validate: Whether to validate the result.
            schema: Optional JSON Schema for validation.

        Returns:
            TransformationResult with mapped data.
        """
        import time
        start = time.monotonic()

        if isinstance(data, list):
            results = []
            errors = []
            warnings = []
            transformed = 0
            skipped = 0

            for i, record in enumerate(data):
                result = self._map_record(record, normalize=normalize)
                if result.success:
                    results.append(result.data)
                    transformed += result.fields_transformed
                    skipped += result.fields_skipped
                    warnings.extend(result.warnings)
                else:
                    errors.extend([f"Record {i}: {e}" for e in result.errors])

            duration_ms = (time.monotonic() - start) * 1000

            if validate and schema:
                validation = self._validator.validate(results, schema)
                if not validation.success:
                    errors.extend(validation.errors)

            return TransformationResult(
                success=len(errors) == 0,
                data=results if len(errors) == 0 else None,
                errors=errors,
                warnings=warnings,
                fields_transformed=transformed,
                fields_skipped=skipped,
                duration_ms=duration_ms,
            )
        else:
            result = self._map_record(data, normalize=normalize)

            if validate and schema and result.success:
                validation = self._validator.validate(result.data, schema)
                if not validation.success:
                    result.success = False
                    result.errors.extend(validation.errors)
                    result.data = None

            result.duration_ms = (time.monotonic() - start) * 1000
            return result

    def _map_record(
        self,
        record: dict[str, Any],
        *,
        normalize: bool = True,
    ) -> TransformationResult:
        """Map a single record."""
        result: dict[str, Any] = {}
        errors: list[str] = []
        warnings: list[str] = []
        transformed = 0
        skipped = 0

        for rule in self._rules:
            if not rule.should_apply(record):
                skipped += 1
                continue

            # Get source value
            source_value = self._get_nested_value(record, rule.source_field)

            if source_value is None:
                if rule.required:
                    errors.append(f"Required field '{rule.source_field}' is missing")
                    continue
                if rule.default_value is not None:
                    result[rule.target_field] = rule.default_value
                    transformed += 1
                else:
                    skipped += 1
                continue

            # Apply transformation
            try:
                transformed_value = self._field_transformer.transform(
                    source_value,
                    rule.transform_type,
                    rule.params,
                )
            except Exception as e:
                warnings.append(f"Transform failed for '{rule.source_field}': {e}")
                transformed_value = source_value

            # Normalize if requested
            if normalize and isinstance(transformed_value, (str, int, float)):
                transformed_value = self._normalizer.normalize_field(transformed_value)

            # Set target value
            self._set_nested_value(result, rule.target_field, transformed_value)
            transformed += 1

        return TransformationResult(
            success=len(errors) == 0,
            data=result,
            errors=errors,
            warnings=warnings,
            fields_transformed=transformed,
            fields_skipped=skipped,
        )

    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        """Get a value from a nested dict using dot notation."""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None
            if current is None:
                return None
        return current

    def _set_nested_value(self, data: dict[str, Any], path: str, value: Any) -> None:
        """Set a value in a nested dict using dot notation."""
        parts = path.split(".")
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def infer_schema(self, data: list[dict[str, Any]], sample_size: int = 100) -> dict[str, Any]:
        """
        Infer a JSON Schema from sample data.

        Args:
            data: List of sample records.
            sample_size: Maximum number of records to sample.

        Returns:
            Inferred JSON Schema.
        """
        if not data:
            return {"type": "object", "properties": {}}

        sample = data[:sample_size]
        properties: dict[str, Any] = {}

        # Collect all keys
        all_keys: set[str] = set()
        for record in sample:
            if isinstance(record, dict):
                all_keys.update(record.keys())

        for key in all_keys:
            values = [r.get(key) for r in sample if isinstance(r, dict) and key in r and r[key] is not None]
            properties[key] = self._infer_field_schema(key, values)

        return {
            "type": "object",
            "properties": properties,
        }

    def _infer_field_schema(self, key: str, values: list[Any]) -> dict[str, Any]:
        """Infer schema for a single field from its values."""
        if not values:
            return {"type": "string"}

        types = set()
        for v in values:
            if isinstance(v, bool):
                types.add("boolean")
            elif isinstance(v, int):
                types.add("integer")
            elif isinstance(v, float):
                types.add("number")
            elif isinstance(v, str):
                types.add("string")
            elif isinstance(v, list):
                types.add("array")
            elif isinstance(v, dict):
                types.add("object")
            else:
                types.add("string")

        if len(types) == 1:
            field_type = types.pop()
        elif types == {"integer", "number"}:
            field_type = "number"
        else:
            field_type = "string"

        schema: dict[str, Any] = {"type": field_type}

        if field_type == "string":
            max_len = max(len(str(v)) for v in values)
            schema["maxLength"] = max_len
        elif field_type in ("integer", "number"):
            nums = [v for v in values if isinstance(v, (int, float))]
            if nums:
                schema["minimum"] = min(nums)
                schema["maximum"] = max(nums)

        return schema

    def create_mapping_from_schema(
        self,
        source_schema: dict[str, Any],
        target_schema: dict[str, Any],
        field_mapping: dict[str, str] | None = None,
    ) -> list[TransformationRule]:
        """
        Auto-generate transformation rules from source and target schemas.

        Args:
            source_schema: Source JSON Schema.
            target_schema: Target JSON Schema.
            field_mapping: Optional explicit field name mapping.

        Returns:
            List of generated TransformationRules.
        """
        rules: list[TransformationRule] = []
        field_mapping = field_mapping or {}

        source_props = source_schema.get("properties", {})
        target_props = target_schema.get("properties", {})

        for target_field, target_schema_info in target_props.items():
            # Find corresponding source field
            source_field = field_mapping.get(target_field, target_field)

            if source_field in source_props:
                source_type = source_props[source_field].get("type", "string")
                target_type = target_schema_info.get("type", "string")

                transform_type = TransformationType.MAP
                params: dict[str, Any] = {}

                if source_type != target_type:
                    transform_type = TransformationType.CONVERT
                    params["target_type"] = target_type

                rules.append(TransformationRule(
                    source_field=source_field,
                    target_field=target_field,
                    transform_type=transform_type,
                    params=params,
                    required=target_field in target_schema.get("required", []),
                ))

        return rules

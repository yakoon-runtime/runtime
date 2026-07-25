"""Parse yds-v1.yaml into an intermediate Schema representation."""

from __future__ import annotations

from pathlib import Path

from .model import ClassDef, PropertyDef, Schema

_BASE_TYPES = {"block", "inline"}

_BLOCK_EXTENDERS: set[str] = set()
_INLINE_EXTENDERS: set[str] = set()


def _to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def _is_base_type(name: str, data: dict) -> bool:
    """Check if a type entry is a base/abstract type (block, inline)."""
    return name in _BASE_TYPES and "properties" in data and "extends" not in data


def _is_concrete_type(name: str, data: dict) -> bool:
    """Check if a type entry is a concrete type (has extends or is document)."""
    if name in ("schema", "runtime", "children_fields", *list(data.keys())):
        if name in ("schema", "runtime", "children_fields", "version", "status"):
            return False
    if name in _BASE_TYPES and "extends" not in data:
        return False
    # metadata keys that are not types
    if name in ("version", "status", "schema", "runtime", "children_fields"):
        return False
    # must have properties or be a known reference
    if "properties" not in data:
        return False
    return True


_BASE_TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "boolean": "bool",
}


def _resolve_items(items_val: object) -> str | None:
    """Resolve the ``items`` field of an array property to a type name.

    ``items`` can be a plain string (type name) or a dict for nested arrays
    (e.g. ``table.rows → list[list[str]]``).
    """
    if isinstance(items_val, str):
        return _BASE_TYPE_MAP.get(items_val, items_val)
    if isinstance(items_val, dict):
        inner = items_val.get("items", "string")
        inner_resolved = (
            _BASE_TYPE_MAP.get(inner, inner) if isinstance(inner, str) else "str"
        )
        return f"list[{inner_resolved}]"
    return None


def _parse_properties(props: dict, required: list[str] | None) -> list[PropertyDef]:
    """Parse property definitions from YAML."""
    result = []
    required = required or []
    for pname, pdata in props.items():
        type_ref = pdata.get("type", "string")
        items_ref = None
        if type_ref == "array":
            items_ref = _resolve_items(pdata.get("items", "string"))

        const = pdata.get("const")
        nullable = pdata.get("nullable", False)
        default = pdata.get("default")
        enum_values = pdata.get("enum")
        is_required = pname in required

        result.append(
            PropertyDef(
                name=pname,
                type_ref=type_ref,
                required=is_required,
                default=default,
                nullable=nullable,
                const=const,
                enum_values=enum_values,
                items_ref=items_ref,
            )
        )
    return result


def parse(path: str | Path) -> Schema:
    """Parse a yds-v1.yaml file into a Schema."""
    import yaml

    with open(path) as f:
        raw = yaml.safe_load(f)

    schema = Schema()
    classes: list[ClassDef] = []

    # Pass 1: collect all defined type names
    type_names: set[str] = set()
    for key, value in raw.items():
        if isinstance(value, dict) and "properties" in value:
            type_names.add(key)

    # Pass 2: build ClassDef for every concrete type
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        if key in ("schema", "runtime", "children_fields", "version", "status"):
            continue

        # Skip abstract base types (block, inline) — they become union aliases
        if key in _BASE_TYPES and "extends" not in value:
            continue

        props = value.get("properties", {})
        required = value.get("required", [])
        extends = value.get("extends")
        type_value = value.get("type", key)
        description = value.get("description", "")

        parsed_props = _parse_properties(props, required)

        # Map extends to Python base class name
        base = None
        if extends == "block":
            base = "Block"
        elif extends == "inline":
            base = "Inline"
        # else: standalone (no extends) inherits YdsModel directly

        class_name = _to_pascal(key)
        is_root = key == "document"

        classes.append(
            ClassDef(
                name=class_name,
                type_value=type_value,
                base=base,
                properties=parsed_props,
                description=description.strip(),
                is_root=is_root,
            )
        )

    schema.classes = classes
    return schema

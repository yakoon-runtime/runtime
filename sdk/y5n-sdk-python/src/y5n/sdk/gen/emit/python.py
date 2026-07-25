"""Emit Python source code from the intermediate Schema representation."""

from __future__ import annotations

from ..model import ClassDef, PropertyDef, Schema

_HEADER = """\
# -----------------------------------------------------------------------------
#  GENERATED FILE
#
#  This file was generated from spec/yds/yds-v1.yaml.
#  DO NOT EDIT — changes will be overwritten.
# -----------------------------------------------------------------------------

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, TypeAlias


class YdsModel:
    __slots__ = ()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for f in dataclasses.fields(self):  # type: ignore[arg-type]
            value = getattr(self, f.name)
            if value is None:
                continue
            if isinstance(value, YdsModel):
                result[f.name] = value.to_dict()
            elif isinstance(value, list):
                if not value:
                    continue
                result[f.name] = [
                    item.to_dict() if isinstance(item, YdsModel) else item
                    for item in value
                ]
            else:
                result[f.name] = value
        return result
"""

_TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "boolean": "bool",
}


def _to_pascal(name: str) -> str:
    return "".join(word.capitalize() for word in name.split("_"))


def _resolve_type(prop: PropertyDef) -> str:
    if prop.type_ref == "array" and prop.items_ref:
        # Nested arrays (e.g. table.rows) are always list-of-primitive
        if prop.items_ref.startswith("list["):
            inner = prop.items_ref
            outer = "list"
        else:
            inner = _TYPE_MAP.get(prop.items_ref, _to_pascal(prop.items_ref))
            # Model references use covariant Sequence; primitives use list
            outer = "list" if prop.items_ref in _TYPE_MAP else "Sequence"
        py_type = f"{outer}[{inner}]"
    elif prop.type_ref in _TYPE_MAP:
        py_type = _TYPE_MAP[prop.type_ref]
    else:
        py_type = _to_pascal(prop.type_ref)

    if prop.nullable and prop.const is None:
        py_type = f"{py_type} | None"

    return py_type


def _double_quoted(val: str) -> str:
    return '"' + val[1:-1].replace('"', '\\"') + '"'


def _default_repr(prop: PropertyDef) -> str | None:
    if prop.const is not None:
        val = repr(prop.const)
        return _double_quoted(val) if isinstance(prop.const, str) else val
    if prop.default is not None:
        val = repr(prop.default)
        return _double_quoted(val) if isinstance(prop.default, str) else val
    if prop.nullable:
        return "None"
    if prop.type_ref == "array" and prop.items_ref:
        return "field(default_factory=list)"
    return None


def _field_line(prop: PropertyDef) -> str:
    py_type = _resolve_type(prop)
    default = _default_repr(prop)
    if default is not None:
        return f"    {prop.name}: {py_type} = {default}"
    return f"    {prop.name}: {py_type}"


def _emit_class(cls: ClassDef, *, add_type_discriminator: bool = False) -> str:
    lines = [f"\n\n@dataclass(slots=True, kw_only=True)\nclass {cls.name}(YdsModel):"]

    if cls.description:
        lines.append(f'    """{cls.description}"""')

    all_props = list(cls.properties)
    if add_type_discriminator and cls.type_value:
        has_type = any(p.name == _DISCRIMINATOR_FIELD for p in all_props)
        if not has_type:
            all_props = all_props + [
                PropertyDef(
                    name=_DISCRIMINATOR_FIELD,
                    type_ref="string",
                    const=cls.type_value,
                )
            ]

    if not all_props:
        lines.append("    pass")
        return "\n".join(lines)

    for prop in all_props:
        lines.append(_field_line(prop))

    return "\n".join(lines)


_DISCRIMINATOR_FIELD = "type"


def emit(schema: Schema) -> str:
    """Emit the full Python source for the generated models module."""
    parts = [_HEADER]

    block_types: list[ClassDef] = []
    inline_types: list[ClassDef] = []
    standalone: list[ClassDef] = []
    document_cls: ClassDef | None = None
    header_cls: ClassDef | None = None

    for cls in schema.classes:
        if cls.is_root:
            document_cls = cls
        elif cls.name == "Header":
            header_cls = cls
        elif cls.base == "Block":
            block_types.append(cls)
        elif cls.base == "Inline":
            inline_types.append(cls)
        else:
            standalone.append(cls)

    # Emit block types (with type discriminator)
    for cls in block_types:
        parts.append(_emit_class(cls, add_type_discriminator=True))

    # Emit inline types (with type discriminator)
    for cls in inline_types:
        parts.append(_emit_class(cls, add_type_discriminator=True))

    # Emit standalone types
    for cls in standalone:
        parts.append(_emit_class(cls))

    # Emit Header before Document
    if header_cls:
        parts.append(_emit_class(header_cls))

    # Emit Document last
    if document_cls:
        parts.append(_emit_class(document_cls))

    # Emit union type aliases at the end
    block_names = [cls.name for cls in block_types]
    inline_names = [cls.name for cls in inline_types]

    if block_names:
        parts.append(
            "\n\nBlock: TypeAlias = ("
            + "\n".join(f"    {n} |" for n in block_names[:-1])
            + f"\n    {block_names[-1]}\n)"
        )
    if inline_names:
        parts.append(
            "\n\nInline: TypeAlias = ("
            + "\n".join(f"    {n} |" for n in inline_names[:-1])
            + f"\n    {inline_names[-1]}\n)"
        )

    return "".join(parts)

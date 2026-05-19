from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, StrictUndefined


@dataclass(slots=True)
class JinjaRenderEngine:
    env: Environment

    def __init__(self):
        self.env = Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            enable_async=False,
            undefined=StrictUndefined,  # !!
            finalize=finalize_template_value,
        )
        register_filters(self.env)

    def render_str(self, template_str: str, *, context: dict) -> str:
        return self.env.from_string(template_str).render(**context)

    def render_any(self, obj: Any, *, context: dict) -> Any:
        if obj is None:
            return None
        if isinstance(obj, str):
            return self.render_str(obj, context=context)
        if isinstance(obj, Mapping):
            return {k: self.render_any(v, context=context) for k, v in obj.items()}
        if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
            rendered = [self.render_any(v, context=context) for v in obj]
            return tuple(rendered) if isinstance(obj, tuple) else rendered
        return obj


# ----------------------------------
# HELPER
# ----------------------------------


def ljust(value: str, width: int) -> str:
    return value.ljust(width)


def register_filters(environment):
    environment.filters["ljust"] = ljust


# ----------------------------------
# TEMPLATE PROTECTION
# ----------------------------------


def finalize_template_value(value):
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value

    raise TypeError(
        f"Cannot render object of type {str(value)} directly. "
        "Render a field instead, e.g. user.name."
    )

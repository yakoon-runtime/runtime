from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, StrictUndefined

from yakoon.platform.runtime.render.jinja.filters import register_filters


@dataclass(slots=True)
class JinjaRenderer:
    env: Environment

    def __init__(self):
        self.env = Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            enable_async=False,
            undefined=StrictUndefined,  # !!
        )
        register_filters(self.env)

    async def render_str(self, template_str: str, *, context: dict) -> str:
        return self.env.from_string(template_str).render(**context)

    async def render_any(self, obj: Any, *, context: dict) -> Any:
        if obj is None:
            return None
        if isinstance(obj, str):
            return await self.render_str(obj, context=context)
        if isinstance(obj, Mapping):
            return {
                k: await self.render_any(v, context=context) for k, v in obj.items()
            }
        if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
            rendered = [await self.render_any(v, context=context) for v in obj]
            return tuple(rendered) if isinstance(obj, tuple) else rendered
        return obj

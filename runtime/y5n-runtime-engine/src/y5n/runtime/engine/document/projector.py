from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from y5n.runtime.api.document.normalize import normalize
from y5n.runtime.api.resources import ResourceRef


class Projector:
    """
    Unified projector.

    Responsibilities:
      - render a view into a UI document
    """

    def __init__(
        self,
        on_render: OnRender,
        on_render_str: Callable[[str, dict], str],
        on_compile: OnCompile,
        tree=None,
    ) -> None:
        self.on_render = on_render
        self.on_render_str = on_render_str
        self.on_compile = on_compile
        self._tree = tree

    async def project(
        self,
        *,
        resource: ResourceRef,
        state: dict[str, Any] | None = None,
    ) -> dict:

        if state is None:
            state = {}

        text = self.on_render(resource=resource, context=state)

        document = normalize(self.on_compile(text=text, context={}))

        return document


# ----------------------------------
# PORTS
# ----------------------------------


class OnRender(Protocol):
    def __call__(self, *, resource: ResourceRef, context: dict[str, Any]) -> str: ...


class OnCompile(Protocol):
    def __call__(self, *, text: str, context: dict) -> dict: ...

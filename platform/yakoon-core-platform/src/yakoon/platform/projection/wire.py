from __future__ import annotations

from typing import Protocol

from yakoon.base.resources import ResourceRef

from .compiler import build_compiler
from .projector import Projector
from .rendering import build_renderer


def build_projector(on_resource: OnGetResourceRef) -> Projector:

    # --- RENDERING ---

    renderer = build_renderer()

    # --- COMPILING ---

    compiler = build_compiler()

    # --- PROJECTING ---

    projector = Projector(
        on_render=renderer.render,
        on_compile=compiler.compile,
        on_resource=on_resource,
    )
    return projector


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetResourceRef(Protocol):
    def __call__(self, *, scope: str, key: str, lang: str) -> ResourceRef | None: ...

from __future__ import annotations

from .compiler import build_compiler
from .projector import Projector
from .rendering import build_renderer


def build_projector() -> Projector:

    # --- RENDERING ---

    renderer = build_renderer()

    # --- COMPILING ---

    compiler = build_compiler()

    # --- PROJECTING ---

    projector = Projector(
        on_render=renderer.render,
        on_compile=compiler.compile,
    )
    return projector

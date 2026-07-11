from y5n.runtime.projection import Projector

from .compiler import build_compiler
from .renderer import build_renderer


def build_projector() -> Projector:

    # --- RENDERING ---

    renderer = build_renderer()

    # --- COMPILING ---

    compiler = build_compiler()

    # --- PROJECTING ---

    projector = Projector(
        on_render=renderer.render,
        on_render_str=renderer.render_str,
        on_compile=compiler.compile,
    )
    return projector

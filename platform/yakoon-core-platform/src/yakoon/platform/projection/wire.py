from .compiler import build_compiler
from .projector import TemplateProjector
from .rendering import build_renderer


def build_projector() -> TemplateProjector:

    # --- RENDERING ---

    renderer = build_renderer()

    # --- COMPILING ---

    compiler = build_compiler()

    # --- PROJECTING ---

    projector = TemplateProjector(
        on_render=renderer.render,
        on_compile=compiler.compile,
    )
    return projector

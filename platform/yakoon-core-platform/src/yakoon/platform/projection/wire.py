from .compiler import TemplateProjectionCompiler
from .projector import TemplateProjector
from .rendering import build_renderer


def build_projector() -> TemplateProjector:

    renderer = build_renderer()

    compiler = TemplateProjectionCompiler()

    projector = TemplateProjector(
        on_render=renderer.render,
        on_compile=compiler.compile,
    )
    return projector

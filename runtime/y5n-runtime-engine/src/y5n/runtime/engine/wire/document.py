"""Document pipeline assembly (the wire layer composes).

Builds the whole document stack — jinja engine, resource loader, renderer,
compiler, and projector — exactly once. ``build_runtime`` consumes the stack
instead of rebuilding its pieces, so the jinja environment and the compiler
are shared between the projector and the root ports / bus adapters.
"""

from __future__ import annotations

from dataclasses import dataclass

from y5n.runtime.engine.document.compiler import Compiler
from y5n.runtime.engine.document.projector import Projector
from y5n.runtime.engine.document.rendering import JinjaRenderEngine, Renderer
from y5n.runtime.engine.resources import PackageReader

from .compiler import build_compiler


@dataclass(frozen=True)
class DocumentStack:
    projector: Projector
    renderer: Renderer
    compiler: Compiler
    jinja: JinjaRenderEngine
    loader: PackageReader


def build_document_stack(tree=None) -> DocumentStack:

    jinja = JinjaRenderEngine()
    loader = PackageReader()

    renderer = Renderer(
        on_load_resource=loader.get_text,
        on_engine_render=jinja.render_str,
    )

    compiler = build_compiler()

    projector = Projector(
        on_render=renderer.render,
        on_render_str=renderer.render_str,
        on_compile=compiler.compile,
        tree=tree,
    )

    return DocumentStack(
        projector=projector,
        renderer=renderer,
        compiler=compiler,
        jinja=jinja,
        loader=loader,
    )

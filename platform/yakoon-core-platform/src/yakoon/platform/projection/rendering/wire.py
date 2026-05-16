from yakoon.platform.resources import PackageReader

from .engine import JinjaRenderEngine
from .renderer import Renderer


def build_renderer() -> Renderer:

    jinja = JinjaRenderEngine()
    loader = PackageReader()

    renderer = Renderer(
        on_load_resource=loader.get_text,
        on_engine_render=jinja.render_str,
    )

    return renderer

from yakoon.platform.resources import PackageResourceLoader

from .engine import JinjaRenderEngine
from .renderer import Renderer


def build_renderer() -> Renderer:

    jinja = JinjaRenderEngine()
    loader = PackageResourceLoader()

    renderer = Renderer(
        on_load_resource=loader.get_text,
        on_engine_render=jinja.render_str,
    )

    return renderer

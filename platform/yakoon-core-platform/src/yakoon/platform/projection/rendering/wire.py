from yakoon.platform.resources import PackageResourceLoader

from .engine import JinjaRenderEngine
from .renderer import TemplateProjectionRenderer


def build_renderer() -> TemplateProjectionRenderer:

    jinja = JinjaRenderEngine()
    loader = PackageResourceLoader()

    renderer = TemplateProjectionRenderer(
        on_load_resource=loader.get_text,
        on_engine_render=jinja.render_str,
    )

    return renderer

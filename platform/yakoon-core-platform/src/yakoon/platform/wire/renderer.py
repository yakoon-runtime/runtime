from yakoon.platform.projection.rendering import JinjaRenderEngine, Renderer
from yakoon.platform.resources import PackageReader


def build_renderer() -> Renderer:

    jinja = JinjaRenderEngine()
    loader = PackageReader()

    renderer = Renderer(
        on_load_resource=loader.get_text,
        on_engine_render=jinja.render_str,
    )

    return renderer

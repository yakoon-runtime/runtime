from pathlib import Path

from y5n.api.data import DataRequest
from y5n.api.dsl import out, view
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnSourceRead
from y5n.base.plugins.ports import OnCompile, OnJinjaRender, OnProject


async def run(space: NodeSpace):
    key = space.request.arg(0)

    if not key:
        projection = await space.ports.get(OnProject)(
            space=space,
            state={},
        )
        yield out(projection)
        return

    on_source = space.ports.get(OnSourceRead)
    result = await on_source(DataRequest(f"system:nodes --by-key {key}"))

    if result.status == "ok":
        node_data = result.one()
        resources = node_data.get("resources", {})
        man_res = resources.get("man", {})
        template_path = man_res.get("default")

        if template_path:
            template = Path(template_path).read_text()
            html = space.ports.get(OnJinjaRender)(
                template,
                context={"key": key},
            )
            projection = space.ports.get(OnCompile)(text=html, context={})
            yield view(clear=True)
            yield out(projection)
            return

    projection = await space.ports.get(OnProject)(
        space=space,
        state={"key": key},
    )

    yield out(projection)

from pathlib import Path

from y5n.api.data import DataRequest
from y5n.api.dsl import out, view
from y5n.api.nodes import NodeSpace
from y5n.api.ports import COMPILE, JINJA_RENDER, PROJECT, SOURCE_READ


async def run(space: NodeSpace):
    key = space.request.arg(0)

    if not key:
        projection = await space.ports.get(PROJECT)(
            space=space,
            state={},
        )
        yield out(projection)
        return

    on_source = space.ports.get(SOURCE_READ)

    # Try contextual path first (e.g. man add from /grant/group)
    lookup = key
    current = space.session.cwd
    if current and current != "/" and not key.startswith("/"):
        lookup = f"{current}/{key}"

    result = await on_source(DataRequest(f"system:nodes --by-key {lookup}"))
    if result.status != "ok" and lookup != key:
        result = await on_source(DataRequest(f"system:nodes --by-key {key}"))
    else:
        key = lookup

    if result.status == "ok":
        node_data = result.one()
        resources = node_data.get("resources", {})
        man_res = resources.get("man", {})
        template_path = man_res.get("default")

        if template_path:
            template = Path(template_path).read_text()
            html = space.ports.get(JINJA_RENDER)(
                template,
                context={"key": key},
            )
            projection = space.ports.get(COMPILE)(text=html, context={})
            yield view(clear=True)
            yield out(projection)
            return

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"key": key},
    )

    yield out(projection)

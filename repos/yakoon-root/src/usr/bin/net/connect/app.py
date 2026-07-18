from y5n.api.data import DataRequest
from y5n.api.dsl import out, view
from y5n.api.nodes import NodeSpace
from y5n.api.ports import SOURCE_READ
from y5n.api.documents import to_text


async def run(space: NodeSpace):
    name = space.request.arg(0)
    on_source = space.ports.get(SOURCE_READ)
    result = await on_source(DataRequest(f"system:runtimes --resolve {name}"))
    if not result.rows:
        yield out(to_text(f"Unknown runtime: {name}"))
        return

    url = result.rows[0]["url"]
    yield view(connect=url, connect_name=name)

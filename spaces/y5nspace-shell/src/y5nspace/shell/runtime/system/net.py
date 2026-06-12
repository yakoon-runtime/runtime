from y5n.api.data import DataRequest
from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnSourceRead
from y5n.api.projections import to_text


async def run(space: NodeSpace):

    on_source = space.ports.get(OnSourceRead)
    result = await on_source(DataRequest("system:runtimes --list"))

    if not result.rows:
        yield out(to_text("no runtimes configured"))
        return

    lines = [f"  {r['name']:<20} {r['url']}" for r in result.rows]
    yield out(to_text("\n".join(lines)))

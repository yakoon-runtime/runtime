from y5n.api.data import DataRequest
from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import SOURCE_READ
from y5n.api.documents import to_text


async def run(space: NodeSpace):
    on_source = space.ports.get(SOURCE_READ)
    result = await on_source(DataRequest("system:sessions --list"))

    current_key = str(space.session.key)
    current = next((r for r in result.rows if r["key"] == current_key), None)

    if current:
        yield out(to_text(f"Session:  {current_key}"))
        yield out(
            to_text(
                f"clients={current['clients']}  homes={current['homes']}  flows={current['flows']}"
            ),
        )
    else:
        yield out(to_text(f"Session:  {current_key}"))

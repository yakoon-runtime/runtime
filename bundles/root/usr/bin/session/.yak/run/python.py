from y5n.api.data import DataRequest
from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnSourceRead
from y5n.api.projections import to_text


async def run(space: NodeSpace):
    on_source = space.ports.get(OnSourceRead)
    result = await on_source(DataRequest("system:sessions --list"))

    if not result.rows:
        yield out(to_text("No sessions."))
        return

    current_key = str(space.session.key)
    lines = []
    for r in result.rows:
        marker = "* " if r["key"] == current_key else "  "
        lines.append(
            f"{marker}{r['key']:<45} clients={r['clients']}  homes={r['homes']}  flows={r['flows']}"
        )

    yield out(to_text("Active sessions:\n" + "\n".join(lines)))

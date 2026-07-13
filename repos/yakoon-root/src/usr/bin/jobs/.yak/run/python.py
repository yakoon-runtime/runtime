from .ports import JOBS_LIST
from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text


async def run(space: NodeSpace):
    on_list = space.ports.get(JOBS_LIST)

    indexed = on_list(space.session)
    if not indexed:
        yield out(to_text("No jobs active."))
        return

    yield out(to_text("Active jobs:\n"), mode="append")

    focused = space.session.foreground_flow
    for i, f in indexed:
        label = f.node.key
        state = f.control.label(f) if f.control else "run"
        marker = "  ←" if focused and focused.id == f.id else ""

        result = to_text(f"  [{i}] {label} - {state}{marker}")
        yield out(result, mode="append")

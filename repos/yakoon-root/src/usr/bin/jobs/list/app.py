from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.documents import to_text

from .ports import JOBS_LIST


async def run(space: NodeSpace):
    on_list = space.ports.get(JOBS_LIST)

    indexed = on_list(space.session)
    if not indexed:
        yield out(to_text("No jobs active."))
        return

    yield out(to_text("Active jobs:\n"), mode="append")

    focused = space.session.foreground_flow  # type: ignore
    for i, f in indexed:
        label = f.node.key  # type: ignore
        state = f.control.label(f) if f.control else "run"  # type: ignore
        marker = "  ←" if focused and focused.id == f.id else ""  # type: ignore

        result = to_text(f"  [{i}] {label} - {state}{marker}")
        yield out(result, mode="append")

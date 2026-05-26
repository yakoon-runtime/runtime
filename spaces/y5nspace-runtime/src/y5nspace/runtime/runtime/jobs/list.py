from y5n.api.flows import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text

from .ports import OnJobsList


async def run(space: NodeSpace):

    on_list = space.ports.get(OnJobsList)

    indexed = on_list(space.session)
    if not indexed:
        yield out(to_text("No jobs active."))
        return

    yield out(to_text("Active jobs:"))

    focused = space.session.interaction_flow  # type: ignore
    for i, f in indexed:
        label = f.node.key
        state = f.control.label(f) if f.control else "run"
        marker = "  ←" if focused and focused.id == f.id else ""

        result = to_text(f"[{i}] {label} - {state}{marker}\n")
        yield out(result)

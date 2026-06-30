from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text


async def run(space: NodeSpace):

    fg = space.session.foreground_flow  # type: ignore
    if not fg:
        yield out(to_text("No job in foreground."))
        return

    yield out(to_text("Job moved to background."))
    yield fg.deactivate()

from y5n.api.flows import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text


async def run(space: NodeSpace):

    if not space.session.has_foreground_flow():  # type: ignore
        yield out(to_text("No job in foreground."))
        return

    space.session.set_foreground_flow(None)  # type: ignore
    yield out(to_text("Job moved to background."))

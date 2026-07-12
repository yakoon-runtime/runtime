from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text


async def run(space: NodeSpace):
    display = space.session.get_current_path()
    if not display:
        display = space.session.get_data("fs:root", "/")
    yield out(to_text(display))

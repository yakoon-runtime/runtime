from pathlib import Path

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    raw = space.session.get_data("fs:cwd", str(Path.home() / ".yakoon" / "test"))
    yield out(to_text(raw))

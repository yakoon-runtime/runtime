from pathlib import Path

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text


async def run(space: NodeSpace):
    raw = space.session.get_data("fs:cwd")
    if not raw:
        raw = space.session.get_data("fs:root", str(Path.home() / ".yakoon"))
    yield out(to_text(raw))

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ports import GREET
from y5n.api.dsl import out, view
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT


async def run(space: NodeSpace):

    greet = space.ports.get(GREET)
    result = greet("John", "Doe")

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"greeting": result},
    )

    yield view(clear=True)
    yield out(projection)

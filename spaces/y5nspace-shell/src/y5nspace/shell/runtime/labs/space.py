from y5n.api.nodes import Node

from .demos.space import demos
from .dsl.space import dsl
from .patterns.space import patterns

# ----------------------------------
# LABS
# ----------------------------------

labs = Node(
    key="labs",
    name="labs",
    anonymous=True,
    navigable=True,
    resolvable=False,
)

labs.mount(dsl)
labs.mount(patterns)
labs.mount(demos)

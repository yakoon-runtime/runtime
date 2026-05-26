from y5n.api.nodes import Node

from .dsl.space import dsl

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

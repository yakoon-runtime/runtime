from y5n.api.nodes import Node, NodeScope

from .actors import on_version, on_welcome
from .on_setup import on_setup

# ----------------------------------
# RUNTIME
# ----------------------------------

runtime = Node(
    key="runtime",
    name="Runtime",
    setup=on_setup,
    anonymous=True,
)


# ----------------------------------
# WELCOME
# ----------------------------------

runtime.add(
    Node(
        key="welcome",
        run=on_welcome,
        anonymous=True,
        scope=NodeScope.NODE,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# VERSION
# ----------------------------------

runtime.add(
    Node(
        key="version",
        run=on_version,
        anonymous=True,
        scope=NodeScope.NODE,
        resolvable=True,
        navigable=False,
    )
)
# runtime.mount(system)

from y5n.api.nodes import Node, NodeScope

from .form import run as form

# ----------------------------------
# PATTERNS
# ----------------------------------

patterns = Node(
    key="patterns",
    anonymous=True,
    navigable=True,
    resolvable=False,
)

# ----------------------------------
# RECEIVE
# ----------------------------------

patterns.add(
    Node(
        key="form",
        run=form,
        anonymous=True,
        resolvable=True,
        navigable=False,
        scope=NodeScope.GLOBAL,
    )
)

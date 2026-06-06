from y5n.api.nodes import Node, NodeScope

from .pdf import run as pdf

# ----------------------------------
# DEMOS
# ----------------------------------

demos = Node(
    key="demos",
    anonymous=True,
    navigable=True,
    resolvable=False,
)

# ----------------------------------
# PDF
# ----------------------------------

demos.add(
    Node(
        key="pdf",
        run=pdf,
        anonymous=True,
        resolvable=True,
        navigable=False,
        scope=NodeScope.GLOBAL,
    )
)

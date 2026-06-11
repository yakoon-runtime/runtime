from y5n.api.nodes import Node
from y5n.base.nodes.types import NodeScope

from .agent import run as agent
from .form import run as form
from .setup import setup

# ----------------------------------
# PATTERNS
# ----------------------------------

patterns = Node(
    key="patterns",
    anonymous=True,
    navigable=True,
    resolvable=False,
    setup=setup,
)

# ----------------------------------
# FORM
# ----------------------------------

patterns.add(
    Node(
        key="form",
        run=form,
        anonymous=True,
        resolvable=True,
        navigable=False,
    )
)

# ----------------------------------
# AGENT (Demo)
# ----------------------------------

patterns.add(
    Node(
        key="agent",
        run=agent,
        anonymous=True,
        resolvable=True,
        navigable=False,
        scope=NodeScope.GLOBAL,
    )
)

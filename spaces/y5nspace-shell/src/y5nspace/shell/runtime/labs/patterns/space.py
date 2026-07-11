from y5n.api.nodes import Node


from .agent import run as agent
from .dlg import run as dlg
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
# DLG (Dialog / field by field)
# ----------------------------------

patterns.add(
    Node(
        key="dlg",
        run=dlg,
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
        anonymous=True,  # GLOBAL
        resolvable=True,
        navigable=False,
    )
)

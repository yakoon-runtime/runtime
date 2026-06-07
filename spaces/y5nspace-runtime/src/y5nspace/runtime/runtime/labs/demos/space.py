from y5n.api.nodes import Node, NodeScope

from .llm import run as llm
from .pdf import run as pdf
from .setup import setup

# ----------------------------------
# DEMOS
# ----------------------------------

demos = Node(
    key="demos",
    setup=setup,
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
    )
)

# ----------------------------------
# LLM
# ----------------------------------

demos.add(
    Node(
        key="llm",
        run=llm,
        anonymous=True,
        resolvable=True,
        navigable=False,
        scope=NodeScope.GLOBAL,
    )
)

from y5n.base.projection.model import PreBlock

from ..core import extract_text


def map_pre(mapper, node):
    return PreBlock(
        type="pre",
        id=None,
        code=extract_text(node),
        language=node.attrs.get("language"),
    )

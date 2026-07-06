from y5n.base.projection.model import CodeBlock

from ..core import extract_text


def map_code_block(mapper, node):
    return CodeBlock(
        type="code",
        id=None,
        code=extract_text(node),
        language=node.attrs.get("language"),
    )

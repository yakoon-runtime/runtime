from y5n.base.projection.model import InlineUnderline


def map_underline(mapper, node):
    children = mapper._map_inline(node.children)

    return InlineUnderline(
        children=children,
    )

from yakoon.base.projection.model import InlineCode


def map_code(mapper, node):
    children = mapper._map_inline(node.children)
    return InlineCode(children=children)

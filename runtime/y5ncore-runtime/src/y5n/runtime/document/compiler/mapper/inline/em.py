from y5n.base.document.model import InlineEm


def map_em(mapper, node):
    children = mapper._map_inline(node.children)
    return InlineEm(children=children)

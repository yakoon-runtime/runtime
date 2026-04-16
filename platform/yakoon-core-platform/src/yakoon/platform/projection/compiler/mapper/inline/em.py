from yakoon.base.projection.model.inline import InlineEm


def map_em(mapper, node):
    children = mapper._map_inline(node.children)
    return InlineEm(children=children)

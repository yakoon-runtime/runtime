from yakoon.base.projection.model.inline import InlineStrong


def map_strong(mapper, node):
    children = mapper._map_inline(node.children)
    return InlineStrong(children=children)

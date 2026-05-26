from y5n.base.projection.model import InlineArg


def map_arg(mapper, node):
    children = mapper._map_inline(node.children)
    return InlineArg(children=children)

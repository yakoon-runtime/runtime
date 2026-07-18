from y5n.base.document.model import StackBlock


def map_stack(mapper, node):
    blocks = mapper._map_nodes(node.children)

    return StackBlock(
        id=None,
        blocks=blocks,
    )

from y5n.base.projection.model import FlowBlock


def map_flow(mapper, node):
    blocks = mapper._map_nodes(node.children)

    return FlowBlock(
        id=None,
        blocks=blocks,
    )

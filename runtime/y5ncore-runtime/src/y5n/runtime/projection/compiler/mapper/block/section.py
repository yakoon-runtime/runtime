from y5n.base.projection.model import SectionBlock


def map_section(mapper, node):
    blocks = mapper._map_nodes(node.children)

    return SectionBlock(
        id=None,
        blocks=blocks,
    )

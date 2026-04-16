from yakoon.base.projection.model import HeadingBlock


def map_heading(level: int):
    def _map(mapper, node):
        inline = mapper._map_inline(node.children)

        return HeadingBlock(
            level=level,
            id=None,
            text=inline,
        )

    return _map

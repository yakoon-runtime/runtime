from yakoon.base.projection.model import InlineSpace


def map_space(mapper, node):
    count = int(node.attrs.get("count", 1))

    return InlineSpace(
        count=count,
    )

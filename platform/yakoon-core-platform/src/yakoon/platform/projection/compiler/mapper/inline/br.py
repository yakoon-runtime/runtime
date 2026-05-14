from yakoon.base.projection.model.inline import InlineBreak


def map_br(mapper, node):

    count = int(node.attrs.get("count", 1))

    return InlineBreak(
        count=count,
    )

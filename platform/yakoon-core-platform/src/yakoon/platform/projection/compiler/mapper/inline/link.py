from yakoon.base.projection.model.inline import InlineLink


def map_link(mapper, node):
    href = node.attrs.get("href")
    if not href:
        raise ValueError("<link> requires href")

    children = mapper._map_inline(node.children)

    return InlineLink(
        href=href,
        children=children,
    )

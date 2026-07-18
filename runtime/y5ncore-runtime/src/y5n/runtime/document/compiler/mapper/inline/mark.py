from y5n.base.document.model import InlineMark


def map_mark(mapper, node):
    children = mapper._map_inline(node.children)

    variant = node.attrs.get("type")  # optional

    return InlineMark(
        variant=variant,
        children=children,
    )

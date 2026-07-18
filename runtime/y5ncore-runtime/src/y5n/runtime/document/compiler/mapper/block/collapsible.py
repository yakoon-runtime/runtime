from y5n.base.document.model import CollapsibleBlock, InlineText


def map_collapsible(mapper, node):
    title_text = node.attrs.get("title", "")
    title = [InlineText(text=title_text)] if title_text else []
    expanded = node.attrs.get("expanded", None) in ("true", "1", "")

    blocks = mapper._map_nodes(node.children)

    return CollapsibleBlock(
        id=None,
        title=title,
        expanded=expanded,
        blocks=blocks,
    )

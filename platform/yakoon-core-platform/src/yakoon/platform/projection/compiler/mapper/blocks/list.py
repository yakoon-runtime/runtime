from yakoon.base.projection.model import ListBlock, ListItemBlock

from ..core import is_element, is_whitespace


def map_list(mapper, node):
    items: list[ListItemBlock] = []

    for child in node.children:
        if is_whitespace(child):
            continue

        if not is_element(child, "item"):
            raise ValueError("<list> can only contain <item>")

        items.append(map_list_item(mapper, child))

    return ListBlock(
        type="list",
        id=None,
        items=items,
    )


def map_list_item(mapper, node):
    inline = mapper._map_inline(node.children)

    return ListItemBlock(
        type="list_item",
        id=None,
        text=inline,
        blocks=None,
    )

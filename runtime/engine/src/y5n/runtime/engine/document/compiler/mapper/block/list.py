from ..core import is_element, is_whitespace


def map_list(mapper, node):
    items = []

    for child in node.children:
        if is_whitespace(child):
            continue

        if not is_element(child, "item"):
            raise ValueError("<list> can only contain <item>")

        items.append(map_list_item(mapper, child))

    return {"type": "list", "items": items}


def map_list_item(mapper, node):
    inline = mapper._map_inline(node.children)

    return {"type": "list_item", "text": inline}

def map_select(mapper, node):
    value = node.attrs.get("value")
    if not value:
        raise ValueError("<select> requires value")

    children = mapper._map_inline(node.children)

    if not children:
        raise ValueError("<select> requires label")

    return {"type": "select", "value": value, "children": children}

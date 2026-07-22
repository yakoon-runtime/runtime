def map_mark(mapper, node):
    children = mapper._map_inline(node.children)

    variant = node.attrs.get("type")  # optional

    return {"type": "mark", "variant": variant, "children": children}

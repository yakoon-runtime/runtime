def map_underline(mapper, node):
    children = mapper._map_inline(node.children)

    return {"type": "underline", "children": children}

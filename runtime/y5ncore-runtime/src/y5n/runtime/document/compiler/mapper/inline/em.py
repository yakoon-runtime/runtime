def map_em(mapper, node):
    children = mapper._map_inline(node.children)
    return {"type": "em", "children": children}

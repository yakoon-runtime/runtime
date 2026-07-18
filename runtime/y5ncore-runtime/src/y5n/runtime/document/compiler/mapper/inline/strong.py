def map_strong(mapper, node):
    children = mapper._map_inline(node.children)
    return {"type": "strong", "children": children}

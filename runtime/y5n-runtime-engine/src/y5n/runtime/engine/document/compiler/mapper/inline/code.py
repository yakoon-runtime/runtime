def map_code(mapper, node):
    children = mapper._map_inline(node.children)
    return {"type": "code", "children": children}

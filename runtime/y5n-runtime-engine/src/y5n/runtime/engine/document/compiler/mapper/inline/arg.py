def map_arg(mapper, node):
    children = mapper._map_inline(node.children)
    return {"type": "arg", "children": children}

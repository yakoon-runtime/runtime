def map_stack(mapper, node):
    blocks = mapper._map_nodes(node.children)

    return {"type": "stack", "blocks": blocks}

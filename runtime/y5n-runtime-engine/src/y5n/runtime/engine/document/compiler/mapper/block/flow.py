def map_flow(mapper, node):
    blocks = mapper._map_nodes(node.children)

    return {"type": "flow", "blocks": blocks}

def map_section(mapper, node):
    blocks = mapper._map_nodes(node.children)

    return {"type": "section", "blocks": blocks}

def map_space(mapper, node):
    count = int(node.attrs.get("count", 1))

    return {"type": "space", "count": count}

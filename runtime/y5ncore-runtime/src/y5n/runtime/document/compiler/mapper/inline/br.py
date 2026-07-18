def map_br(mapper, node):

    count = int(node.attrs.get("count", 1))

    return {"type": "break", "count": count}

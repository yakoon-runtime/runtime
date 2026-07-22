def map_heading(level: int):
    def _map(mapper, node):
        inline = mapper._map_inline(node.children)

        return {"type": "heading", "level": level, "text": inline}

    return _map

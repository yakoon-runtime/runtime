def map_paragraph(mapper, node):
    inline = mapper._map_inline(node.children)

    return {"type": "paragraph", "text": inline}

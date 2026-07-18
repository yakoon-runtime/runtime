def map_link(mapper, node):
    href = node.attrs.get("href")
    if not href:
        raise ValueError("<link> requires href")

    children = mapper._map_inline(node.children)

    return {"type": "link", "href": href, "children": children}

from ..core import extract_text


def map_pre(mapper, node):
    return {
        "type": "pre",
        "code": extract_text(node),
        "language": node.attrs.get("language"),
    }

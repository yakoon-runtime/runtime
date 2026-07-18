from y5n.base.document.model import ImageBlock


def map_image(mapper, node):
    ref = node.attrs.get("ref")
    if not ref:
        raise ValueError("<image> requires ref")

    alt = node.attrs.get("alt")

    return ImageBlock(
        src=None,
        ref=ref,
        alt=alt,
    )

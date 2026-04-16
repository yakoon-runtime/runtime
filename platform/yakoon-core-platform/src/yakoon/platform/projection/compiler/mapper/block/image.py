from yakoon.base.projection.model import ImageBlock


def map_image(mapper, node):
    src = node.attrs.get("src")
    if not src:
        raise ValueError("<image> requires src")

    alt = node.attrs.get("alt")

    return ImageBlock(
        src=src,
        alt=alt,
    )

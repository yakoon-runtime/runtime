from yakoon.base.projection.model import ImageBlock
from yakoon.base.resources.resource import ResourceRef


def map_image(mapper, node):
    ref = node.attrs.get("src")
    if not ref:
        raise ValueError("<image> requires src")

    alt = node.attrs.get("alt")

    return ImageBlock(
        src=ref,
        alt=alt,
    )


from dataclasses import replace
from pathlib import PurePosixPath


def resolve_assets(blocks, asset_root: ResourceRef):
    result = []

    for block in blocks:
        if isinstance(block, ImageBlock):
            # 👉 wichtig: src ist RELATIV
            full_path = str(PurePosixPath(asset_root.path) / block.src)

            new_ref = ResourceRef(
                package=asset_root.package,
                path=full_path,
            )

            new_block = replace(block, src=asset_url(new_ref))
        else:
            new_block = block

        # 👉 rekursiv
        children = new_block.children()
        if children:
            new_children = resolve_assets(children, asset_root)

            # nur wenn Block children speichert!
            if hasattr(new_block, "blocks"):
                new_block = replace(new_block, blocks=new_children)

        result.append(new_block)

    return result


def asset_url(ref: ResourceRef) -> str:
    return f"/api/assets/{ref.package}/{ref.path}"

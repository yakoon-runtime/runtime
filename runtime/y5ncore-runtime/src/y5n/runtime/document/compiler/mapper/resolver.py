from pathlib import PurePosixPath

from y5n.runtime.engine.resources import ResourceRef


class BlockResolver:
    def resolve(self, block: dict) -> dict:
        raise NotImplementedError


class ImageResolver(BlockResolver):

    def __init__(self, resource: ResourceRef):
        self.resource = resource

    def resolve(self, block: dict) -> dict:
        ref = block.get("ref", "")
        full = str(PurePosixPath(self.resource.path) / ref)
        block["src"] = f"/api/assets/{self.resource.package}/{full}"
        return block

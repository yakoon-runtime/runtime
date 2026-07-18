from dataclasses import replace
from pathlib import PurePosixPath

from y5n.base.resources import ResourceRef


class BlockResolver:
    def resolve(self, block):
        raise NotImplementedError


class ImageResolver(BlockResolver):

    def __init__(self, resource: ResourceRef):
        self.resource = resource

    def resolve(self, block):
        full = str(PurePosixPath(self.resource.path) / block.ref)

        return replace(block, src=f"/api/assets/{self.resource.package}/{full}")

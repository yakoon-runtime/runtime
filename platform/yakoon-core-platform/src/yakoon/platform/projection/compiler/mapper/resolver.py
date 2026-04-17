from dataclasses import replace
from pathlib import PurePosixPath

from yakoon.base.resources.resource import ResourceRef


class BlockResolver:
    def resolve(self, block):
        raise NotImplementedError


class ImageResolver(BlockResolver):

    def __init__(self, ref: ResourceRef):
        self._ref = ref

    def resolve(self, block):
        full = str(PurePosixPath(self._ref.path) / block.ref)

        return replace(block, src=f"/api/assets/{self._ref.package}/{full}")

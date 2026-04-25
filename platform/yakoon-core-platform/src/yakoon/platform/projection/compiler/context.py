from pydantic.dataclasses import dataclass

from yakoon.base.resources import ResourceRef


@dataclass(frozen=True, slots=True)
class ResolverContext:
    assets: ResourceRef
